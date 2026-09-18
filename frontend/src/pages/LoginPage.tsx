import { useState, type FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'

import { ApiRequestError } from '../api/client'
import { ScenicIllustration } from '../components/ScenicIllustration'
import { useAuth } from '../context/AuthContext'

export function LoginPage() {
  const { login, user } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  // Current live date & day
  const now = new Date()
  const dayNumber = now.getDate()
  const monthName = now.toLocaleString('en-US', { month: 'long' })
  const dayName = now.toLocaleString('en-US', { weekday: 'long' })
  const monthUpper = monthName.toUpperCase()

  if (user) {
    return <Navigate to="/compare" replace />
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)

    try {
      await login(username, password)
      navigate('/compare')
    } catch (caught) {
      const message =
        caught instanceof ApiRequestError
          ? caught.message
          : 'Unable to sign in. Please try again.'
      setError(message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className="container auth-page">
      <div className="auth-card-split">
        <div className="auth-split-left">
          <div className="auth-date-block">
            <div className="auth-date-header">
              <span>TODAY</span>
              <span className="divider">|</span>
              <span>{monthUpper} &gt;</span>
            </div>
            <div className="auth-date-number">{dayNumber}</div>
            <div className="auth-date-day">
              {monthName} · {dayName}
            </div>
          </div>

          <div>
            <p className="eyebrow">Welcome back</p>
            <h1 style={{ fontFamily: 'var(--font-title)', fontSize: '1.8rem', margin: '0.15rem 0 0.4rem', color: 'var(--text-main)' }}>
              Sign in to analyze resumes
            </h1>
            <p className="lead" style={{ fontSize: '0.95rem', margin: '0 0 1.25rem' }}>
              Access candidate analysis, ATS comparison, and multi-agent rewrites.
            </p>

            <form className="stack-form" onSubmit={handleSubmit}>
              <div className="field">
                <label htmlFor="username">Username</label>
                <input
                  id="username"
                  name="username"
                  autoComplete="username"
                  value={username}
                  onChange={(event) => setUsername(event.target.value)}
                  required
                />
              </div>

              <div className="field">
                <label htmlFor="password">Password</label>
                <input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="current-password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  required
                />
              </div>

              {error ? <p className="form-error">{error}</p> : null}

              <button type="submit" className="btn btn-primary btn-block" disabled={submitting}>
                {submitting ? 'Signing in…' : 'Sign In'}
              </button>
            </form>

            <p className="auth-switch">
              New here? <Link to="/register">Create an account (Sign up)</Link>
            </p>
          </div>
        </div>

        <div className="auth-split-right">
          <ScenicIllustration />
        </div>
      </div>
    </section>
  )
}
