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

export interface ResumeComparisonResponse {
  resume_file: string | null
  job_description_file: string | null
  resume_skills: ResumeSkills
  job_description_skills: JobDescriptionSkills
  similarity: SkillComparisonResult
  llm_analysis: LLMRecommendation | null
}

export interface ApiError {
  detail: string | { msg: string; type: string }[]
}
