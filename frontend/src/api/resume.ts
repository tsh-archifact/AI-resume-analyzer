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

export const DEFAULT_TEMPLATES: ResumeTemplateInfo[] = [
  {
    template_id: 'modern_teal',
    name: 'Modern Minimalist',
    description: 'Clean sans-serif layout with deep teal accents. Ideal for tech, product, and modern businesses.',
    persona: 'Recommended for Tech, Product, & Startups',
    font_family: 'Calibri',
    accent_hex: '#0F766E',
    secondary_hex: '#475569',
    features: ['Teal section underline', 'Calibri clean sans', 'Modern layout'],
    is_default: true,
  },
  {
    template_id: 'executive_navy',
    name: 'Executive Classic',
    description: 'Authoritative serif typography in rich navy blue. Engineered for leadership, finance, and consulting.',
    persona: 'Recommended for Leadership, Finance, & Consulting',
    font_family: 'Georgia',
    accent_hex: '#1E3A8A',
    secondary_hex: '#334155',
    features: ['Centered prestige header', 'Georgia elegant serif', 'Navy dividers'],
    is_default: false,
  },
  {
    template_id: 'tech_indigo',
    name: 'Tech & Developer',
    description: 'Modern high-clarity typography with electric indigo accents. Tailored for software engineers and DevOps.',
    persona: 'Recommended for Software Engineers & DevOps',
    font_family: 'Segoe UI',
    accent_hex: '#4338CA',
    secondary_hex: '#374151',
    features: ['Indigo accent line', 'Segoe UI tech font', 'Clean compact bullets'],
    is_default: false,
  },
  {
    template_id: 'elegant_burgundy',
    name: 'Elegant Academic',
    description: 'Refined serif aesthetic with deep burgundy accents. Perfect for academia, research, and writing.',
    persona: 'Recommended for Academia, Research, & Medical',
    font_family: 'Cambria',
    accent_hex: '#881337',
    secondary_hex: '#4A5568',
    features: ['Centered title', 'Deep burgundy styling', 'Cambria academic serif'],
    is_default: false,
  },
  {
    template_id: 'compact_slate',
    name: 'Compact High-Density',
    description: 'Space-efficient, high-density layout designed to fit extensive career histories into fewer pages.',
    persona: 'Recommended for Multi-Page Content / Maximum Space',
    font_family: 'Arial',
    accent_hex: '#1F2937',
    secondary_hex: '#4B5563',
    features: ['Slim 0.55-in margins', 'High data density', 'Graphite ATS-optimized'],
    is_default: false,
  },
]

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

export interface AgentThoughtEvent {
  type: 'thought' | 'complete' | 'error'
  agent?: string
  title?: string
  thought?: string
  progress?: number
  iteration?: number
  score?: number
  result?: any
  error?: string
}

export type OnThoughtCallback = (event: AgentThoughtEvent) => void

async function processNdjsonStream<T>(
  response: Response,
  onThought?: OnThoughtCallback,
): Promise<T> {
  if (!response.ok) {
    let errorDetail = response.statusText
    try {
      const errJson = (await response.json()) as { detail?: string }
      if (errJson.detail) errorDetail = errJson.detail
    } catch {
      // Ignore parse failure
    }
    throw new ApiRequestError(errorDetail, response.status)
  }

  const reader = response.body?.getReader()
  if (!reader) {
    throw new ApiRequestError('ReadableStream not supported by browser', 500)
  }

  const decoder = new TextDecoder('utf-8')
  let buffer = ''
  let finalResult: T | null = null

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() ?? ''

    for (const line of lines) {
      const trimmed = line.trim()
      if (!trimmed) continue
      try {
        const event = JSON.parse(trimmed) as AgentThoughtEvent
        if (onThought) {
          onThought(event)
        }
        if (event.type === 'complete' && event.result) {
          finalResult = event.result as T
        } else if (event.type === 'error') {
          throw new ApiRequestError(event.error ?? 'Stream error occurred', 500)
        }
      } catch (err) {
        if (err instanceof ApiRequestError) throw err
        // Ignore JSON parse errors on partial chunks
      }
    }
  }

  if (buffer.trim()) {
    try {
      const event = JSON.parse(buffer.trim()) as AgentThoughtEvent
      if (onThought) onThought(event)
      if (event.type === 'complete' && event.result) {
        finalResult = event.result as T
      } else if (event.type === 'error') {
        throw new ApiRequestError(event.error ?? 'Stream error occurred', 500)
      }
    } catch (err) {
      if (err instanceof ApiRequestError) throw err
    }
  }

  if (!finalResult) {
    throw new ApiRequestError('Stream ended without complete result', 500)
  }

  return finalResult
}

export async function compareResumeStream(
  input: ResumeJobInput,
  token: string,
  onThought?: OnThoughtCallback,
): Promise<ResumeComparisonResponse> {
  const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
  const response = await fetch(`${API_BASE}/compare-resume-stream`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: buildCompareForm(input),
  })

  return processNdjsonStream<ResumeComparisonResponse>(response, onThought)
}

export async function runAgentRewriteStream(
  input: ResumeJobInput,
  token: string,
  onThought?: OnThoughtCallback,
  targetScore: number = 80,
  maxIterations: number = 3,
): Promise<import('../types/api').RefinementLoopResult> {
  const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
  const formData = buildCompareForm(input)
  formData.append('target_score', String(targetScore))
  formData.append('max_iterations', String(maxIterations))

  const response = await fetch(`${API_BASE}/agent/rewrite-stream`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: formData,
  })

  return processNdjsonStream<import('../types/api').RefinementLoopResult>(response, onThought)
}


