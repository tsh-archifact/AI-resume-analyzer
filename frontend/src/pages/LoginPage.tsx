import { useState, type FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'

import { ApiRequestError } from '../api/client'
import { useAuth } from '../context/AuthContext'

export function LoginPage() {
  const { login, user } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

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
      <div className="auth-card">
        <p className="eyebrow">Welcome back</p>
        <h1>Sign in to analyze resumes</h1>
        <p className="lead">Use the account you created on the API to access compare and rewrite tools.</p>

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
            {submitting ? 'Signing in…' : 'Sign in'}
          </button>
        </form>

        <p className="auth-switch">
          New here? <Link to="/register">Create an account</Link>
        </p>
      </div>
    </section>
  )
}
