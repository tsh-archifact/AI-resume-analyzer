import { useState, useEffect, type FormEvent } from 'react'

import {
  compareResumeStream,
  runAgentRewriteStream,
  exportDocx,
  getResumeTemplates,
  type ResumeTemplateInfo,
  type AgentRewriteMetadata,
  type AgentThoughtEvent,
  DEFAULT_TEMPLATES,
} from '../api/resume'
import { ApiRequestError } from '../api/client'
import { AnalysisCard } from '../components/AnalysisCard'
import { AgentAuditCard } from '../components/AgentAuditCard'
import { AgentActivityFeed, type AgentThoughtLogItem } from '../components/AgentActivityFeed'
import { FileUpload } from '../components/FileUpload'
import { MatchScore } from '../components/MatchScore'
import { SkillTags } from '../components/SkillTags'
import { TemplateSelector } from '../components/TemplateSelector'
import { useAuth } from '../context/AuthContext'
import type {
  ResumeComparisonResponse,
  RefinementLoopResult,
  AgentIterationStep,
} from '../types/api'

const RESUME_ACCEPT = '.pdf,.doc,.docx'
const JD_ACCEPT = '.pdf,.doc,.docx,.txt,.png,.jpg,.jpeg'

type HitlDecision = 'pending' | 'declined' | 'accepted' | 'rewriting' | 'completed'

