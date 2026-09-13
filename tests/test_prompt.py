import pytest

from trendy.prompt import MAX_PROMPT_CHARS, build_prompt


def test_prompt_contains_every_trend():
    trends = ["Solar Eclipse", "World Cup", "AI"]
    prompt = build_prompt(trends)
    for t in trends:
        assert t in prompt


def test_prompt_is_deterministic_and_bounded():
    a = build_prompt(["x", "y"])
    b = build_prompt(["x", "y"])
    assert a == b
    assert len(a) <= MAX_PROMPT_CHARS


def test_prompt_truncates_very_long_input():
    prompt = build_prompt(["w" * 10_000])
    assert len(prompt) == MAX_PROMPT_CHARS


def test_prompt_rejects_empty():
    with pytest.raises(ValueError):
        build_prompt(["", "  "])
