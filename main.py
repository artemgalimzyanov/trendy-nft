"""Trendy CLI: run each pipeline step on its own, or the whole thing.

Examples:
  python main.py trends
  python main.py prompt --trends "a,b,c"
  python main.py image --trends "a,b,c" [--dry-run]
  python main.py metadata --trends "a,b,c" --image-uri ipfs://CID
  python main.py upload --file output/2026-09-07/image.png
  python main.py run [--dry-run] [--force]
  python main.py serve
"""

import argparse
import json
import logging
import sys
from pathlib import Path

from trendy import gallery, image, metadata, pipeline, prompt, storage, trends
from trendy.config import output_dir_for


def _split_trends(value: str | None) -> list[str] | None:
    if not value:
        return None
    return [t.strip() for t in value.split(",") if t.strip()]


def cmd_trends(args) -> int:
    result = trends.get_trends(n=args.n, source=args.source, geo=args.geo, dry_run=args.dry_run)
    out = output_dir_for(pipeline.today()) / "trends.json"
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    for t in result:
        print(t)
    print(f"\nSaved to {out}", file=sys.stderr)
    return 0


def cmd_prompt(args) -> int:
    print(prompt.build_prompt(_split_trends(args.trends)))
    return 0


def cmd_image(args) -> int:
    text = args.prompt or prompt.build_prompt(_split_trends(args.trends))
    png = image.placeholder_png() if args.dry_run else image.generate_image(text)
    out = Path(args.out) if args.out else output_dir_for(pipeline.today()) / "image.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(png)
    jpg = out.with_suffix(".jpg")
    jpg.write_bytes(image.shrink_to_jpeg(png))
    print(f"{out}  (full size PNG)")
    print(f"{jpg}  ({image.PIN_SIZE}x{image.PIN_SIZE} JPEG, this one gets pinned)")
    return 0


def cmd_serve(args) -> int:
    import http.server
    from functools import partial

    handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(gallery.DOCS_DIR))
    print(f"Serving {gallery.DOCS_DIR} at http://localhost:{args.port}  (Ctrl+C to stop)")
    http.server.ThreadingHTTPServer(("", args.port), handler).serve_forever()
    return 0


def cmd_metadata(args) -> int:
    data = metadata.build_metadata(
        _split_trends(args.trends), args.image_uri, args.date or pipeline.today(), args.prompt or ""
    )
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return 0


def cmd_upload(args) -> int:
    path = Path(args.file)
    if path.suffix == ".json":
        cid = storage.upload_json(json.loads(path.read_text()), path.name)
    else:
        cid = storage.upload_file(path.read_bytes(), path.name)
    print(f"CID: {cid}")
    print(f"URI: {storage.ipfs_uri(cid)}")
    print(f"URL: {storage.gateway_url(cid)}")
    return 0


def cmd_run(args) -> int:
    result = pipeline.run(
        run_date=args.date,
        n=args.n,
        source=args.source,
        geo=args.geo,
        trends=_split_trends(args.trends),
        dry_run=args.dry_run,
        force=args.force,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Trendy: trends -> AI image -> IPFS")
    parser.add_argument("-v", "--verbose", action="store_true", help="debug logging")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("trends", help="fetch today's top trends")
    p.add_argument("--n", type=int, default=trends.DEFAULT_COUNT, help="how many trends")
    p.add_argument("--source", choices=["news", "google"], default="news",
                   help="news = world headlines distilled by OpenAI (default); google = Google Trends")
    p.add_argument("--geo", default=trends.DEFAULT_GEO, help='google source only, e.g. "US,GB,IN"')
    p.add_argument("--dry-run", action="store_true", help="news source: skip the model, use raw headlines")
    p.set_defaults(func=cmd_trends)

    p = sub.add_parser("prompt", help="build the image prompt from trends")
    p.add_argument("--trends", required=True, help='comma-separated, e.g. "a,b,c"')
    p.set_defaults(func=cmd_prompt)

    p = sub.add_parser("image", help="generate an image (OpenAI)")
    p.add_argument("--trends", help="comma-separated trends (builds the prompt)")
    p.add_argument("--prompt", help="use this exact prompt instead")
    p.add_argument("--out", help="output PNG path (default output/<date>/image.png)")
    p.add_argument("--dry-run", action="store_true", help="write a placeholder PNG, no API call")
    p.set_defaults(func=cmd_image)

    p = sub.add_parser("metadata", help="build ERC-721 metadata JSON")
    p.add_argument("--trends", required=True)
    p.add_argument("--image-uri", required=True, help="e.g. ipfs://CID")
    p.add_argument("--date", help="ISO date (default today)")
    p.add_argument("--prompt", help="prompt to record in properties")
    p.set_defaults(func=cmd_metadata)

    p = sub.add_parser("upload", help="upload a file or .json to IPFS via Pinata")
    p.add_argument("--file", required=True)
    p.set_defaults(func=cmd_upload)

    p = sub.add_parser("run", help="run the whole pipeline")
    p.add_argument("--date", help="ISO date (default today)")
    p.add_argument("--n", type=int, default=trends.DEFAULT_COUNT, help="how many trends")
    p.add_argument("--source", choices=["news", "google"], default="news")
    p.add_argument("--geo", default=trends.DEFAULT_GEO, help='google source only, e.g. "US,GB,IN"')
    p.add_argument("--trends", help="skip fetching; use these comma-separated trends")
    p.add_argument("--dry-run", action="store_true", help="no paid API calls")
    p.add_argument("--force", action="store_true", help="redo even if today's result exists")
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("serve", help="preview the gallery page locally")
    p.add_argument("--port", type=int, default=8000)
    p.set_defaults(func=cmd_serve)

    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )
    if args.command == "image" and not args.prompt and not args.trends:
        print("error: image needs --trends or --prompt", file=sys.stderr)
        return 2
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
