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
| `tests/test_extractor.py` | Unit tests for `extract_pages` (mocked, no real PDF needed) |
| `Dockerfile` | `python:3.11-slim` + Tesseract + Poppler |

## What's working

- Full scaffold is in place and importable
- `extractor.py` and `ocr.py` are implemented and tested (mocked unit tests pass without any installed dependencies)
- `classifier.py` builds its system prompt dynamically from `taxonomy.yaml` — changing the taxonomy automatically changes what Claude looks for
- API key is handled automatically by the Anthropic SDK via `ANTHROPIC_API_KEY` env var (set in `.env`, loaded with `python-dotenv`)
- `.gitignore` correctly excludes `input/`, `output/`, and `.env`

## What's not tested yet

- End-to-end run against a real PDF (no sample PDF in the repo)
- OCR path (requires Tesseract installed locally or Docker)
- Claude API call (requires a live `ANTHROPIC_API_KEY`)

## Next step

Drop a real donor agreement PDF into `input/` and run the pipeline end-to-end:

```bash
cp .env.example .env          # add your ANTHROPIC_API_KEY
pip install -r requirements.txt
python -c "
from dotenv import load_dotenv; load_dotenv()
from pathlib import Path
from src.extractor import extract_pages
from src.ocr import ocr_pdf_page
from src.classifier import classify
from src.writer import write_result

for pdf in Path('input').glob('*.pdf'):
    pages = extract_pages(str(pdf))
    for p in pages:
        if p['needs_ocr']:
            p['text'] = ocr_pdf_page(str(pdf), p['page_num'])
    result = classify(pages, donor='ECHO', filename=pdf.name)
    print(write_result(result, pdf.name))
"
```

Then review `output/<filename>.json` and tune the taxonomy or system prompt as needed.
