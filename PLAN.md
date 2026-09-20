# Trendy App – MVP build plan

## Context

`idea.md` describes a daily pipeline: pick top global trends → generate an AI image from them → store it online (decentralized) → optionally mint an NFT → run every day. The folder is empty apart from `idea.md`, so this is a greenfield build.

Decisions already made with the user:

| Decision | Choice |
|---|---|
| Stack | Python 3.11+ |
| Trend source | Free: Google Trends daily RSS feed (no key), news RSS as fallback |
| Image generation | OpenAI Images API (`gpt-image-1`), key already available |
| Storage | IPFS via Pinata (free tier, one JWT) |
| Minting | Skipped for MVP; metadata kept ERC‑721 compatible so it can be added later |
| Scheduling | GitHub Actions cron |

Guiding principle: **one small module per step, one CLI command per step, one test file per step.** Every step can be run and verified on its own before the next one is started.

## Target layout

```
trendy-nft/
  trendy/
    __init__.py
    config.py        # loads .env, exposes settings
    trends.py        # Step 1: get_trends(n=5) -> list[str]
    prompt.py        # Step 2a: build_prompt(trends) -> str  (pure function)
    image.py         # Step 2b: generate_image(prompt) -> bytes (PNG)
    metadata.py      # Step 3a: build_metadata(trends, image_uri, date) -> dict
    storage.py       # Step 3b: upload_file(bytes) / upload_json(dict) -> CID
    pipeline.py      # Step 4: run(date, dry_run) chains everything
  main.py            # CLI: python main.py <step> [options]
  tests/
    test_trends.py
    test_prompt.py
    test_image.py
    test_metadata.py
    test_storage.py
    test_pipeline.py
  output/            # local artifacts per run (git-ignored)
  .github/workflows/daily.yml
  .env.example
  requirements.txt
  README.md
```

Runtime deps (keep minimal): `requests`, `feedparser`, `openai`, `python-dotenv`. Dev: `pytest`, `responses` (HTTP mocking).

## Steps

### Step 0 – Project skeleton
- Create the layout above, `requirements.txt`, `.env.example` (`OPENAI_API_KEY`, `PINATA_JWT`), `.gitignore` (`.env`, `output/`, `.venv/`).
- `config.py` reads env vars; raises a clear error naming the missing variable.
- `main.py` uses `argparse` with sub-commands `trends`, `prompt`, `image`, `metadata`, `upload`, `run`.

**Test:** `python -m venv .venv && pip install -r requirements.txt && python main.py --help` lists all sub-commands. `pytest` runs (zero tests) without import errors.

### Step 1 – Get trends (`trendy/trends.py`)
- `fetch_google_trends(geo="US") -> list[str]`: parse `https://trends.google.com/trending/rss?geo=<geo>` with `feedparser`, return entry titles in order.
- `fetch_news_headlines() -> list[str]`: fallback, parse a news RSS (e.g. BBC world) and return titles.
- `get_trends(n=3) -> list[str]`: try Google Trends, fall back to news if empty or on error; return first `n`, de-duplicated, stripped.
- CLI: `python main.py trends [--n 3] [--geo US]` prints one trend per line and writes `output/<date>/trends.json`.

**Test:**
- Unit: `tests/test_trends.py` feeds a saved RSS sample (string fixture) to the parser and asserts 3 titles come out; asserts fallback is used when the first source returns nothing.
- Manual: `python main.py trends` prints 3 real, current trends.

### Step 2a – Build the prompt (`trendy/prompt.py`)
- Pure function `build_prompt(trends: list[str], style: str = DEFAULT_STYLE) -> str`. Deterministic, no network. Template lives in one constant so it's easy to tweak.
- CLI: `python main.py prompt --trends "a,b,c"` prints the prompt.

**Test:** `tests/test_prompt.py` asserts every trend word appears in the output and the prompt is under the OpenAI length limit.

### Step 2b – Generate the image (`trendy/image.py`)
- `generate_image(prompt: str, size="1024x1024") -> bytes` calling `client.images.generate(model="gpt-image-1", ...)` and decoding the base64 result.
- CLI: `python main.py image --trends "a,b,c"` (or `--prompt "..."`) saves `output/<date>/image.png` and prints the path. `--dry-run` writes a solid-colour placeholder PNG instead of calling OpenAI, so downstream steps can be tested for free.

**Test:**
- Unit: `tests/test_image.py` mocks the OpenAI client and asserts the returned bytes start with the PNG header; asserts dry-run needs no key.
- Manual: `python main.py image --trends "solar eclipse,world cup,AI"` and open the PNG.

### Step 3a – Build NFT metadata (`trendy/metadata.py`)
- `build_metadata(trends, image_uri, date, prompt) -> dict` in ERC‑721 JSON schema: `name` ("Trendy – 2026-09-07"), `description`, `image` (`ipfs://<cid>`), `attributes` (one per trend + date). Pure function.
- CLI: `python main.py metadata --trends "a,b,c" --image-uri ipfs://x` prints JSON.

**Test:** `tests/test_metadata.py` asserts required keys exist and `image` starts with `ipfs://`.

### Step 3b – Upload to IPFS via Pinata (`trendy/storage.py`)
- `upload_file(data: bytes, filename: str) -> str` → POST `https://api.pinata.cloud/pinning/pinFileToIPFS`, return `IpfsHash`.
- `upload_json(obj: dict, name: str) -> str` → POST `pinJSONToIPFS`, return `IpfsHash`.
- Helper `gateway_url(cid)` → `https://gateway.pinata.cloud/ipfs/<cid>` for quick viewing.
- CLI: `python main.py upload --file output/<date>/image.png` prints CID and gateway URL.

