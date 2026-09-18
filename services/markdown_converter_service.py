from __future__ import annotations

import re
from pathlib import Path
from utils.logger import LOGS_DIR, get_pipeline_logger

logger = get_pipeline_logger()

# Known common resume & job description section titles for markdown structuring
_SECTION_HEADERS = [
    # General / Resume headers
    "summary",
    "professional summary",
    "executive summary",
    "about me",
    "profile",
    "skills",
    "technical skills",
    "core competencies",
    "competencies",
    "technologies",
    "tools & technologies",
    "experience",
    "work experience",
    "professional experience",
    "employment history",
    "work history",
    "education",
    "academic background",
    "projects",
    "key projects",
    "academic projects",
    "personal projects",
    "certifications",
    "licenses & certifications",
    "achievements",
    "awards & honors",
    "publications",
    "languages",
    "interests",
    # Job Description headers
    "job description",
    "job summary",
    "position summary",
    "role summary",
    "the role",
    "about the role",
    "role overview",
    "overview",
    "about us",
    "about the company",
    "company overview",
    "who we are",
    "responsibilities",
    "key responsibilities",
    "duties & responsibilities",
    "what you'll do",
    "what you will do",
    "day-to-day responsibilities",
    "requirements",
    "minimum requirements",
    "required qualifications",
    "basic qualifications",
    "must haves",
    "must have",
    "what you'll bring",
    "what you bring",
    "what we're looking for",
    "what we look for",
    "qualifications",
    "preferred qualifications",
    "desired qualifications",
    "nice to have",
    "nice to haves",
    "bonus qualifications",
    "bonus points",
    "skills required",
    "required skills",
    "technical requirements",
    "benefits",
    "perks",
    "perks & benefits",
    "what we offer",
    "compensation & benefits",
]


# Root keywords commonly found in resume and job description headings
_HEADING_KEYWORDS = {
    "summary", "profile", "overview", "about", "role", "roles",
    "job", "responsibility", "responsibilities", "duty", "duties",
    "requirement", "requirements", "qualification", "qualifications",
    "education", "educational", "academic", "skill", "skills", "competency", "competencies",
    "experience", "employment", "history", "project", "projects",
    "certification", "certifications", "achievement", "achievements",
    "award", "awards", "benefit", "benefits", "perk", "perks", "compensation",
    "language", "languages", "criteria", "eligibility", "scope", "specification", "specifications",
    "technology", "technologies"
}


def convert_cleaned_text_to_markdown(
    text: str,
    document_title: str = "",
    save_path: str | Path | None = None,
) -> str:
    """
    Transforms extracted & cleaned text (Resume or Job Description) into clean, structured Markdown.
    
    1. Detects section titles and converts them to H2 markdown headers (`## Section`).
    2. Formats bullet points with standard markdown list indicators (`- `).
    3. Converts labeled requirement items (`Keyword: Details`) into bold bullet items (`- **Keyword**: Details`).
    4. Retains and structures paragraph flow.
    5. Optionally saves the generated Markdown to a file (e.g. logs/extracted_jd.md).
    """
    if not text or not text.strip():
        logger.warning("[MARKDOWN CONVERSION] Empty text provided for markdown conversion.")
        return ""

    logger.info(f"[MARKDOWN CONVERSION] Starting text to Markdown conversion (Input length: {len(text)} chars)")

    lines = [line.strip() for line in text.replace("\r", "\n").split("\n")]
    md_lines: list[str] = []
    headers_found: list[str] = []

    if document_title:
        md_lines.append(f"# {document_title}")
        md_lines.append("")
        logger.info(f"   [SECTION DETECTED] Title: '# {document_title}'")

    for line in lines:
        if not line:
            if md_lines and md_lines[-1] != "":
                md_lines.append("")
            continue

        clean_lower = line.lower().strip(" :#-—*•")
        words = [w.lower() for w in re.findall(r"\b\w+\b", clean_lower)]

        # 1. Check if line matches known section headers or is a standalone section heading
        is_known_header = clean_lower in _SECTION_HEADERS or (len(line) < 45 and any(clean_lower == h for h in _SECTION_HEADERS))
        is_dynamic_header = (
            1 <= len(words) <= 6
            and len(line) < 50
            and not any(char in line for char in [".", ";", ","])
            and (
                line.endswith(":")
                or any(w in _HEADING_KEYWORDS for w in words)
            )
        )

        if is_known_header or is_dynamic_header:
            md_lines.append("")
            header_title = " ".join(word.capitalize() for word in clean_lower.split())
            md_lines.append(f"## {header_title}")
            md_lines.append("")
            headers_found.append(header_title)
            logger.info(f"   [SECTION DETECTED] Header: '## {header_title}'")
            continue

        # 2. Check if line is already a bullet item
        bullet_match = re.match(r"^[-*•–—\d\.\)]\s*(.+)$", line)
        if bullet_match:
            bullet_text = bullet_match.group(1).strip()
            md_lines.append(f"- {bullet_text}")
            continue

        # 3. Check for labeled criteria (common in JDs: "Skill/Topic: Description")
        if ":" in line and not line.startswith("http"):
            parts = line.split(":", 1)
            prefix = parts[0].strip()
            details = parts[1].strip()
            # If the label is short (1-4 words) and followed by substantial text
            if 1 <= len(prefix.split()) <= 4 and len(details) > 8 and not any(p in prefix for p in [".", ",", ";"]):
                md_lines.append(f"- **{prefix}**: {details}")
                continue

        # 4. Regular text line
        md_lines.append(line)

    markdown_result = "\n".join(md_lines).strip()
    logger.info(
        f"[MARKDOWN CONVERSION] Completed. Generated {len(markdown_result)} chars with {len(headers_found)} sections: {headers_found}"
    )

    # Save to file if save_path is provided
    if save_path:
        out_file = Path(save_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(markdown_result, encoding="utf-8")
        logger.info(f"[MARKDOWN SAVED] Saved markdown to file: {out_file.resolve()}")

    return markdown_result


def convert_file_to_markdown(file_path: str | Path) -> str:
    """
    Converts a document file (PDF, DOCX, TXT) into Markdown using MarkItDown
    (LangChain ecosystem document converter), with fallback to text-to-markdown transformation.
    """
    path = Path(file_path)
    if not path.exists():
        logger.error(f"[MARKDOWN CONVERSION] File not found: {path}")
        raise FileNotFoundError(f"File not found: {path}")

    logger.info(f"[MARKDOWN CONVERSION] Attempting MarkItDown converter on file: {path.name} ({path.stat().st_size} bytes)")

    try:
        from markitdown import MarkItDown
        md = MarkItDown()
        result = md.convert(str(path))
        content = result.text_content.strip()
        if content:
            logger.info(f"[MARKDOWN CONVERSION] MarkItDown successfully converted {path.name} ({len(content)} markdown chars)")
            return content
    except Exception as error:
        logger.warning(f"[MARKDOWN CONVERSION] MarkItDown file conversion failed ({error}), falling back to text extraction + markdown formatter.")

    # Fallback: Extract text and convert to markdown
    from services.text_extraction_service import extract_text_from_file
    extracted_text = extract_text_from_file(path)
    return convert_cleaned_text_to_markdown(extracted_text, document_title=path.stem)
