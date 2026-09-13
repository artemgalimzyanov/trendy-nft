import json

from trendy import gallery


def _result(date, cid="Qm" + "x"):
    return {
        "date": date,
        "trends": ["A", "B"],
        "prompt": "p",
        "image_cid": cid,
        "metadata_cid": "QmMeta",
        "extra_field_not_stored": True,
    }


def test_add_entry_creates_file_with_only_gallery_fields(tmp_path):
    path = tmp_path / "docs" / "gallery.json"
    entries = gallery.add_entry(_result("2026-09-07"), path)
    assert path.exists()
    assert entries == json.loads(path.read_text())
    assert set(entries[0]) == set(gallery.FIELDS)


def test_add_entry_sorts_by_date_and_replaces_same_day(tmp_path):
    path = tmp_path / "gallery.json"
    gallery.add_entry(_result("2026-09-08", "Qm8"), path)
    gallery.add_entry(_result("2026-09-06", "Qm6"), path)
    entries = gallery.add_entry(_result("2026-09-08", "Qm8-redo"), path)

    assert [e["date"] for e in entries] == ["2026-09-06", "2026-09-08"]
    assert entries[1]["image_cid"] == "Qm8-redo"


def test_load_missing_file_is_empty(tmp_path):
    assert gallery.load(tmp_path / "nope.json") == []
