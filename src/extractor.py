import pdfplumber
from pathlib import Path


def extract_pages(pdf_path: str) -> list[dict]:
    """Extract text from each page of a PDF.

    Returns a list of dicts with keys:
      - page_num (int): 1-based page number
      - text (str): extracted text
      - needs_ocr (bool): True if the page yielded no text
    """
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            pages.append({
                "page_num": i,
                "text": text,
                "needs_ocr": not text.strip(),
            })
    return pages
