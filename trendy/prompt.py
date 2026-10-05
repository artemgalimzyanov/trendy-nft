"""Step 2a: turn trends and their actions into an image prompt (pure function)."""

from trendy.scene import HOUSEHOLD, fallback_actions

DEFAULT_STYLE = (
    "Classic British single-panel newspaper cartoon. Loose, wobbly pen-and-ink linework "
    "with soft watercolour washes on cream paper, gentle muted colours and plenty of white "
    "space. Characters are drawn as affectionate caricatures with big noses, rosy cheeks, "
    "droopy tweeds, wellies and headscarves. Warm, gently satirical English country humour, "
    "never cruel. Square panel with a thin hand-drawn border, one short witty handwritten "
    "caption in plain English beneath the drawing, and no other text"
)

# The same boy every day, so the gallery reads as one series.
HERO = (
    "a curious boy of about eight with tousled ginger hair, an oversized green "
    "hand-knitted jumper, grey shorts and red wellies"
)

TEMPLATE = (
    "A single-panel comic cartoon set in a slightly shabby English country house or its "
    "muddy grounds. The hero is {hero}. He lives there with {household}, and today the "
    "whole household is acting out the world news: {topics}. {scene} Each action should "
    "read at a glance and be funny in a gentle, innocent way. Show real public figures "
    "only as symbols or props, never as realistic portraits. Treat tragic events with "
    "restraint, never showing violence. Style: {style}."
)


def _scene(actions: list[str]) -> str:
    """Boy in the centre, household around him, the rest as props (roles as in scene.py)."""
    parts = [f"In the centre: {actions[0]}."]
    if actions[1:3]:
        parts.append(f"Around him: {'; '.join(actions[1:3])}.")
    if actions[3:]:
        parts.append(f"Small background details: {'; '.join(actions[3:])}.")
    return " ".join(parts)


def build_prompt(
    trends: list[str], actions: list[str] | None = None, style: str = DEFAULT_STYLE
) -> str:
    """Build a deterministic prompt from trends and one action per trend.

    Without actions the generic fallback actions are used, so this stays free and offline.
    """
    cleaned = [t.strip() for t in trends if t and t.strip()]
    if not cleaned:
        raise ValueError("At least one trend is required to build a prompt")

    return TEMPLATE.format(
        hero=HERO,
        household=HOUSEHOLD,
        topics="; ".join(cleaned),
        scene=_scene(actions or fallback_actions(cleaned)),
        style=style,
    )
