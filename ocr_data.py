"""
Compatibility shim — re-exports OCR and text-extraction helpers from
``services.text_extraction_service``.

.. deprecated::
   Import directly from ``services.text_extraction_service`` instead.
   This module exists only to avoid breaking any external scripts that
   referenced the old top-level ``ocr_data`` module.

   Note: ``extract_text_from_image`` (the primary OCR entry-point) was
   previously missing from this shim's ``__all__`` despite the module name.
   It is now included.
"""

from services.text_extraction_service import (
    clean_text,
    extract_text_from_docx,
    extract_text_from_file,
    extract_text_from_image,
    extract_text_from_pdf,
    extract_text_from_txt,
)


__all__ = [
    "clean_text",
    "extract_text_from_docx",
    "extract_text_from_file",
    "extract_text_from_image",
    "extract_text_from_pdf",
    "extract_text_from_txt",
]
