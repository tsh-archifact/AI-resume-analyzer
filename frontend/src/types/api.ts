export interface User {
  id: number
  username: string
  role: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
  user: User
}

export interface ResumeSkills {
  section_name: string
  skills: string[]
}

export interface JobDescriptionSkills {
  section_name: string
  skills: string[]
}

export interface SkillComparisonResult {
  matched_skills: string[]
  missing_skills: string[]
  match_score: number
}

export interface LLMRecommendation {
  summary: string
  overall_fit: string
  required_skills: string[]
  nice_to_have_skills: string[]
  strengths: string[]
  missing_skills: string[]
  recommendations: string[]
  model_used: string
}

export interface ATSCritiqueItem {
  category: 'keywords' | 'metrics' | 'action_verbs' | 'structure' | 'relevance'
  severity: 'high' | 'medium' | 'low'
  issue: string
  suggestion: string
}

export interface ATSAuditResult {
  overall_score: number
  keyword_score: number
  metric_score: number
  structure_score: number
  matched_keywords: string[]
  missing_keywords: string[]
  strengths: string[]
  critiques: ATSCritiqueItem[]
}

export interface FactCheckResult {
  is_clean: boolean
  grounding_score: number
  hallucinated_skills: string[]
  unverified_organizations: string[]
  warnings: string[]
}

export interface AgentIterationStep {
  iteration: number
  draft_snippet: string
  audit_result: ATSAuditResult
  fact_check?: FactCheckResult | null
  refinement_prompt_used?: string | null
}

export interface RefinementLoopResult {
  final_draft: string
  initial_score: number
  final_score: number
  score_improvement: number
  iterations_count: number
  target_score_met: boolean
  target_score: number
  iteration_history: AgentIterationStep[]
  final_audit: ATSAuditResult
  final_fact_check?: FactCheckResult | null
}

export interface ResumeComparisonResponse {
  resume_file: string | null
  job_description_file: string | null
  resume_skills: ResumeSkills
  job_description_skills: JobDescriptionSkills
  similarity: SkillComparisonResult
  llm_analysis: LLMRecommendation | null
  agent_audit?: ATSAuditResult | null
}

export interface ApiError {
  detail: string | { msg: string; type: string }[]
}
