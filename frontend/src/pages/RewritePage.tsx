import { useState, useEffect, type FormEvent } from 'react'

import {
  runAgentRewriteStream,
  exportDocx,
  getResumeTemplates,
  type AgentRewriteMetadata,
  type ResumeTemplateInfo,
  type AgentThoughtEvent,
  DEFAULT_TEMPLATES,
} from '../api/resume'
import { ApiRequestError } from '../api/client'
import { FileUpload } from '../components/FileUpload'
import { AgentActivityFeed, type AgentThoughtLogItem } from '../components/AgentActivityFeed'
import { TemplateSelector } from '../components/TemplateSelector'
import { useAuth } from '../context/AuthContext'
import type { RefinementLoopResult, AgentIterationStep } from '../types/api'

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

  // Real-time agent activity feed states
  const [rewriteThought, setRewriteThought] = useState<string | null>(null)
  const [rewriteAgent, setRewriteAgent] = useState<string | null>(null)
  const [rewriteProgress, setRewriteProgress] = useState(0)
  const [rewriteLog, setRewriteLog] = useState<AgentThoughtLogItem[]>([])

  const [templates, setTemplates] = useState<ResumeTemplateInfo[]>(DEFAULT_TEMPLATES)
  const [selectedTemplate, setSelectedTemplate] = useState<string>('modern_teal')

  useEffect(() => {
    if (!token) return
    getResumeTemplates(token)
      .then((items) => {
        if (items && items.length) {
          setTemplates(items)
        }
      })
      .catch(() => {
        // Fallback already pre-populated
      })
  }, [token])

  const formatTimestamp = () => {
    const now = new Date()
    return now.toTimeString().split(' ')[0]
  }

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
    setRewriteThought('Initializing agent perception and document parsing…')
    setRewriteAgent('Perception Agent')
    setRewriteProgress(10)
    setRewriteLog([
      {
        id: String(Date.now()),
        agent: 'Perception Agent',
        thought: `Extracting candidate achievements and target job requirements (${resume.name})…`,
        timestamp: formatTimestamp(),
      },
    ])

    try {
      // Execute the multi-agent reflection loop (Drafter + Auditor + Fact-Checker) with live thoughts
      const result = await runAgentRewriteStream(
        {
          resume,
          jobDescriptionFile: jdMode === 'file' ? jdFile : null,
          jobDescriptionText: jdMode === 'text' ? jdText : undefined,
        },
        token,
        (event: AgentThoughtEvent) => {
          if (event.thought) {
            setRewriteThought(event.thought)
            setRewriteAgent(event.agent ?? 'Supervisor Agent')
            if (event.progress) setRewriteProgress(event.progress)
            setRewriteLog((prev) => [
              ...prev,
              {
                id: `${Date.now()}-${Math.random().toString(36).substring(2, 6)}`,
                agent: event.agent ?? 'Supervisor Agent',
                thought: event.thought ?? '',
                timestamp: formatTimestamp(),
              },
            ])
          }
        },
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
      const message =
        caught instanceof ApiRequestError
          ? caught.message
          : 'Rewrite failed. Please try again.'
      setError(message)
    } finally {
      setSubmitting(false)
    }
  }

  async function handleDownloadDocx() {
    if (!loopResult || !token) return
    setDownloading(true)
    try {
      const blob = await exportDocx(loopResult.final_draft, token, selectedTemplate)
      const url = URL.createObjectURL(blob)
      const anchor = document.createElement('a')
      anchor.href = url
      anchor.download = `optimized_resume_${selectedTemplate}.docx`
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
        <form className="note-card form-panel" onSubmit={handleSubmit}>
          <div className="note-banner banner-peach">
            <span>AGENTIC RESUME OPTIMIZER</span>
            <span style={{ opacity: 0.8, fontSize: '0.82rem', letterSpacing: '0.08em' }}>INPUT</span>
          </div>

          <div className="form-panel-body">
            <FileUpload
              id="rewrite-resume"
              label="Source Resume"
              hint="PDF, DOC, or DOCX"
              accept={RESUME_ACCEPT}
              file={resume}
              onChange={setResume}
            />

            <fieldset className="mode-toggle">
              <legend>Job description format</legend>
              <label>
                <input
                  type="radio"
                  name="rewrite-jd-mode"
                  checked={jdMode === 'text'}
                  onChange={() => setJdMode('text')}
                />
                ✏️ Paste text
              </label>
              <label>
                <input
                  type="radio"
                  name="rewrite-jd-mode"
                  checked={jdMode === 'file'}
                  onChange={() => setJdMode('file')}
                />
                📁 Upload file
              </label>
            </fieldset>

            {jdMode === 'text' ? (
              <div className="field">
                <label htmlFor="rewrite-jd-text">Target Job Description</label>
                <textarea
                  id="rewrite-jd-text"
                  rows={7}
                  placeholder="Paste the target job posting / requirements here…"
                  value={jdText}
                  onChange={(event) => setJdText(event.target.value)}
                />
              </div>
            ) : (
              <FileUpload
                id="rewrite-jd"
                label="Job Description File"
                hint="PDF, DOC, DOCX, TXT, PNG, JPG, or JPEG"
                accept={JD_ACCEPT}
                file={jdFile}
                onChange={setJdFile}
              />
            )}

            {error ? <p className="form-error">{error}</p> : null}
            {successMessage ? <p className="form-success">{successMessage}</p> : null}

            <button type="submit" className="btn btn-primary btn-block" disabled={submitting}>
              {submitting ? 'Agents Drafting, Auditing & Refining…' : 'Run Autonomous Optimizer'}
            </button>
          </div>
        </form>

        <div className="results-stack">
          {submitting ? (
            <AgentActivityFeed
              currentThought={rewriteThought}
              activeAgent={rewriteAgent}
              progress={rewriteProgress}
              history={rewriteLog}
            />
          ) : (
            <aside className="note-card info-panel" style={{ padding: 0, overflow: 'hidden', width: '100%' }}>
              <div className="note-banner banner-peach">
                <span>MULTI-AGENT SPECIFICATION</span>
                <span style={{ opacity: 0.8, fontSize: '0.82rem', letterSpacing: '0.08em' }}>WORKFLOW</span>
              </div>

              <div style={{ padding: '1.25rem' }}>
                {agentStats && agentStats.finalScore !== null ? (
                  <div className="agent-summary-card" style={{ marginBottom: '1.25rem', padding: '1rem', background: 'var(--surface-cream)', border: '1.5px dashed var(--border-dashed)', borderRadius: 'var(--radius-sm)' }}>
                    <h2 className="marker-blue-title" style={{ marginTop: 0 }}>🤖 Agent Performance Card</h2>
                    <div style={{ margin: '0.75rem 0', display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontFamily: 'var(--font-notes)', fontSize: '1.1rem', fontWeight: 700 }}>Iterations Performed:</span>
                        <span className="badge" style={{ background: 'var(--banner-blue)', color: '#0c4a6e', padding: '0.2rem 0.65rem', borderRadius: 'var(--radius-pill)', border: '1px solid var(--contour-ink)', fontFamily: 'var(--font-mono)', fontSize: '0.82rem', fontWeight: 700 }}>
                          {agentStats.iterations ?? 1} passes
                        </span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontFamily: 'var(--font-notes)', fontSize: '1.1rem', fontWeight: 700 }}>ATS Score Progression:</span>
                        <span style={{ fontFamily: 'var(--font-title)', fontSize: '1.2rem', fontWeight: 700, color: 'var(--success)' }}>
                          {agentStats.initialScore ?? 0}% → {agentStats.finalScore}%
                          {agentStats.scoreImprovement && agentStats.scoreImprovement > 0 ? ` (+${agentStats.scoreImprovement}%)` : ''}
                        </span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontFamily: 'var(--font-notes)', fontSize: '1.1rem', fontWeight: 700 }}>Fact-Checking Guardrail:</span>
                        <span style={{ color: agentStats.isFactClean ? 'var(--success)' : 'var(--warning)', fontWeight: 700, fontFamily: 'var(--font-notes)', fontSize: '1.1rem' }}>
                          {agentStats.isFactClean ? '✅ 100% Grounded (0 Hallucinations)' : '⚠️ Grounded with notes'}
                        </span>
                      </div>
                    </div>
                  </div>
                ) : null}

                <h2 className="marker-blue-title" style={{ marginTop: 0 }}>How the agentic flow works</h2>
                <ul className="note-bullets">
                  <li><strong>Perception:</strong> Ingests resume &amp; JD, extracting keywords and metrics.</li>
                  <li><strong>Drafter Agent:</strong> Produces role-targeted bullet points using active verbs.</li>
                  <li><strong>ATS Auditor Critic:</strong> Scans keyword density, quantification &amp; ATS structure.</li>
                  <li><strong>Fact-Checker:</strong> Verifies every technical skill against your source resume.</li>
                  <li><strong>Reflection Loop:</strong> Iterates until the resume hits the ATS quality threshold.</li>
                </ul>
              </div>
            </aside>
          )}
        </div>
      </div>

      {/* When Agentic Optimization finishes: Display full on-screen preview & iteration history */}
      {loopResult ? (
        <section className="note-card" style={{ marginTop: '2rem' }}>
          <div className="note-banner banner-teal">
            <span>REFINED RESUME PREVIEW &amp; DOCX EXPORT</span>
            <span style={{ opacity: 0.85, fontSize: '0.82rem', letterSpacing: '0.08em' }}>READY</span>
          </div>

          <div style={{ padding: '1.25rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '1rem', borderBottom: '1.5px dashed var(--border-dashed)', paddingBottom: '0.75rem' }}>
              <div>
                <span style={{ fontSize: '0.85rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--success)', letterSpacing: '0.05em', fontFamily: 'var(--font-notes)' }}>
                  ✨ Optimization Complete
                </span>
                <h2 style={{ margin: '0.15rem 0 0 0', fontFamily: 'var(--font-title)', fontSize: '1.5rem' }}>
                  Auditor-Approved Resume Draft
                </h2>
              </div>
              <div style={{ display: 'flex', gap: '0.75rem' }}>
                <button
                  type="button"
                  className="btn btn-ghost"
                  onClick={handleCopyText}
                >
                  {copied ? '✓ Copied!' : '📋 Copy Text'}
                </button>
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={handleDownloadDocx}
                  disabled={downloading}
                >
                  {downloading
                    ? 'Preparing DOCX…'
                    : `📥 Download DOCX (${templates.find((t) => t.template_id === selectedTemplate)?.name ?? 'Default'})`}
                </button>
              </div>
            </div>

            {/* Template Selector */}
            <TemplateSelector
              templates={templates}
              selectedTemplate={selectedTemplate}
              onSelectTemplate={setSelectedTemplate}
            />

            {/* Iteration Timeline */}
            {loopResult.iteration_history && loopResult.iteration_history.length > 1 ? (
              <div style={{ background: 'var(--surface-cream)', padding: '1rem', borderRadius: 'var(--radius-sm)', marginBottom: '1.25rem', border: '1.5px dashed var(--border-dashed)' }}>
                <h3 className="marker-blue-title" style={{ fontSize: '1.15rem', margin: '0 0 0.5rem 0' }}>
                  🔄 Autonomous Refinement Timeline ({loopResult.iteration_history.length} iterations)
                </h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {loopResult.iteration_history.map((step: AgentIterationStep) => (
                    <div key={step.iteration} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.9rem', fontFamily: 'var(--font-body)' }}>
                      <span>
                        <strong>Pass #{step.iteration}:</strong> {step.refinement_prompt_used ?? 'Initial draft evaluated'}
                      </span>
                      <span style={{ fontWeight: 700, fontFamily: 'var(--font-title)', color: step.audit_result.overall_score >= 80 ? 'var(--success)' : 'var(--warning)' }}>
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
                fontFamily: 'var(--font-mono)',
                fontSize: '0.88rem',
                lineHeight: '1.6',
                padding: '1rem',
                borderRadius: 'var(--radius-sm)',
                border: 'var(--border-width) solid var(--contour-ink)',
                background: 'var(--surface-card)',
                color: 'var(--text)',
                boxShadow: 'inset 1px 1px 3px rgba(0, 0, 0, 0.05)',
              }}
              value={loopResult.final_draft}
            />
          </div>
        </section>
      ) : null}
    </div>
  )
}

