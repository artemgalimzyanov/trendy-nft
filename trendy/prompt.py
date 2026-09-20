"""Step 2a: turn trend words into an image prompt (pure function)."""

DEFAULT_STYLE = (
    "Editorial surrealist illustrations that transform each news story into a symbolic "
    "visual narrative. Combine recognizable people, places, objects, and cultural "
    "references in unexpected but coherent compositions. Use bold shapes, expressive "
    "gestures, selective exaggeration, and a refined magazine-art aesthetic. Rich but "
    "controlled colors, dramatic perspective, and subtle visual metaphors should create "
    "images that feel intelligent, memorable, and immediately connected to the story"
)

TEMPLATE = (
    "A single striking artwork that visually blends these trending topics of the day "
    "into one coherent scene: {topics}. Style: {style}."
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
