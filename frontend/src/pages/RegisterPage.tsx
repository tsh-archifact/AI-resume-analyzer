import { useState, type FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'

import { ApiRequestError } from '../api/client'
import { ScenicIllustration } from '../components/ScenicIllustration'
import { useAuth } from '../context/AuthContext'

export function RegisterPage() {
  const { register, user } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
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

    if (password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }

    setSubmitting(true)

    try {
      await register(username, password)
      navigate('/compare')
    } catch (caught) {
      const message =
        caught instanceof ApiRequestError
          ? caught.message
          : 'Unable to create your account. Please try again.'
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
            <p className="eyebrow">Get started</p>
            <h1 style={{ fontFamily: 'var(--font-title)', fontSize: '1.8rem', margin: '0.15rem 0 0.4rem', color: 'var(--text-main)' }}>
              Create your account
            </h1>
            <p className="lead" style={{ fontSize: '0.95rem', margin: '0 0 1.25rem' }}>
              Registration stores your account credentials in the local database.
            </p>

            <form className="stack-form" onSubmit={handleSubmit}>
              <div className="field">
                <label htmlFor="register-username">Username</label>
                <input
                  id="register-username"
                  name="username"
                  autoComplete="username"
                  minLength={3}
                  value={username}
                  onChange={(event) => setUsername(event.target.value)}
                  required
                />
              </div>

              <div className="field">
                <label htmlFor="register-password">Password</label>
                <input
                  id="register-password"
                  name="password"
                  type="password"
                  autoComplete="new-password"
                  minLength={8}
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  required
                />
              </div>

              <div className="field">
                <label htmlFor="confirm-password">Confirm password</label>
                <input
                  id="confirm-password"
                  name="confirmPassword"
                  type="password"
                  autoComplete="new-password"
                  minLength={8}
                  value={confirmPassword}
                  onChange={(event) => setConfirmPassword(event.target.value)}
                  required
                />
              </div>

              {error ? <p className="form-error">{error}</p> : null}

              <button type="submit" className="btn btn-primary btn-block" disabled={submitting}>
                {submitting ? 'Creating account…' : 'Create Account'}
              </button>
            </form>

            <p className="auth-switch">
              Already registered? <Link to="/login">Sign in</Link>
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
