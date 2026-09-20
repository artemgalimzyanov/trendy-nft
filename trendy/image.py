"""Step 2b: generate a PNG image from a prompt with the OpenAI Images API."""

import base64
import struct
import zlib
from io import BytesIO

from trendy.config import require_env

MODEL = "gpt-image-2"
DEFAULT_SIZE = "1024x1024"  # smallest size gpt-image-1 offers
DEFAULT_QUALITY = "medium"  # low | medium | high
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
JPEG_MAGIC = b"\xff\xd8"

# The version that gets pinned to IPFS: small square JPEG, ~50 KB.
PIN_SIZE = 512
JPEG_QUALITY = 85


def shrink_to_jpeg(png: bytes, size: int = PIN_SIZE, quality: int = JPEG_QUALITY) -> bytes:
    """Resize a PNG to size x size and encode it as JPEG."""
    from PIL import Image  # lazy import keeps the CLI fast for non-image commands

    with Image.open(BytesIO(png)) as im:
        im = im.convert("RGB").resize((size, size), Image.LANCZOS)
        buf = BytesIO()
        im.save(buf, format="JPEG", quality=quality, optimize=True)
    return buf.getvalue()


def _default_client():
    from openai import OpenAI  # imported lazily so tests/dry-run don't need a key

    return OpenAI(api_key=require_env("OPENAI_API_KEY"))


def generate_image(
    prompt: str,
    size: str = DEFAULT_SIZE,
    quality: str = DEFAULT_QUALITY,
    client=None,
) -> bytes:
    """Call OpenAI and return the raw PNG bytes."""
    client = client or _default_client()
    response = client.images.generate(
        model=MODEL,
        prompt=prompt,
        size=size,
        quality=quality,
        n=1,
    )
    b64 = response.data[0].b64_json
    if not b64:
        raise RuntimeError("OpenAI returned no image data")
    return base64.b64decode(b64)


def _png_chunk(tag: bytes, data: bytes) -> bytes:
    body = tag + data
    return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)


def placeholder_png(width: int = 256, height: int = 256, color=(80, 120, 200)) -> bytes:
    """A solid-colour PNG, built without any image library. Used by --dry-run."""
    row = b"\x00" + bytes(color) * width  # filter byte 0 + RGB pixels
    raw = row * height
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (
        PNG_MAGIC
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"IDAT", zlib.compress(raw))
        + _png_chunk(b"IEND", b"")
    )
