import { apiFetch, ApiRequestError } from './client'
import type { ResumeComparisonResponse } from '../types/api'

export interface ResumeJobInput {
  resume: File
  jobDescriptionFile?: File | null
  jobDescriptionText?: string
}

function buildCompareForm({ resume, jobDescriptionFile, jobDescriptionText }: ResumeJobInput): FormData {
  const formData = new FormData()
  formData.append('resume', resume)

  if (jobDescriptionFile) {
    formData.append('job_description', jobDescriptionFile)
  } else if (jobDescriptionText?.trim()) {
    formData.append('job_description_text', jobDescriptionText.trim())
  }

  return formData
}

export async function compareResume(
  input: ResumeJobInput,
  token: string,
): Promise<ResumeComparisonResponse> {
  return apiFetch<ResumeComparisonResponse>(
    '/compare-resume',
    {
      method: 'POST',
      body: buildCompareForm(input),
    },
    token,
  )
}

export interface AgentRewriteMetadata {
  initialScore: number | null
  finalScore: number | null
  scoreImprovement: number | null
  iterations: number | null
  isFactClean: boolean
}

export interface RewriteResumeResult {
  blob: Blob
  filename: string
  agentMetadata: AgentRewriteMetadata
}

export async function rewriteResume(
  input: ResumeJobInput,
  token: string,
): Promise<RewriteResumeResult> {
  const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
  const response = await fetch(`${API_BASE}/rewrite-resume`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: buildCompareForm(input),
  })

  if (!response.ok) {
    let message = response.statusText
    try {
      const body = (await response.json()) as { detail?: string }
      if (body.detail) {
        message = body.detail
      }
    } catch {
      // Ignore JSON parse failures.
    }
    throw new ApiRequestError(message, response.status)
  }

  const blob = await response.blob()
  const disposition = response.headers.get('content-disposition') ?? ''
  const filenameMatch = disposition.match(/filename="?([^"]+)"?/)
  const filename = filenameMatch?.[1] ?? 'rewritten_resume.docx'

  const initialScore = response.headers.get('x-agent-initial-score')
  const finalScore = response.headers.get('x-agent-final-score')
  const improvement = response.headers.get('x-agent-score-improvement')
  const iterations = response.headers.get('x-agent-iterations')
  const factClean = response.headers.get('x-agent-fact-clean')

  const agentMetadata: AgentRewriteMetadata = {
    initialScore: initialScore ? parseFloat(initialScore) : null,
    finalScore: finalScore ? parseFloat(finalScore) : null,
    scoreImprovement: improvement ? parseFloat(improvement) : null,
    iterations: iterations ? parseInt(iterations, 10) : null,
    isFactClean: factClean ? factClean.toLowerCase() === 'true' : true,
  }

  return { blob, filename, agentMetadata }
}

export async function runAgentRewrite(
  input: ResumeJobInput,
  token: string,
  targetScore: number = 80,
  maxIterations: number = 3,
): Promise<import('../types/api').RefinementLoopResult> {
  const formData = buildCompareForm(input)
  formData.append('target_score', String(targetScore))
  formData.append('max_iterations', String(maxIterations))

  return apiFetch<import('../types/api').RefinementLoopResult>(
    '/agent/rewrite',
    {
      method: 'POST',
      body: formData,
    },
    token,
  )
}

export interface ResumeTemplateInfo {
  template_id: string
  name: string
  description: string
  persona: string
  font_family: string
  accent_hex: string
  secondary_hex: string
  features: string[]
  is_default: boolean
}

export async function getResumeTemplates(token: string): Promise<ResumeTemplateInfo[]> {
  const data = await apiFetch<{ templates: ResumeTemplateInfo[] }>('/agent/templates', {}, token)
  return data.templates
}

export async function exportDocx(content: string, token: string, templateId: string = 'modern_teal'): Promise<Blob> {
  const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
  const response = await fetch(`${API_BASE}/agent/export-docx`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ content, template_id: templateId }),
  })
  if (!response.ok) {
    throw new ApiRequestError('Failed to generate DOCX from text', response.status)
  }
  return response.blob()
}


