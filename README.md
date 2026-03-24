# regmap

Extracts, classifies, and compares obligation clauses from donor agreement PDFs. Uses a modal language taxonomy and the Claude API to produce structured JSON per document, then maps restrictions across donors to identify shared compliance baselines.

## How it works

1. **Extract** — `src/extractor.py` opens each PDF with `pdfplumber` and pulls text page-by-page. Pages with no text are flagged for OCR.
2. **OCR** — `src/ocr.py` renders flagged pages to images via `pdf2image` and runs `pytesseract`.
3. **Classify** — `src/classifier.py` sends page text to Claude (`claude-sonnet-4-6`) with the taxonomy and receives a structured JSON list of classified clauses, each with a tier, domain, actor, and dead-end classification.
4. **Write** — `src/writer.py` saves the result to `output/<filename>.json`.
5. **Compare** — `src/compare.py` runs N-way tier distribution comparison across output JSONs.
6. **Flow** — `src/main.py` builds a typed flow graph per donor and renders `output/flow_viz.html` (D3.js, per-donor view — draft).

## Taxonomy

Defined in `config/taxonomy.yaml`. All classification rules are data-driven — changes to the YAML automatically update what Claude extracts.

### Tiers

| Tier | Description | Trigger words |
|------|-------------|---------------|
| RESTRICTION | Mandatory obligations | must, will, shall, required, binding, obliged, mandatory |
| QUALIFIED_RESTRICTION | Mandatory but softened by a qualifier phrase | RESTRICTION trigger + qualifier |
| DECISION | Permissive language | may, can |
| HIGH_RISK | Soft obligations with compliance risk | recommended, suggested, encouraged, should, ideally |

### Qualifiers

Phrases that downgrade a RESTRICTION to QUALIFIED_RESTRICTION: `where possible`, `where feasible`, `where appropriate`, `as far as possible`, `to the extent possible`, `if applicable`, `unless otherwise specified`, `subject to availability`

### Context patterns

Verb-first clauses that signal an obligation regardless of modal word (`submit`, `ensure`, `verify`, `demonstrate`, `confirm`, `provide`, `notify`, `comply`, `maintain`, `retain`) — sets `context_flag: true`.

### Dead ends

Terminal restrictions that stop a decision path. Classified as:
- **UNCONDITIONAL** — applies regardless of any upstream decision; candidate for cross-donor pooling
- **CONDITIONAL** — reachable only via a specific decision branch
- **AMBIGUOUS** — looks absolute but contains unresolved scope; flagged for audit

Signal phrases: `must not`, `shall not`, `not permitted`, `not allowed`, `cannot be`, `only from`, `no exceptions`, `not acceptable`

### Domains

Each clause is assigned one semantic domain for cross-donor grouping:
`PROCUREMENT`, `REPORTING`, `RECORD_KEEPING`, `ELIGIBILITY`, `FINANCIAL`, `SAFEGUARDING`, `SCOPE`

## Cross-donor analysis

The goal is a visual matrix that answers: *which restrictions appear across which donors, and where do they overlap?*

Pooling logic:
1. Identify UNCONDITIONAL dead-end clauses across donor output JSONs
2. Group by `domain`
3. Use Claude to normalize phrasing into canonical form within each group
4. Render as a matrix: rows = domain, columns = donor, cells = present/absent

This is under development and will be a standalone visualization separate from `flow_viz.html`.

## Setup

```bash
git clone <repo-url>
cd regmap

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

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

### N-way comparison

```bash
python -m src.compare output/file1.json output/file2.json output/file3.json
```

### Flow visualization

```bash
python src/main.py
# opens output/flow_viz.html
```

## Running tests

```bash
pytest tests/
```

## Docker

```bash
docker build -t regmap .
docker run --rm \
  -e ANTHROPIC_API_KEY=sk-ant-... \
  -v $(pwd)/input:/app/input \
  -v $(pwd)/output:/app/output \
  regmap
```

## Output format

See `schemas/output_schema.json` for the full JSON schema. Example clause:

```json
{
  "clause_id": "ECHO-001",
  "text": "The grantee must not procure goods from sanctioned entities.",
  "page": 4,
  "trigger_word": "must not",
  "tier": "RESTRICTION",
  "context_flag": false,
  "actor": "NGO",
  "creates_ngo_dependency": false,
  "dead_end": true,
  "dead_end_type": "UNCONDITIONAL",
  "domain": "PROCUREMENT",
  "notes": ""
}
```

