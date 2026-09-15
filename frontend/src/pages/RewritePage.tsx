import { useState, type FormEvent } from 'react'

import { runAgentRewrite, exportDocx, rewriteResume, type AgentRewriteMetadata } from '../api/resume'
import { ApiRequestError } from '../api/client'
import { FileUpload } from '../components/FileUpload'
import { useAuth } from '../context/AuthContext'
import type { RefinementLoopResult } from '../types/api'

const RESUME_ACCEPT = '.pdf,.doc,.docx'
const JD_ACCEPT = '.pdf,.doc,.docx,.txt,.png,.jpg,.jpeg'

export function RewritePage() {
  const { token } = useAuth()
  const [resume, setResume] = useState<File | null>(null)
  const [jdFile, setJdFile] = useState<File | null>(null)
  const [jdText, setJdText] = useState('')
  const [jdMode, setJdMode] = useState<'text' | 'file'>('text')
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [agentStats, setAgentStats] = useState<AgentRewriteMetadata | null>(null)
  const [loopResult, setLoopResult] = useState<RefinementLoopResult | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [downloading, setDownloading] = useState(false)
  const [copied, setCopied] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setSuccessMessage(null)
    setLoopResult(null)
    setAgentStats(null)

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
      setError('You must be signed in to optimize resumes.')
      return
    }

    setSubmitting(true)

    try {
      // Execute the multi-agent reflection loop (Drafter + Auditor + Fact-Checker)
      const result = await runAgentRewrite(
        {
          resume,
          jobDescriptionFile: jdMode === 'file' ? jdFile : null,
          jobDescriptionText: jdMode === 'text' ? jdText : undefined,
        },
        token,
        80, // Target score threshold
        3,  // Max iterations
      )

      setLoopResult(result)
      setAgentStats({
        initialScore: result.initial_score,
        finalScore: result.final_score,
        scoreImprovement: result.score_improvement,
        iterations: result.iterations_count,
        isFactClean: result.final_fact_check ? result.final_fact_check.is_clean : true,
      })

      setSuccessMessage(
        `Agentic optimization complete! ATS score improved from ${result.initial_score}% to ${result.final_score}%.`
      )
    } catch (caught) {
      // Fallback to direct download if structured agent endpoint has an issue
      try {
        const { blob, filename, agentMetadata } = await rewriteResume(
          {
            resume,
            jobDescriptionFile: jdMode === 'file' ? jdFile : null,
            jobDescriptionText: jdMode === 'text' ? jdText : undefined,
          },
          token,
        )

        setAgentStats(agentMetadata)
        const url = URL.createObjectURL(blob)
        const anchor = document.createElement('a')
        anchor.href = url
        anchor.download = filename
        anchor.click()
        URL.revokeObjectURL(url)
        setSuccessMessage(`Download started: ${filename}`)
      } catch {
        const message =
          caught instanceof ApiRequestError
            ? caught.message
            : 'Rewrite failed. Please try again.'
        setError(message)
      }
    } finally {
      setSubmitting(false)
    }
  }

  async function handleDownloadDocx() {
    if (!loopResult || !token) return
    setDownloading(true)
    try {
      const blob = await exportDocx(loopResult.final_draft, token)
      const url = URL.createObjectURL(blob)
      const anchor = document.createElement('a')
      anchor.href = url
      anchor.download = 'optimized_resume.docx'
      anchor.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to download DOCX')
    } finally {
      setDownloading(false)
    }
  }

  function handleCopyText() {
    if (!loopResult) return
    navigator.clipboard.writeText(loopResult.final_draft)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="container workspace-page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Autonomous Multi-Agent Rewrite</p>
          <h1>Agentic Resume Optimizer</h1>
          <p className="lead">
            An autonomous collaboration between a Drafter Agent, ATS Auditor Critic, and Fact-Checking Guardrail
            that iteratively refines your resume until it hits top ATS alignment.
          </p>
        </div>
      </header>

      <div className="workspace-grid rewrite-grid">
        <form className="panel form-panel" onSubmit={handleSubmit}>
          <FileUpload
            id="rewrite-resume"
            label="Resume"
            hint="PDF, DOC, or DOCX"
            accept={RESUME_ACCEPT}
            file={resume}
            onChange={setResume}
          />

          <div className="form-group">
            <label>Job description format</label>
            <div className="segmented-control">
              <button
                type="button"
                className={`segmented-button ${jdMode === 'text' ? 'active' : ''}`}
                onClick={() => setJdMode('text')}
              >
                Paste text
              </button>
              <button
                type="button"
                className={`segmented-button ${jdMode === 'file' ? 'active' : ''}`}
                onClick={() => setJdMode('file')}
              >
                Upload file
              </button>
            </div>
          </div>

          {jdMode === 'text' ? (
            <div className="form-group">
              <label htmlFor="rewrite-jd-text">Job description text</label>
              <textarea
                id="rewrite-jd-text"
                rows={6}
                placeholder="Paste the full job posting here…"
                value={jdText}
                onChange={(event) => setJdText(event.target.value)}
              />
            </div>
          ) : (
            <FileUpload
              id="rewrite-jd"
              label="Job description file"
              hint="PDF, DOC, DOCX, TXT, PNG, JPG, or JPEG"
              accept={JD_ACCEPT}
              file={jdFile}
              onChange={setJdFile}
            />
          )}

          {error ? <p className="form-error">{error}</p> : null}
          {successMessage ? <p className="form-success">{successMessage}</p> : null}

          <button type="submit" className="btn btn-primary btn-block" disabled={submitting}>
            {submitting ? '🤖 Agents are drafting, auditing & refining…' : 'Run Autonomous Agentic Optimizer'}
          </button>
        </form>

        <aside className="panel info-panel">
          {agentStats && agentStats.finalScore !== null ? (
            <div className="agent-summary-card">
              <h2>🤖 Agent Performance Card</h2>
              <div style={{ margin: '1rem 0', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontWeight: 600 }}>Iterations Performed:</span>
                  <span className="badge" style={{ background: '#3b82f6', color: '#fff', padding: '0.2rem 0.6rem', borderRadius: '4px' }}>
                    {agentStats.iterations ?? 1} passes
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontWeight: 600 }}>ATS Score Progression:</span>
                  <span style={{ fontWeight: 700, color: '#10b981' }}>
                    {agentStats.initialScore ?? 0}% → {agentStats.finalScore}%
                    {agentStats.scoreImprovement && agentStats.scoreImprovement > 0 ? ` (+${agentStats.scoreImprovement}%)` : ''}
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontWeight: 600 }}>Fact-Checking Guardrail:</span>
                  <span style={{ color: agentStats.isFactClean ? '#10b981' : '#f59e0b', fontWeight: 600 }}>
                    {agentStats.isFactClean ? '✅ 100% Grounded (0 Hallucinations)' : '⚠️ Grounded with notes'}
                  </span>
                </div>
              </div>
              <hr style={{ margin: '1rem 0', opacity: 0.2 }} />
            </div>
          ) : null}

          <h2>How the agentic flow works</h2>
          <ul className="info-list">
            <li><strong>Perception:</strong> Ingests resume & JD, extracting keywords and experience metrics.</li>
            <li><strong>Drafter Agent:</strong> Produces role-targeted bullet points using high-impact action verbs.</li>
            <li><strong>ATS Auditor Critic:</strong> Scans keyword density, bullet quantification, and ATS structure.</li>
            <li><strong>Fact-Checker Guardrail:</strong> Verifies every technical skill against your source resume.</li>
            <li><strong>Reflection Loop:</strong> Iterates until the resume meets ATS quality standards.</li>
          </ul>
        </aside>
      </div>

      {/* When Agentic Optimization finishes: Display full on-screen preview & iteration history */}
      {loopResult ? (
        <section className="panel" style={{ marginTop: '2rem', border: '1px solid #cbd5e1' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '1rem' }}>
            <div>
              <span style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', color: '#10b981', letterSpacing: '0.05em' }}>
                ✨ Optimization Complete
              </span>
              <h2 style={{ margin: '0.25rem 0 0 0', fontSize: '1.4rem' }}>
                Refined Resume Preview
              </h2>
            </div>
            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={handleCopyText}
              >
                {copied ? '✓ Copied!' : 'Copy to Clipboard'}
              </button>
              <button
                type="button"
                className="btn btn-primary"
                onClick={handleDownloadDocx}
                disabled={downloading}
              >
                {downloading ? 'Preparing DOCX…' : '📥 Download DOCX'}
              </button>
            </div>
          </div>

          {/* Iteration Timeline */}
          {loopResult.iteration_history && loopResult.iteration_history.length > 1 ? (
            <div style={{ background: '#f8fafc', padding: '1rem', borderRadius: '8px', marginBottom: '1.5rem', border: '1px solid #e2e8f0' }}>
              <h3 style={{ fontSize: '0.95rem', fontWeight: 700, margin: '0 0 0.75rem 0', color: '#334155' }}>
                🔄 Autonomous Refinement Timeline ({loopResult.iteration_history.length} iterations)
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {loopResult.iteration_history.map((step) => (
                  <div key={step.iteration} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.875rem' }}>
                    <span>
                      <strong>Pass #{step.iteration}:</strong> {step.refinement_prompt_used ?? 'Initial draft evaluated'}
                    </span>
                    <span style={{ fontWeight: 700, color: step.audit_result.overall_score >= 80 ? '#10b981' : '#f59e0b' }}>
                      Score: {step.audit_result.overall_score}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ) : null}

          {/* Full Draft Viewer */}
          <textarea
            readOnly
            rows={18}
            style={{
              width: '100%',
              fontFamily: 'monospace',
              fontSize: '0.9rem',
              lineHeight: '1.5',
              padding: '1rem',
              borderRadius: '8px',
              border: '1px solid #cbd5e1',
              background: '#ffffff',
              color: '#0f172a',
            }}
            value={loopResult.final_draft}
          />
        </section>
      ) : null}
    </div>
  )
}
