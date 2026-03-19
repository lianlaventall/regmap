# Session Notes — 2026-03-19

## What we built

A Python-based PDF clause extraction pipeline with these components:

| File | Purpose |
|------|---------|
| `src/extractor.py` | Opens PDFs with `pdfplumber`, returns pages as `{page_num, text, needs_ocr}` |
| `src/ocr.py` | Renders flagged pages via `pdf2image`, runs `pytesseract` |
| `src/classifier.py` | Sends page text + taxonomy to Claude (`claude-sonnet-4-6`), returns structured JSON |
| `src/writer.py` | Writes classifier output to `output/<filename>.json` |
| `config/taxonomy.yaml` | Three-tier modal language taxonomy (RESTRICTIONS / DECISIONS / HIGH_RISK) + context pattern verbs |
| `schemas/output_schema.json` | JSON Schema for the output format |
| `src/compare.py` | Compares tier distributions across two output JSONs; prints counts, percentages, and Δ pct points per tier |
| `tests/test_extractor.py` | Unit tests for `extract_pages` (mocked, no real PDF needed) |
| `Dockerfile` | `python:3.11-slim` + Tesseract + Poppler |

## What's working

- Full scaffold is in place and importable
- `extractor.py` and `ocr.py` are implemented and tested (mocked unit tests pass without any installed dependencies)
- `classifier.py` builds its system prompt dynamically from `taxonomy.yaml` — changing the taxonomy automatically changes what Claude looks for
- API key is in `.env` (gitignored), loaded via `python-dotenv`
- `.gitignore` correctly excludes `input/`, `output/`, and `.env`
- Extractor confirmed working against real PDF: `Provisions_on_medical_and_food_supplies_EN_2025_technical_update_final.pdf` (12 pages, all digital — no OCR needed)
- Taxonomy expanded: added `binding`, `obliged`, `mandatory` to RESTRICTIONS; `ideally`, `where possible` to HIGH_RISK; `comply`, `maintain`, `retain` to context_pattern verbs (committed + pushed)
- Bug fixed in `classifier.py`: `Anthropic()` client moved inside `classify()` so it initialises after `load_dotenv()` runs
- SOCKS proxy issue resolved: run pipeline with `ALL_PROXY= all_proxy= FTP_PROXY= ftp_proxy= GRPC_PROXY= grpc_proxy=` prefix

## What's working (confirmed end-to-end)

- API credits active, classifier running successfully
- Full pipeline run completed on ECHO document (`Provisions_on_medical_and_food_supplies_EN_2025_technical_update_final.pdf`)
- Full pipeline run completed on BHA document (`USAID_BHA PMC Guidance Dec 2023.pdf`) — 113 clauses extracted
- Output JSON files written to `output/`

## What's not tested yet

- OCR path (requires Tesseract installed locally or Docker)

## Next step

Credits should be active — rerun the pipeline:

```bash
ALL_PROXY= all_proxy= FTP_PROXY= ftp_proxy= GRPC_PROXY= grpc_proxy= .venv/bin/python -c "
from dotenv import load_dotenv; load_dotenv()
from pathlib import Path
from src.extractor import extract_pages
from src.ocr import ocr_pdf_page
from src.classifier import classify
from src.writer import write_result

for pdf in Path('input').glob('*.pdf'):
    print(f'Processing {pdf.name}...')
    pages = extract_pages(str(pdf))
    for p in pages:
        if p['needs_ocr']:
            p['text'] = ocr_pdf_page(str(pdf), p['page_num'])
    result = classify(pages, donor='ECHO', filename=pdf.name)
    out = write_result(result, pdf.name)
    print(f'Done. {len(result[\"clauses\"])} clauses written to {out}')
"
```

Then review `output/<filename>.json` and tune the taxonomy or system prompt as needed.

## Phase transition — 2026-03-19

Moving into **flow diagram phase**: the extraction pipeline is stable; next work will focus on generating visual flow diagrams from the extracted clause data.
