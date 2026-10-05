"""Step 1b: turn today's topics into drawable actions for the cartoon cast.

The hero (a young boy) acts out the top story, his household acts out the next two,
and any later topics become small props. A small OpenAI text model writes the actions;
fallback_actions() is used on dry runs or if the model fails.
"""

import json
import logging

from trendy.config import openai_client

log = logging.getLogger(__name__)

HOUSEHOLD = (
    "his eccentric elderly grandparents, a weary butler, a gardener and two overweight "
    "small dogs"
)
FALLBACK_CAST = ("Grandfather", "The butler")

SCENE_MODEL = "gpt-5.4-mini"
SCENE_SYSTEM_PROMPT = (
    "You direct a gentle British single-panel comic cartoon. The recurring hero is a "
    "curious young boy who lives in a slightly shabby English country house with "
    f"{HOUSEHOLD}. Every day the household hears the world news and acts it out at home. "
    "You receive today's news topics, ranked by importance. For each topic, in the same "
    "order, write one short, concrete, drawable action of 8 to 20 words. Build it on the "
    "topic's main verb; if the topic has no verb, use the action most typical of that "
    "event (a summit is chaired, an election is voted in, a storm is weathered). "
    "Topic 1: what the boy himself does, starting with 'The boy'. "
    "Topics 2 and 3: what one other member of the household does (grandfather, "
    "grandmother, butler, gardener or the dogs), starting with who it is. "
    "Any further topic: a small prop or background detail that hints at the story. "
    "Act everything out with household objects, toys, garden things and animals. Never "
    "show real people, weapons, blood or injury; for deaths, wars and disasters the action "
    "must be quiet and caring, never a joke. No written words, signs or speech. "
    'Respond with JSON only, in the form {"actions": ["...", "..."]}.'
)


def fallback_actions(topics: list[str]) -> list[str]:
    """No-model fallback: generic actions in the same hero / household / prop pattern."""
    hero = [f"The boy acts out the news about {t} with his toys" for t in topics[:1]]
    cast = [f"{who} reacts to the news about {t}" for who, t in zip(FALLBACK_CAST, topics[1:3])]
    props = [f"a small prop hinting at {t}" for t in topics[3:]]
    return hero + cast + props


def _clean(action) -> str:
    return action.strip().rstrip(".").strip() if isinstance(action, str) else ""


def write_actions(topics: list[str], client=None) -> list[str]:
    """Ask the model for one action per topic, in order; gaps are filled from the fallback."""
    client = client or openai_client()
    response = client.chat.completions.create(
        model=SCENE_MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SCENE_SYSTEM_PROMPT},
            {"role": "user", "content": "\n".join(f"{i}. {t}" for i, t in enumerate(topics, 1))},
        ],
    )
    content = response.choices[0].message.content or ""
    raw = json.loads(content).get("actions", [])
    if not isinstance(raw, list) or not any(_clean(a) for a in raw):
        raise RuntimeError(f"Model returned no actions: {content[:200]}")
    padded = raw + [""] * len(topics)
    return [_clean(a) or fallback for a, fallback in zip(padded, fallback_actions(topics))]


def get_actions(topics: list[str], dry_run: bool = False, client=None) -> list[str]:
    """Return one action per topic: written by OpenAI, or the fallback on dry runs/failure."""
    if dry_run:
        return fallback_actions(topics)
    try:
        return write_actions(topics, client=client)
    except Exception as exc:
        log.warning("Scene model failed (%s); using fallback actions", exc)
        return fallback_actions(topics)
