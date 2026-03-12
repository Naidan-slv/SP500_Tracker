import { Link, NavLink } from 'react-router-dom'
import { useState } from 'react'

import { useAuth } from '../auth/AuthContext'
import { AuthModal } from './AuthModal'

export function Navbar() {
  const [authOpen, setAuthOpen] = useState(false)
  const { user, logout, sessionLoading } = useAuth()

  return (
    <>
      <header className="navbar">
        <div>
          <div className="eyebrow">SP500 Tracker · live analytics</div>
          <Link to="/" className="navbar-title">
            Stock Intelligence Dashboard
          </Link>
          <div className="navbar-subtitle">Frontend wired to your live Render API</div>
        </div>

        <nav className="nav-links">
          <NavLink to="/" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`} end>
            Discover
          </NavLink>
          <NavLink
            to="/watchlists"
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          >
            Watchlists
          </NavLink>
          <NavLink
            to="/portfolio"
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          >
            Portfolio
          </NavLink>
        </nav>

        <div style={{ display: 'flex', gap: '0.6rem', alignItems: 'center' }}>
          {sessionLoading && <span className="muted">Checking session...</span>}

          {!sessionLoading && !user && (
            <button className="button secondary" type="button" onClick={() => setAuthOpen(true)}>
              Login / Register
            </button>
          )}

          {!sessionLoading && user && (
            <>
              <span className="user-pill">{user.email}</span>
              <button className="button secondary" type="button" onClick={logout}>
                Logout
              </button>
            </>
          )}
        </div>
      </header>

      <AuthModal open={authOpen} onClose={() => setAuthOpen(false)} />
    </>
  )
}
