import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'

import { useAuth } from '../auth/AuthContext'
import {
  addWatchlistItem,
  createWatchlist,
  fetchStocksUniverse,
  deleteWatchlist,
  fetchWatchlistInsights,
  fetchWatchlistItems,
  fetchWatchlists,
  removeWatchlistItem,
} from '../lib/api'

export function WatchlistsPage() {
  const queryClient = useQueryClient()
  const { token, user } = useAuth()
  const [newWatchlistName, setNewWatchlistName] = useState('')
  const [newTicker, setNewTicker] = useState('')
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [selectedWatchlistId, setSelectedWatchlistId] = useState<number | null>(null)
  const [pageError, setPageError] = useState<string | null>(null)

  const stocksUniverseQuery = useQuery({
    queryKey: ['stocks-universe', 'watchlists-page'],
    queryFn: () => fetchStocksUniverse(),
    staleTime: 1000 * 60 * 10,
    gcTime: 1000 * 60 * 30,
  })

  const watchlistsQuery = useQuery({
    queryKey: ['watchlists', token],
    queryFn: () => fetchWatchlists(token!),
    enabled: Boolean(token),
  })

  useEffect(() => {
    if (!selectedWatchlistId && watchlistsQuery.data?.items.length) {
      setSelectedWatchlistId(watchlistsQuery.data.items[0].id)
    }
  }, [selectedWatchlistId, watchlistsQuery.data])

  const itemsQuery = useQuery({
    queryKey: ['watchlist-items', token, selectedWatchlistId],
    queryFn: () => fetchWatchlistItems(token!, selectedWatchlistId!),
    enabled: Boolean(token && selectedWatchlistId),
  })

  const insightsQuery = useQuery({
    queryKey: ['watchlist-insights', token, selectedWatchlistId],
    queryFn: () => fetchWatchlistInsights(token!, selectedWatchlistId!),
    enabled: Boolean(token && selectedWatchlistId),
  })

  const createMutation = useMutation({
    mutationFn: (name: string) => createWatchlist(token!, name),
    onSuccess: async (watchlist) => {
      setNewWatchlistName('')
      await queryClient.invalidateQueries({ queryKey: ['watchlists', token] })
      setSelectedWatchlistId(watchlist.id)
    },
    onError: (error: Error) => setPageError(error.message),
  })

  const addTickerMutation = useMutation({
    mutationFn: (ticker: string) => addWatchlistItem(token!, selectedWatchlistId!, ticker),
    onSuccess: async () => {
      setNewTicker('')
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['watchlist-items', token, selectedWatchlistId] }),
        queryClient.invalidateQueries({ queryKey: ['watchlist-insights', token, selectedWatchlistId] }),
        queryClient.invalidateQueries({ queryKey: ['watchlists', token] }),
      ])
    },
    onError: (error: Error) => setPageError(error.message),
  })

  const deleteMutation = useMutation({
    mutationFn: (watchlistId: number) => deleteWatchlist(token!, watchlistId),
    onSuccess: async (_, watchlistId) => {
      const remaining = watchlistsQuery.data?.items.filter((item) => item.id !== watchlistId) ?? []
      setSelectedWatchlistId(remaining[0]?.id ?? null)
      await queryClient.invalidateQueries({ queryKey: ['watchlists', token] })
    },
    onError: (error: Error) => setPageError(error.message),
  })

  const removeTickerMutation = useMutation({
    mutationFn: (ticker: string) => removeWatchlistItem(token!, selectedWatchlistId!, ticker),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['watchlist-items', token, selectedWatchlistId] }),
        queryClient.invalidateQueries({ queryKey: ['watchlist-insights', token, selectedWatchlistId] }),
        queryClient.invalidateQueries({ queryKey: ['watchlists', token] }),
      ])
    },
    onError: (error: Error) => setPageError(error.message),
  })

  const selectedWatchlist = useMemo(
    () => watchlistsQuery.data?.items.find((item) => item.id === selectedWatchlistId) ?? null,
    [selectedWatchlistId, watchlistsQuery.data],
  )

  const suggestions = useMemo(() => {
    const search = newTicker.trim().toUpperCase()
    const allStocks = stocksUniverseQuery.data?.items ?? []

    if (!search) {
      return allStocks.slice(0, 12)
    }

    return allStocks
      .filter((stock) => {
        const ticker = stock.ticker.toUpperCase()
        const company = (stock.company_name ?? '').toUpperCase()
        return ticker.includes(search) || company.includes(search)
      })
      .slice(0, 12)
  }, [newTicker, stocksUniverseQuery.data])

  if (!user || !token) {
    return (
      <section className="grid page-section" style={{ gap: '1rem' }}>
        <div className="card hero-card smooth-enter">
          <div className="eyebrow">Your personal workspace</div>
          <h1 className="hero-title">Create watchlists and monitor your best ideas.</h1>
          <p className="hero-copy">
            Log in first to save tickers, build custom watchlists, and view insights cards powered by
            your backend analytics endpoint.
          </p>
        </div>
      </section>
    )
  }

  return (
    <section className="grid page-section" style={{ gap: '1rem' }}>
      <div className="card hero-card smooth-enter">
        <div className="eyebrow">Watchlists + insights</div>
        <h1 className="hero-title">Track curated baskets and surface quick signals.</h1>
        <p className="hero-copy">
          Build saved lists of symbols, then inspect movers, volatility, concentration, and 30-day
          activity without leaving the dashboard.
        </p>
      </div>

      {pageError && <div className="card negative">{pageError}</div>}

      <div className="dashboard-grid stagger-columns">
        <div className="card sidebar-card">
          <div className="panel-header">
            <div>
              <h2 className="section-title">Your watchlists</h2>
              <div className="muted">{watchlistsQuery.data?.total ?? 0} saved</div>
            </div>
          </div>

          <div className="grid" style={{ gap: '0.75rem' }}>
            <div className="grid" style={{ gap: '0.55rem' }}>
              <input
                className="input"
                value={newWatchlistName}
                onChange={(event) => setNewWatchlistName(event.target.value)}
                placeholder="Create a new watchlist"
              />
              <button
                className="button"
                type="button"
                disabled={!newWatchlistName.trim() || createMutation.isPending}
                onClick={() => createMutation.mutate(newWatchlistName.trim())}
              >
                {createMutation.isPending ? 'Creating...' : 'Create watchlist'}
              </button>
            </div>

            {watchlistsQuery.isLoading && <div className="empty-state">Loading watchlists...</div>}

            {!watchlistsQuery.isLoading && !watchlistsQuery.data?.items.length && (
              <div className="empty-state">No watchlists yet. Create your first one above.</div>
            )}

            {watchlistsQuery.data?.items.map((watchlist) => (
              <button
                key={watchlist.id}
                className={`list-card ${selectedWatchlistId === watchlist.id ? 'active' : ''}`}
                type="button"
                onClick={() => setSelectedWatchlistId(watchlist.id)}
              >
                <div>
                  <strong>{watchlist.name}</strong>
                  <div className="muted">{watchlist.items_count} tickers</div>
                </div>
                <span className="chip">#{watchlist.id}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="grid stagger-children" style={{ gap: '1rem' }}>
          <div className="card">
            <div className="panel-header">
              <div>
                <h2 className="section-title">{selectedWatchlist?.name ?? 'Select a watchlist'}</h2>
                <div className="muted">
                  {selectedWatchlist ? 'Manage symbols and review analytics.' : 'Pick a watchlist to begin.'}
                </div>
              </div>
              {selectedWatchlist && (
                <button
                  className="button secondary"
                  type="button"
                  onClick={() => deleteMutation.mutate(selectedWatchlist.id)}
                >
                  Delete watchlist
                </button>
              )}
            </div>

            {selectedWatchlist ? (
              <div className="search-row">
                <div className="search-box">
                  <input
                    className="input"
                    value={newTicker}
                    onFocus={() => setShowSuggestions(true)}
                    onBlur={() => setTimeout(() => setShowSuggestions(false), 150)}
                    onChange={(event) => {
                      setNewTicker(event.target.value)
                      setShowSuggestions(true)
                    }}
                    placeholder="Add ticker or company (e.g. AAPL, Microsoft)"
                  />

                  {showSuggestions && suggestions.length > 0 && (
                    <div className="suggestions-card">
                      {suggestions.map((stock) => (
                        <button
                          key={stock.ticker}
                          type="button"
                          className="suggestion-item"
                          onClick={() => {
                            setNewTicker(stock.ticker)
                            setShowSuggestions(false)
                          }}
                        >
                          <div>
                            <strong>{stock.ticker}</strong>
                            <div className="suggestion-subtitle">{stock.company_name ?? stock.ticker}</div>
                          </div>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
                <button
                  className="button"
                  type="button"
                  disabled={!newTicker.trim() || addTickerMutation.isPending}
                  onClick={() => addTickerMutation.mutate(newTicker.trim())}
                >
                  {addTickerMutation.isPending ? 'Adding...' : 'Add ticker'}
                </button>
              </div>
            ) : (
              <div className="empty-state">Create or select a watchlist from the left panel.</div>
            )}
          </div>

          {selectedWatchlist && (
            <>
              <div className="stats-grid">
                <MiniStat label="Top Gainer 1W" value={insightsQuery.data?.top_gainer_1w ?? '—'} />
                <MiniStat label="Top Loser 1W" value={insightsQuery.data?.top_loser_1w ?? '—'} />
                <MiniStat label="Highest Vol" value={insightsQuery.data?.highest_volatility ?? '—'} />
                <MiniStat label="Tickers" value={String(insightsQuery.data?.ticker_count ?? 0)} />
              </div>

              <div className="card table-shell table-wrap">
                <div className="panel-header">
                  <div>
                    <h3 className="section-title">Saved Tickers</h3>
                    <div className="muted">Manage symbols in this watchlist.</div>
                  </div>
                </div>

                {itemsQuery.isLoading ? (
                  <div className="empty-state">Loading watchlist items...</div>
                ) : !itemsQuery.data?.items.length ? (
                  <div className="empty-state">No tickers saved yet.</div>
                ) : (
                  <table>
                    <thead>
                      <tr>
                        <th>Ticker</th>
                        <th>Added</th>
                        <th>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {itemsQuery.data.items.map((item) => (
                        <tr key={item.id}>
                          <td>
                            <Link to={`/stocks/${item.ticker}`} className="link-inline">
                              {item.ticker}
                            </Link>
                            <div className="muted" style={{ fontSize: '0.82rem' }}>
                              {item.company_name ?? item.ticker}
                            </div>
                          </td>
                          <td>{new Date(item.added_at).toLocaleDateString()}</td>
                          <td>
                            <button
                              className="button secondary"
                              type="button"
                              onClick={() => removeTickerMutation.mutate(item.ticker)}
                            >
                              Remove
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>

              <div className="card table-shell table-wrap">
                <div className="panel-header">
                  <div>
                    <h3 className="section-title">Insights Cards</h3>
                    <div className="muted">Real analytics from `/watchlists/{'{id}'}/insights`.</div>
                  </div>
                  {insightsQuery.data?.as_of_date && (
                    <span className="chip">As of {insightsQuery.data.as_of_date}</span>
                  )}
                </div>

                {insightsQuery.isLoading ? (
                  <div className="empty-state">Calculating insights...</div>
                ) : !insightsQuery.data?.tickers.length ? (
                  <div className="empty-state">Add tickers to unlock insights.</div>
                ) : (
                  <table>
                    <thead>
                      <tr>
                        <th>Ticker</th>
                        <th>1W</th>
                        <th>1M</th>
                        <th>1Y</th>
                        <th>Volatility</th>
                        <th>Weight</th>
                      </tr>
                    </thead>
                    <tbody>
                      {insightsQuery.data.tickers.map((ticker) => (
                        <tr key={ticker.ticker}>
                          <td>
                            <Link to={`/stocks/${ticker.ticker}`} className="link-inline">
                              {ticker.ticker}
                            </Link>
                          </td>
                          <td className={pctClass(ticker.change_pct_1w)}>{formatPct(ticker.change_pct_1w)}</td>
                          <td className={pctClass(ticker.change_pct_1m)}>{formatPct(ticker.change_pct_1m)}</td>
                          <td className={pctClass(ticker.change_pct_1y)}>{formatPct(ticker.change_pct_1y)}</td>
                          <td>{formatPct(ticker.volatility_30d)}</td>
                          <td>{ticker.weight_pct.toFixed(1)}%</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </section>
  )
}

function MiniStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="stat-card">
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
    </div>
  )
}

function formatPct(value: number | null) {
  if (value === null) return '—'
  return `${value.toFixed(2)}%`
}

function pctClass(value: number | null) {
  if (value === null) return ''
  return value >= 0 ? 'positive' : 'negative'
}
