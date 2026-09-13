"""Step 2a: turn trend words into an image prompt (pure function)."""

DEFAULT_STYLE = (
    "vibrant digital illustration, surreal and dreamlike, highly detailed, "
    "cinematic lighting, no text, no letters, no watermark"
)

TEMPLATE = (
    "A single striking artwork that visually blends these trending topics of the day "
    "into one coherent scene: {topics}. Style: {style}."
)

# gpt-image-1 accepts far more, but keep prompts short and safe for any model.
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
