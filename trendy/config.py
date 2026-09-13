"""Environment and path configuration."""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "output"

load_dotenv(ROOT / ".env")


def require_env(name: str) -> str:
    """Return the value of an environment variable or raise a clear error."""
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(
            f"Missing environment variable {name}. "
            "Copy .env.example to .env and fill it in."
        )
    return value


def output_dir_for(run_date: str) -> Path:
    """Return (and create) the output folder for a given ISO date."""
    path = OUTPUT_DIR / run_date
    path.mkdir(parents=True, exist_ok=True)
    return path
