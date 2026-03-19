# Plan: pdf-extractor Project Setup

## Context
Scaffold a new Python-based PDF extraction tool that takes PDFs from an `input/` folder, extracts text (with OCR fallback for scanned pages), applies rules via the Claude API, and writes structured JSON results to `output/`.

## Project Structure
```
projects/pdf-extractor/
├── input/              # drop PDFs here
├── output/             # JSON results land here
├── src/
│   ├── extractor.py    # PDF → raw text/pages (via pdfplumber or PyMuPDF)
│   ├── ocr.py          # handles scanned pages (via pytesseract)
│   └── parser.py       # applies rules → JSON via Claude API
├── requirements.txt
└── README.md
```

## Implementation Steps

1. **Create directories**
   - `input/`, `output/`, `src/`

2. **`src/extractor.py`**
   - Use `pdfplumber` to open each PDF and extract text page by page
   - Return a list of `{page_num, text}` dicts
   - If a page yields empty/whitespace text, flag it for OCR

3. **`src/ocr.py`**
   - Accept a page image (rendered via `pdf2image`) and run `pytesseract` OCR
   - Return extracted text string

4. **`src/parser.py`**
   - Accept pages list from extractor
   - Send text to Claude API (`claude-sonnet-4-6`) with a system prompt instructing it to extract structured JSON
   - Return parsed JSON result
   - Write result to `output/<filename>.json`

5. **`requirements.txt`**
   ```
   pdfplumber
   pdf2image
   pytesseract
   anthropic
   ```

6. **`README.md`**
   - Usage instructions: drop PDFs into `input/`, run `python src/parser.py`

## Key Libraries
- `pdfplumber` — text extraction from digital PDFs
- `pdf2image` + `pytesseract` — OCR for scanned pages
- `anthropic` — Claude API for rule-based JSON parsing

## Git & GitHub Setup

7. **Initialize git repo**
   - `git init` inside `projects/pdf-extractor/`
   - Create `.gitignore` (ignore `input/`, `output/`, `__pycache__/`, `.env`)
   - Initial commit with project scaffold

8. **Create GitHub repo and push**
   - `gh repo create pdf-extractor --public --source=. --remote=origin --push`
   - This creates the repo on GitHub, sets `origin`, and pushes the initial commit

## Verification
- Drop a sample PDF into `input/` and run `python src/parser.py`
- Check `output/` for the resulting `.json` file
- Test with a scanned PDF to verify OCR path triggers correctly
