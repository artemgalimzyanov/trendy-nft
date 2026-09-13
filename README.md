# Trendy

Daily pipeline: **top trends → AI image → IPFS**, with NFT‑ready metadata.

```
headlines (10 world news RSS feeds) → 5 global topics (OpenAI gpt-5.4-mini) → prompt
→ image (OpenAI gpt-image-1) → 512x512 JPEG → IPFS (Pinata) → metadata.json → IPFS
→ docs/gallery.json → static grid page (GitHub Pages)
```

Trends come from BBC, CNN, Al Jazeera, The Guardian, DW, France 24, CNA, Times of India, NYT and SCMP.
A small text model picks the 5 topics covered by the most outlets. `--source google --geo US,GB,IN` switches to
Google Trends (sorted by search traffic) instead.

Only the small JPEG (~50 KB) is pinned; the full 1024x1024 PNG stays in `output/` and in the workflow artifact.

Every step is a small module, a CLI sub-command and a test file, so each can be run and checked on its own. See [PLAN.md](PLAN.md) for the build plan.

## Setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env      # then fill in OPENAI_API_KEY and PINATA_JWT
```

## Run each step

```bash
python main.py trends                                   # 1. 5 global topics from world news (OpenAI, <1 cent)
python main.py trends --dry-run                         #    same, without the model: raw headlines
python main.py trends --source google --geo US,GB,IN    #    Google Trends instead, sorted by traffic
python main.py prompt --trends "a,b,c"                  # 2a. show the image prompt
python main.py image --trends "a,b,c" --dry-run         # 2b. placeholder PNG + JPEG, free
python main.py image --trends "a,b,c"                   #     real image (OpenAI, ~$0.04)
python main.py metadata --trends "a,b,c" --image-uri ipfs://CID   # 3a. ERC-721 JSON
python main.py upload --file output/<date>/image.jpg    # 3b. pin to IPFS, prints CID + URL
python main.py run --dry-run                            # 4. whole pipeline, no paid calls
python main.py run                                      #    whole pipeline for real
python main.py serve                                    # 5. preview the grid at localhost:8000
```

Artefacts land in `output/<date>/`: `trends.json`, `prompt.txt`, `image.png` (full size), `image.jpg` (pinned), `metadata.json`, `result.json`.
A real run also adds the day to `docs/gallery.json`. A day is only run once; add `--force` to redo it.

## Gallery page

`docs/index.html` is a static page that reads `docs/gallery.json` and shows a scrollable 365-cell grid starting
at 2026-09-08 (first cell) and running forward in time. Past days without an image are empty cells, future days are
dashed placeholders that fill in as the daily run adds pictures. Click a cell for the full image, trends and IPFS links.
The start date and the IPFS gateway are constants at the top of the script in `index.html`.

Preview locally with `python main.py serve`, then open http://localhost:8000.

To publish: in the GitHub repo go to Settings → Pages → "Deploy from a branch", pick `main` and the `/docs` folder.
The daily workflow commits `docs/gallery.json` after each run, so the page updates itself.

## Tests

```bash
pytest
```

All tests run offline and need no API keys.

## Daily schedule (GitHub Actions)

1. Push this folder to a GitHub repo.
2. In the repo: Settings → Secrets and variables → Actions → add `OPENAI_API_KEY` and `PINATA_JWT`.
3. The workflow in `.github/workflows/daily.yml` runs at 09:00 UTC. Trigger it manually from the Actions tab ("Run workflow", optionally as dry run) to test.
4. Each real run commits `docs/gallery.json` back to the repo and uploads `output/` as a workflow artifact.

## Next: minting

`metadata.json` already follows the ERC‑721 schema with an `ipfs://` image. To mint, add a `mint` step that calls a simple ERC‑721 contract (e.g. on Base Sepolia testnet) with the metadata URI from `result.json`.
