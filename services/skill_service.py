import json
import re

from config.llm_setup import get_llm_api_key, get_llm_client, get_llm_model
from schemas.resume import SkillComparisonResult,ResumeSkills,JobDescriptionSkills
from services.prompts import build_skill_extraction_prompt


def normalize_skill(skill: str) -> str:
    return re.sub(r"\s+", " ", skill.strip()).strip(" -;:|")

def is_skill_match(skill1: str, skill2: str) -> bool:
    words1 = set(skill1.lower().split())
    words2 = set(skill2.lower().split())

    return words1.issubset(words2) or words2.issubset(words1)



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

def compare_skill_lists(
    resume_skills: ResumeSkills,
    jd_skills: JobDescriptionSkills
) -> SkillComparisonResult:

    resume_set = {skill.lower() for skill in resume_skills.skills}
    jd_set = {skill.lower() for skill in jd_skills.skills}

    matched_skills = []
    missing_skills = []

    for resume_skill in resume_skills.skills:

        resume_normalized = resume_skill.lower()

        found_match = any(
            is_skill_match(resume_normalized, jd_skill)
            for jd_skill in jd_set
        )

        if found_match:
            matched_skills.append(resume_skill)

    for jd_skill in jd_skills.skills:

        jd_normalized = jd_skill.lower()

        found_match = any(
            is_skill_match(jd_normalized, resume_skill)
            for resume_skill in resume_set
        )

        if not found_match:
            missing_skills.append(jd_skill)

    # Calculate score
    matched_count = len(matched_skills)
    total_jd_skills = len(jd_set)

    score = (
        round((matched_count / total_jd_skills) * 100, 2)
        if total_jd_skills
        else 0.0
    )

    return SkillComparisonResult(
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        match_score=score,
    )


def calculate_similarity(resume_text:ResumeSkills, jd_text:JobDescriptionSkills) -> SkillComparisonResult:
    resume_skills = resume_text
    jd_skills = jd_text
    return compare_skill_lists(resume_skills, jd_skills)
