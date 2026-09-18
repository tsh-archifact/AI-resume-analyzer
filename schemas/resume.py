from pydantic import BaseModel, Field


class ResumeSkills(BaseModel):
    section_name: str = Field(default="skills", description="Resume skills section name")
    skills: list[str] = Field(default_factory=list, description="List of skills found in the resume")


class JobDescriptionSkills(BaseModel):
    section_name: str = Field(default="job_description_skills", description="JD skills section name")
    skills: list[str] = Field(default_factory=list, description="List of skills found in the job description")


class SkillComparisonResult(BaseModel):
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    match_score: float = Field(default=0.0)


class Evidence(BaseModel):
    text: str
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class ExtractedSkill(BaseModel):
    name: str
    category: str = "technical"
    years_experience: float | None = Field(default=None, ge=0.0)
    evidence: list[Evidence] = Field(default_factory=list)


class ExperiencePeriod(BaseModel):
    title: str = ""
    company: str = ""
    start_date: str | None = None
    end_date: str | None = None
    evidence: list[Evidence] = Field(default_factory=list)


class ExperienceRequirement(BaseModel):
    minimum_years: float | None = Field(default=None, ge=0.0)
    preferred_years: float | None = Field(default=None, ge=0.0)
    evidence: list[Evidence] = Field(default_factory=list)


class ResumeProfile(BaseModel):
    keywords: list[str] = Field(default_factory=list)
    skills: list[ExtractedSkill] = Field(default_factory=list)
    total_years_experience: float | None = Field(default=None, ge=0.0)
    experience_periods: list[ExperiencePeriod] = Field(default_factory=list)
    experience_evidence: list[Evidence] = Field(default_factory=list)


class JobDescriptionProfile(BaseModel):
    keywords: list[str] = Field(default_factory=list)
    required_skills: list[ExtractedSkill] = Field(default_factory=list)
    preferred_skills: list[ExtractedSkill] = Field(default_factory=list)
    experience_requirement: ExperienceRequirement = Field(default_factory=ExperienceRequirement)


class SkillMatch(BaseModel):
    job_skill: str
    resume_skill: str | None = None
    matched: bool = False
    similarity: float = Field(default=0.0, ge=0.0, le=100.0)


class StructuredComparison(BaseModel):
    matched_required_skills: list[str] = Field(default_factory=list)
    missing_required_skills: list[str] = Field(default_factory=list)
    matched_preferred_skills: list[str] = Field(default_factory=list)
    missing_preferred_skills: list[str] = Field(default_factory=list)
    skill_matches: list[SkillMatch] = Field(default_factory=list)
    skill_coverage_score: float = Field(default=0.0, ge=0.0, le=100.0)
    experience_score: float = Field(default=0.0, ge=0.0, le=100.0)
    overall_score: float = Field(default=0.0, ge=0.0, le=100.0)
    experience_fit: str = "unknown"
    experience_summary: str = ""


class LLMRecommendation(BaseModel):
    summary: str = Field(default="")
    overall_fit: str = Field(default="")
    required_skills:list[str]=Field(default_factory=list)
    nice_to_have_skills:list[str]=Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    model_used: str = Field(default="heuristic")


from schemas.agent import ATSAuditResult


class ResumeComparisonResponse(BaseModel):
    resume_file: str | None = None
    job_description_file: str | None = None
    resume_skills: ResumeSkills
    job_description_skills: JobDescriptionSkills
    similarity: SkillComparisonResult
    llm_analysis: LLMRecommendation | None = None
    resume_profile: ResumeProfile | None = None
    job_description_profile: JobDescriptionProfile | None = None
    structured_comparison: StructuredComparison | None = None
    agent_audit: ATSAuditResult | None = None

