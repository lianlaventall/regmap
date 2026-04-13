"""
pipeline.py — Run the full extract → classify → write pipeline.

Usage:
    # Single PDF (donor name derived from filename stem):
    python -m src.pipeline input/GFFO\ ANBest-P\ 2019_Annotated.pdf --donor GFFO

    # Donor folder (all PDFs merged into one output, donor name derived from folder name):
    python -m src.pipeline input/AFD/

    # Override donor name explicitly:
    python -m src.pipeline input/AFD/ --donor AFD
"""

import argparse
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from src.extractor import extract_pages
from src.ocr import ocr_pdf_page
from src.classifier import classify
from src.writer import write_result

DEDUP_THRESHOLD = 0.85  # similarity ratio above which a clause is considered a duplicate


def _normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def dedup_clauses(clauses: list[dict]) -> list[dict]:
    """Remove near-duplicate clauses produced by overlapping source documents.

    When two clauses have normalized text similarity >= DEDUP_THRESHOLD, the
    longer (more complete) clause is kept and the other is discarded.
    Clause IDs are reassigned after dedup.
    """
    seen_norms: list[str] = []
    kept: list[dict] = []

    for clause in clauses:
        norm = _normalize(clause.get("text", ""))
        duplicate_idx = None
        for i, seen in enumerate(seen_norms):
            if SequenceMatcher(None, norm, seen).ratio() >= DEDUP_THRESHOLD:
                duplicate_idx = i
                break

        if duplicate_idx is None:
            seen_norms.append(norm)
            kept.append(clause)
        else:
            # Keep whichever has longer source text
            if len(clause.get("text", "")) > len(kept[duplicate_idx].get("text", "")):
                kept[duplicate_idx] = clause
                seen_norms[duplicate_idx] = norm

    return kept


def extract_with_ocr(pdf_path: Path) -> list[dict]:
    pages = extract_pages(str(pdf_path))
    for page in pages:
        if page["needs_ocr"]:
            print(f"    OCR fallback: {pdf_path.name} page {page['page_num']}")
            page["text"] = ocr_pdf_page(str(pdf_path), page["page_num"])
            page["needs_ocr"] = False
    return pages


def collect_pdfs(input_path: Path) -> tuple[list[Path], str]:
    """Return (list of PDF paths, derived donor name)."""
    if input_path.is_dir():
        pdfs = sorted(input_path.glob("*.pdf"))
        if not pdfs:
            print(f"No PDFs found in {input_path}", file=sys.stderr)
            sys.exit(1)
        donor = input_path.name
    else:
        pdfs = [input_path]
        donor = input_path.stem
    return pdfs, donor


def merge_pages(pdfs: list[Path]) -> tuple[list[dict], str]:
    """Extract and merge pages from multiple PDFs. Returns (pages, document label)."""
    all_pages = []
    global_page = 0
    for pdf in pdfs:
        print(f"  Extracting: {pdf.name}")
        pages = extract_with_ocr(pdf)
        for page in pages:
            global_page += 1
            page["source_file"] = pdf.name
            page["original_page_num"] = page["page_num"]
            page["page_num"] = global_page
        all_pages.extend(pages)
        print(f"    {len(pages)} pages extracted")

    document_label = " + ".join(p.name for p in pdfs)
    return all_pages, document_label


def run(input_path: Path, donor_override: str | None = None) -> None:
    pdfs, derived_donor = collect_pdfs(input_path)
    donor = donor_override or derived_donor

    print(f"Donor: {donor}")
    print(f"PDFs:  {', '.join(p.name for p in pdfs)}")

    pages, document_label = merge_pages(pdfs)
    print(f"Total pages: {len(pages)}")

    print("Classifying...")
    result = classify(pages, donor, document_label)
    print(f"  {len(result['clauses'])} clauses extracted")

    if len(pdfs) > 1:
        before = len(result["clauses"])
        result["clauses"] = dedup_clauses(result["clauses"])
        # Reassign clause IDs after dedup
        for idx, clause in enumerate(result["clauses"], start=1):
            clause["clause_id"] = f"{donor}-{idx:03d}"
        removed = before - len(result["clauses"])
        if removed:
            print(f"  Dedup: removed {removed} near-duplicate clause(s) → {len(result['clauses'])} kept")

    out_path = write_result(result, f"{donor}.json")
    print(f"Written: {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the regmap pipeline on a PDF or donor folder.")
    parser.add_argument("input", help="Path to a PDF file or a folder of PDFs")
    parser.add_argument("--donor", help="Donor name (overrides derived name)")
    args = parser.parse_args()

    run(Path(args.input), donor_override=args.donor)
