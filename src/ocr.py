from pdf2image import convert_from_path
import pytesseract
from PIL.Image import Image


def ocr_page_image(image: Image) -> str:
    """Run OCR on a PIL Image and return the extracted text."""
    return pytesseract.image_to_string(image)


def ocr_pdf_page(pdf_path: str, page_num: int) -> str:
    """Render a single PDF page (1-based) to an image and OCR it."""
    images = convert_from_path(pdf_path, first_page=page_num, last_page=page_num)
    if not images:
        return ""
    return ocr_page_image(images[0])
