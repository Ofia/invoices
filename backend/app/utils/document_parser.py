"""
Document Text Extraction Utilities

Extracts text from various document formats (PDFs, images, docs) for AI processing.

Supported formats:
- PDFs: PyPDF2 and pdfplumber (fallback)
- Images: pytesseract OCR (PNG, JPG, JPEG, WEBP)
- Docs: Not implemented yet (Phase 5)
"""

import logging
from pathlib import Path
from typing import Optional
import PyPDF2
import pdfplumber

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path: Path) -> str:
    """
    Extract text from PDF file.

    Uses two methods:
    1. PyPDF2 (fast, works for text-based PDFs)
    2. pdfplumber (fallback, better for complex layouts)

    Args:
        file_path: Path to PDF file

    Returns:
        Extracted text string

    Raises:
        Exception: If both extraction methods fail
    """
    try:
        # Method 1: PyPDF2 (faster)
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""

            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text()

            # If we got meaningful text, return it
            if text.strip():
                logger.info(f"Extracted {len(text)} chars from PDF using PyPDF2")
                return text.strip()

    except Exception as e:
        logger.warning(f"PyPDF2 extraction failed: {str(e)}, trying pdfplumber")

    try:
        # Method 2: pdfplumber (fallback, more robust)
        with pdfplumber.open(file_path) as pdf:
            text = ""

            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

            if text.strip():
                logger.info(f"Extracted {len(text)} chars from PDF using pdfplumber")
                return text.strip()

    except Exception as e:
        logger.error(f"pdfplumber extraction failed: {str(e)}")

    # Both methods failed
    raise Exception("Failed to extract text from PDF")


def extract_text_from_image(file_path: Path) -> str:
    """
    Extract text from image using OCR (Optical Character Recognition).

    Requires Tesseract to be installed on the system.
    Install: https://github.com/tesseract-ocr/tesseract

    Args:
        file_path: Path to image file (PNG, JPG, JPEG, WEBP)

    Returns:
        Extracted text string

    Raises:
        Exception: If OCR fails or Tesseract not installed
    """
    try:
        import pytesseract
        from PIL import Image

        # Open image and run OCR
        image = Image.open(file_path)
        text = pytesseract.image_to_string(image)

        if text.strip():
            logger.info(f"Extracted {len(text)} chars from image using OCR")
            return text.strip()
        else:
            raise Exception("No text found in image")

    except ImportError:
        raise Exception("pytesseract or PIL not installed. Run: pip install pytesseract Pillow")

    except pytesseract.pytesseract.TesseractNotFoundError:
        raise Exception(
            "Tesseract OCR not installed. "
            "Install from: https://github.com/tesseract-ocr/tesseract"
        )

    except Exception as e:
        raise Exception(f"OCR extraction failed: {str(e)}")


def extract_text_from_document(file_path: Path) -> str:
    """
    Extract text from any supported document format.

    Automatically detects file type and uses appropriate extraction method.

    Args:
        file_path: Path to document file

    Returns:
        Extracted text string

    Raises:
        Exception: If file type unsupported or extraction fails

    Example:
        >>> text = extract_text_from_document(Path("invoice.pdf"))
        >>> print(text[:100])
        INVOICE
        Date: 12/10/2025
        From: ABC Electric
        Total: $100.00
    """
    # Get file extension
    ext = file_path.suffix.lower()

    # Route to appropriate extractor
    if ext == '.pdf':
        return extract_text_from_pdf(file_path)

    elif ext in {'.png', '.jpg', '.jpeg', '.webp'}:
        return extract_text_from_image(file_path)

    elif ext in {'.doc', '.docx'}:
        # TODO: Implement Word document extraction (Phase 5)
        # Could use python-docx library
        raise Exception(f"Word document extraction not yet implemented")

    else:
        raise Exception(f"Unsupported file format: {ext}")
