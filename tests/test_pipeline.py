import json

import pytest

from trendy import image, pipeline


@pytest.fixture
def out_dir(tmp_path, monkeypatch):
    """Redirect output/ into a temp folder and stub the gallery writer for every test."""
    monkeypatch.setattr(pipeline, "output_dir_for", lambda d: _mk(tmp_path / d))
    monkeypatch.setattr(pipeline, "add_entry", lambda result: None)
    return tmp_path


def _mk(path):
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_run_calls_steps_in_order_and_writes_result(out_dir, monkeypatch):
    calls = []
    uploaded = {}

    def fake_upload_file(data, name):
        calls.append("upload_file")
        uploaded["data"], uploaded["name"] = data, name
        return "QmImg"

    monkeypatch.setattr(pipeline, "get_trends", lambda **kw: calls.append("trends") or ["A", "B", "C"])
    monkeypatch.setattr(pipeline, "generate_image", lambda p: calls.append("image") or image.placeholder_png(64, 64))
    monkeypatch.setattr(pipeline, "upload_file", fake_upload_file)
    monkeypatch.setattr(pipeline, "upload_json", lambda obj, name: calls.append("upload_json") or "QmMeta")
    monkeypatch.setattr(pipeline, "add_entry", lambda result: calls.append("gallery"))

    result = pipeline.run(run_date="2026-09-07")

    assert calls == ["trends", "image", "upload_file", "upload_json", "gallery"]
    assert result["image_uri"] == "ipfs://QmImg"
    assert result["metadata_uri"] == "ipfs://QmMeta"

    # the small JPEG is what gets pinned, not the PNG
    assert uploaded["data"].startswith(image.JPEG_MAGIC)
    assert uploaded["name"].endswith(".jpg")

    folder = out_dir / "2026-09-07"
    for name in ["trends.json", "prompt.txt", "image.png", "image.jpg", "metadata.json", "result.json"]:
        assert (folder / name).exists(), name
    assert json.loads((folder / "metadata.json").read_text())["image"] == "ipfs://QmImg"


def test_dry_run_makes_no_paid_calls_and_skips_gallery(out_dir, monkeypatch):
    def boom(*a, **k):
        raise AssertionError("should not be called in dry run")

    monkeypatch.setattr(pipeline, "generate_image", boom)
    monkeypatch.setattr(pipeline, "upload_file", boom)
    monkeypatch.setattr(pipeline, "upload_json", boom)
    monkeypatch.setattr(pipeline, "add_entry", boom)

    result = pipeline.run(run_date="2026-09-07", trends=["A", "B"], dry_run=True)
    assert result["dry_run"] is True
    assert result["image_cid"] == pipeline.DRY_RUN_IMAGE_CID
    assert (out_dir / "2026-09-07" / "image.png").read_bytes().startswith(image.PNG_MAGIC)
    assert (out_dir / "2026-09-07" / "image.jpg").read_bytes().startswith(image.JPEG_MAGIC)


def test_run_is_idempotent_per_day_unless_forced(out_dir, monkeypatch):
    counter = {"n": 0}

    def fake_trends(**kwargs):
        counter["n"] += 1
        assert kwargs["dry_run"] is True  # dry run must reach the trends step too
        return ["A"]

    monkeypatch.setattr(pipeline, "get_trends", fake_trends)

    pipeline.run(run_date="2026-09-07", dry_run=True)
    pipeline.run(run_date="2026-09-07", dry_run=True)  # skipped
    assert counter["n"] == 1

    pipeline.run(run_date="2026-09-07", dry_run=True, force=True)
    assert counter["n"] == 2
