import { useState, type FormEvent } from 'react'

import { compareResume } from '../api/resume'
import { ApiRequestError } from '../api/client'
import { AnalysisCard } from '../components/AnalysisCard'
import { AgentAuditCard } from '../components/AgentAuditCard'
import { FileUpload } from '../components/FileUpload'
import { MatchScore } from '../components/MatchScore'
import { SkillTags } from '../components/SkillTags'
import { useAuth } from '../context/AuthContext'
import type { ResumeComparisonResponse } from '../types/api'

const RESUME_ACCEPT = '.pdf,.doc,.docx'
const JD_ACCEPT = '.pdf,.doc,.docx,.txt,.png,.jpg,.jpeg'

export function ComparePage() {
  const { token } = useAuth()
  const [resume, setResume] = useState<File | null>(null)
  const [jdFile, setJdFile] = useState<File | null>(null)
  const [jdText, setJdText] = useState('')
  const [jdMode, setJdMode] = useState<'text' | 'file'>('text')
  const [result, setResult] = useState<ResumeComparisonResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setResult(null)

    if (!resume) {
      setError('Please upload a resume file.')
      return
    }

    if (jdMode === 'file' && !jdFile) {
      setError('Please upload a job description file or switch to pasted text.')
      return
    }

    if (jdMode === 'text' && !jdText.trim()) {
      setError('Please paste a job description or switch to file upload.')
      return
    }

    if (!token) {
      setError('You must be signed in to compare resumes.')
      return
    }

    setSubmitting(true)

    try {
      const response = await compareResume(
        {
          resume,
          jobDescriptionFile: jdMode === 'file' ? jdFile : null,
          jobDescriptionText: jdMode === 'text' ? jdText : undefined,
        },
        token,
      )
      setResult(response)
    } catch (caught) {
      const message =
        caught instanceof ApiRequestError
          ? caught.message
          : 'Comparison failed. Please try again.'
      setError(message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="container workspace-page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Skill comparison</p>
          <h1>Compare your resume to a role</h1>
          <p className="lead">
            Upload a resume and provide the job description as text or file. The backend extracts
            skills and returns a match score plus recruiter-style analysis.
          </p>
        </div>
      </header>

      <div className="workspace-grid">
        <form className="panel form-panel" onSubmit={handleSubmit}>
          <FileUpload
            id="compare-resume"
            label="Resume"
            hint="PDF, DOC, or DOCX"
            accept={RESUME_ACCEPT}
            file={resume}
            onChange={setResume}
          />

          <fieldset className="mode-toggle">
            <legend>Job description input</legend>
            <label>
              <input
                type="radio"
                name="jd-mode"
                checked={jdMode === 'text'}
                onChange={() => setJdMode('text')}
              />
              Paste text
            </label>
            <label>
              <input
                type="radio"
                name="jd-mode"
                checked={jdMode === 'file'}
                onChange={() => setJdMode('file')}
              />
              Upload file
            </label>
          </fieldset>

          {jdMode === 'text' ? (
            <div className="field">
              <label htmlFor="jd-text">Job description</label>
              <textarea
                id="jd-text"
                rows={10}
                placeholder="Paste the full job description here…"
                value={jdText}
                onChange={(event) => setJdText(event.target.value)}
              />
            </div>
          ) : (
            <FileUpload
              id="compare-jd"
              label="Job description file"
              hint="PDF, DOC, DOCX, TXT, PNG, JPG, or JPEG"
              accept={JD_ACCEPT}
              file={jdFile}
              onChange={setJdFile}
            />
          )}

          {error ? <p className="form-error">{error}</p> : null}

          <button type="submit" className="btn btn-primary btn-block" disabled={submitting}>
            {submitting ? 'Analyzing…' : 'Run comparison'}
          </button>
        </form>

        <div className="results-stack">
          {!result && !submitting ? (
            <div className="panel empty-panel">
              <h2>Results appear here</h2>
              <p>Submit a resume and job description to see skill overlap and AI recommendations.</p>
            </div>
          ) : null}

          {submitting ? (
            <div className="panel empty-panel">
              <div className="spinner" aria-hidden="true" />
              <p>Extracting text, identifying skills, and generating analysis…</p>
            </div>
          ) : null}

          {result ? (
            <>
              <div className="panel results-summary">
                <MatchScore
                  score={result.similarity.match_score}
                  overallFit={result.llm_analysis?.overall_fit}
                />
                <div className="file-meta">
                  <p>
                    <strong>Resume:</strong> {result.resume_file ?? 'Uploaded resume'}
                  </p>
                  <p>
                    <strong>Job description:</strong>{' '}
                    {result.job_description_file ?? (jdMode === 'text' ? 'Pasted text' : 'Uploaded file')}
                  </p>
                </div>
              </div>

              <div className="panel skill-grid">
                <SkillTags title="Resume skills" skills={result.resume_skills.skills} variant="neutral" />
                <SkillTags
                  title="Job description skills"
                  skills={result.job_description_skills.skills}
                  variant="neutral"
                />
                <SkillTags title="Matched skills" skills={result.similarity.matched_skills} variant="matched" />
                <SkillTags title="Missing skills" skills={result.similarity.missing_skills} variant="missing" />
              </div>

              {result.llm_analysis ? <AnalysisCard analysis={result.llm_analysis} /> : null}
              {result.agent_audit ? <AgentAuditCard audit={result.agent_audit} /> : null}
            </>
          ) : null}
        </div>
      </div>
    </div>
  )
}
