# skynetjoe-batch7-content

Media hosting for **GHL Batch 7 — Content Command Center** (55 scheduled posts, Apr 15 -> May 24, 2026).

This repo exists solely to serve raw media URLs via `raw.githubusercontent.com/...` so that the GoHighLevel Social Planner CSV importer can reach every asset from a single public path.

## Structure

```
skynetjoe-batch7-content/
|-- images/          # 15 rendered text-design PNGs (1080x1080) -> img-01..img-15
|   |-- waseem/      # 15-20 best-lit Waseem photos (personal brand pool)
|-- photos/          # Raw Waseem photos referenced by CSV engagement/funny/community rows
|-- videos/          # Source MP4 reels (10) - NOTE: GHL requires its own Media Library CDN, see below
|-- pdfs/            # Lead-magnet PDFs, served via raw.githubusercontent and linked from each post's pinned/follow-up comment (ManyChat was cut)
|-- scripts/         # render-batch7.js (Playwright renderer), helper scripts
```

## URL contract (used by CSV)

```
https://raw.githubusercontent.com/waseemnasir2k26/skynetjoe-batch7-content/main/images/img-NN-slug.png
https://raw.githubusercontent.com/waseemnasir2k26/skynetjoe-batch7-content/main/photos/<filename>
https://raw.githubusercontent.com/waseemnasir2k26/skynetjoe-batch7-content/main/videos/<filename>.mp4
```

## Usage

1. `gh repo create waseemnasir2k26/skynetjoe-batch7-content --public --source=. --push`
2. Videos: upload MP4s to GHL Media Library, collect `assets.cdn.filesafe.space/...` URLs, then run the URL-swap helper in `scripts/` against the CSV. (Already done — the FINAL CSV carries live `assets.cdn.filesafe.space/...` video URLs.)
3. PDFs: already hosted in this repo (`pdfs/`). Lead magnets are delivered as the pinned/follow-up comment link on each post (the `followUpComment` column in the CSV) — no ManyChat keyword flow, no email gate.

## Related

- CSV source (canonical, import this): `../ghl-batch7-content-engine.FINAL.csv`
- CSV source (videos-only 10-day drip): `../ghl-batch7-VIDEOS-10day-2026-06-01.csv`
- ManyChat removal record: `scripts/patch_csv_remove_manychat.py` (historical migration that stripped the keyword flows)
