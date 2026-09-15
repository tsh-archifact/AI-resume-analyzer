import type { ATSAuditResult } from '../types/api'

interface Props {
  audit: ATSAuditResult
}

export function AgentAuditCard({ audit }: Props) {
  const getScoreColor = (score: number) => {
    if (score >= 80) return '#10b981'
    if (score >= 60) return '#f59e0b'
    return '#ef4444'
  }

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'high':
        return { background: '#fee2e2', color: '#b91c1c', label: 'HIGH PRIORITY' }
      case 'medium':
        return { background: '#fef3c7', color: '#b45309', label: 'MEDIUM' }
      default:
        return { background: '#f3f4f6', color: '#4b5563', label: 'LOW' }
    }
  }

  return (
    <section className="panel card-panel" style={{ marginTop: '1.5rem', border: '1px solid var(--border, #e2e8f0)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem', marginBottom: '1.25rem' }}>
        <div>
          <span style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: '#6366f1' }}>
            🤖 Multi-Agent Intelligence
          </span>
          <h2 style={{ margin: '0.25rem 0 0 0', fontSize: '1.25rem', fontWeight: 700 }}>
            ATS Auditor Agent Critique & Scorecard
          </h2>
        </div>
        <div style={{ textAlign: 'right' }}>
          <span style={{ fontSize: '1.75rem', fontWeight: 800, color: getScoreColor(audit.overall_score) }}>
            {audit.overall_score}
          </span>
          <span style={{ fontSize: '0.875rem', color: '#64748b', fontWeight: 600 }}> / 100 ATS Score</span>
        </div>
      </div>

      {/* Sub-scores grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '1.5rem', background: '#f8fafc', padding: '1rem', borderRadius: '8px' }}>
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '0.35rem', fontWeight: 600 }}>
            <span>Keyword Coverage (40%)</span>
            <span style={{ color: getScoreColor(audit.keyword_score) }}>{audit.keyword_score}%</span>
          </div>
          <div style={{ width: '100%', height: '8px', background: '#e2e8f0', borderRadius: '4px', overflow: 'hidden' }}>
            <div style={{ width: `${Math.min(audit.keyword_score, 100)}%`, height: '100%', background: getScoreColor(audit.keyword_score), borderRadius: '4px' }} />
          </div>
        </div>

        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '0.35rem', fontWeight: 600 }}>
            <span>Quantified Metrics (30%)</span>
            <span style={{ color: getScoreColor(audit.metric_score) }}>{audit.metric_score}%</span>
          </div>
          <div style={{ width: '100%', height: '8px', background: '#e2e8f0', borderRadius: '4px', overflow: 'hidden' }}>
            <div style={{ width: `${Math.min(audit.metric_score, 100)}%`, height: '100%', background: getScoreColor(audit.metric_score), borderRadius: '4px' }} />
          </div>
        </div>

        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '0.35rem', fontWeight: 600 }}>
            <span>Action Verbs & Layout (30%)</span>
            <span style={{ color: getScoreColor(audit.structure_score) }}>{audit.structure_score}%</span>
          </div>
          <div style={{ width: '100%', height: '8px', background: '#e2e8f0', borderRadius: '4px', overflow: 'hidden' }}>
            <div style={{ width: `${Math.min(audit.structure_score, 100)}%`, height: '100%', background: getScoreColor(audit.structure_score), borderRadius: '4px' }} />
          </div>
        </div>
      </div>

      {/* Critiques List */}
      {audit.critiques && audit.critiques.length > 0 ? (
        <div style={{ marginBottom: '1.5rem' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '0.75rem', color: '#1e293b' }}>
            🎯 Actionable Fixes Identified by Auditor ({audit.critiques.length})
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {audit.critiques.map((item, idx) => {
              const badge = getSeverityBadge(item.severity)
              return (
                <div
                  key={idx}
                  style={{
                    padding: '0.85rem',
                    borderRadius: '8px',
                    border: '1px solid #e2e8f0',
                    background: '#ffffff',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem' }}>
                    <span
                      style={{
                        fontSize: '0.65rem',
                        fontWeight: 700,
                        padding: '0.15rem 0.45rem',
                        borderRadius: '4px',
                        background: badge.background,
                        color: badge.color,
                        letterSpacing: '0.04em',
                      }}
                    >
                      {badge.label}
                    </span>
                    <span style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: '#64748b', fontWeight: 600 }}>
                      {item.category}
                    </span>
                  </div>
                  <p style={{ margin: '0 0 0.35rem 0', fontWeight: 600, fontSize: '0.9rem', color: '#0f172a' }}>
                    {item.issue}
                  </p>
                  <p style={{ margin: 0, fontSize: '0.85rem', color: '#475569' }}>
                    <span style={{ fontWeight: 600, color: '#2563eb' }}>Fix: </span>
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
          <h3 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '0.5rem', color: '#15803d' }}>
            ✨ Confirmed Strengths
          </h3>
          <ul style={{ margin: 0, paddingLeft: '1.25rem', fontSize: '0.875rem', color: '#334155' }}>
            {audit.strengths.map((str, idx) => (
              <li key={idx} style={{ marginBottom: '0.25rem' }}>{str}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  )
}
