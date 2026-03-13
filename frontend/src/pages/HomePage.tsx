import { Link } from 'react-router-dom'

export function HomePage() {
  return (
    <section className="grid" style={{ gap: '1rem' }}>
      <div className="card hero-card home-hero">
        <div className="home-hero-overlay" />
        <div className="home-hero-content">
          <div className="eyebrow">Institution-grade market intelligence</div>
          <h1 className="hero-title">Trade smarter with live market context.</h1>
          <p className="hero-copy">
            SP500 Tracker combines curated equity coverage, structured watchlists,
            portfolio monitoring, and deep ticker analytics in one professional workspace.
          </p>
          <div className="hero-meta">
            <span className="chip">Live market activity</span>
            <span className="chip">News + history insights</span>
            <span className="chip">Portfolio + watchlists</span>
          </div>
          <div style={{ display: 'flex', gap: '0.65rem', marginTop: '1rem', flexWrap: 'wrap' }}>
            <Link className="button" to="/discover">Open Market Explorer</Link>
            <Link className="button secondary" to="/watchlists">View Watchlists</Link>
          </div>
        </div>
      </div>

      <div className="home-feature-grid">
        <article className="card home-feature-card reveal-up">
          <div className="home-feature-icon">📊</div>
          <h3 className="section-title">Market Explorer</h3>
          <p className="muted">
            Navigate global tickers with intelligent filters, clean cards, and direct deep-dive access.
          </p>
        </article>

        <article className="card home-feature-card reveal-up" style={{ animationDelay: '80ms' }}>
          <div className="home-feature-icon">📰</div>
          <h3 className="section-title">News + Signals</h3>
          <p className="muted">
            Pair price action with relevant headlines and timeline context to improve decision quality.
          </p>
        </article>

        <article className="card home-feature-card reveal-up" style={{ animationDelay: '160ms' }}>
          <div className="home-feature-icon">🧭</div>
          <h3 className="section-title">Portfolio Command</h3>
          <p className="muted">
            Track holdings, organize watchlists, and review multi-horizon performance from one place.
          </p>
        </article>
      </div>

      <div className="card home-cta reveal-up" style={{ animationDelay: '220ms' }}>
        <div>
          <h2 className="section-title" style={{ fontSize: '1.35rem' }}>
            Built for serious analysis — not clutter.
          </h2>
          <p className="muted" style={{ marginTop: '0.35rem' }}>
            Clean visuals, focused data, and deliberate interactions designed for disciplined investors.
          </p>
        </div>
        <Link className="button" to="/discover">Start Exploring</Link>
      </div>
    </section>
  )
}
