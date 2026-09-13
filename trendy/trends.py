"""Step 1: today's top trends.

Default source "news": headlines from world news outlets, distilled into the
N most widely covered global topics by a small OpenAI text model.
Alternative source "google": Google Trends daily RSS for one or more countries,
sorted by search traffic.
"""

import json
import logging
import re

import feedparser
import requests

from trendy.config import require_env

log = logging.getLogger(__name__)

DEFAULT_COUNT = 5
USER_AGENT = "trendy-nft/0.1 (+https://github.com)"
TIMEOUT = 15

# --- news source -------------------------------------------------------------

NEWS_FEEDS = {
    "BBC World": "https://feeds.bbci.co.uk/news/world/rss.xml",
    "CNN World": "http://rss.cnn.com/rss/edition_world.rss",
    "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
    "The Guardian World": "https://www.theguardian.com/world/rss",
    "DW": "https://rss.dw.com/rdf/rss-en-all",
    "France 24": "https://www.france24.com/en/rss",
    "CNA Singapore": "https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml",
    "Times of India": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
    "NYT World": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "SCMP": "https://www.scmp.com/rss/91/feed",
}
HEADLINES_PER_FEED = 15

TOPIC_MODEL = "gpt-5.4-mini"
TOPIC_SYSTEM_PROMPT = (
    "You are a world news editor. You receive today's top headlines from several "
    "international outlets. Identify the {n} most widely covered global news topics of "
    "the day, ranked by how many different outlets cover them. Each topic must be a short "
    "English phrase of 2 to 6 words naming the concrete event, person or subject "
    "(for example 'Norway state funeral for King Harald'), not a broad category. "
    "No duplicates, no near-duplicates. "
    'Respond with JSON only, in the form {{"topics": ["...", "..."]}}.'
)

# --- google trends source ----------------------------------------------------

GOOGLE_TRENDS_RSS = "https://trends.google.com/trending/rss?geo={geo}"
DEFAULT_GEO = "US"

# kept for the fallback path
NEWS_RSS = NEWS_FEEDS["BBC World"]


# --- shared helpers ----------------------------------------------------------


def _fetch_feed(url: str) -> str:
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
    response.raise_for_status()
    return response.text


def parse_titles(xml_text: str) -> list[str]:
    """Extract entry titles from RSS/Atom XML, in feed order."""
    return [t for t, _ in parse_entries(xml_text)]


def parse_entries(xml_text: str) -> list[tuple[str, int]]:
    """Extract (title, approx_traffic) pairs; traffic is 0 when the feed has none."""
    feed = feedparser.parse(xml_text)
    entries = []
    for entry in feed.entries:
        title = (getattr(entry, "title", "") or "").strip()
        if title:
            entries.append((title, _parse_traffic(entry.get("ht_approx_traffic"))))
    return entries


def _parse_traffic(value) -> int:
    digits = re.sub(r"[^\d]", "", str(value or ""))
    return int(digits) if digits else 0


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result = []
    for item in items:
        key = item.strip().lower()
        if key and key not in seen:
            seen.add(key)
            result.append(item.strip())
    return result


# --- news: fetch + distil ----------------------------------------------------


def fetch_headlines(
    feeds: dict[str, str] | None = None, per_feed: int = HEADLINES_PER_FEED
) -> dict[str, list[str]]:
    """Return {outlet: [headline, ...]} for every feed that responds."""
    feeds = feeds or NEWS_FEEDS
    headlines: dict[str, list[str]] = {}
    for outlet, url in feeds.items():
        try:
            titles = parse_titles(_fetch_feed(url))[:per_feed]
        except Exception as exc:
            log.warning("Feed %s failed (%s); skipping", outlet, exc)
            continue
        if titles:
            headlines[outlet] = titles
    if not headlines:
        raise RuntimeError("No news feed responded")
    log.info("Fetched %d headlines from %d outlets", sum(map(len, headlines.values())), len(headlines))
    return headlines


def _default_client():
    from openai import OpenAI  # lazy import: dry-run and tests need no key

    return OpenAI(api_key=require_env("OPENAI_API_KEY"))


def pick_topics(headlines: dict[str, list[str]], n: int = DEFAULT_COUNT, client=None) -> list[str]:
    """Ask the model for the n most widely covered topics across the given headlines."""
    client = client or _default_client()
    user_text = "\n\n".join(
        f"## {outlet}\n" + "\n".join(f"- {h}" for h in titles) for outlet, titles in headlines.items()
    )
    response = client.chat.completions.create(
        model=TOPIC_MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": TOPIC_SYSTEM_PROMPT.format(n=n)},
            {"role": "user", "content": user_text},
        ],
    )
    content = response.choices[0].message.content or ""
    topics = json.loads(content).get("topics", [])
    topics = _dedupe([t for t in topics if isinstance(t, str)])[:n]
    if not topics:
        raise RuntimeError(f"Model returned no topics: {content[:200]}")
    return topics


def fallback_topics(headlines: dict[str, list[str]], n: int = DEFAULT_COUNT) -> list[str]:
    """No-model fallback: first headline of each outlet, round-robin, until n."""
    picked: list[str] = []
    columns = list(headlines.values())
    depth = max((len(c) for c in columns), default=0)
    for i in range(depth):
        for column in columns:
            if i < len(column):
                picked.append(column[i])
    return _dedupe(picked)[:n]


# --- google trends -----------------------------------------------------------


def fetch_google_trends(geo: str = DEFAULT_GEO) -> list[str]:
    """Daily trending searches for one or more comma-separated geos, sorted by traffic."""
    entries: list[tuple[str, int]] = []
    for code in [g.strip().upper() for g in geo.split(",") if g.strip()]:
        try:
            entries += parse_entries(_fetch_feed(GOOGLE_TRENDS_RSS.format(geo=code)))
        except Exception as exc:
            log.warning("Google Trends %s failed (%s); skipping", code, exc)
    entries.sort(key=lambda e: e[1], reverse=True)
    return _dedupe([title for title, _ in entries])


def fetch_news_headlines() -> list[str]:
    """Flat list of BBC World headlines (simple fallback)."""
    return parse_titles(_fetch_feed(NEWS_RSS))


# --- entry point -------------------------------------------------------------


def get_trends(
    n: int = DEFAULT_COUNT,
    source: str = "news",
    geo: str = DEFAULT_GEO,
    dry_run: bool = False,
    client=None,
) -> list[str]:
    """Return the top n trends.

    source="news":   world headlines distilled by OpenAI (fallback: round-robin headlines).
    source="google": Google Trends for `geo` (comma-separated codes), sorted by traffic.
    dry_run=True skips the model call and uses the fallback.
    """
    if source == "google":
        trends = fetch_google_trends(geo)[:n]
    elif source == "news":
        headlines = fetch_headlines()
        if dry_run:
            trends = fallback_topics(headlines, n)
        else:
            try:
                trends = pick_topics(headlines, n, client=client)
            except Exception as exc:
                log.warning("Topic model failed (%s); using headline fallback", exc)
                trends = fallback_topics(headlines, n)
    else:
        raise ValueError(f"Unknown source {source!r}; use 'news' or 'google'")

    if not trends:
        raise RuntimeError("No trends found from any source")
    return trends
