import { Link } from 'react-router-dom'

export function Navbar() {
  return (
    <header className="navbar">
      <div>
        <Link to="/" className="navbar-title">
          Stock Intelligence Dashboard
        </Link>
        <div className="navbar-subtitle">Frontend wired to your live Render API</div>
      </div>

      <div style={{ display: 'flex', gap: '0.6rem' }}>
        <button className="button secondary" type="button" title="Auth UI comes next">
          Login (next)
        </button>
      </div>
    </header>
  )
}
