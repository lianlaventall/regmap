# Session Notes — regmap

## Session 2026-03-24

### Goal
Reshape the taxonomy and classifier to support cross-donor pooling and visual comparison — the foundation for a dedicated cross-donor analysis view separate from the per-donor flow visualization.

### Changes made

**`config/taxonomy.yaml`**
- Removed `where possible` from `HIGH_RISK` trigger words — it belongs only in `qualifiers`. Having it in both caused the classifier to misclassify softened mandatory language as HIGH_RISK instead of QUALIFIED_RESTRICTION.
- Added `unless otherwise specified` and `subject to availability` to `qualifiers` — both are common softening phrases in donor/humanitarian regulatory language.
- Added `dead_ends` top-level key with three types (UNCONDITIONAL, CONDITIONAL, AMBIGUOUS) and a set of signal phrases (`must not`, `shall not`, `not permitted`, etc.). UNCONDITIONAL dead ends are the candidates for cross-donor pooling.
- Added `domains` top-level key with 7 semantic buckets (PROCUREMENT, REPORTING, RECORD_KEEPING, ELIGIBILITY, FINANCIAL, SAFEGUARDING, SCOPE). Domain assignment enables grouping equivalent obligations across donors regardless of phrasing variance.

**`src/classifier.py`**
- Extended `_build_system_prompt` to read `dead_ends.signals` and `domains.values` from the taxonomy and inject them into the Claude prompt.
- Claude now outputs `dead_end` (bool), `dead_end_type` (UNCONDITIONAL/CONDITIONAL/AMBIGUOUS/null), and `domain` per clause.

**`schemas/output_schema.json`**
- Added `dead_end`, `dead_end_type`, and `domain` to the required clause fields with enums matching the taxonomy.

### Design decisions
- Cross-donor analysis will be a separate visualization from `flow_viz.html`, which was a per-donor draft.
- Pooling logic: group UNCONDITIONAL dead-end clauses by `domain`, then use Claude to normalize phrasing into canonical form within each group. The visual will be a matrix — rows = domain, columns = donor, cells = present/absent.
- AMBIGUOUS dead ends are flagged for human audit before entering any baseline pool.
- Next step: re-run pipeline on BHA and ECHO to get enriched output with new fields, then build the pooling/visualization layer.

---

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
