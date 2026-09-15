"""
Text extraction service.

Supports PDF (pdfplumber with per-page OCR fallback for scanned pages), DOCX
(body paragraphs + tables + section headers/footers), plain text, and images
(EasyOCR with Pillow preprocessing).
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import easyocr

# Module-level singleton so the heavy EasyOCR model loads only once.
_ocr_reader: easyocr.Reader | None = None

# Minimum character count for a PDF page to be considered text-based.
# Pages below this threshold are treated as scanned and re-processed with OCR.
_PDF_TEXT_THRESHOLD = 50

# Minimum EasyOCR confidence score to accept a detection.
_OCR_CONFIDENCE_THRESHOLD = 0.4


def _get_ocr_reader() -> easyocr.Reader:
    """Return a cached EasyOCR reader instance."""
    global _ocr_reader
    if _ocr_reader is None:
        _ocr_reader = easyocr.Reader(["en"], gpu=False)
    return _ocr_reader


# ---------------------------------------------------------------------------
# Text normalisation
# ---------------------------------------------------------------------------

def clean_text(raw_text: str | list[str]) -> str:
    """Normalize extracted text so downstream services receive predictable input.

    Handles:
    - CRLF / CR line endings
    - BOM characters
    - Repeated whitespace and blank lines
    - Unicode ligatures (ﬁ → fi, ﬂ → fl, etc.) via NFKC normalisation
    - Smart quotes / curly apostrophes → ASCII equivalents
    - Non-breaking spaces
    - En-dashes / em-dashes → hyphens (preserves readability for skill names)
    """
    if isinstance(raw_text, list):
        text = "\n".join(raw_text)
    else:
        text = raw_text

    # NFKC resolves ligatures, superscripts, and other compatibility forms.
    text = unicodedata.normalize("NFKC", text)

    # Line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # BOM / zero-width chars
    text = re.sub(r"[\ufeff\u200b\u200c\u200d\ufffe]", "", text)

    # Non-breaking space → regular space
    text = text.replace("\u00a0", " ").replace("\u202f", " ")

    # Smart quotes → ASCII
    text = text.translate(str.maketrans("\u2018\u2019\u201c\u201d", "''\"\""))

    # En-dash / em-dash → hyphen (preserves skill-name boundaries)
    text = text.translate(str.maketrans("\u2013\u2014", "--"))

    # Collapse horizontal whitespace; tidy vertical spacing
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# ---------------------------------------------------------------------------
# OCR helpers
# ---------------------------------------------------------------------------

def _ocr_image_path(image_path: str | Path) -> str:
    """Run EasyOCR on a file path with Pillow preprocessing.

    Preprocessing (grayscale + contrast boost) significantly improves
    recognition accuracy on low-contrast or photocopied documents.
    """
    from PIL import Image, ImageEnhance, ImageOps  # noqa: PLC0415

    img = Image.open(str(image_path)).convert("L")  # grayscale
    img = ImageOps.autocontrast(img)
    img = ImageEnhance.Contrast(img).enhance(2.0)

    reader = _get_ocr_reader()
    # EasyOCR accepts a PIL image or a numpy array.
    import numpy as np  # noqa: PLC0415
    result = reader.readtext(np.array(img))

    lines = [
        detection[1]
        for detection in result
        if detection[2] >= _OCR_CONFIDENCE_THRESHOLD
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# PDF extraction (pdfplumber + per-page OCR fallback)
# ---------------------------------------------------------------------------

def extract_text_from_pdf(file_path: str | Path) -> str:
    """Extract text from a PDF file.

    Strategy:
    1. Use pdfplumber for each page — it preserves reading order and handles
       multi-column layouts far better than PyPDF2.
    2. If a page yields fewer than ``_PDF_TEXT_THRESHOLD`` characters it is
       likely scanned / image-based.  In that case the page is rendered to a
       PIL image and processed with EasyOCR.
    """
    import pdfplumber  # noqa: PLC0415

    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {path}")

    page_texts: list[str] = []

    with pdfplumber.open(str(path)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text(layout=True) or ""

            if len(page_text.strip()) < _PDF_TEXT_THRESHOLD:
                # Scanned page — render to image and OCR.
                try:
                    pil_image = page.to_image(resolution=200).original
                    reader = _get_ocr_reader()
                    import numpy as np  # noqa: PLC0415
                    result = reader.readtext(np.array(pil_image))
                    page_text = "\n".join(
                        det[1]
                        for det in result
                        if det[2] >= _OCR_CONFIDENCE_THRESHOLD
                    )
                except Exception:
                    # If image rendering fails, keep whatever text we got.
                    pass

            if page_text.strip():
                page_texts.append(page_text)

    return clean_text("\n\n".join(page_texts))


# ---------------------------------------------------------------------------
# DOCX extraction (body + tables + section headers/footers)
# ---------------------------------------------------------------------------

def _iter_docx_text(document) -> list[str]:  # type: ignore[type-arg]
    """Yield all text blocks from a python-docx Document in document order.

    Covers:
    - Body paragraphs (the main text flow)
    - Tables (skills matrices, experience grids)
    - Section headers and footers (contact info often lives here)
    """
    parts: list[str] = []

    # Body paragraphs
    for para in document.paragraphs:
        stripped = para.text.strip()
        if stripped:
            parts.append(stripped)

    # Tables — visit every cell in every row of every table
    for table in document.tables:
        for row in table.rows:
            row_cells: list[str] = []
            for cell in row.cells:
                cell_text = " ".join(
                    p.text.strip() for p in cell.paragraphs if p.text.strip()
                )
                if cell_text:
                    row_cells.append(cell_text)
            if row_cells:
                parts.append(" | ".join(row_cells))

    # Section headers and footers
    for section in document.sections:
        for region in (section.header, section.footer):
            try:
                for para in region.paragraphs:
                    stripped = para.text.strip()
                    if stripped:
                        parts.append(stripped)
            except Exception:
                pass

    return parts


def extract_text_from_docx(file_path: str | Path) -> str:
    """Extract text from a DOCX file including tables and section headers/footers."""
    from docx import Document  # noqa: PLC0415

    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"DOCX file not found: {path}")

    document = Document(str(path))
    parts = _iter_docx_text(document)
    return clean_text("\n".join(parts))


# ---------------------------------------------------------------------------
# Plain-text extraction
# ---------------------------------------------------------------------------

def extract_text_from_txt(file_path: str | Path) -> str:
    """Extract text from a plain-text file (TXT, MD, CSV, RTF)."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Text file not found: {path}")

    return clean_text(path.read_text(encoding="utf-8", errors="ignore"))


# ---------------------------------------------------------------------------
# Image extraction (EasyOCR + Pillow preprocessing)
# ---------------------------------------------------------------------------

def extract_text_from_image(file_path: str | Path) -> str:
    """Extract text from an image file using EasyOCR with preprocessing."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {path}")

    text = _ocr_image_path(path)
    if not text.strip():
        raise ValueError(
            f"No text could be detected in the image: {path.name}. "
            "Ensure the image is clear and well-lit."
        )
    return clean_text(text)


# ---------------------------------------------------------------------------
# Unified dispatcher
# ---------------------------------------------------------------------------

def extract_text_from_file(file_path: str | Path) -> str:
    """Dispatch to the appropriate extractor based on file extension."""
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return extract_text_from_pdf(path)
    if suffix == ".docx":
        return extract_text_from_docx(path)
    if suffix == ".doc":
        raise ValueError(
            "Legacy .doc format is not supported. Please convert to .docx or .pdf before uploading."
        )
    if suffix in {".txt", ".md", ".csv", ".rtf"}:
        return extract_text_from_txt(path)
    if suffix in {".png", ".jpg", ".jpeg"}:
        return extract_text_from_image(path)

    raise ValueError(f"Unsupported file type: {path.suffix or 'no extension'}")
