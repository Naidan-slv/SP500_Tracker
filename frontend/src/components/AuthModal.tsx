import { useState } from 'react'

import { useAuth } from '../auth/AuthContext'

type AuthTab = 'login' | 'register'

export function AuthModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { login, register } = useAuth()

  const [activeTab, setActiveTab] = useState<AuthTab>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  if (!open) {
    return null
  }

  async function handleLogin() {
    setLoading(true)
    setError(null)
    setMessage(null)
    try {
      await login(email, password)
      setMessage('Logged in successfully')
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  async function handleRegister() {
    setLoading(true)
    setError(null)
    setMessage(null)
    try {
      const response = await register(email, password)
      setMessage(response.message)
      setActiveTab('login')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-modal-overlay" role="dialog" aria-modal="true">
      <div className="auth-modal card">
        <div className="auth-modal-header">
          <div>
            <div className="eyebrow" style={{ marginBottom: '0.55rem' }}>Secure session access</div>
            <h3 style={{ margin: 0 }}>Account</h3>
          </div>
          <button className="button secondary" type="button" onClick={onClose}>
            Close
          </button>
        </div>

        <div className="auth-tabs">
          <button
            className={`button secondary ${activeTab === 'login' ? 'active' : ''}`}
            type="button"
            onClick={() => setActiveTab('login')}
          >
            Login
          </button>
          <button
            className={`button secondary ${activeTab === 'register' ? 'active' : ''}`}
            type="button"
            onClick={() => setActiveTab('register')}
          >
            Register
          </button>
        </div>

        <div className="grid" style={{ marginTop: '1rem' }}>
          <label>
            <div className="muted">Email</div>
            <input
              className="input"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="you@example.com"
            />
          </label>
          <label>
            <div className="muted">Password</div>
            <input
              className="input"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Minimum 8 characters"
            />
          </label>

          {message && <div className="chip positive">{message}</div>}
          {error && <div className="chip negative">{error}</div>}

          <div className="auth-action-row">
            {activeTab === 'login' && (
              <button className="button" type="button" disabled={loading} onClick={handleLogin}>
                {loading ? 'Logging in...' : 'Login'}
              </button>
            )}
            {activeTab === 'register' && (
              <button className="button" type="button" disabled={loading} onClick={handleRegister}>
                {loading ? 'Creating account...' : 'Register'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
