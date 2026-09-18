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


async def resolve_job_description(
    job_description: UploadFile | None,
    job_description_text: str | None,
) -> tuple[str | None, str, str]:
    """Validate and resolve job description from an uploaded file or direct text input."""
    if job_description is not None and job_description_text and job_description_text.strip():
        raise HTTPException(status_code=400, detail="Provide either job_description or job_description_text, not both.")

    if job_description is None and not job_description_text:
        raise HTTPException(status_code=400, detail="Provide a job_description file or job_description_text.")

    if job_description_text is not None:
        text = job_description_text.strip()
        if not text:
            raise HTTPException(status_code=400, detail="job_description_text must not be empty.")
        return None, text, "job_description_text"

    validate_upload_file(job_description, JOB_DESCRIPTION_UPLOAD_EXTENSIONS)
    job_description_path = await save_upload_to_temp_file(job_description)
    from services.text_extraction_service import extract_text_from_file

    return job_description_path, extract_text_from_file(job_description_path), job_description.filename or "job_description"


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


def write_resume_docx(resume_text: str, template_id: str = "modern_teal") -> str:
    """Write a styled DOCX from the rewritten resume markdown or plain text using the selected template."""
    from services.docx_generator_service import generate_resume_docx

    return generate_resume_docx(resume_text, template_id=template_id)

