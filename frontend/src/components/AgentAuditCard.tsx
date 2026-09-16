import type { ATSAuditResult } from '../types/api'

interface Props {
  audit: ATSAuditResult
}

export function AgentAuditCard({ audit }: Props) {
  const getScoreColor = (score: number) => {
    if (score >= 80) return 'var(--accent-teal)'
    if (score >= 60) return 'var(--accent-sun)'
    return 'var(--danger)'
  }

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'high':
        return { background: 'var(--danger-bg)', color: '#be123c', label: 'HIGH PRIORITY' }
      case 'medium':
        return { background: 'var(--warning-bg)', color: '#b45309', label: 'MEDIUM' }
      default:
        return { background: 'var(--accent-ice-bg)', color: '#0369a1', label: 'LOW' }
    }
  }

  return (
    <section className="note-card" style={{ marginTop: '1.5rem' }}>
      <div className="note-banner banner-peach">
        <span>MULTI-AGENT ATS CRITIQUE &amp; SCORECARD</span>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', letterSpacing: '0.08em' }}>
          AUDITOR AGENT
        </span>
      </div>

      <div style={{ padding: '1.5rem' }}>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '0.75rem',
            marginBottom: '1.25rem',
            borderBottom: '1px solid var(--contour-subtle)',
            paddingBottom: '0.85rem',
          }}
        >
          <div>
            <span
              style={{
                fontSize: '0.8rem',
                fontWeight: 700,
                textTransform: 'uppercase',
                letterSpacing: '0.1em',
                color: 'var(--accent-sun)',
                fontFamily: 'var(--font-body)',
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
              }}
            >
              <span
                style={{
                  width: '6px',
                  height: '6px',
                  borderRadius: '2px',
                  background: 'var(--accent-sun)',
                  display: 'inline-block',
                }}
              />
              Autonomous Multi-Agent Reflection
            </span>
            <h2
              style={{
                margin: '0.2rem 0 0 0',
                fontFamily: 'var(--font-title)',
                fontSize: '1.55rem',
                color: 'var(--text-main)',
              }}
            >
              ATS Auditor Scorecard
            </h2>
          </div>
          <div style={{ textAlign: 'right', display: 'flex', alignItems: 'baseline', gap: '0.35rem' }}>
            <span
              style={{
                fontFamily: 'var(--font-body)',
                fontSize: '2.4rem',
                fontWeight: 700,
                color: getScoreColor(audit.overall_score),
                letterSpacing: '-0.02em',
              }}
            >
              {audit.overall_score}
            </span>
            <span
              style={{
                fontFamily: 'var(--font-body)',
                fontSize: '1.05rem',
                fontWeight: 600,
                color: 'var(--text-muted)',
              }}
            >
              {' '}
              / 100 ATS Score
            </span>
          </div>
        </div>

        {/* Sub-scores grid */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '1.25rem',
            marginBottom: '1.5rem',
            background: 'var(--surface-peach-subtle)',
            padding: '1.25rem',
            borderRadius: 'var(--radius-md)',
            border: '1.5px dashed var(--border-dashed)',
          }}
        >
          <div>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                fontSize: '0.9rem',
                marginBottom: '0.45rem',
                fontFamily: 'var(--font-body)',
                fontWeight: 700,
              }}
            >
              <span>Keyword Coverage (40%)</span>
              <span style={{ color: getScoreColor(audit.keyword_score) }}>{audit.keyword_score}%</span>
            </div>
            <div
              style={{
                width: '100%',
                height: '10px',
                background: 'var(--surface-tint)',
                borderRadius: '999px',
                border: '1px solid var(--contour-ink)',
                overflow: 'hidden',
              }}
            >
              <div
                style={{
                  width: `${Math.min(audit.keyword_score, 100)}%`,
                  height: '100%',
                  background: getScoreColor(audit.keyword_score),
                  transition: 'width 0.7s cubic-bezier(0.16, 1, 0.3, 1)',
                }}
              />
            </div>
          </div>

          <div>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                fontSize: '0.9rem',
                marginBottom: '0.45rem',
                fontFamily: 'var(--font-body)',
                fontWeight: 700,
              }}
            >
              <span>Quantified Metrics (30%)</span>
              <span style={{ color: getScoreColor(audit.metric_score) }}>{audit.metric_score}%</span>
            </div>
            <div
              style={{
                width: '100%',
                height: '10px',
                background: 'var(--surface-tint)',
                borderRadius: '999px',
                border: '1px solid var(--contour-ink)',
                overflow: 'hidden',
              }}
            >
              <div
                style={{
                  width: `${Math.min(audit.metric_score, 100)}%`,
                  height: '100%',
                  background: getScoreColor(audit.metric_score),
                  transition: 'width 0.7s cubic-bezier(0.16, 1, 0.3, 1)',
                }}
              />
            </div>
          </div>

          <div>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                fontSize: '0.9rem',
                marginBottom: '0.45rem',
                fontFamily: 'var(--font-body)',
                fontWeight: 700,
              }}
            >
              <span>Action Verbs &amp; Format (30%)</span>
              <span style={{ color: getScoreColor(audit.structure_score) }}>{audit.structure_score}%</span>
            </div>
            <div
              style={{
                width: '100%',
                height: '10px',
                background: 'var(--surface-tint)',
                borderRadius: '999px',
                border: '1px solid var(--contour-ink)',
                overflow: 'hidden',
              }}
            >
              <div
                style={{
                  width: `${Math.min(audit.structure_score, 100)}%`,
                  height: '100%',
                  background: getScoreColor(audit.structure_score),
                  transition: 'width 0.7s cubic-bezier(0.16, 1, 0.3, 1)',
                }}
              />
            </div>
          </div>
        </div>

        {/* Critiques List */}
        {audit.critiques && audit.critiques.length > 0 ? (
          <div style={{ marginBottom: '1.5rem' }}>
            <h3 className="marker-blue-title" style={{ fontSize: '1.25rem', marginBottom: '0.85rem' }}>
              Actionable Auditor Fixes ({audit.critiques.length})
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
              {audit.critiques.map((item, idx) => {
                const badge = getSeverityBadge(item.severity)
                return (
                  <div
                    key={idx}
                    style={{
                      padding: '0.95rem 1.15rem',
                      borderRadius: 'var(--radius-sm)',
                      border: 'var(--border-width) solid var(--contour-ink)',
                      background: 'var(--surface-card)',
                      boxShadow: 'var(--shadow-sm)',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.4rem' }}>
                      <span
                        style={{
                          fontSize: '0.72rem',
                          fontFamily: 'var(--font-body)',
                          fontWeight: 700,
                          padding: '0.2rem 0.6rem',
                          borderRadius: 'var(--radius-pill)',
                          border: '1px solid var(--contour-ink)',
                          background: badge.background,
                          color: badge.color,
                          letterSpacing: '0.04em',
                        }}
                      >
                        {badge.label}
                      </span>
                      <span
                        style={{
                          fontSize: '0.78rem',
                          fontFamily: 'var(--font-mono)',
                          textTransform: 'uppercase',
                          color: 'var(--text-muted)',
                          fontWeight: 600,
                        }}
                      >
                        {item.category}
                      </span>
                    </div>
                    <p style={{ margin: '0 0 0.35rem 0', fontWeight: 600, fontSize: '0.96rem', color: 'var(--text-main)' }}>
                      {item.issue}
                    </p>
                    <p style={{ margin: 0, fontSize: '0.92rem', color: 'var(--text-muted)' }}>
                      <strong style={{ color: 'var(--accent-teal)' }}>Suggestion: </strong>
                      {item.suggestion}
                    </p>
                  </div>
                )
              })}
            </div>
          </div>
        ) : null}

        {/* Strengths */}
        {audit.strengths && audit.strengths.length > 0 ? (
          <div>
            <h3 className="marker-blue-title" style={{ color: 'var(--accent-teal)' }}>
              Confirmed Strengths
            </h3>
            <ul className="note-bullets">
              {audit.strengths.map((str, idx) => (
                <li key={idx}>
                  <strong>Strength:</strong> {str}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </div>
    </section>
  )
}
