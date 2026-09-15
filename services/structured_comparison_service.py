from rapidfuzz import fuzz

from schemas.resume import (
    ExtractedSkill,
    JobDescriptionProfile,
    ResumeProfile,
    SkillMatch,
    StructuredComparison,
)
from services.profile_service import normalize_keyword


def _match(job_skill: ExtractedSkill, resume_skills: list[ExtractedSkill]) -> SkillMatch:
    target = normalize_keyword(job_skill.name)
    best_name = None
    best_score = 0.0
    for candidate in resume_skills:
        score = float(fuzz.token_set_ratio(target, normalize_keyword(candidate.name)))
        if score > best_score:
            best_score, best_name = score, candidate.name
    return SkillMatch(job_skill=job_skill.name, resume_skill=best_name if best_score >= 80 else None,
                      matched=best_score >= 80, similarity=round(best_score, 2))


def compare_profiles(resume: ResumeProfile, jd: JobDescriptionProfile) -> StructuredComparison:
    required = [_match(skill, resume.skills) for skill in jd.required_skills]
    preferred = [_match(skill, resume.skills) for skill in jd.preferred_skills]
    required_matches = [item.job_skill for item in required if item.matched]
    required_missing = [item.job_skill for item in required if not item.matched]
    preferred_matches = [item.job_skill for item in preferred if item.matched]
    preferred_missing = [item.job_skill for item in preferred if not item.matched]

    total_weight = len(required) * 2 + len(preferred)
    weighted_matches = len(required_matches) * 2 + len(preferred_matches)
    skill_score = round((weighted_matches / total_weight) * 100, 2) if total_weight else 0.0

    minimum = jd.experience_requirement.minimum_years
    candidate_years = resume.total_years_experience
    if minimum is None or candidate_years is None:
        experience_score, fit = 0.0, "unknown"
        summary = "Experience fit could not be determined from the available evidence."
    elif candidate_years >= minimum:
        experience_score, fit = 100.0, "meets_requirement"
        summary = f"Candidate has approximately {candidate_years:g} years versus a minimum of {minimum:g}."
    else:
        experience_score = round(candidate_years / minimum * 100, 2) if minimum else 100.0
        fit = "below_requirement"
        summary = f"Candidate has approximately {candidate_years:g} years versus a minimum of {minimum:g}."

    overall = round(skill_score * 0.7 + experience_score * 0.3, 2)
    return StructuredComparison(
        matched_required_skills=required_matches,
        missing_required_skills=required_missing,
        matched_preferred_skills=preferred_matches,
        missing_preferred_skills=preferred_missing,
        skill_matches=required + preferred,
        skill_coverage_score=skill_score,
        experience_score=experience_score,
        overall_score=overall,
        experience_fit=fit,
        experience_summary=summary,
    )
