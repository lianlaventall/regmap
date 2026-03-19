import io
import pytest
from unittest.mock import patch, MagicMock

from src.extractor import extract_pages


class FakePage:
    def __init__(self, text):
        self._text = text

    def extract_text(self):
        return self._text


class FakePDF:
    def __init__(self, pages):
        self.pages = [FakePage(t) for t in pages]

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


def test_extract_pages_returns_list():
    fake_texts = ["Hello world", "Second page text", ""]
    with patch("src.extractor.pdfplumber.open", return_value=FakePDF(fake_texts)):
        result = extract_pages("dummy.pdf")

    assert isinstance(result, list)
    assert len(result) == 3


def test_extract_pages_page_numbers_are_one_based():
    fake_texts = ["Page one", "Page two"]
    with patch("src.extractor.pdfplumber.open", return_value=FakePDF(fake_texts)):
        result = extract_pages("dummy.pdf")

    assert result[0]["page_num"] == 1
    assert result[1]["page_num"] == 2


def test_extract_pages_text_captured():
    fake_texts = ["Hello world"]
    with patch("src.extractor.pdfplumber.open", return_value=FakePDF(fake_texts)):
        result = extract_pages("dummy.pdf")

    assert result[0]["text"] == "Hello world"


def test_extract_pages_needs_ocr_false_when_text_present():
    fake_texts = ["Some text here"]
    with patch("src.extractor.pdfplumber.open", return_value=FakePDF(fake_texts)):
        result = extract_pages("dummy.pdf")

    assert result[0]["needs_ocr"] is False


def test_extract_pages_needs_ocr_true_when_empty():
    fake_texts = ["   "]  # whitespace-only
    with patch("src.extractor.pdfplumber.open", return_value=FakePDF(fake_texts)):
        result = extract_pages("dummy.pdf")

    assert result[0]["needs_ocr"] is True


def test_extract_pages_needs_ocr_true_when_none():
    fake_texts = [None]  # pdfplumber returns None for image-only pages
    with patch("src.extractor.pdfplumber.open", return_value=FakePDF(fake_texts)):
        result = extract_pages("dummy.pdf")

    assert result[0]["needs_ocr"] is True
