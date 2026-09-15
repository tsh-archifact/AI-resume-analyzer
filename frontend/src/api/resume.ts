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

export async function rewriteResume(
  input: ResumeJobInput,
  token: string,
): Promise<{ blob: Blob; filename: string }> {
  const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '/api'
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

  return { blob, filename }
}