**Test:**
- Unit: `tests/test_storage.py` uses `responses` to mock Pinata and asserts the CID is parsed and the auth header is set.
- Manual: upload the PNG from Step 2b, open the gateway URL in a browser.

### Step 4 – Pipeline (`trendy/pipeline.py`)
- `run(date=today, n=3, dry_run=False) -> dict`: trends → prompt → image → upload image → metadata → upload metadata. Saves every intermediate artefact to `output/<date>/` (`trends.json`, `prompt.txt`, `image.png`, `metadata.json`, `result.json` with both CIDs).
- Idempotent per day: if `output/<date>/result.json` exists, skip unless `--force`.
- CLI: `python main.py run [--dry-run] [--force]`.

**Test:**
- Unit: `tests/test_pipeline.py` monkeypatches each step function with a stub and asserts they are called in order and `result.json` is written.
- Manual: `python main.py run --dry-run` (no cost) then `python main.py run` (real). Verify both gateway URLs open.

### Step 5 – Daily schedule (`.github/workflows/daily.yml`)
- Cron `0 18 * * *` (18:00 UTC) plus `workflow_dispatch` for manual triggering.
- Steps: checkout → setup Python → install → `python main.py run` with `OPENAI_API_KEY` and `PINATA_JWT` from repo secrets → upload `output/` as a workflow artifact.
- Requires: `git init`, push to GitHub, add the two secrets.

**Test:** Trigger via "Run workflow" button; check the job log and the artifact; open the metadata gateway URL.

### Step 6 – README
- How to install, set up `.env`, run each step, run tests, and set up the GitHub secrets. Short "Next: minting" section.

## Phase 2 (added 2026-09-08): small JPEG + gallery page

Decisions: pin only a 512x512 JPEG (~50 KB) instead of the raw 1024 PNG; show a scrollable 365-cell grid on GitHub Pages fed by a JSON file the daily workflow commits.

### Step 7 – Shrink before pinning (`trendy/image.py`, `trendy/pipeline.py`)
- `shrink_to_jpeg(png, size=512, quality=85)` using Pillow. Pipeline writes `image.png` (full) and `image.jpg` (pinned) and uploads only the JPEG.
- **Test:** `tests/test_image.py` checks a 512x512 JPEG; `tests/test_pipeline.py` asserts the uploaded bytes are JPEG.

### Step 8 – Gallery data (`trendy/gallery.py`)
- `add_entry(result)` inserts/replaces the day in `docs/gallery.json` (date, trends, prompt, image_cid, metadata_cid), sorted by date. Skipped on dry runs.
- **Test:** `tests/test_gallery.py`; `python main.py run --force` then inspect `docs/gallery.json`.

### Step 9 – Static grid (`docs/index.html`)
- Plain HTML/CSS/JS, no build. Fetches `gallery.json`, renders 365 cells from a fixed start date (2026-09-08) forward, empty cells for missed days, dashed cells for future days, lazy-loaded images, click for full image + trends + IPFS links. Start date and gateway are constants.
- **Test:** `python main.py serve` → http://localhost:8000.

### Step 11 (added 2026-09-09) – Global trends from world news (`trendy/trends.py`)
- Google Trends per country turned out to be local sports/celebrity searches, ordered by recency, with no China feed. Replaced as default.
- `fetch_headlines()` pulls 15 headlines from each of 10 world outlets (BBC, CNN, Al Jazeera, Guardian, DW, France 24, CNA, Times of India, NYT, SCMP); failing feeds are skipped.
- `pick_topics()` sends them to OpenAI `gpt-5.4-mini` (JSON mode) and gets the 5 topics covered by the most outlets. `fallback_topics()` (first headline of each outlet, round-robin) is used on dry runs or if the model fails.
- **Test:** `tests/test_trends.py` (mocked feeds + fake model client); `python main.py trends --dry-run` (free); `python main.py trends` (real, <1 cent).

### Step 12 (added 2026-09-20) – Global feed coverage, Google Trends removed
- `NEWS_FEEDS` expanded from 10 to 21 outlets to cover regions that had no representation: Africa (AllAfrica, Africanews), Latin America (MercoPress, Folha de S.Paulo), Russia/Eastern Europe (The Moscow Times, Kyiv Independent), Oceania (ABC News Australia), plus Middle East Eye, Japan Times, Le Monde and El Pais.
- The Google Trends fallback path (`fetch_google_trends`, `--source google --geo`) was unused since Step 11 replaced it as the default and is now removed entirely, along with `parse_entries`/`_parse_traffic` (traffic sorting) and the dead `fetch_news_headlines` helper. `get_trends()` no longer takes `source`/`geo`.

### Step 10 – Auto-publish (`.github/workflows/daily.yml`)
- Workflow has `contents: write`; after a real run it commits `docs/gallery.json` and pushes. GitHub Pages serves `/docs` from `main`.
- **Test:** manual "Run workflow", then refresh the Pages URL.

## Future phase (not in MVP): minting
Metadata is already ERC‑721 compatible with an `ipfs://` image. When ready: add `trendy/mint.py` using a simple ERC‑721 contract on Base Sepolia (testnet), one `mint` sub-command, one extra secret (`WALLET_PRIVATE_KEY`). Nothing in the MVP needs to change.

## Verification (end-to-end)
1. `pytest` – all unit tests pass offline with no keys set.
2. `python main.py trends` → 3 real trends printed.
3. `python main.py run --dry-run` → `output/<date>/` contains all artefacts, no API calls made.
4. `python main.py run` → real image + metadata on IPFS; both gateway URLs open in a browser.
5. Manual `workflow_dispatch` on GitHub succeeds and produces the same artefacts.
