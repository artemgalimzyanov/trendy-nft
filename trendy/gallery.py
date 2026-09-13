"""Step 5: keep docs/gallery.json up to date for the static grid page."""

import json
from pathlib import Path

from trendy.config import ROOT

DOCS_DIR = ROOT / "docs"
GALLERY_PATH = DOCS_DIR / "gallery.json"
FIELDS = ("date", "trends", "prompt", "image_cid", "metadata_cid")


def load(path: Path = GALLERY_PATH) -> list[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text() or "[]")


def add_entry(result: dict, path: Path = GALLERY_PATH) -> list[dict]:
    """Insert or replace the entry for result['date'], keep the list sorted by date."""
    entries = [e for e in load(path) if e.get("date") != result["date"]]
    entries.append({key: result[key] for key in FIELDS})
    entries.sort(key=lambda e: e["date"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(entries, indent=2, ensure_ascii=False) + "\n")
    return entries
