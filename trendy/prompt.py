"""Step 2a: turn trend words into an image prompt (pure function)."""

DEFAULT_STYLE = (
    "Classic British single-panel newspaper cartoon. Loose, wobbly pen-and-ink linework "
    "with soft watercolour washes on cream paper, gentle muted colours and plenty of white "
    "space. Characters are drawn as affectionate caricatures with big noses, rosy cheeks, "
    "droopy tweeds, wellies and headscarves. Warm, gently satirical English country humour, "
    "never cruel. Square panel with a thin hand-drawn border, one short witty handwritten "
    "caption in plain English beneath the drawing, and no other text"
)

TEMPLATE = (
    "A single-panel comic cartoon set in a slightly shabby English country house or its "
    "muddy grounds. An eccentric elderly aristocratic couple, surrounded by their "
    "overweight small dogs, react to today's world news with absurd, out-of-touch "
    "misunderstanding. The news topics, in order of importance: {topics}. Make the first "
    "topic the heart of the joke; hint at the others through small props, a newspaper, a "
    "television or a portrait on the wall. Show real public figures only as symbols or "
    "props, never as realistic portraits. Treat tragic events with restraint, never "
    "showing violence. Style: {style}."
)

MAX_PROMPT_CHARS = 4000


def build_prompt(trends: list[str], style: str = DEFAULT_STYLE) -> str:
    """Build a deterministic prompt from a list of trend strings."""
    cleaned = [t.strip() for t in trends if t and t.strip()]
    if not cleaned:
        raise ValueError("At least one trend is required to build a prompt")

    topics = "; ".join(cleaned)
    prompt = TEMPLATE.format(topics=topics, style=style)
    if len(prompt) > MAX_PROMPT_CHARS:
        prompt = prompt[:MAX_PROMPT_CHARS]
    return prompt
