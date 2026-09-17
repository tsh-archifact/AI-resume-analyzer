from schemas.resume import ExtractedSkill, ExperienceRequirement, JobDescriptionProfile, ResumeProfile
from services.structured_comparison_service import compare_profiles


def test_required_skills_are_weighted_more_than_preferred_skills():
    resume = ResumeProfile(skills=[ExtractedSkill(name="Python")], total_years_experience=4)
    jd = JobDescriptionProfile(
        required_skills=[ExtractedSkill(name="Python"), ExtractedSkill(name="FastAPI")],
        preferred_skills=[ExtractedSkill(name="Docker")],
        experience_requirement=ExperienceRequirement(minimum_years=3),
    )
    result = compare_profiles(resume, jd)
    assert result.matched_required_skills == ["Python"]
    assert result.missing_required_skills == ["FastAPI"]
    assert result.missing_preferred_skills == ["Docker"]
    assert result.experience_fit == "meets_requirement"
    assert result.skill_coverage_score == 40.0
    assert result.overall_score == 58.0


def test_aliases_match_semantically():
    resume = ResumeProfile(skills=[ExtractedSkill(name="Postgres")], total_years_experience=2)
    jd = JobDescriptionProfile(
        required_skills=[ExtractedSkill(name="PostgreSQL")],
        experience_requirement=ExperienceRequirement(minimum_years=5),
    )
    result = compare_profiles(resume, jd)
    assert result.matched_required_skills == ["PostgreSQL"]
    assert result.experience_fit == "below_requirement"
    assert result.experience_score == 40.0


def test_unknown_experience_is_reported_without_inventing_a_fit():
    result = compare_profiles(
        ResumeProfile(skills=[ExtractedSkill(name="Python")]),
        JobDescriptionProfile(
            required_skills=[ExtractedSkill(name="Python")],
            experience_requirement=ExperienceRequirement(minimum_years=3),
        ),
    )
    assert result.experience_fit == "unknown"
    assert result.experience_score == 0.0
