# CLAUDE.md — regmap

## Purpose

Extract, classify, and compare obligation clauses from donor agreement PDFs. Helps humanitarian specialists understand donor regulation complexity — what is mandatory, what is discretionary, where donors converge, and where they diverge.

---

## Environment

- Python 3.13, virtualenv at `.venv/`
- API key in `.env` (gitignored), loaded via `python-dotenv`
- **SOCKS proxy must be cleared before running the pipeline.** Prefix commands with:
  ```
  ALL_PROXY= all_proxy= FTP_PROXY= ftp_proxy= GRPC_PROXY= grpc_proxy=
  ```

---

## Pipeline

Four-step chain — run in order on a new PDF:

```bash
# 1. Extract text from PDF (pdfplumber, flags scanned pages)
# 2. OCR fallback for scanned pages (pdf2image + pytesseract)
# 3. Classify clauses via Claude (claude-sonnet-4-6) using taxonomy
# 4. Write structured JSON to output/
```

The pipeline modules are `src/extractor.py`, `src/ocr.py`, `src/classifier.py`, `src/writer.py`.

Output lands in `output/<filename>.json` (gitignored).

---

## Taxonomy

`config/taxonomy.yaml` is the single source of truth for:
- **Tiers:** RESTRICTION, QUALIFIED_RESTRICTION, HIGH_RISK, DECISION
- **Qualifiers:** phrases that downgrade RESTRICTION → QUALIFIED_RESTRICTION
- **Dead ends:** UNCONDITIONAL, CONDITIONAL, AMBIGUOUS (with signal phrases)
- **Domains:** PROCUREMENT, REPORTING, RECORD_KEEPING, ELIGIBILITY, FINANCIAL, SAFEGUARDING, SCOPE

The classifier reads this file dynamically — changes here automatically update what Claude extracts.

Output schema is defined in `schemas/output_schema.json`.

---

## Analysis

N-way tier distribution comparison across any set of output JSONs:

```bash
python -m src.compare output/file1.json output/file2.json [...]
```

---

## Visualizations

All four scripts are self-contained and write to `output/`. Run independently:

```bash
python -m src.flow      # per-donor D3 force-directed graph → output/flow_viz.html
python -m src.heatmap   # cross-donor domain × tier density + dead-end analysis → output/heatmap.html
python -m src.sankey    # cross-donor Donor → Domain → Tier flow → output/sankey.html
python -m src.dag       # hierarchical decision DAG per donor → output/dag.html
```

---

## Gitignored paths

- `input/` — source PDFs
- `output/` — generated JSONs and HTML visualizations
- `reports/` — local analysis reports
- `.env` — API key

---

## Known gaps

- OCR path untested end-to-end (requires Tesseract locally or Docker)
- No tests beyond `src/tests/test_extractor.py`
- SCOPE domain: 0–1 clauses across all current donors — possibly underassigned by classifier
- SAFEGUARDING: BHA-only so far — likely document-type specific, not a classifier issue

---

## Key files

| File | Purpose |
|---|---|
| `src/extractor.py` | pdfplumber → pages with `needs_ocr` flag |
| `src/ocr.py` | pdf2image + pytesseract for scanned pages |
| `src/classifier.py` | Sends page text + taxonomy to Claude, returns structured JSON |
| `src/writer.py` | Writes classifier output to `output/<filename>.json` |
| `src/compare.py` | N-way tier distribution comparison (CLI) |
| `src/flow.py` | Per-donor force-directed graph |
| `src/heatmap.py` | Cross-donor domain × tier heatmap + dead-end analysis |
| `src/sankey.py` | Cross-donor Sankey flow |
| `src/dag.py` | Decision flow DAG per donor |
| `config/taxonomy.yaml` | Tier taxonomy, qualifiers, dead ends, domains |
| `schemas/output_schema.json` | JSON Schema for classifier output |
| `Dockerfile` | python:3.11-slim + Tesseract + Poppler |
