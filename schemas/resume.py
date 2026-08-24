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


class LLMRecommendation(BaseModel):
    summary: str = Field(default="")
    overall_fit: str = Field(default="")
    required_skills:list[str]=Field(default_factory=list)
    nice_to_have_skills:list[str]=Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    model_used: str = Field(default="heuristic")


class ResumeComparisonResponse(BaseModel):
    resume_file: str | None = None
    job_description_file: str | None = None
    resume_skills: ResumeSkills
    job_description_skills: JobDescriptionSkills
    similarity: SkillComparisonResult
    llm_analysis: LLMRecommendation | None = None
