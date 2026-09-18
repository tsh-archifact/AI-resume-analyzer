import { Link } from 'react-router-dom'
import { ScenicIllustration } from '../components/ScenicIllustration'

export function HomePage() {
  const now = new Date()
  const dayNumber = now.getDate()
  const monthName = now.toLocaleString('en-US', { month: 'long' })
  const dayName = now.toLocaleString('en-US', { weekday: 'long' })
  const monthUpper = monthName.toUpperCase()

  return (
    <section className="hero container">
      <div className="hero-copy">
        <div className="hero-title-wrapper">
          <h1>Resume Intelligence — Complete Notes</h1>
          <svg
            className="marker-scribble"
            viewBox="0 0 540 22"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            aria-hidden="true"
          >
            <path
              d="M3 15C95 6 220 18 310 12C385 7 470 14 537 11"
              stroke="#f97316"
              strokeWidth="5"
              strokeLinecap="round"
            />
          </svg>
        </div>

        <p className="hero-subtitle">
          candidate analysis · job-fit intelligence to interview ready
        </p>

        <p className="lead">
          Upload your resume and a target job description to extract core competencies, calculate
          real ATS match scores, and generate auditor-grade rewrites without hallucinating experience.
        </p>

        <div className="hero-actions">
          <Link to="/compare" className="btn btn-primary">
            ⚡ Compare Resume
          </Link>
          <Link to="/rewrite" className="btn btn-secondary">
            ✍️ Rewrite Resume
          </Link>
        </div>
      </div>

      {/* Illustrated Intelligence Showcase Card inspired directly by user screenshot */}
      <div className="hero-art-card">
        <div className="hero-art-left">
          <div>
            <div className="hero-art-header">
              <span>TODAY</span>
              <span className="divider">|</span>
              <span>{monthUpper} &gt;</span>
            </div>

            <div className="hero-art-date">
              <div className="hero-art-number">{dayNumber}</div>
              <div className="hero-art-month">{monthName} · {dayName}</div>
            </div>

            <div className="hero-art-section-title">TO-DO</div>
            <ul className="hero-art-items">
              <li className="hero-art-item">
                <span className="dot-orange" />
                <span>Plan career milestone &amp; role targets</span>
              </li>
              <li className="hero-art-item">
                <span className="dot-teal" />
                <span>Extract skills &amp; benchmark against JD</span>
              </li>
            </ul>

            <div className="hero-art-section-title" style={{ marginTop: '1.25rem' }}>
              AGENTS
            </div>
            <ul className="hero-art-items">
              <li className="hero-art-item">
                <span className="dot-orange" />
                <span>Multi-agent critique &amp; ATS reflection loop</span>
              </li>
            </ul>
          </div>
        </div>

        <div className="hero-art-right">
          <ScenicIllustration />
        </div>
      </div>

      {/* 3 Note Sheets styled in the serene modern illustrated aesthetic */}
      <div className="hero-notes-grid">
        {/* Card 1 */}
        <article className="hero-note-card">
          <div className="note-banner banner-peach">
            <span>EXTRACTION &amp; OCR</span>
            <span style={{ fontSize: '0.82rem', letterSpacing: '0.08em', opacity: 0.85 }}>DOCUMENTS</span>
          </div>
          <div className="card-body">
            <h2 className="marker-blue-title">Extract Skills &amp; Work History</h2>
            <div className="code-note">
              <div># Ingest candidate profile</div>
              <div>extract(resume.pdf, lang=&quot;en&quot;) <span className="comment"># Windows/Mac</span></div>
              <div>yield -&gt; skills, experience, projects</div>
            </div>

            <h3 className="marker-blue-title" style={{ fontSize: '1.15rem', marginTop: '0.5rem' }}>
              Input Channels
            </h3>
            <ul className="note-bullets">
              <li>
                <strong>PDF / DOCX</strong> <span className="bullet-arrow">→</span> semantic layout extraction
              </li>
              <li>
                <strong>Job Spec</strong> <span className="bullet-arrow">→</span> pasted text or uploaded file
              </li>
              <li>
                <strong>OCR Engine</strong> <span className="bullet-arrow">→</span> handles scanned images &amp; graphics
              </li>
            </ul>
          </div>
        </article>

        {/* Card 2 */}
        <article className="hero-note-card">
          <div className="note-banner banner-peach">
            <span>ATS SCORING &amp; GAPS</span>
            <span style={{ fontSize: '0.82rem', letterSpacing: '0.08em', opacity: 0.85 }}>BENCHMARK</span>
          </div>
          <div className="card-body">
            <p style={{ margin: '0 0 0.6rem', color: 'var(--text-muted)', fontSize: '0.94rem' }}>
              <strong>Fit Score:</strong> weighted keyword overlap + recruiter semantic intent.
            </p>

            <h2 className="marker-blue-title">Auditor Score Breakdown</h2>
            <div className="code-note">
              <div>keyword_coverage: 40% <span className="comment"># Hard skills</span></div>
              <div>quantified_metrics: 30% <span className="comment"># Measurable impact</span></div>
              <div>ats_formatting: 30% <span className="comment"># Clean sections</span></div>
            </div>

            <h3 className="marker-blue-title" style={{ fontSize: '1.15rem', marginTop: '0.5rem' }}>
              Output Deliverables
            </h3>
            <ul className="note-bullets">
              <li>
                <strong>Matched Tags</strong> <span className="bullet-arrow">→</span> skills confirmed in resume
              </li>
              <li>
                <strong>Missing Tags</strong> <span className="bullet-arrow">→</span> critical gaps to address
              </li>
              <li>
                <strong>Recruiter Notes</strong> <span className="bullet-arrow">→</span> actionable bullet advice
              </li>
            </ul>
          </div>
        </article>

        {/* Card 3 */}
        <article className="hero-note-card">
          <div className="note-banner banner-peach">
            <span>MULTI-AGENT REFLECTION LOOP</span>
            <span style={{ fontSize: '0.82rem', letterSpacing: '0.08em', opacity: 0.85 }}>OPTIMIZE</span>
          </div>
          <div className="card-body">
            <h2 className="marker-blue-title">Iterative Reflection Loop</h2>
            <div className="code-note">
              <div>drafter.write(resume, job_desc)</div>
              <div>auditor.critique(target=80) <span className="comment"># Loop</span></div>
              <div>fact_checker.verify(hallucination=False)</div>
            </div>

            <h3 className="marker-blue-title" style={{ fontSize: '1.15rem', marginTop: '0.5rem' }}>
              Agent Safeguards
            </h3>
            <ul className="note-bullets">
              <li>
                <strong>Drafter</strong> <span className="bullet-arrow">→</span> rewrites high-impact bullets
              </li>
              <li>
                <strong>Auditor</strong> <span className="bullet-arrow">→</span> tests against ATS screening
              </li>
              <li>
                <strong>Export DOCX</strong> <span className="bullet-arrow">→</span> clean, job-ready document
              </li>
            </ul>
          </div>
        </article>
      </div>
    </section>
  )
}
