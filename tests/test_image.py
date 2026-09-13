import base64
from types import SimpleNamespace

from trendy import image

FAKE_PNG = image.PNG_MAGIC + b"fake-body"


class FakeImages:
    def __init__(self):
        self.calls = []

    def generate(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(data=[SimpleNamespace(b64_json=base64.b64encode(FAKE_PNG).decode())])


class FakeClient:
    def __init__(self):
        self.images = FakeImages()


def test_generate_image_decodes_png_from_client():
    client = FakeClient()
    png = image.generate_image("a prompt", client=client)
    assert png == FAKE_PNG
    assert client.images.calls[0]["prompt"] == "a prompt"
    assert client.images.calls[0]["model"] == image.MODEL


def test_shrink_to_jpeg_produces_square_jpeg():
    from io import BytesIO

    from PIL import Image

    png = image.placeholder_png(width=1024, height=1024)
    jpeg = image.shrink_to_jpeg(png)

    assert jpeg.startswith(image.JPEG_MAGIC)
    with Image.open(BytesIO(jpeg)) as im:
        assert im.format == "JPEG"
        assert im.size == (image.PIN_SIZE, image.PIN_SIZE)
    assert len(jpeg) < len(png)


def test_placeholder_png_is_valid_png_without_any_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    png = image.placeholder_png(width=4, height=4)
    assert png.startswith(image.PNG_MAGIC)
    assert b"IHDR" in png and b"IDAT" in png and png.endswith(b"IEND\xaeB`\x82")