export function ComparePage() {
  const { token } = useAuth()
  const [resume, setResume] = useState<File | null>(null)
  const [jdFile, setJdFile] = useState<File | null>(null)
  const [jdText, setJdText] = useState('')
  const [jdMode, setJdMode] = useState<'text' | 'file'>('text')
  const [result, setResult] = useState<ResumeComparisonResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  // Real-time comparison streaming thought state
  const [compareThought, setCompareThought] = useState<string | null>(null)
  const [compareAgent, setCompareAgent] = useState<string | null>(null)
  const [compareProgress, setCompareProgress] = useState(0)
  const [compareLog, setCompareLog] = useState<AgentThoughtLogItem[]>([])

  // Human-in-the-Loop & Agentic Rewriting state
  const [hitlDecision, setHitlDecision] = useState<HitlDecision>('pending')
  const [templates, setTemplates] = useState<ResumeTemplateInfo[]>(DEFAULT_TEMPLATES)
  const [selectedTemplate, setSelectedTemplate] = useState<string>('modern_teal')
  const [loopResult, setLoopResult] = useState<RefinementLoopResult | null>(null)
  const [agentStats, setAgentStats] = useState<AgentRewriteMetadata | null>(null)
  const [rewriting, setRewriting] = useState(false)
  const [rewriteError, setRewriteError] = useState<string | null>(null)
  const [downloading, setDownloading] = useState(false)
  const [copied, setCopied] = useState(false)

  // Real-time rewrite streaming thought state
  const [rewriteThought, setRewriteThought] = useState<string | null>(null)
  const [rewriteAgent, setRewriteAgent] = useState<string | null>(null)
  const [rewriteProgress, setRewriteProgress] = useState(0)
  const [rewriteLog, setRewriteLog] = useState<AgentThoughtLogItem[]>([])

  useEffect(() => {
    if (!token) return
    getResumeTemplates(token)
      .then((items) => {
        if (items && items.length) {
          setTemplates(items)
        }
      })
      .catch(() => {
        // Fallback to DEFAULT_TEMPLATES
      })
  }, [token])

  const formatTimestamp = () => {
    const now = new Date()
    return now.toTimeString().split(' ')[0]
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setResult(null)
    setHitlDecision('pending')
    setLoopResult(null)
    setAgentStats(null)
    setRewriteError(null)

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
    setCompareThought('Initializing document extraction and parsing…')
    setCompareAgent('Perception Agent')
    setCompareProgress(10)
    setCompareLog([
      {
        id: String(Date.now()),
        agent: 'Perception Agent',
        thought: `Reading uploaded resume (${resume.name}) and target job description…`,
        timestamp: formatTimestamp(),
      },
    ])

    try {
      const response = await compareResumeStream(
        {
          resume,
          jobDescriptionFile: jdMode === 'file' ? jdFile : null,
          jobDescriptionText: jdMode === 'text' ? jdText : undefined,
        },
        token,
        (event: AgentThoughtEvent) => {
          if (event.thought) {
            setCompareThought(event.thought)
            setCompareAgent(event.agent ?? 'Autonomous Agent')
            if (event.progress) setCompareProgress(event.progress)
            setCompareLog((prev) => [
              ...prev,
              {
                id: String(Date.now()) + Math.random(),
                agent: event.agent ?? 'Agent',
                thought: event.thought ?? '',
                timestamp: formatTimestamp(),
              },
            ])
          }
        },
      )
      setResult(response)
      setHitlDecision('pending')
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

  async function handleStartRewrite() {
    if (!resume || !token) return
    setRewriteError(null)
    setRewriting(true)
    setHitlDecision('rewriting')
    setRewriteThought('Initializing autonomous Drafter, ATS Auditor, and Fact-Checking guardrail…')
    setRewriteAgent('Supervisor Agent')
    setRewriteProgress(10)
    setRewriteLog([
      {
        id: String(Date.now()),
        agent: 'Supervisor Agent',
        thought: 'Multi-agent reflection loop initiated. Target ATS score: 80%.',
        timestamp: formatTimestamp(),
      },
    ])

    try {
      const rewriteData = await runAgentRewriteStream(
        {
          resume,
          jobDescriptionFile: jdMode === 'file' ? jdFile : null,
          jobDescriptionText: jdMode === 'text' ? jdText : undefined,
        },
        token,
        (event: AgentThoughtEvent) => {
          if (event.thought) {
            setRewriteThought(event.thought)
            setRewriteAgent(event.agent ?? 'Agentic Optimizer')
            if (event.progress) setRewriteProgress(event.progress)
            setRewriteLog((prev) => [
              ...prev,
              {
                id: String(Date.now()) + Math.random(),
                agent: event.agent ?? 'Agent',
                thought: event.thought ?? '',
                timestamp: formatTimestamp(),
              },
            ])
          }
        },
        80, // Target score threshold
        3,  // Max iterations
      )

      setLoopResult(rewriteData)
      setAgentStats({
        initialScore: rewriteData.initial_score,
        finalScore: rewriteData.final_score,
        scoreImprovement: rewriteData.score_improvement,
        iterations: rewriteData.iterations_count,
        isFactClean: rewriteData.final_fact_check ? rewriteData.final_fact_check.is_clean : true,
      })
      setHitlDecision('completed')
    } catch (caught) {
      const message =
        caught instanceof ApiRequestError
          ? caught.message
          : 'Agent rewrite failed. Please check the logs and try again.'
      setRewriteError(message)
      setHitlDecision('accepted')
    } finally {
      setRewriting(false)
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
      setRewriteError(err instanceof Error ? err.message : 'Failed to download DOCX')
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
          <p className="eyebrow">Skill comparison &amp; Copilot</p>
          <h1>Compare your resume to a role</h1>
          <p className="lead">
            Upload your resume and target job description to audit ATS alignment with real-time agent thoughts.
            Then, review detailed recruiter notes or approve our multi-agent AI to rewrite your resume.
          </p>
        </div>
      </header>

      <div className="workspace-grid">
        <form className="note-card form-panel" onSubmit={handleSubmit}>
          <div className="note-banner banner-peach">
            <span>RESUME &amp; JOB INPUT</span>
            <span style={{ opacity: 0.8, fontSize: '0.82rem', letterSpacing: '0.08em' }}>INPUT</span>
          </div>

          <div className="form-panel-body">
            <FileUpload
              id="compare-resume"
              label="Candidate Resume"
              hint="PDF, DOC, or DOCX"
              accept={RESUME_ACCEPT}
              file={resume}
              onChange={setResume}
            />

            <fieldset className="mode-toggle">
              <legend>Job description input mode</legend>
              <label>
                <input
                  type="radio"
                  name="jd-mode"
                  checked={jdMode === 'text'}
                  onChange={() => setJdMode('text')}
                />
                ✏️ Paste text
              </label>
              <label>
                <input
                  type="radio"
                  name="jd-mode"
                  checked={jdMode === 'file'}
                  onChange={() => setJdMode('file')}
                />
                📁 Upload file
              </label>
            </fieldset>

            {jdMode === 'text' ? (
              <div className="field">
                <label htmlFor="jd-text">Target Job Description</label>
                <textarea
                  id="jd-text"
                  rows={9}
                  placeholder="Paste job description, requirements, or tech stack here…"
                  value={jdText}
                  onChange={(event) => setJdText(event.target.value)}
                />
              </div>
            ) : (
              <FileUpload
                id="compare-jd"
                label="Job Description File"
                hint="PDF, DOC, DOCX, TXT, PNG, JPG, or JPEG"
                accept={JD_ACCEPT}
                file={jdFile}
                onChange={setJdFile}
              />
            )}

            {error ? <p className="form-error">{error}</p> : null}

            <button type="submit" className="btn btn-primary btn-block" disabled={submitting}>
              {submitting ? 'Analyzing Live…' : 'Run Role Comparison'}
            </button>
          </div>
        </form>

        <div className="results-stack">
          {!result && !submitting ? (
            <div className="note-card empty-panel">
              <div className="note-banner banner-peach" style={{ width: '100%', margin: '-2rem -2rem 1.5rem' }}>
                <span>SCORECARD &amp; ANALYSIS</span>
                <span style={{ opacity: 0.8, fontSize: '0.82rem' }}>READY</span>
              </div>
              <h2>Results appear here</h2>
              <p>Submit a resume and job description to see live model reasoning, skill overlap, ATS audit, and AI recommendations.</p>
            </div>
          ) : null}

          {submitting ? (
            <AgentActivityFeed
              currentThought={compareThought}
              activeAgent={compareAgent}
              progress={compareProgress}
              history={compareLog}
            />
          ) : null}

          {result ? (
            <>
              <div className="note-card results-summary" style={{ padding: 0, overflow: 'hidden' }}>
                <div className="note-banner banner-peach" style={{ width: '100%' }}>
                  <span>ATS MATCH SCORECARD</span>
                  <span style={{ opacity: 0.8, fontSize: '0.82rem', letterSpacing: '0.08em' }}>VERIFIED</span>
                </div>
                <div style={{ padding: '1.25rem', width: '100%', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
                  <MatchScore
                    score={result.similarity.match_score}
                    overallFit={result.llm_analysis?.overall_fit}
                  />
                  <div className="file-meta" style={{ fontFamily: 'var(--font-notes)', fontSize: '1.1rem' }}>
                    <p style={{ margin: '0 0 0.3rem' }}>
                      <strong>Resume:</strong> {result.resume_file ?? 'Uploaded resume'}
                    </p>
                    <p style={{ margin: 0 }}>
                      <strong>Job description:</strong>{' '}
                      {result.job_description_file ?? (jdMode === 'text' ? 'Pasted text' : 'Uploaded file')}
                    </p>
                  </div>
                </div>
              </div>

              {/* ------------------------------------------------------------- */}
              {/* HUMAN-IN-THE-LOOP (HITL) DECISION & REWRITE WORKFLOW          */}
              {/* ------------------------------------------------------------- */}
              <div className="hitl-container">
                {hitlDecision === 'pending' ? (
                  <div className="hitl-prompt-card">
                    <div className="hitl-prompt-header">
                      <span className="hitl-badge">Human-in-the-Loop</span>
                      <h3 className="hitl-title">Would you like our Multi-Agent AI to rewrite &amp; optimize your resume?</h3>
                    </div>
                    <p className="hitl-desc">
                      Based on your match score ({result.similarity.match_score}%) and the detected skill gaps,
                      our autonomous Drafter, ATS Auditor Critic, and Fact-Checking Guardrail can rewrite your resume
                      bullets to maximize keyword density and truthfulness.
                    </p>
                    <div className="hitl-actions">
                      <button
                        type="button"
                        className="hitl-btn-yes"
                        onClick={() => setHitlDecision('accepted')}
                      >
                        ✨ Yes, optimize &amp; rewrite my resume
                      </button>
                      <button
                        type="button"
                        className="hitl-btn-no"
                        onClick={() => setHitlDecision('declined')}
                      >
                        No, view comparison only
                      </button>
                    </div>
                  </div>
                ) : null}

                {hitlDecision === 'declined' ? (
                  <div className="hitl-declined-strip">
                    <span>
                      📋 <strong>Comparison Mode Active:</strong> You chose to review the comparison output only.
                    </span>
                    <button
                      type="button"
                      className="btn btn-ghost"
                      style={{ fontSize: '0.86rem', padding: '0.35rem 0.75rem' }}
                      onClick={() => setHitlDecision('accepted')}
                    >
                      ✨ Change mind? Rewrite &amp; optimize now
                    </button>
                  </div>
                ) : null}

                {hitlDecision === 'accepted' || hitlDecision === 'rewriting' ? (
                  <div className="hitl-accepted-panel">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
                      <div>
                        <span className="hitl-badge">Step 2: Choose Template &amp; Launch</span>
                        <h3 className="hitl-title" style={{ marginTop: '0.3rem' }}>
                          Select DOCX Template Style
                        </h3>
                      </div>
                      <button
                        type="button"
                        className="btn btn-ghost"
                        style={{ fontSize: '0.85rem' }}
                        onClick={() => setHitlDecision('declined')}
                        disabled={rewriting}
                      >
                        ✕ Cancel
                      </button>
                    </div>

                    <TemplateSelector
                      templates={templates}
                      selectedTemplate={selectedTemplate}
                      onSelectTemplate={setSelectedTemplate}
                      disabled={rewriting}
                    />

                    {rewriteError ? <p className="form-error">{rewriteError}</p> : null}

                    {rewriting ? (
                      <AgentActivityFeed
                        currentThought={rewriteThought}
                        activeAgent={rewriteAgent}
                        progress={rewriteProgress}
                        history={rewriteLog}
                      />
                    ) : (
                      <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
                        <button
                          type="button"
                          className="btn btn-primary"
                          onClick={handleStartRewrite}
                          disabled={rewriting}
                        >
                          🚀 Launch Multi-Agent Rewrite
                        </button>
                        <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                          Reuses your uploaded resume and job description. Target score: 80%.
                        </span>
                      </div>
                    )}
                  </div>
                ) : null}

                {hitlDecision === 'completed' && loopResult ? (
                  <section className="note-card" style={{ padding: 0, overflow: 'hidden' }}>
                    <div className="note-banner banner-teal" style={{ width: '100%' }}>
                      <span>REFINED RESUME PREVIEW &amp; DOCX EXPORT</span>
                      <span style={{ opacity: 0.85, fontSize: '0.82rem', letterSpacing: '0.08em' }}>READY</span>
                    </div>

                    <div style={{ padding: '1.25rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '1rem', borderBottom: '1.5px dashed var(--border-dashed)', paddingBottom: '0.75rem' }}>
                        <div>
                          <span style={{ fontSize: '0.85rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--success)', letterSpacing: '0.05em', fontFamily: 'var(--font-notes)' }}>
                            ✨ Optimization Complete
                          </span>
                          <h2 style={{ margin: '0.15rem 0 0 0', fontFamily: 'var(--font-title)', fontSize: '1.4rem' }}>
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

                      {/* Performance card */}
                      {agentStats && agentStats.finalScore !== null ? (
                        <div className="agent-summary-card" style={{ marginBottom: '1.25rem', padding: '1rem', background: 'var(--surface-cream)', border: '1.5px dashed var(--border-dashed)', borderRadius: 'var(--radius-sm)' }}>
                          <h3 className="marker-blue-title" style={{ marginTop: 0, fontSize: '1.15rem' }}>🤖 Agent Performance Card</h3>
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

                      {/* Draft Viewer */}
                      <textarea
                        readOnly
                        rows={16}
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
