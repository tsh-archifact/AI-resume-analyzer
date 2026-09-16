import type { LLMRecommendation } from '../types/api'

interface AnalysisCardProps {
  analysis: LLMRecommendation
}

export function AnalysisCard({ analysis }: AnalysisCardProps) {
  return (
    <article className="note-card analysis-card">
      <div className="note-banner banner-peach">
        <span>RECRUITER AUDIT NOTES</span>
        <span className="model-badge">LLM: {analysis.model_used}</span>
      </div>

      <div className="analysis-content">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', borderBottom: '1.5px dashed var(--border-dashed)', paddingBottom: '0.6rem' }}>
          <div>
            <span style={{ fontFamily: 'var(--font-notes)', fontSize: '1.05rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Candidate Assessment
            </span>
            <h2 style={{ margin: '0.1rem 0 0', fontFamily: 'var(--font-title)', fontSize: '1.6rem', color: 'var(--text-main)' }}>
              {analysis.overall_fit || 'Analysis'} Fit
            </h2>
          </div>
        </div>

        {analysis.summary ? (
          <p className="analysis-summary">
            <strong>Recruiter Takeaway:</strong> {analysis.summary}
          </p>
        ) : null}

        <div className="analysis-grid">
          {analysis.strengths.length > 0 ? (
            <section>
              <h3 className="marker-blue-title">✨ Key Strengths</h3>
              <ul className="note-bullets">
                {analysis.strengths.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </section>
          ) : null}

          {analysis.missing_skills.length > 0 ? (
            <section>
              <h3 className="marker-blue-title" style={{ color: 'var(--danger)' }}>
                ⚠️ Gaps to Address
              </h3>
              <ul className="note-bullets">
                {analysis.missing_skills.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </section>
          ) : null}

          {analysis.required_skills.length > 0 ? (
            <section>
              <h3 className="marker-blue-title">🎯 Required Skills</h3>
              <ul className="note-bullets">
                {analysis.required_skills.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </section>
          ) : null}

          {analysis.nice_to_have_skills.length > 0 ? (
            <section>
              <h3 className="marker-blue-title">💡 Nice to Have</h3>
              <ul className="note-bullets">
                {analysis.nice_to_have_skills.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </section>
          ) : null}
        </div>

        {analysis.recommendations.length > 0 ? (
          <section className="recommendations" style={{ borderTop: '1.5px dashed var(--border-dashed)', paddingTop: '0.85rem' }}>
            <h3 className="marker-blue-title">📝 Targeted Recommendations</h3>
            <ol style={{ paddingLeft: '1.25rem', margin: '0.4rem 0 0', lineHeight: 1.6 }}>
              {analysis.recommendations.map((item) => (
                <li key={item} style={{ marginBottom: '0.35rem' }}>{item}</li>
              ))}
            </ol>
          </section>
        ) : null}
      </div>
    </article>
  )
}
