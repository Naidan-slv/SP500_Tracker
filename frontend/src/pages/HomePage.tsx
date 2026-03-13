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
            SP500 Tracker monitors the <strong>top 50 S&amp;P 500 companies</strong> by market
            capitalisation — names like Apple, Microsoft, Amazon, and NVIDIA — with 230,000+ rows of
            curated OHLCV history dating back to 2006. Every query is backed by a two-tier caching
            strategy so the experience stays fast even on free-tier hosting.
          </p>
          <div className="hero-meta">
            <span className="chip">49 tracked tickers</span>
            <span className="chip">Two-tier smart caching</span>
            <span className="chip">Live + historical data</span>
          </div>
          <div style={{ display: 'flex', gap: '0.65rem', marginTop: '1rem', flexWrap: 'wrap' }}>
            <Link className="button" to="/discover">Open Market Explorer</Link>
            <Link className="button secondary" to="/watchlists">View Watchlists</Link>
          </div>
        </div>
      </div>

      <div className="home-feature-grid">
        <article className="card home-feature-card reveal-up">
          <div className="home-feature-icon">⚡</div>
          <h3 className="section-title">Two-Tier Caching</h3>
          <p className="muted">
            The backend caches live market quotes (45 s TTL) and news feeds (5 min TTL) in memory to
            avoid hitting external provider limits. The React frontend uses TanStack Query with
            per-page stale windows (2–10 min) so page navigations feel instant and repeat searches
            never re-fetch unchanged data.
          </p>
        </article>

        <article className="card home-feature-card reveal-up" style={{ animationDelay: '80ms' }}>
          <div className="home-feature-icon">📊</div>
          <h3 className="section-title">Top 50 Focus</h3>
          <p className="muted">
            Rather than tracking the entire S&amp;P 500, the platform focuses on the 49 most
            impactful tickers by market cap, ensuring deep data quality — including company profiles,
            deterministic name overrides, and reliable provider fallbacks — for every stock that
            matters most to investors.
          </p>
        </article>

        <article className="card home-feature-card reveal-up" style={{ animationDelay: '160ms' }}>
          <div className="home-feature-icon">📰</div>
          <h3 className="section-title">News + Signals</h3>
          <p className="muted">
            Pair price action with relevant headlines filtered by timeframe (1 week → 5 years).
            Google News RSS feeds are time-scoped per filter, cached server-side, and client-side
            queries are keyed by ticker + window so switching filters is always responsive.
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
