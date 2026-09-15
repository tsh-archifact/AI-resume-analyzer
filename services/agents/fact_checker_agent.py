import re
from schemas.agent import (
    ATSCritiqueItem,
    CritiqueCategory,
    CritiqueSeverity,
    FactCheckResult,
)
from services.skill_service import extract_skills_from_text, normalize_skill


def _load_spacy_safe():
    """Attempt to load spaCy model for named entity recognition; return None if unavailable."""
    try:
        from services.profile_service import _load_spacy
        return _load_spacy()
    except Exception:
        return None


def _is_term_grounded(term: str, source_text: str) -> bool:
    """Check if a term or skill is grounded in the source resume."""
    clean = normalize_skill(term)
    if not clean or len(clean) < 2:
        return True

    source_lower = source_text.lower()
    escaped = re.escape(clean.lower())

    # Direct word-boundary match
    if re.search(r"(?:^|[\s,;|/()\-._])" + escaped + r"(?:$|[\s,;|/()\-._])", source_lower):
        return True

    # Word subset match for compound terms (e.g. "PostgreSQL Database" matches "PostgreSQL")
    words = [w for w in clean.lower().split() if len(w) > 2]
    if words and all(w in source_lower for w in words):
        return True

    return False


def _extract_org_entities(text: str, nlp) -> list[str]:
    """Extract organization names using spaCy NER if available."""
    if not nlp:
        return []
    doc = nlp(text[:10000])
    orgs = set()
    for ent in doc.ents:
        if ent.label_ == "ORG" and len(ent.text.strip()) > 2:
            # Clean newlines and leading punctuation
            raw = ent.text.strip().split("\n")[0].strip()
            clean = re.sub(r"^[^\w]+|[^\w]+$", "", raw).strip()
            if not clean or len(clean) < 3:
                continue
            # Exclude common tech/resume keywords mistakenly tagged as ORG
            if clean.lower() not in {"python", "fastapi", "docker", "kubernetes", "aws", "sql", "linux", "experience", "education", "skills", "projects"}:
                orgs.add(clean)
    return list(orgs)


def verify_resume_truthfulness(
    draft_text: str,
    source_resume: str,
) -> FactCheckResult:
    """
    Compares the generated or refined draft against the candidate's original source resume.
    Ensures the LLM did not hallucinate new technologies, companies, or credentials.
    """
    nlp = _load_spacy_safe()

    # 1. Extract skills from draft and verify against source resume
    draft_skills = extract_skills_from_text(draft_text, section_name="skills")
    hallucinated_skills: list[str] = []

    for skill in draft_skills:
        if not _is_term_grounded(skill, source_resume):
            hallucinated_skills.append(skill)

    # 2. Extract organizations/employers from draft and verify against source resume
    unverified_orgs: list[str] = []
    if nlp:
        draft_orgs = _extract_org_entities(draft_text, nlp)
        source_lower = source_resume.lower()
        for org in draft_orgs:
            clean_org = org.strip()
            if clean_org.lower() not in source_lower:
                unverified_orgs.append(clean_org)

    # 3. Calculate grounding score and assemble warnings
    total_claims = len(draft_skills) + len(unverified_orgs)
    total_violations = len(hallucinated_skills) + len(unverified_orgs)

    if total_claims == 0:
        grounding_score = 100.0
    else:
        grounding_score = max(0.0, round(((total_claims - total_violations) / total_claims) * 100.0, 1))

    warnings: list[str] = []
    is_clean = len(hallucinated_skills) == 0 and len(unverified_orgs) == 0

    if hallucinated_skills:
        warnings.append(
            f"Detected {len(hallucinated_skills)} hallucinated skill(s) not supported by source resume: {', '.join(hallucinated_skills)}."
        )
    if unverified_orgs:
        warnings.append(
            f"Detected unverified organization/company claim(s): {', '.join(unverified_orgs)}."
        )

    return FactCheckResult(
        is_clean=is_clean,
        grounding_score=grounding_score,
        hallucinated_skills=hallucinated_skills,
        unverified_organizations=unverified_orgs,
        warnings=warnings,
    )


def convert_fact_check_to_critiques(fact_check: FactCheckResult) -> list[ATSCritiqueItem]:
    """Converts fact-check violations into high-severity critique items for the refinement loop."""
    critiques: list[ATSCritiqueItem] = []

    if fact_check.hallucinated_skills:
        skills_str = ", ".join(fact_check.hallucinated_skills[:5])
        critiques.append(
            ATSCritiqueItem(
                category=CritiqueCategory.RELEVANCE,
                severity=CritiqueSeverity.HIGH,
                issue=f"Draft hallucinated technical skill(s) not found in candidate's original resume: {skills_str}.",
                suggestion=f"Remove {skills_str} or replace them with genuine technologies from the candidate's actual background.",
            )
        )

    if fact_check.unverified_organizations:
        orgs_str = ", ".join(fact_check.unverified_organizations[:3])
        critiques.append(
            ATSCritiqueItem(
                category=CritiqueCategory.RELEVANCE,
                severity=CritiqueSeverity.HIGH,
                issue=f"Draft includes unverified company/organization name(s): {orgs_str}.",
                suggestion="Retain only the exact employer names listed in the original resume.",
            )
        )

    return critiques
