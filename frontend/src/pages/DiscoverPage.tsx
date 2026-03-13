import { useMemo, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'

import { useAuth } from '../auth/AuthContext'
import { fetchStockDetail, fetchStockHistory, fetchStocks, fetchWatchlists, getApiBaseUrl } from '../lib/api'
import { getMarketLabel, matchesMarketFilter, type MarketFilter } from '../lib/market'

const PAGE_SIZE = 12

const filters: Array<{ value: MarketFilter; label: string }> = [
  { value: 'all', label: 'All Markets' },
  { value: 'us', label: 'US' },
  { value: 'asia', label: 'Asia' },
  { value: 'middle-east', label: 'Middle East' },
]

function StockPreviewCard({
  ticker,
  companyName,
  logoUrl,
  onMouseEnter,
}: {
  ticker: string
  companyName: string | null
  logoUrl: string | null
  onMouseEnter: () => void
}) {
  return (
    <Link to={`/stocks/${ticker}`} className="stock-card" onMouseEnter={onMouseEnter}>
      <div className="stock-card-header">
        <div className="stock-card-identity">
          {logoUrl ? (
            <img className="stock-logo" src={logoUrl} alt={ticker} onError={(e) => ((e.target as HTMLImageElement).style.display = 'none')} />
          ) : (
            <div className="stock-logo-placeholder">{ticker.slice(0, 3)}</div>
          )}
          <div>
            <div className="stock-ticker">{ticker}</div>
            <div className="stock-name">{companyName ?? 'Unknown company'}</div>
          </div>
        </div>
        <span className="market-badge">{getMarketLabel(ticker)}</span>
      </div>

      <div className="muted" style={{ fontSize: '0.86rem' }}>
        Open for full analytics, price history, live market activity and news.
      </div>
    </Link>
  )
}

export function DiscoverPage() {
  const apiBaseUrl = getApiBaseUrl()
  const queryClient = useQueryClient()
  const { token, user } = useAuth()

  const [searchInput, setSearchInput] = useState('')
  const [activeFilter, setActiveFilter] = useState<MarketFilter>('all')
  const [page, setPage] = useState(1)
  const [showSuggestions, setShowSuggestions] = useState(false)

  const stocksQuery = useQuery({
    queryKey: ['stocks-universe'],
    queryFn: () => fetchStocks('', 100, 0),
    staleTime: 1000 * 60 * 10,
    gcTime: 1000 * 60 * 30,
  })

  const watchlistsQuery = useQuery({
    queryKey: ['watchlists-home', token],
    queryFn: () => fetchWatchlists(token!),
    enabled: Boolean(token),
  })

  const filteredStocks = useMemo(() => {
    const allStocks = stocksQuery.data?.items ?? []
    const search = searchInput.trim().toUpperCase()

    return allStocks.filter((stock) => {
      const matchesSearch =
        !search ||
        stock.ticker.toUpperCase().includes(search) ||
        (stock.company_name ?? '').toUpperCase().includes(search)

      return matchesSearch && matchesMarketFilter(stock.ticker, activeFilter)
    })
  }, [activeFilter, searchInput, stocksQuery.data])

  const pagedStocks = useMemo(() => {
    const start = (page - 1) * PAGE_SIZE
    return filteredStocks.slice(start, start + PAGE_SIZE)
  }, [filteredStocks, page])

  const totalPages = Math.max(1, Math.ceil(filteredStocks.length / PAGE_SIZE))

  const suggestions = useMemo(() => {
    const allStocks = stocksQuery.data?.items ?? []
    const search = searchInput.trim().toUpperCase()
    if (!search) return []

    return allStocks
      .filter((stock) => {
        const ticker = stock.ticker.toUpperCase()
        const name = (stock.company_name ?? '').toUpperCase()
        return ticker.includes(search) || name.includes(search)
      })
      .slice(0, 8)
  }, [searchInput, stocksQuery.data])

  function prefetchStock(ticker: string) {
    void import('./StockDetailPage')
    void queryClient.prefetchQuery({
      queryKey: ['stock-detail', ticker],
      queryFn: () => fetchStockDetail(ticker),
      staleTime: 1000 * 60 * 5,
    })
    void queryClient.prefetchQuery({
      queryKey: ['stock-history', ticker, '6m'],
      queryFn: () => fetchStockHistory(ticker, '6m'),
      staleTime: 1000 * 60 * 5,
    })
  }

  return (
    <section className="grid" style={{ gap: '1rem' }}>
      <div className="card hero-card">
        <div className="eyebrow">Palette-driven dashboard refresh</div>
        <h1 className="hero-title">Explore the market with faster filtering and smoother browsing.</h1>
        <p className="hero-copy">
          This is now a proper client-side dashboard: cached data, market filters, saved watchlist
          previews, and quick jumps into stock detail views without clunky refetch-heavy UX.
        </p>

        <div className="hero-meta">
          <span className="chip">49 tickers indexed</span>
          <span className="chip">Client-side cached queries</span>
          <span className="chip">API: {apiBaseUrl}</span>
        </div>

        <div className="search-row" style={{ marginTop: '1.2rem' }}>
          <div className="search-box">
            <input
              className="input"
              placeholder="Search ticker/company (e.g. AAPL, Microsoft)"
              value={searchInput}
              onFocus={() => setShowSuggestions(true)}
              onBlur={() => {
                setTimeout(() => setShowSuggestions(false), 150)
              }}
              onChange={(event) => {
                setSearchInput(event.target.value)
                setPage(1)
                setShowSuggestions(true)
              }}
            />

            {showSuggestions && suggestions.length > 0 && (
              <div className="suggestions-card">
                {suggestions.map((stock) => (
                  <button
                    key={stock.ticker}
                    type="button"
                    className="suggestion-item"
                    onClick={() => {
                      setSearchInput(stock.ticker)
                      setPage(1)
                      setShowSuggestions(false)
                    }}
                  >
                    <div>
                      <strong>{stock.ticker}</strong>
                      <div className="muted" style={{ fontSize: '0.84rem' }}>
                        {stock.company_name ?? 'Unknown company'}
                      </div>
                    </div>
                    <span className="chip">{getMarketLabel(stock.ticker)}</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          <button
            className="button secondary"
            type="button"
            onClick={() => {
              setSearchInput('')
              setActiveFilter('all')
              setPage(1)
              setShowSuggestions(false)
            }}
          >
            Reset
          </button>
        </div>

        <div className="filter-row" style={{ marginTop: '1rem' }}>
          {filters.map((filter) => (
            <button
              key={filter.value}
              className={`button secondary ${activeFilter === filter.value ? 'active' : ''}`}
              type="button"
              onClick={() => {
                setActiveFilter(filter.value)
                setPage(1)
              }}
            >
              {filter.label}
            </button>
          ))}
        </div>
      </div>

      {user && (
        <div className="card">
          <div className="panel-header">
            <div>
              <h2 className="section-title">Saved Watchlists</h2>
              <div className="muted">Quick jump into your personal market themes.</div>
            </div>
            <Link to="/watchlists" className="button secondary">Open Watchlists</Link>
          </div>

          {watchlistsQuery.isLoading ? (
            <div className="empty-state">Loading your watchlists...</div>
          ) : !watchlistsQuery.data?.items.length ? (
            <div className="empty-state">No saved watchlists yet. Create one from the watchlists page.</div>
          ) : (
            <div className="mini-grid">
              {watchlistsQuery.data.items.slice(0, 4).map((watchlist) => (
                <Link key={watchlist.id} to="/watchlists" className="list-card card-link">
                  <div>
                    <strong>{watchlist.name}</strong>
                    <div className="muted">{watchlist.items_count} tickers</div>
                  </div>
                  <span className="chip">#{watchlist.id}</span>
                </Link>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="card table-shell table-wrap">
        {stocksQuery.isLoading && <div className="empty-state">Loading stocks...</div>}
        {stocksQuery.error && (
          <div className="card" style={{ borderColor: '#7f1d1d', marginBottom: '0.8rem' }}>
            <strong className="negative">Could not load stocks</strong>
            <p className="negative" style={{ marginBottom: 0 }}>
              {(stocksQuery.error as Error).message}
            </p>
          </div>
        )}

        {!stocksQuery.isLoading && !stocksQuery.error && (
          <>
            <div className="panel-header">
              <div>
                <h2 className="section-title">Browse universe</h2>
                <div className="muted">
                  {filteredStocks.length} matching stocks · page {page} of {totalPages}
                </div>
              </div>
              <div className="chip">FastAPI + Render + Supabase</div>
            </div>

            {!pagedStocks.length ? (
              <div className="empty-state">No stocks match the current search and market filter.</div>
            ) : (
              <div className="stock-cards-grid">
                {pagedStocks.map((stock) => (
                  <StockPreviewCard
                    key={stock.ticker}
                    ticker={stock.ticker}
                    companyName={stock.company_name}
                    logoUrl={stock.logo_url}
                    onMouseEnter={() => prefetchStock(stock.ticker)}
                  />
                ))}
              </div>
            )}

            <div className="pager-row">
              <button
                className="button secondary"
                type="button"
                onClick={() => setPage((value) => Math.max(1, value - 1))}
                disabled={page === 1}
              >
                Previous
              </button>
              <span className="chip">Page {page}</span>
              <button
                className="button"
                type="button"
                onClick={() => setPage((value) => Math.min(totalPages, value + 1))}
                disabled={page >= totalPages}
              >
                Next
              </button>
            </div>
          </>
        )}
      </div>
    </section>
  )
}
