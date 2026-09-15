import { Link } from 'react-router-dom'

export function HomePage() {
  return (
    <section className="hero container">
      <div className="hero-copy">
        <p className="eyebrow">Resume intelligence for job seekers</p>
        <h1>See how your resume stacks up before you apply.</h1>
        <p className="lead">
          Upload your resume and a job description to extract skills, measure fit, and generate a
          tailored rewrite powered by your backend LLM.
        </p>
        <div className="hero-actions">
          <Link to="/compare" className="btn btn-primary">
            Compare resume
          </Link>
          <Link to="/rewrite" className="btn btn-secondary">
            Rewrite resume
          </Link>
        </div>
      </div>

      <div className="hero-panel">
        <div className="stat-card">
          <span className="stat-value">01</span>
          <h2>Extract</h2>
          <p>Pull skills from PDF, DOC, or DOCX resumes and rich job-description formats.</p>
        </div>
        <div className="stat-card">
          <span className="stat-value">02</span>
          <h2>Score</h2>
          <p>Compare matched and missing skills with a clear percentage match score.</p>
        </div>
        <div className="stat-card">
          <span className="stat-value">03</span>
          <h2>Improve</h2>
          <p>Download an LLM-rewritten DOCX aligned to the role without inventing experience.</p>
        </div>
      </div>
    </section>
  )
}
