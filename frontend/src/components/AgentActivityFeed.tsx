import { useState, useEffect } from 'react'

export interface AgentThoughtLogItem {
  id: string
  agent: string
  thought: string
  timestamp: string
}

interface AgentActivityFeedProps {
  currentThought: string | null
  activeAgent: string | null
  progress: number
  history: AgentThoughtLogItem[]
  isComplete?: boolean
  error?: string | null
}

export function AgentActivityFeed({
  currentThought,
  activeAgent,
  progress,
  history,
  isComplete = false,
  error = null,
}: AgentActivityFeedProps) {
  const [seconds, setSeconds] = useState(0)
  const [showLog, setShowLog] = useState(true)

  useEffect(() => {
    if (isComplete || error) return
    const timer = setInterval(() => {
      setSeconds((prev) => prev + 1)
    }, 1000)
    return () => clearInterval(timer)
  }, [isComplete, error])

  const formatTimer = (secs: number) => {
    const m = Math.floor(secs / 60)
      .toString()
      .padStart(2, '0')
    const s = (secs % 60).toString().padStart(2, '0')
    return `${m}:${s}`
  }

  const getAgentIcon = (agentName: string | null) => {
    if (!agentName) return '🤖'
    const lower = agentName.toLowerCase()
    if (lower.includes('perception')) return '👁️'
    if (lower.includes('markdown')) return '📝'
    if (lower.includes('auditor') || lower.includes('critic')) return '🔍'
    if (lower.includes('fact')) return '🛡️'
    if (lower.includes('drafter')) return '✍️'
    if (lower.includes('similarity')) return '⚡'
    if (lower.includes('supervisor')) return '🧠'
    return '🤖'
  }

  return (
    <div className="agent-feed-card">
      <div className="agent-feed-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          <span className="agent-feed-icon">{getAgentIcon(activeAgent)}</span>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <h3 className="agent-feed-title">{activeAgent ?? 'Autonomous Agent Ecosystem'}</h3>
              {!isComplete && !error && (
                <span className="agent-pulse-badge">
                  <span className="agent-pulse-dot" />
                  THINKING
                </span>
              )}
              {isComplete && <span className="agent-complete-badge">✓ COMPLETED</span>}
            </div>
            <p className="agent-feed-subtitle">
              {isComplete ? 'All verification gates satisfied' : 'Real-time multi-agent reasoning stream'}
            </p>
          </div>
        </div>
        <div className="agent-feed-timer">
          <span>⏱️ {formatTimer(seconds)}</span>
        </div>
      </div>

      {/* Current Thought Card */}
      <div className="agent-current-thought-box">
        <div className="agent-thought-label">CURRENT AGENT THOUGHT &amp; ACTION</div>
        <p className="agent-thought-text">
          {currentThought ?? 'Initializing agent perception and reasoning pipelines…'}
        </p>
      </div>

      {/* Progress Bar */}
      <div className="agent-progress-container">
        <div className="agent-progress-bar" style={{ width: `${Math.min(Math.max(progress, 8), 100)}%` }} />
      </div>

      {/* Reasoning Steps History */}
      {history.length > 0 && (
        <div className="agent-log-section">
          <button
            type="button"
            className="agent-log-toggle"
            onClick={() => setShowLog((prev) => !prev)}
          >
            <span>📜 Agent Reasoning History ({history.length} steps)</span>
            <span>{showLog ? '▲ Hide' : '▼ View log'}</span>
          </button>

          {showLog && (
            <div className="agent-log-terminal">
              {history.map((item) => (
                <div key={item.id} className="agent-log-entry">
                  <span className="agent-log-time">[{item.timestamp}]</span>
                  <span className="agent-log-agent">{getAgentIcon(item.agent)} {item.agent}:</span>
                  <span className="agent-log-msg">{item.thought}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {error && <div className="agent-feed-error">⚠️ {error}</div>}
    </div>
  )
}
