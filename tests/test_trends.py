import json
from types import SimpleNamespace

import pytest
import responses

from trendy import trends

GOOGLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:ht="https://trends.google.com/trending/rss">
  <channel>
    <title>Daily Search Trends</title>
    <item><title>small thing</title><ht:approx_traffic>200+</ht:approx_traffic></item>
    <item><title>Big Story</title><ht:approx_traffic>50,000+</ht:approx_traffic></item>
    <item><title>  big story </title><ht:approx_traffic>1,000+</ht:approx_traffic></item>
    <item><title>Medium Story</title><ht:approx_traffic>2,000+</ht:approx_traffic></item>
  </channel>
</rss>
"""

NEWS_A = """<?xml version="1.0"?><rss version="2.0"><channel>
<item><title>A1 headline</title></item>
<item><title>A2 headline</title></item>
</channel></rss>"""

NEWS_B = """<?xml version="1.0"?><rss version="2.0"><channel>
<item><title>B1 headline</title></item>
<item><title>B2 headline</title></item>
<item><title>B3 headline</title></item>
</channel></rss>"""

FEEDS = {"A": "https://a.example/rss", "B": "https://b.example/rss", "C": "https://c.example/rss"}


class FakeChat:
    def __init__(self, reply):
        self.reply = reply
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=self.reply))])


class FakeClient:
    def __init__(self, reply):
        self.chat = SimpleNamespace(completions=FakeChat(reply))


# --- parsing ---------------------------------------------------------------


def test_parse_entries_reads_titles_and_traffic():
    entries = trends.parse_entries(GOOGLE_RSS)
    assert entries[0] == ("small thing", 200)
    assert entries[1] == ("Big Story", 50000)


def test_parse_titles_strips():
    assert trends.parse_titles(NEWS_A) == ["A1 headline", "A2 headline"]


# --- news source ----------------------------------------------------------


@responses.activate
def test_fetch_headlines_skips_failing_feeds_and_limits_per_feed():
    responses.get(FEEDS["A"], body=NEWS_A)
    responses.get(FEEDS["B"], body=NEWS_B)
    responses.get(FEEDS["C"], status=500)
    result = trends.fetch_headlines(FEEDS, per_feed=2)
    assert result == {"A": ["A1 headline", "A2 headline"], "B": ["B1 headline", "B2 headline"]}


@responses.activate
def test_fetch_headlines_raises_when_everything_fails():
    for url in FEEDS.values():
        responses.get(url, status=500)
    with pytest.raises(RuntimeError):
        trends.fetch_headlines(FEEDS)


def test_pick_topics_sends_headlines_and_parses_json():
    client = FakeClient(json.dumps({"topics": ["Topic One", "Topic Two", "topic one", "Topic Three"]}))
    headlines = {"A": ["A1 headline"], "B": ["B1 headline"]}

    topics = trends.pick_topics(headlines, n=2, client=client)

    assert topics == ["Topic One", "Topic Two"]  # de-duplicated, capped at n
    call = client.chat.completions.calls[0]
    assert call["model"] == trends.TOPIC_MODEL
    assert call["response_format"] == {"type": "json_object"}
    user_msg = call["messages"][1]["content"]
    assert "## A" in user_msg and "A1 headline" in user_msg and "B1 headline" in user_msg


def test_pick_topics_raises_on_empty_answer():
    with pytest.raises(RuntimeError):
        trends.pick_topics({"A": ["x"]}, client=FakeClient('{"topics": []}'))


def test_fallback_topics_round_robin_across_outlets():
    headlines = {"A": ["A1", "A2"], "B": ["B1", "B2", "B3"], "C": ["C1"]}
    assert trends.fallback_topics(headlines, n=4) == ["A1", "B1", "C1", "A2"]


@responses.activate
def test_get_trends_news_uses_model(monkeypatch):
    monkeypatch.setattr(trends, "NEWS_FEEDS", {"A": FEEDS["A"]})
    responses.get(FEEDS["A"], body=NEWS_A)
    client = FakeClient('{"topics": ["Model Topic"]}')
    assert trends.get_trends(n=1, client=client) == ["Model Topic"]


@responses.activate
def test_get_trends_news_dry_run_never_calls_model(monkeypatch):
    monkeypatch.setattr(trends, "NEWS_FEEDS", {"A": FEEDS["A"]})
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    responses.get(FEEDS["A"], body=NEWS_A)
    assert trends.get_trends(n=1, dry_run=True) == ["A1 headline"]


@responses.activate
def test_get_trends_news_falls_back_when_model_fails(monkeypatch):
    monkeypatch.setattr(trends, "NEWS_FEEDS", {"A": FEEDS["A"]})
    responses.get(FEEDS["A"], body=NEWS_A)

    class Broken:
        chat = SimpleNamespace(completions=SimpleNamespace(create=lambda **k: 1 / 0))

    assert trends.get_trends(n=1, client=Broken()) == ["A1 headline"]


# --- google source --------------------------------------------------------


@responses.activate
def test_get_trends_google_sorts_by_traffic_and_dedupes():
    responses.get(trends.GOOGLE_TRENDS_RSS.format(geo="US"), body=GOOGLE_RSS)
    assert trends.get_trends(n=3, source="google", geo="US") == ["Big Story", "Medium Story", "small thing"]


@responses.activate
def test_get_trends_google_merges_multiple_geos_and_skips_failures():
    responses.get(trends.GOOGLE_TRENDS_RSS.format(geo="US"), body=GOOGLE_RSS)
    responses.get(trends.GOOGLE_TRENDS_RSS.format(geo="GB"), status=400)
    assert trends.get_trends(n=1, source="google", geo="us, gb") == ["Big Story"]


def test_get_trends_rejects_unknown_source():
    with pytest.raises(ValueError):
        trends.get_trends(source="bing")
