import json
import re
from datetime import date
from typing import Any

from config.llm_setup import get_llm_api_key, get_llm_client, get_llm_model
from schemas.resume import (
    Evidence,
    ExperiencePeriod,
    ExtractedSkill,
    JobDescriptionProfile,
    ResumeProfile,
)
from services.prompts import build_profile_extraction_prompt


_DATE_RE = re.compile(r"\b((?:19|20)\d{2})(?:\s*[-/]\s*((?:19|20)\d{2}|present|current))?\b", re.I)
_YEARS_RE = re.compile(r"(?<!\d)(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)\b", re.I)
_ALIASES = {
    "js": "javascript",
    "ts": "typescript",
    "postgres": "postgresql",
    "postgres sql": "postgresql",
    "reactjs": "react",
    "nodejs": "node.js",
    "rest": "restful apis",
}


def normalize_keyword(value: str) -> str:
    value = re.sub(r"\s+", " ", value.lower().strip(" -;:|."))
    value = re.sub(r"\b(?:v|version)\s*(\d+(?:\.\d+)*)\b", r"\1", value)
    return _ALIASES.get(value, value)


def _unique(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        clean = value.strip()
        key = normalize_keyword(clean)
        if key and key not in seen:
            result.append(clean)
            seen.add(key)
    return result


def _evidence(value: Any) -> list[Evidence]:
    if not isinstance(value, list):
        return []
    result = []
    for item in value:
        if isinstance(item, str):
            result.append(Evidence(text=item, confidence=0.5))
        elif isinstance(item, dict) and item.get("text"):
            result.append(Evidence(text=str(item["text"]), confidence=float(item.get("confidence", 0.5))))
    return result


def _skills(values: Any) -> list[ExtractedSkill]:
    if not isinstance(values, list):
        return []
    result = []
    for item in values:
        if isinstance(item, str):
            result.append(ExtractedSkill(name=item))
        elif isinstance(item, dict) and item.get("name"):
            result.append(ExtractedSkill(
                name=str(item["name"]),
                category=str(item.get("category") or "technical"),
                years_experience=item.get("years_experience"),
                evidence=_evidence(item.get("evidence")),
            ))
    unique: dict[str, ExtractedSkill] = {}
    for skill in result:
        unique.setdefault(normalize_keyword(skill.name), skill)
    return list(unique.values())


def _periods(values: Any) -> list[ExperiencePeriod]:
    if not isinstance(values, list):
        return []
    result = []
    for item in values:
        if isinstance(item, dict):
            result.append(ExperiencePeriod(
                title=str(item.get("title") or ""),
                company=str(item.get("company") or ""),
                start_date=item.get("start_date"),
                end_date=item.get("end_date"),
                evidence=_evidence(item.get("evidence")),
            ))
    return result


def _parse_json(content: str) -> dict[str, Any]:
    parsed = json.loads(content)
    if not isinstance(parsed, dict):
        raise ValueError("Profile response is not a JSON object")
    return parsed


def _load_spacy():
    try:
        import spacy
        from config.llm_setup import get_spacy_model
        return spacy.load(get_spacy_model())
    except Exception as error:
        raise RuntimeError("spaCy model is unavailable. Install spaCy and the configured English model.") from error


def _validate_with_spacy(text: str, keywords: list[str]) -> list[str]:
    nlp = _load_spacy()
    doc = nlp(text[:12000])
    source = {token.text.lower() for token in doc if not token.is_space}
    # spaCy performs tokenization/entity validation; retain multi-word LLM phrases
    # when at least one meaningful token occurs in the document.
    return _unique([keyword for keyword in keywords if any(part in source for part in normalize_keyword(keyword).split())])


def _infer_years(text: str) -> float | None:
    matches = [float(match.group(1)) for match in _YEARS_RE.finditer(text)]
    return max(matches) if matches else None


def _timeline_years(periods: list[ExperiencePeriod]) -> float | None:
    intervals: list[tuple[int, int]] = []
    current_year = date.today().year
    for period in periods:
        if not period.start_date:
            continue
        start_match = re.search(r"(?:19|20)\d{2}", period.start_date)
        end_match = re.search(r"(?:19|20)\d{2}", period.end_date or "")
        if not start_match:
            continue
        start = int(start_match.group())
        end = int(end_match.group()) if end_match else current_year
        if end >= start:
            intervals.append((start, end))
    if not intervals:
        return None
    intervals.sort()
    merged = [list(intervals[0])]
    for start, end in intervals[1:]:
        if start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return round(sum(end - start for start, end in merged), 2)


def extract_profile(text: str, document_type: str) -> ResumeProfile | JobDescriptionProfile:
    if not get_llm_api_key():
        raise RuntimeError("Structured profile extraction requires a configured LLM API key.")
    try:
        client = get_llm_client()
        response = client.chat.completions.create(
            model=get_llm_model(),
            temperature=0.1,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "Extract resume and job-description entities as strict JSON. Never invent facts."},
                {"role": "user", "content": build_profile_extraction_prompt(text, document_type)},
            ],
        )
        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty profile response from LLM")
        parsed = _parse_json(content)
        keywords = _validate_with_spacy(text, [str(item) for item in parsed.get("keywords", []) if isinstance(item, str)])
        if document_type == "resume":
            periods = _periods(parsed.get("experience_periods"))
            total = parsed.get("total_years_experience") or _infer_years(text) or _timeline_years(periods)
            return ResumeProfile(
                keywords=keywords,
                skills=_skills(parsed.get("skills")),
                total_years_experience=total,
                experience_periods=periods,
                experience_evidence=_evidence(parsed.get("experience_evidence")),
            )
        requirement = parsed.get("experience_requirement") or {}
        return JobDescriptionProfile(
            keywords=keywords,
            required_skills=_skills(parsed.get("required_skills")),
            preferred_skills=_skills(parsed.get("preferred_skills")),
            experience_requirement={
                "minimum_years": requirement.get("minimum_years"),
                "preferred_years": requirement.get("preferred_years"),
                "evidence": _evidence(requirement.get("evidence")),
            },
        )
    except RuntimeError:
        raise
    except Exception as error:
        raise RuntimeError(f"Structured profile extraction failed: {error}") from error
