import re
from collections import Counter

import pdfplumber


MIN_TABLE_ROWS = 2             # ignore single-row "tables" (usually just bordered text)
HEADER_FOOTER_THRESHOLD = 0.4  # line appearing on >40% of pages is structural boilerplate


def _normalize_text(text: str) -> str:
    """Fix hyphenation at line breaks, strip page numbers, collapse whitespace."""
    # Fix soft hyphens at line breaks: "obli-\ngation" → "obligation"
    text = re.sub(r'(\w)-\n(\w)', r'\1\2', text)
    # Strip standalone page number lines: "- 12 -", "Page 3 of 45", bare integers
    text = re.sub(r'(?m)^\s*[-\u2013\u2014]?\s*\d+\s*[-\u2013\u2014]?\s*$', '', text)
    text = re.sub(r'(?m)^\s*[Pp]age\s+\d+\s+of\s+\d+\s*$', '', text)
    # Strip visual separator lines (----, ====, ____)
    text = re.sub(r'(?m)^\s*[-_=]{3,}\s*$', '', text)
    # Collapse 3+ blank lines into one
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def _format_table(rows: list[list]) -> str:
    """Format a pdfplumber table as pipe-delimited rows."""
    lines = []
    for row in rows:
        cells = [str(cell or '').strip().replace('\n', ' ') for cell in row]
        lines.append('| ' + ' | '.join(cells) + ' |')
    return '\n'.join(lines)


def _extract_annotations(page) -> str:
    """Extract text from the PDF annotation layer (sticky notes, comments)."""
    try:
        annots = page.annots
    except Exception:
        return ''
    if not annots:
        return ''
    texts = []
    for annot in annots:
        try:
            content = annot.get('data', {}).get('Contents', '')
            if content and content.strip():
                texts.append(content.strip())
        except Exception:
            continue
    if not texts:
        return ''
    return '\n\n[ANNOTATIONS]\n' + '\n'.join(f'- {t}' for t in texts)


def _extract_page_content(page) -> str:
    """
    Extract text from a single page, handling tables and non-table regions separately.
    Tables are formatted as pipe-delimited rows; non-table text is extracted normally.
    Falls back to plain extract_text() if table handling fails.
    """
    try:
        tables = page.find_tables()
    except Exception:
        return page.extract_text() or ''

    if not tables:
        return page.extract_text() or ''

    table_bboxes = [t.bbox for t in tables]

    def _outside_all_tables(obj):
        x0 = obj.get('x0', 0)
        x1 = obj.get('x1', 0)
        top = obj.get('top', 0)
        bottom = obj.get('bottom', 0)
        for tx0, ttop, tx1, tbottom in table_bboxes:
            if not (x1 <= tx0 or x0 >= tx1 or bottom <= ttop or top >= tbottom):
                return False
        return True

    try:
        non_table_text = page.filter(_outside_all_tables).extract_text() or ''
    except Exception:
        non_table_text = page.extract_text() or ''

    table_blocks = []
    for table in tables:
        try:
            rows = table.extract()
            if rows and len(rows) >= MIN_TABLE_ROWS:
                formatted = _format_table(rows)
                if formatted.strip():
                    table_blocks.append(f'[TABLE]\n{formatted}\n[/TABLE]')
        except Exception:
            continue

    parts = [non_table_text] + table_blocks
    return '\n\n'.join(p for p in parts if p.strip())


def _strip_headers_footers(pages: list[dict]) -> list[dict]:
    """
    Remove structural boilerplate — lines appearing on more than 40% of pages
    are headers/footers and stripped from all pages. Skips short lines (<5 chars)
    to avoid stripping meaningful short content.
    """
    if len(pages) < 3:
        return pages

    line_counts: Counter = Counter()
    for page in pages:
        seen = {line.strip() for line in page['text'].split('\n') if len(line.strip()) > 4}
        line_counts.update(seen)

    threshold = max(3, len(pages) * HEADER_FOOTER_THRESHOLD)
    boilerplate = {line for line, count in line_counts.items() if count >= threshold}

    if not boilerplate:
        return pages

    for page in pages:
        lines = page['text'].split('\n')
        page['text'] = '\n'.join(l for l in lines if l.strip() not in boilerplate)

    return pages


def extract_pages(pdf_path: str) -> list[dict]:
    """Extract text from each page of a PDF.

    Four-pass extraction per page:
      1. Table-aware text extraction (pdfplumber find_tables + filter)
      2. Annotation layer extraction (sticky notes, comments)
      3. Text normalization (hyphenation, page numbers, whitespace)
    Then across all pages:
      4. Header/footer stripping (lines on >40% of pages removed)

    Returns a list of dicts with keys:
      - page_num (int): 1-based page number
      - text (str): extracted and cleaned text
      - needs_ocr (bool): True if the page yielded no text after extraction
    """
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            raw = _extract_page_content(page)
            annotations = _extract_annotations(page)
            combined = raw + annotations
            normalized = _normalize_text(combined)
            pages.append({
                'page_num': i,
                'text': normalized,
                'needs_ocr': not normalized.strip(),
            })

    pages = _strip_headers_footers(pages)
    return pages
