interface MatchScoreProps {
  score: number
  overallFit?: string
}

function scoreTone(score: number): 'strong' | 'moderate' | 'weak' {
  if (score >= 70) return 'strong'
  if (score >= 40) return 'moderate'
  return 'weak'
}

export function MatchScore({ score, overallFit }: MatchScoreProps) {
  const tone = scoreTone(score)
  const rounded = Math.round(score)

  return (
    <div className={`match-score match-score-${tone}`}>
      <div className="score-ring" style={{ ['--score' as string]: `${rounded}%` }}>
        <div className="score-value">
          <span>{rounded}</span>
          <small>%</small>
        </div>
      </div>
      <div className="score-copy">
        <p className="score-label">Match score</p>
        {overallFit ? <p className="score-fit">{overallFit} fit</p> : null}
      </div>
    </div>
  )
}
