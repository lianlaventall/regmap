# Session Notes — regmap

## Project state (as of 2026-03-23)

The extraction pipeline is stable and the flow visualization phase is complete.

## Components

| File | Purpose |
|------|---------|
| `src/extractor.py` | Opens PDFs with `pdfplumber`, returns pages as `{page_num, text, needs_ocr}` |
| `src/ocr.py` | Renders flagged pages via `pdf2image`, runs `pytesseract` |
| `src/classifier.py` | Sends page text + taxonomy to Claude (`claude-sonnet-4-6`), returns structured JSON |
| `src/writer.py` | Writes classifier output to `output/<filename>.json` |
| `src/compare.py` | N-way tier distribution comparison across output JSONs; prints counts, percentages, and Δ pct points vs baseline |
| `src/main.py` | Builds typed flow graph per donor → `output/flow_data.json` + `output/flow_viz.html` (D3.js, donor dropdown, hover tooltips) |
| `config/taxonomy.yaml` | Three-tier modal language taxonomy (RESTRICTIONS / DECISIONS / HIGH_RISK) + context pattern verbs |
| `schemas/output_schema.json` | JSON Schema for the output format |
| `tests/test_extractor.py` | Mocked unit tests for `extract_pages` — no real PDF or dependencies needed |
| `Dockerfile` | `python:3.11-slim` + Tesseract + Poppler |

## What's confirmed working

- Full pipeline: extract → OCR fallback → classify → JSON output
- Completed runs: ECHO (`Provisions_on_medical_and_food_supplies_EN_2025_technical_update_final.pdf`) and BHA (`USAID_BHA PMC Guidance Dec 2023.pdf`, 113 clauses)
- N-way comparison via `python -m src.compare <path1> <path2> [...]`
- Flow visualization: `python src/main.py` regenerates `output/flow_data.json` and `output/flow_viz.html`
- Taxonomy is dynamic — changes to `config/taxonomy.yaml` automatically update what Claude extracts

## Known gaps

- OCR path untested (requires Tesseract locally or Docker)
- No tests for `classifier.py`, `compare.py`, or `main.py`

## Environment notes

- API key in `.env` (gitignored), loaded via `python-dotenv`
- SOCKS proxy must be cleared before running the pipeline: prefix commands with `ALL_PROXY= all_proxy= FTP_PROXY= ftp_proxy= GRPC_PROXY= grpc_proxy=`
- `input/`, `output/`, and `.env` are gitignored
