from config.llm_setup import get_llm_api_key, get_llm_client, get_llm_model
from services.prompts import build_resume_rewrite_prompt


def format_resume_text(resume_text: str) -> str:
    """Keep fallback output readable without inventing new resume content."""
    section_names = {"profile", "education", "projects", "skills", "languages"}
    lines = [line.strip() for line in resume_text.replace("\r", "\n").split("\n") if line.strip()]
    formatted_lines: list[str] = []

    for line in lines:
        lower = line.lower().strip()
        if lower in section_names and formatted_lines and formatted_lines[-1] != "":
            formatted_lines.append("")

        if lower in section_names:
            formatted_lines.append(line)
            continue

        previous_line = formatted_lines[-1].lower() if formatted_lines else ""
        is_skill_line = ":" in line and previous_line == "skills"
        is_skill_category = ":" in line and any(
            line.lower().startswith(prefix) for prefix in ["programming", "core", "databases", "soft skills"]
        )

        if is_skill_line or (formatted_lines and formatted_lines[-1].startswith("- ") and is_skill_category):
            formatted_lines.append(f"- {line.removeprefix('-').strip()}")
        else:
            formatted_lines.append(line)

    return "\n".join(formatted_lines).strip()


def build_fallback_resume(resume_text: str, _jd_text: str) -> str:
    return format_resume_text(resume_text)


def rewrite_resume_with_llm(resume_text: str, jd_text: str) -> str:
    if not get_llm_api_key():
        return build_fallback_resume(resume_text, jd_text)

    try:
        client = get_llm_client()
        response = client.chat.completions.create(
            model=get_llm_model(),
            temperature=0.3,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert resume writer. Rewrite resumes to match job descriptions while keeping them truthful and ATS-friendly.",
                },
                {"role": "user", "content": build_resume_rewrite_prompt(resume_text, jd_text)},
            ],
        )
        content = response.choices[0].message.content
        return content.strip() if content else build_fallback_resume(resume_text, jd_text)
    except Exception:
        return build_fallback_resume(resume_text, jd_text)
