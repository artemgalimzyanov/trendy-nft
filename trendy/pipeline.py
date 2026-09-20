"""Step 4: chain all steps into one daily run."""

import json
import logging
from datetime import date

from trendy.config import output_dir_for
from trendy.gallery import add_entry
from trendy.image import generate_image, placeholder_png, shrink_to_jpeg
from trendy.metadata import build_metadata
from trendy.prompt import build_prompt
from trendy.storage import gateway_url, ipfs_uri, upload_file, upload_json
from trendy.trends import DEFAULT_COUNT, get_trends

log = logging.getLogger(__name__)

DRY_RUN_IMAGE_CID = "dry-run-image-cid"
DRY_RUN_METADATA_CID = "dry-run-metadata-cid"


def today() -> str:
    return date.today().isoformat()


def run(
    run_date: str | None = None,
    n: int = DEFAULT_COUNT,
    trends: list[str] | None = None,
    dry_run: bool = False,
    force: bool = False,
) -> dict:
    """Run trends -> prompt -> image -> shrink -> upload -> metadata -> upload -> gallery.

    Every intermediate artefact is written to output/<date>/.
    With dry_run=True no paid API is called (headline fallback instead of the topic
    model, placeholder image, fake CIDs) and docs/gallery.json is left untouched.
    """
    run_date = run_date or today()
    out = output_dir_for(run_date)
    result_path = out / "result.json"

    if result_path.exists() and not force:
        log.info("Run for %s already exists; use force=True to redo", run_date)
        return json.loads(result_path.read_text())

    # 1. trends
    trends = trends or get_trends(n=n, dry_run=dry_run)
    (out / "trends.json").write_text(json.dumps(trends, indent=2, ensure_ascii=False))
    log.info("Trends: %s", trends)

    # 2. prompt + image (full-size PNG kept locally, small JPEG is what gets pinned)
    prompt = build_prompt(trends)
    (out / "prompt.txt").write_text(prompt)
    png = placeholder_png() if dry_run else generate_image(prompt)
    (out / "image.png").write_bytes(png)
    jpeg = shrink_to_jpeg(png)
    jpeg_path = out / "image.jpg"
    jpeg_path.write_bytes(jpeg)
    log.info("Image written to %s (%d KB pinned version)", jpeg_path, len(jpeg) // 1024)

    # 3. upload JPEG, build + upload metadata
    image_cid = DRY_RUN_IMAGE_CID if dry_run else upload_file(jpeg, f"trendy-{run_date}.jpg")
    metadata = build_metadata(trends, ipfs_uri(image_cid), run_date, prompt)
    (out / "metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False))
    metadata_cid = (
        DRY_RUN_METADATA_CID if dry_run else upload_json(metadata, f"trendy-{run_date}.json")
    )

    result = {
        "date": run_date,
        "dry_run": dry_run,
        "trends": trends,
        "prompt": prompt,
        "image_cid": image_cid,
        "image_uri": ipfs_uri(image_cid),
        "image_url": gateway_url(image_cid),
        "metadata_cid": metadata_cid,
        "metadata_uri": ipfs_uri(metadata_cid),
        "metadata_url": gateway_url(metadata_cid),
    }
    result_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))

    # 4. gallery data for the static page
    if not dry_run:
        add_entry(result)
        log.info("Gallery updated")

    log.info("Done: %s", result_path)
    return result
