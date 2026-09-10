import type { LLMRecommendation } from '../types/api'

interface AnalysisCardProps {
  analysis: LLMRecommendation
}

export function AnalysisCard({ analysis }: AnalysisCardProps) {
  return (
    <article className="analysis-card">
      <header className="analysis-header">
        <div>
          <p className="eyebrow">Recruiter analysis</p>
          <h2>{analysis.overall_fit || 'Analysis'} fit</h2>
        </div>
        <span className="model-badge">{analysis.model_used}</span>
      </header>

      {analysis.summary ? <p className="analysis-summary">{analysis.summary}</p> : null}

      <div className="analysis-grid">
        {analysis.strengths.length > 0 ? (
          <section>
            <h3>Strengths</h3>
            <ul>
              {analysis.strengths.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </section>
        ) : null}

        {analysis.missing_skills.length > 0 ? (
          <section>
            <h3>Gaps to address</h3>
            <ul>
              {analysis.missing_skills.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </section>
        ) : null}

        {analysis.required_skills.length > 0 ? (
          <section>
            <h3>Required skills</h3>
            <ul>
              {analysis.required_skills.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </section>
        ) : null}

        {analysis.nice_to_have_skills.length > 0 ? (
          <section>
            <h3>Nice to have</h3>
            <ul>
              {analysis.nice_to_have_skills.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </section>
        ) : null}
      </div>

      {analysis.recommendations.length > 0 ? (
        <section className="recommendations">
          <h3>Recommendations</h3>
          <ol>
            {analysis.recommendations.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ol>
        </section>
      ) : null}
    </article>
  )
}
