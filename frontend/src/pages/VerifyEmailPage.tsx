import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { verifyEmailToken } from '../lib/api'

type VerifyStatus = 'idle' | 'loading' | 'success' | 'error'

export function VerifyEmailPage() {
  const [searchParams] = useSearchParams()
  const token = useMemo(() => searchParams.get('token')?.trim() ?? '', [searchParams])

  const [status, setStatus] = useState<VerifyStatus>(token ? 'loading' : 'error')
  const [message, setMessage] = useState(
    token ? 'Verifying your email…' : 'Missing verification token. Please use the link from your email.',
  )

  useEffect(() => {
    if (!token) {
      return
    }

    let active = true

    async function verify() {
      setStatus('loading')
      setMessage('Verifying your email…')
      try {
        const response = await verifyEmailToken(token)
        if (!active) {
          return
        }
        setStatus('success')
        setMessage(response.message)
      } catch (error) {
        if (!active) {
          return
        }
        setStatus('error')
        setMessage(error instanceof Error ? error.message : 'Verification failed')
      }
    }

    void verify()

    return () => {
      active = false
    }
  }, [token])

  return (
    <section className="grid" style={{ gap: '1rem' }}>
      <div className="card" style={{ maxWidth: 720, margin: '0 auto' }}>
        <div className="eyebrow">Email Verification</div>
        <h2 style={{ marginTop: '0.4rem' }}>Confirm your account</h2>
        <p className="muted" style={{ marginBottom: '1rem' }}>
          We are activating your account so you can access watchlists and portfolio features.
        </p>

        {status === 'loading' && <div className="chip">{message}</div>}
        {status === 'success' && <div className="chip positive">{message}</div>}
        {status === 'error' && <div className="chip negative">{message}</div>}

        <div style={{ display: 'flex', gap: '0.6rem', marginTop: '1rem', flexWrap: 'wrap' }}>
          <Link to="/discover" className="button secondary">
            Continue to Discover
          </Link>
          <Link to="/" className="button secondary">
            Back to Home
          </Link>
        </div>
      </div>
    </section>
  )
}
