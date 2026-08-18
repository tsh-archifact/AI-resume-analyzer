import json
import re

from config.llm_setup import get_llm_api_key, get_llm_client, get_llm_model
from schemas.resume import SkillComparisonResult
from services.prompts import build_skill_extraction_prompt


def normalize_skill(skill: str) -> str:
    return re.sub(r"\s+", " ", skill.strip()).strip(" -;:|")


def unique_skills(skills: list[str]) -> list[str]:
    unique = []
    seen = set()

    for skill in skills:
        clean = normalize_skill(skill)
        key = clean.lower()
        if clean and key not in seen:
            unique.append(clean)
            seen.add(key)

    return unique


def extract_skills_from_text(text: str, section_name: str = "skills") -> list[str]:
    """Extract skills without an LLM as a best-effort fallback."""
    if not text:
        return []

    lines = [line.strip() for line in text.replace("\r", "\n").split("\n")]
    skills: list[str] = []

    for idx, line in enumerate(lines):
        lower = line.lower()
        has_skill_header = any(
            keyword in lower
            for keyword in ["skill", "technologies", "tools", "core competencies", "competencies", "stack"]
        )
        if not has_skill_header:
            continue

        remainder = line.split(":", 1)[1] if ":" in line else ""
        if remainder:
            skills.extend(normalize_skill(part) for part in re.split(r"[,|/]+", remainder))
            continue

        for next_line in lines[idx + 1 : idx + 8]:
            next_lower = next_line.lower()
            if next_line and not any(keyword in next_lower for keyword in ["experience", "education", "projects", "summary"]):
                skills.extend(normalize_skill(part) for part in re.split(r"[,|/]+", next_line))
            if len(skills) >= 20:
                break

    if not skills:
        for line in lines:
            if any(char in line for char in [",", ";", "|"]):
                skills.extend(
                    clean
                    for clean in (normalize_skill(part) for part in re.split(r"[,;|]+", line))
                    if clean and len(clean.split()) <= 4
                )
            if len(skills) >= 20:
                break

    return unique_skills(skills)[:20]


def extract_skills_with_llm(text: str, label: str) -> list[str]:
    if not get_llm_api_key():
        return []

    try:
        client = get_llm_client()
        response = client.chat.completions.create(
            model=get_llm_model(),
            temperature=0.1,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "Extract skills only. No explanations."},
                {"role": "user", "content": build_skill_extraction_prompt(text, label)},
            ],
        )
        content = response.choices[0].message.content
        if not content:
            return []

        parsed = json.loads(content)
        skills = parsed.get("skills", [])
        if not isinstance(skills, list):
            return []

        return unique_skills([str(item) for item in skills])
    except Exception:
        return []


def get_best_skill_list(text: str, label: str) -> list[str]:
    return extract_skills_with_llm(text, label) or extract_skills_from_text(text, label)


def compare_skill_lists(resume_skills: list[str], jd_skills: list[str]) -> SkillComparisonResult:
    resume_set = {skill.lower() for skill in resume_skills}
    jd_set = {skill.lower() for skill in jd_skills}
    union = resume_set | jd_set
    score = round((len(resume_set & jd_set) / len(union)) * 100, 2) if union else 0.0

    return SkillComparisonResult(
        matched_skills=[skill for skill in resume_skills if skill.lower() in jd_set],
        missing_skills=[skill for skill in jd_skills if skill.lower() not in resume_set],
        match_score=score,
    )


def calculate_similarity(resume_text: str, jd_text: str) -> SkillComparisonResult:
    resume_skills = get_best_skill_list(resume_text, "resume")
    jd_skills = get_best_skill_list(jd_text, "job description")
    return compare_skill_lists(resume_skills, jd_skills)
