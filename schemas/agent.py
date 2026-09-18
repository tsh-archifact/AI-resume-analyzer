from enum import Enum
from pydantic import BaseModel, Field


class CritiqueCategory(str, Enum):
    KEYWORDS = "keywords"
    METRICS = "metrics"
    ACTION_VERBS = "action_verbs"
    STRUCTURE = "structure"
    RELEVANCE = "relevance"


class CritiqueSeverity(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ATSCritiqueItem(BaseModel):
    category: CritiqueCategory = Field(description="Category of the critique (e.g. keywords, metrics, structure)")
    severity: CritiqueSeverity = Field(description="Severity level of the issue")
    issue: str = Field(description="Concise description of the detected issue")
    suggestion: str = Field(description="Actionable instruction on how to fix the issue in the next iteration")


class ATSAuditResult(BaseModel):
    overall_score: float = Field(default=0.0, ge=0.0, le=100.0, description="Overall ATS composite score from 0 to 100")
    keyword_score: float = Field(default=0.0, ge=0.0, le=100.0, description="Keyword match & coverage score")
    metric_score: float = Field(default=0.0, ge=0.0, le=100.0, description="Metric & quantified achievement score")
    structure_score: float = Field(default=0.0, ge=0.0, le=100.0, description="ATS readability and action verb score")
    
    matched_keywords: list[str] = Field(default_factory=list, description="Target keywords successfully matched")
    missing_keywords: list[str] = Field(default_factory=list, description="Target keywords missing from the draft")
    strengths: list[str] = Field(default_factory=list, description="Notable strengths of the draft")
    critiques: list[ATSCritiqueItem] = Field(default_factory=list, description="List of specific, actionable critiques for refinement")


class FactCheckResult(BaseModel):
    is_clean: bool = Field(default=True, description="Whether the draft is completely grounded with zero hallucinations")
    grounding_score: float = Field(default=100.0, ge=0.0, le=100.0, description="Percentage of extracted claims grounded in the source")
    hallucinated_skills: list[str] = Field(default_factory=list, description="Skills present in the draft that do not exist in the source resume")
    unverified_organizations: list[str] = Field(default_factory=list, description="Companies/employers in the draft not supported by the source resume")
    warnings: list[str] = Field(default_factory=list, description="Safety and truthfulness warnings")


class AgentIterationStep(BaseModel):
    iteration: int = Field(description="Iteration sequence number (1-based)")
    draft_snippet: str = Field(description="Brief snippet or summary of the draft in this iteration")
    audit_result: ATSAuditResult = Field(description="Audit result produced for this iteration")
    fact_check: FactCheckResult | None = Field(default=None, description="Fact-checking guardrail result for this draft")
    refinement_prompt_used: str | None = Field(default=None, description="The critique feedback prompt passed to the next iteration")


class RefinementLoopResult(BaseModel):
    final_draft: str = Field(description="The finalized, refined resume text")
    initial_score: float = Field(default=0.0, description="ATS score of the initial draft (v1)")
    final_score: float = Field(default=0.0, description="ATS score of the final refined draft")
    score_improvement: float = Field(default=0.0, description="Score delta between final and initial draft")
    iterations_count: int = Field(default=1, description="Total number of iterations performed")
    target_score_met: bool = Field(default=False, description="Whether the configured target score was reached")
    target_score: float = Field(default=80.0, description="Target score threshold used")
    iteration_history: list[AgentIterationStep] = Field(default_factory=list, description="Step-by-step history of iterations")
    final_audit: ATSAuditResult = Field(description="Final ATS audit result")
    final_fact_check: FactCheckResult | None = Field(default=None, description="Final fact check validation result")


