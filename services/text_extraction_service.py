from pathlib import Path
import re

import easyocr
from docx import Document
from PyPDF2 import PdfReader


def clean_text(raw_text: str) -> str:
    """Normalize extracted text so downstream services receive predictable input."""
    if raw_text is None:
        return ""

    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\ufeff", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_text_from_pdf(file_path: str | Path) -> str:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {path}")

    reader = PdfReader(str(path))
    pages = [page.extract_text() or "" for page in reader.pages]
    return clean_text("\n\n".join(pages))


def extract_text_from_docx(file_path: str | Path) -> str:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"DOCX file not found: {path}")

    document = Document(str(path))
    paragraphs = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
    return clean_text("\n".join(paragraphs))


def extract_text_from_txt(file_path: str | Path) -> str:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Text file not found: {path}")

    return clean_text(path.read_text(encoding="utf-8", errors="ignore"))


def extract_text_from_image(file_path: str | Path) -> str:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {path}")

    reader = easyocr.Reader(["en"], gpu=False)
    result = reader.readtext(str(path))
    text = "\n".join(detection[1] for detection in result)
    return clean_text(text)


def extract_text_from_file(file_path: str | Path) -> str:
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return extract_text_from_pdf(path)
    if suffix in {".doc", ".docx"}:
        return extract_text_from_docx(path)
    if suffix in {".txt", ".md", ".csv", ".rtf"}:
        return extract_text_from_txt(path)
    if suffix in {".png", ".jpg", ".jpeg"}:
        return extract_text_from_image(path)

    raise ValueError(f"Unsupported file type: {path.suffix or 'no extension'}")
