import { NavLink, Outlet } from 'react-router-dom'

import { useAuth } from '../context/AuthContext'

export function Layout() {
  const { user, logout } = useAuth()

  return (
    <div className="app-shell">
      <header className="site-header">
        <div className="container header-inner">
          <NavLink to="/" className="brand">
            <span className="brand-mark" aria-hidden="true">
              📝
            </span>
            <span>
              <strong>Resume Analyzer</strong>
              <small>complete notes · job-fit intelligence</small>
            </span>
          </NavLink>

          <nav className="site-nav" aria-label="Main navigation">
            <NavLink to="/compare" className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}>
              Compare
            </NavLink>
            <NavLink to="/rewrite" className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}>
              Rewrite
            </NavLink>
          </nav>

          <div className="header-actions">
            {user ? (
              <>
                <span className="user-chip">user: {user.username}</span>
                <button type="button" className="btn btn-ghost" onClick={logout}>
                  Sign out
                </button>
              </>
            ) : (
              <>
                <NavLink to="/login" className="btn btn-ghost">
                  Sign in
                </NavLink>
                <NavLink to="/register" className="btn btn-primary">
                  Sign up
                </NavLink>
              </>
            )}
          </div>
        </div>
      </header>

      <main className="site-main">
        <Outlet />
      </main>

      <footer className="site-footer">
        <div className="container footer-inner">
          <p>
            <strong>AI Resume Analyzer</strong> — revision notes &amp; multi-agent reflection loop for job applicants.
          </p>
          <p className="footer-meta">
            Backend API: <code style={{ fontFamily: 'var(--font-mono)' }}>http://127.0.0.1:8000</code> · FastAPI + Groq LLM
          </p>
        </div>
      </footer>
    </div>
  )
}
