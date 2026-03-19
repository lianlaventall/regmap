# pdf-extractor

Extracts and classifies obligation clauses from donor agreement PDFs using a three-tier modal language taxonomy and the Claude API.

## How it works

1. **Extract** — `src/extractor.py` opens each PDF with `pdfplumber` and pulls text page-by-page. Pages with no text are flagged for OCR.
2. **OCR** — `src/ocr.py` renders flagged pages to images via `pdf2image` and runs `pytesseract`.
3. **Classify** — `src/classifier.py` sends the full page text to Claude (`claude-sonnet-4-6`) with the taxonomy, and receives a structured JSON list of classified clauses.
4. **Write** — `src/writer.py` saves the result to `output/<filename>.json`.

## Taxonomy tiers

| Tier | Trigger words |
|------|--------------|
| RESTRICTION | must, will, shall, required, shall not |
| DECISION | may, can |
| HIGH_RISK | recommended, suggested, encouraged, should |

Context pattern verbs (verb-first clauses): `submit`, `ensure`, `verify`, `demonstrate`, `confirm`, `provide`, `notify`

## Setup

```bash
# 1. Clone and enter the project
git clone <repo-url>
cd pdf-extractor

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set your API key
cp .env.example .env
# edit .env and set ANTHROPIC_API_KEY=sk-ant-...
```

## Usage

Drop one or more PDFs into `input/`, then run:

```bash
python -c "
from dotenv import load_dotenv
load_dotenv()
from pathlib import Path
from src.extractor import extract_pages
from src.ocr import ocr_pdf_page
from src.classifier import classify
from src.writer import write_result

for pdf in Path('input').glob('*.pdf'):
    pages = extract_pages(str(pdf))
    for page in pages:
        if page['needs_ocr']:
            page['text'] = ocr_pdf_page(str(pdf), page['page_num'])
    result = classify(pages, donor='DONOR', filename=pdf.name)
    out = write_result(result, pdf.name)
    print(f'Written: {out}')
"
```

Results land in `output/<filename>.json`.

## Running tests

```bash
pytest tests/
```

## Docker

```bash
docker build -t pdf-extractor .
docker run --rm \
  -e ANTHROPIC_API_KEY=sk-ant-... \
  -v $(pwd)/input:/app/input \
  -v $(pwd)/output:/app/output \
  pdf-extractor
```

## Output format

See `schemas/output_schema.json` for the full JSON schema. Example:

```json
{
  "donor": "ECHO",
  "document": "agreement.pdf",
  "processed_at": "2026-03-19T12:00:00Z",
  "pages_processed": 7,
  "clauses": [
    {
      "clause_id": "ECHO-001",
      "text": "The grantee must submit quarterly financial reports.",
      "page": 2,
      "trigger_word": "must",
      "tier": "RESTRICTION",
      "context_flag": false,
      "notes": ""
    }
  ]
}
```
