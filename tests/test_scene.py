import json
from types import SimpleNamespace

import pytest

from trendy import scene

TOPICS = ["Royal funeral", "Climate summit", "Cup final", "Tariff row", "Moon landing"]


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


def test_fallback_actions_hero_then_household_then_props():
    actions = scene.fallback_actions(TOPICS)
    assert len(actions) == len(TOPICS)
    assert actions[0].startswith("The boy") and "Royal funeral" in actions[0]
    assert actions[1].startswith("Grandfather") and "Climate summit" in actions[1]
    assert actions[2].startswith("The butler") and "Cup final" in actions[2]
    assert all(a.startswith("a small prop") for a in actions[3:])


def test_write_actions_sends_ranked_topics_and_cleans_answer():
    client = FakeClient(json.dumps({"actions": ["The boy crowns the cat.", "  Grandmother votes  "]}))

    actions = scene.write_actions(TOPICS[:2], client=client)

    assert actions == ["The boy crowns the cat", "Grandmother votes"]
    call = client.chat.completions.calls[0]
    assert call["model"] == scene.SCENE_MODEL
    assert call["response_format"] == {"type": "json_object"}
    assert call["messages"][1]["content"] == "1. Royal funeral\n2. Climate summit"


def test_write_actions_fills_gaps_from_fallback_and_caps_to_topic_count():
    fallback = scene.fallback_actions(TOPICS[:3])

    short = scene.write_actions(TOPICS[:3], client=FakeClient('{"actions": ["The boy salutes", ""]}'))
    assert short == ["The boy salutes", fallback[1], fallback[2]]

    long = scene.write_actions(TOPICS[:2], client=FakeClient('{"actions": ["a", "b", "c", "d"]}'))
    assert long == ["a", "b"]


def test_write_actions_raises_on_empty_answer():
    with pytest.raises(RuntimeError):
        scene.write_actions(TOPICS, client=FakeClient('{"actions": []}'))


def test_get_actions_dry_run_never_calls_model(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert scene.get_actions(TOPICS, dry_run=True) == scene.fallback_actions(TOPICS)


def test_get_actions_falls_back_when_model_fails():
    class Broken:
        chat = SimpleNamespace(completions=SimpleNamespace(create=lambda **k: 1 / 0))

    assert scene.get_actions(TOPICS, client=Broken()) == scene.fallback_actions(TOPICS)
