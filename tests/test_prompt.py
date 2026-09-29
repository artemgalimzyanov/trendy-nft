import pytest

from trendy.prompt import HERO, MAX_PROMPT_CHARS, build_prompt


def test_prompt_contains_every_trend():
    trends = ["Solar Eclipse", "World Cup", "AI"]
    prompt = build_prompt(trends)
    for t in trends:
        assert t in prompt


def test_prompt_places_boy_household_and_props():
    actions = ["The boy crowns the cat", "Grandmother votes", "The dogs play football", "a tiny tariff notice"]
    prompt = build_prompt(["A", "B", "C", "D"], actions)
    assert HERO in prompt
    assert "In the centre: The boy crowns the cat." in prompt
    assert "Around him: Grandmother votes; The dogs play football." in prompt
    assert "Small background details: a tiny tariff notice." in prompt


def test_prompt_without_actions_uses_fallback_and_skips_empty_groups():
    prompt = build_prompt(["Royal funeral"])
    assert "In the centre: The boy acts out the news about Royal funeral" in prompt
    assert "Around him" not in prompt
    assert "background details" not in prompt


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
