"""
File upload utilities: validation, temp file handling, size enforcement, and
DOCX output generation.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH  # noqa: F401 – available for callers
from fastapi import HTTPException, UploadFile


# ---------------------------------------------------------------------------
# Allowed upload extensions
# ---------------------------------------------------------------------------

# .doc is intentionally excluded — the extractor cannot handle legacy binary
# Word format and would raise a ValueError, producing a confusing 500 error.
# Users should convert to .docx or .pdf first.
RESUME_UPLOAD_EXTENSIONS = {".pdf", ".docx"}
JOB_DESCRIPTION_UPLOAD_EXTENSIONS = {".pdf", ".docx", ".txt", ".png", ".jpg", ".jpeg"}

# Maximum upload size per file (10 MB). Override via MAX_UPLOAD_BYTES env var.
MAX_UPLOAD_BYTES: int = int(os.getenv("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_upload_file(uploaded_file: UploadFile, allowed_extensions: set[str]) -> None:
    """Raise HTTP 400 if the file extension is not in the allowed set."""
    suffix = Path(uploaded_file.filename or "").suffix.lower()
    if suffix not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type '{suffix}' for {uploaded_file.filename!r}. "
                f"Allowed types: {sorted(allowed_extensions)}"
            ),
        )


# ---------------------------------------------------------------------------
# Temp file management
# ---------------------------------------------------------------------------

async def save_upload_to_temp_file(uploaded_file: UploadFile) -> str:
    """Save an uploaded file to a temporary path, enforcing MAX_UPLOAD_BYTES.

    Reads the file in 64 KB chunks to avoid loading the entire payload into
    memory at once.  Raises HTTP 413 if the file exceeds the size limit.
    """
    suffix = Path(uploaded_file.filename or "").suffix
    total = 0
    chunk_size = 64 * 1024  # 64 KB

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        temp_path = tmp.name
        while True:
            chunk = await uploaded_file.read(chunk_size)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_UPLOAD_BYTES:
                tmp.close()
                Path(temp_path).unlink(missing_ok=True)
                raise HTTPException(
                    status_code=413,
                    detail=(
                        f"Upload too large. Maximum allowed size is "
                        f"{MAX_UPLOAD_BYTES // (1024 * 1024)} MB."
                    ),
                )
            tmp.write(chunk)

    return temp_path


def remove_temp_files(*paths: str | None) -> None:
    """Delete temporary files, ignoring missing files."""
    for temp_path in paths:
        if temp_path and Path(temp_path).exists():
            Path(temp_path).unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# DOCX output — styled resume writer
# ---------------------------------------------------------------------------

# Common resume section titles or standard ALL-CAPS headings (1 to 6 words)
_KNOWN_HEADINGS = {
    "EXPERIENCE", "WORK EXPERIENCE", "PROFESSIONAL EXPERIENCE", "EMPLOYMENT HISTORY",
    "EDUCATION", "ACADEMIC BACKGROUND",
    "SKILLS", "TECHNICAL SKILLS", "CORE COMPETENCIES", "KEY SKILLS", "AREAS OF EXPERTISE",
    "PROJECTS", "KEY PROJECTS", "PERSONAL PROJECTS",
    "CERTIFICATIONS", "CERTIFICATES", "LICENSES & CERTIFICATIONS",
    "SUMMARY", "PROFESSIONAL SUMMARY", "EXECUTIVE SUMMARY", "CAREER OBJECTIVE", "OBJECTIVE",
    "AWARDS", "HONORS & AWARDS", "ACHIEVEMENTS",
    "PUBLICATIONS", "VOLUNTEER WORK", "VOLUNTEERING", "LANGUAGES", "INTERESTS", "REFERENCES"
}

def _looks_like_heading(line: str) -> bool:
    """Check if a line looks like a resume section heading."""
    stripped = line.strip()
    if not stripped or len(stripped) > 60:
        return False

    normalized = stripped.rstrip(":").upper()
    if normalized in _KNOWN_HEADINGS:
        return True

    words = stripped.split()
    if not (1 <= len(words) <= 6):
        return False

    # Check if all letters are uppercase and at least 3 letters are present
    alpha_chars = [c for c in stripped if c.isalpha()]
    return len(alpha_chars) >= 3 and all(c.isupper() for c in alpha_chars)


def write_resume_docx(resume_text: str) -> str:
    """Write a styled DOCX from the rewritten resume plain text.

    Improvements over plain paragraph-per-line approach:
    - Calibri 11pt default body font for a professional look.
    - ALL-CAPS section lines (e.g. EXPERIENCE, EDUCATION) → Heading 2 style
      with teal accent colour matching the app palette.
    - Proper paragraph spacing (6pt after body paragraphs).
    - Empty lines produce compact spacers instead of blank paragraphs.
    """
    document = Document()

    # --- Set default body font ---
    style_normal = document.styles["Normal"]
    style_normal.font.name = "Calibri"
    style_normal.font.size = Pt(11)

    # --- Customise Heading 2 to match the app's teal primary colour ---
    style_h2 = document.styles["Heading 2"]
    style_h2.font.name = "Calibri"
    style_h2.font.size = Pt(12)
    style_h2.font.bold = True
    style_h2.font.color.rgb = RGBColor(0x14, 0xB8, 0x90)  # --primary-strong

    lines = resume_text.split("\n")

    for line in lines:
        stripped = line.strip()

        if not stripped:
            # Compact spacer — add a tiny empty paragraph
            spacer = document.add_paragraph("")
            spacer.paragraph_format.space_after = Pt(2)
            continue

        if _looks_like_heading(stripped):
            document.add_heading(stripped, level=2)
        else:
            para = document.add_paragraph(stripped)
            para.paragraph_format.space_after = Pt(6)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
        temp_docx_path = tmp.name

    document.save(temp_docx_path)
    return temp_docx_path
