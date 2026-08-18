import tempfile
from pathlib import Path

from docx import Document
from fastapi import HTTPException, UploadFile


ALLOWED_UPLOAD_EXTENSIONS = {".pdf", ".doc", ".docx", ".txt", ".md", ".csv", ".rtf", ".png", ".jpg", ".jpeg"}


def validate_upload_file(uploaded_file: UploadFile) -> None:
    suffix = Path(uploaded_file.filename or "").suffix.lower()
    if suffix not in ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type for {uploaded_file.filename}. Allowed: {sorted(ALLOWED_UPLOAD_EXTENSIONS)}",
        )


async def save_upload_to_temp_file(uploaded_file: UploadFile) -> str:
    suffix = Path(uploaded_file.filename or "").suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file.write(await uploaded_file.read())
        return temp_file.name


def remove_temp_files(*paths: str | None) -> None:
    for temp_path in paths:
        if temp_path and Path(temp_path).exists():
            Path(temp_path).unlink(missing_ok=True)


def write_resume_docx(resume_text: str) -> str:
    document = Document()

    for paragraph in resume_text.split("\n"):
        document.add_paragraph(paragraph.strip() if paragraph.strip() else "")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as temp_doc:
        temp_docx_path = temp_doc.name

    document.save(temp_docx_path)
    return temp_docx_path
