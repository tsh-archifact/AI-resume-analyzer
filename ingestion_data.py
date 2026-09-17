"""
Compatibility shim — re-exports all public symbols from
``services.text_extraction_service``.

.. deprecated::
   Import directly from ``services.text_extraction_service`` instead.
   This module exists only to avoid breaking any external scripts that
   referenced the old top-level ``ingestion_data`` module.
"""

from services.text_extraction_service import (
    clean_text,
    extract_markdown_from_file,
    extract_text_from_docx,
    extract_text_from_file,
    extract_text_from_image,
    extract_text_from_pdf,
    extract_text_from_txt,
)


__all__ = [
    "clean_text",
    "extract_markdown_from_file",
    "extract_text_from_docx",
    "extract_text_from_file",
    "extract_text_from_image",
    "extract_text_from_pdf",
    "extract_text_from_txt",
]
