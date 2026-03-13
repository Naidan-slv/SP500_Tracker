import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'

import { useAuth } from '../auth/AuthContext'
import { PortfolioPieChart } from '../components/PortfolioPieChart'
import {
  addPortfolioHolding,
  createPortfolio,
  deletePortfolio,
  fetchPortfolioHoldings,
  fetchPortfolios,
  fetchStocksUniverse,
  removePortfolioHolding,
  updatePortfolioHolding,
} from '../lib/api'

export function PortfolioPage() {
  const queryClient = useQueryClient()
  const { token, user } = useAuth()
  const [newPortfolioName, setNewPortfolioName] = useState('')
  const [holdingTicker, setHoldingTicker] = useState('')
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [quantity, setQuantity] = useState('')
  const [avgCost, setAvgCost] = useState('')
  const [selectedPortfolioId, setSelectedPortfolioId] = useState<number | null>(null)
  const [pageError, setPageError] = useState<string | null>(null)
  const [editingHoldingId, setEditingHoldingId] = useState<number | null>(null)
  const [editQuantity, setEditQuantity] = useState('')
  const [editAvgCost, setEditAvgCost] = useState('')

  const portfoliosQuery = useQuery({
    queryKey: ['portfolios', token],
    queryFn: () => fetchPortfolios(token!),
    enabled: Boolean(token),
  })

  useEffect(() => {
    if (!selectedPortfolioId && portfoliosQuery.data?.items.length) {
      setSelectedPortfolioId(portfoliosQuery.data.items[0].id)
    }
  }, [selectedPortfolioId, portfoliosQuery.data])

  const holdingsQuery = useQuery({
    queryKey: ['portfolio-holdings', token, selectedPortfolioId],
    queryFn: () => fetchPortfolioHoldings(token!, selectedPortfolioId!),
    enabled: Boolean(token && selectedPortfolioId),
  })

  const stocksUniverseQuery = useQuery({
    queryKey: ['stocks-universe', 'portfolio-page'],
    queryFn: () => fetchStocksUniverse(),
    staleTime: 1000 * 60 * 10,
    gcTime: 1000 * 60 * 30,
  })

  const createMutation = useMutation({
    mutationFn: (name: string) => createPortfolio(token!, name),
    onSuccess: async (portfolio) => {
      setNewPortfolioName('')
      await queryClient.invalidateQueries({ queryKey: ['portfolios', token] })
      setSelectedPortfolioId(portfolio.id)
    },
    onError: (error: Error) => setPageError(error.message),
  })

  const addHoldingMutation = useMutation({
    mutationFn: () =>
      addPortfolioHolding(token!, selectedPortfolioId!, {
        ticker: holdingTicker.trim(),
        quantity: Number(quantity),
        avg_cost: avgCost ? Number(avgCost) : null,
      }),
    onSuccess: async () => {
      setHoldingTicker('')
      setQuantity('')
      setAvgCost('')
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['portfolio-holdings', token, selectedPortfolioId] }),
        queryClient.invalidateQueries({ queryKey: ['portfolios', token] }),
      ])
    },
    onError: (error: Error) => setPageError(error.message),
  })

  const deleteMutation = useMutation({
    mutationFn: (portfolioId: number) => deletePortfolio(token!, portfolioId),
    onSuccess: async (_, portfolioId) => {
      const remaining = portfoliosQuery.data?.items.filter((item) => item.id !== portfolioId) ?? []
      setSelectedPortfolioId(remaining[0]?.id ?? null)
      await queryClient.invalidateQueries({ queryKey: ['portfolios', token] })
    },
    onError: (error: Error) => setPageError(error.message),
  })

  const removeHoldingMutation = useMutation({
    mutationFn: (ticker: string) => removePortfolioHolding(token!, selectedPortfolioId!, ticker),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['portfolio-holdings', token, selectedPortfolioId] }),
        queryClient.invalidateQueries({ queryKey: ['portfolios', token] }),
      ])
    },
    onError: (error: Error) => setPageError(error.message),
  })

  const updateHoldingMutation = useMutation({
    mutationFn: (payload: { ticker: string; quantity: number; avg_cost: number | null }) =>
      updatePortfolioHolding(token!, selectedPortfolioId!, payload.ticker, {
        quantity: payload.quantity,
        avg_cost: payload.avg_cost,
      }),
    onSuccess: async () => {
      setEditingHoldingId(null)
      setEditQuantity('')
      setEditAvgCost('')
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['portfolio-holdings', token, selectedPortfolioId] }),
        queryClient.invalidateQueries({ queryKey: ['portfolios', token] }),
      ])
    },
    onError: (error: Error) => setPageError(error.message),
  })

  function beginEdit(quantityValue: number, avgCostValue: number | null, holdingId: number) {
    setPageError(null)
    setEditingHoldingId(holdingId)
    setEditQuantity(String(quantityValue))
    setEditAvgCost(avgCostValue == null ? '' : String(avgCostValue))
  }

  function cancelEdit() {
    setEditingHoldingId(null)
    setEditQuantity('')
    setEditAvgCost('')
  }

  function saveHolding(ticker: string) {
    const parsedQuantity = Number(editQuantity)
    const normalizedAvgCost = editAvgCost.trim()
    const parsedAvgCost = normalizedAvgCost ? Number(normalizedAvgCost) : null

    if (!Number.isFinite(parsedQuantity) || parsedQuantity <= 0) {
      setPageError('Quantity must be greater than 0.')
      return
    }
    if (parsedAvgCost !== null && (!Number.isFinite(parsedAvgCost) || parsedAvgCost <= 0)) {
      setPageError('Average cost must be greater than 0, or left empty.')
      return
    }

    setPageError(null)
    updateHoldingMutation.mutate({
      ticker,
      quantity: parsedQuantity,
      avg_cost: parsedAvgCost,
    })
  }

  const selectedPortfolio = useMemo(
    () => portfoliosQuery.data?.items.find((item) => item.id === selectedPortfolioId) ?? null,
    [portfoliosQuery.data, selectedPortfolioId],
  )

  const portfolioStats = useMemo(() => {
    const holdings = holdingsQuery.data?.items ?? []
    const positions = holdings.length
    const totalUnits = holdings.reduce((acc, holding) => acc + holding.quantity, 0)
    const estimatedCost = holdings.reduce(
      (acc, holding) => acc + holding.quantity * (holding.avg_cost ?? 0),
      0,
    )
    return {
      positions,
      totalUnits,
      estimatedCost,
    }
  }, [holdingsQuery.data])

  const suggestions = useMemo(() => {
    const search = holdingTicker.trim().toUpperCase()
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
  }, [holdingTicker, stocksUniverseQuery.data])

  if (!user || !token) {
    return (
      <section className="grid page-section" style={{ gap: '1rem' }}>
        <div className="card hero-card smooth-enter">
          <div className="eyebrow">Portfolio management</div>
          <h1 className="hero-title">Log in to manage holdings and average costs.</h1>
          <p className="hero-copy">
            Your portfolio page lets you create portfolios, track tickers, and store basic holding
            metadata in your backend.
          </p>
        </div>
      </section>
    )
  }

  return (
    <section className="grid page-section" style={{ gap: '1rem' }}>
      <div className="card hero-card smooth-enter">
        <div className="eyebrow">Portfolio workspace</div>
        <h1 className="hero-title">Keep holdings organised across investment themes.</h1>
        <p className="hero-copy">
          Build named portfolios, save quantities and average cost, and navigate straight into stock
          detail pages when you want more context.
        </p>
      </div>

      {pageError && <div className="card negative">{pageError}</div>}

      <div className="dashboard-grid stagger-columns">
        <div className="card sidebar-card">
          <div className="panel-header">
            <div>
              <h2 className="section-title">Portfolios</h2>
              <div className="muted">{portfoliosQuery.data?.total ?? 0} saved</div>
            </div>
          </div>

          <div className="grid" style={{ gap: '0.75rem' }}>
            <div className="grid" style={{ gap: '0.55rem' }}>
              <input
                className="input"
                value={newPortfolioName}
                onChange={(event) => setNewPortfolioName(event.target.value)}
                placeholder="Create a new portfolio"
              />
              <button
                className="button"
                type="button"
                disabled={!newPortfolioName.trim() || createMutation.isPending}
                onClick={() => createMutation.mutate(newPortfolioName.trim())}
              >
                {createMutation.isPending ? 'Creating...' : 'Create portfolio'}
              </button>
            </div>

            {portfoliosQuery.isLoading && <div className="empty-state">Loading portfolios...</div>}

            {!portfoliosQuery.isLoading && !portfoliosQuery.data?.items.length && (
              <div className="empty-state">No portfolios yet. Create one to begin tracking.</div>
            )}

            {portfoliosQuery.data?.items.map((portfolio) => (
              <button
                key={portfolio.id}
                className={`list-card ${selectedPortfolioId === portfolio.id ? 'active' : ''}`}
                type="button"
                onClick={() => setSelectedPortfolioId(portfolio.id)}
              >
                <div>
                  <strong>{portfolio.name}</strong>
                  <div className="muted">{portfolio.holdings_count} holdings</div>
                </div>
                <span className="chip">#{portfolio.id}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="grid stagger-children" style={{ gap: '1rem' }}>
          <div className="card">
            <div className="panel-header">
              <div>
                <h2 className="section-title">{selectedPortfolio?.name ?? 'Select a portfolio'}</h2>
                <div className="muted">
                  {selectedPortfolio ? 'Add holdings and inspect position mix.' : 'Choose a portfolio from the left.'}
                </div>
              </div>
              {selectedPortfolio && (
                <button
                  className="button secondary"
                  type="button"
                  onClick={() => deleteMutation.mutate(selectedPortfolio.id)}
                >
                  Delete portfolio
                </button>
              )}
            </div>

            {selectedPortfolio ? (
              <div className="grid grid-2">
                <div className="search-box">
                  <input
                    className="input"
                    value={holdingTicker}
                    onFocus={() => setShowSuggestions(true)}
                    onBlur={() => setTimeout(() => setShowSuggestions(false), 150)}
                    onChange={(event) => {
                      setHoldingTicker(event.target.value)
                      setShowSuggestions(true)
                    }}
                    placeholder="Ticker or company"
                  />

                  {showSuggestions && suggestions.length > 0 && (
                    <div className="suggestions-card">
                      {suggestions.map((stock) => (
                        <button
                          key={stock.ticker}
                          type="button"
                          className="suggestion-item"
                          onClick={() => {
                            setHoldingTicker(stock.ticker)
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
                <input
                  className="input"
                  value={quantity}
                  onChange={(event) => setQuantity(event.target.value)}
                  placeholder="Quantity"
                  type="number"
                  min="0"
                  step="0.0001"
                />
                <input
                  className="input"
                  value={avgCost}
                  onChange={(event) => setAvgCost(event.target.value)}
                  placeholder="Average cost (optional)"
                  type="number"
                  min="0"
                  step="0.0001"
                />
                <button
                  className="button"
                  type="button"
                  disabled={!holdingTicker.trim() || !quantity || addHoldingMutation.isPending}
                  onClick={() => addHoldingMutation.mutate()}
                >
                  {addHoldingMutation.isPending ? 'Adding...' : 'Add holding'}
                </button>
              </div>
            ) : (
              <div className="empty-state">Create or select a portfolio to manage holdings.</div>
            )}
          </div>

          {selectedPortfolio && (
            <>
              <div className="stats-grid">
                <MiniStat label="Positions" value={String(portfolioStats.positions)} />
                <MiniStat label="Total Units" value={portfolioStats.totalUnits.toFixed(2)} />
                <MiniStat label="Estimated Cost" value={`$${portfolioStats.estimatedCost.toFixed(2)}`} />
                <MiniStat label="Selected" value={selectedPortfolio.name} />
              </div>

              <div className="card">
                <div className="panel-header">
                  <div>
                    <h3 className="section-title">Allocation</h3>
                    <div className="muted">
                      {holdingsQuery.data?.items.length
                        ? 'Portfolio weight by estimated cost. Hover segments for detail.'
                        : 'Add holdings to view your portfolio allocation.'}
                    </div>
                  </div>
                </div>
                <PortfolioPieChart holdings={holdingsQuery.data?.items ?? []} totalValue={portfolioStats.estimatedCost} />
              </div>

              <div className="card table-shell table-wrap">
                <div className="panel-header">
                  <div>
                    <h3 className="section-title">Holdings</h3>
                    <div className="muted">Saved quantity and average cost per ticker.</div>
                  </div>
                </div>

                {holdingsQuery.isLoading ? (
                  <div className="empty-state">Loading holdings...</div>
                ) : !holdingsQuery.data?.items.length ? (
                  <div className="empty-state">No holdings yet.</div>
                ) : (
                  <table>
                    <thead>
                      <tr>
                        <th>Ticker</th>
                        <th>Quantity</th>
                        <th>Avg Cost</th>
                        <th>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {holdingsQuery.data.items.map((holding) => (
                        <tr key={holding.id}>
                          <td>
                            <Link to={`/stocks/${holding.ticker}`} className="link-inline">
                              {holding.ticker}
                            </Link>
                            <div className="muted" style={{ fontSize: '0.82rem' }}>
                              {holding.company_name ?? holding.ticker}
                            </div>
                          </td>
                          <td>
                            {editingHoldingId === holding.id ? (
                              <input
                                className="input"
                                value={editQuantity}
                                onChange={(event) => setEditQuantity(event.target.value)}
                                placeholder="Quantity"
                                type="number"
                                min="0"
                                step="0.0001"
                              />
                            ) : (
                              holding.quantity.toFixed(4)
                            )}
                          </td>
                          <td>
                            {editingHoldingId === holding.id ? (
                              <input
                                className="input"
                                value={editAvgCost}
                                onChange={(event) => setEditAvgCost(event.target.value)}
                                placeholder="Avg cost"
                                type="number"
                                min="0"
                                step="0.0001"
                              />
                            ) : holding.avg_cost ? (
                              `$${holding.avg_cost.toFixed(2)}`
                            ) : (
                              '—'
                            )}
                          </td>
                          <td>
                            {editingHoldingId === holding.id ? (
                              <div style={{ display: 'flex', gap: '0.5rem' }}>
                                <button
                                  className="button"
                                  type="button"
                                  onClick={() => saveHolding(holding.ticker)}
                                  disabled={updateHoldingMutation.isPending}
                                >
                                  {updateHoldingMutation.isPending ? 'Saving...' : 'Save'}
                                </button>
                                <button className="button secondary" type="button" onClick={cancelEdit}>
                                  Cancel
                                </button>
                              </div>
                            ) : (
                              <div style={{ display: 'flex', gap: '0.5rem' }}>
                                <button
                                  className="button secondary"
                                  type="button"
                                  onClick={() => beginEdit(holding.quantity, holding.avg_cost, holding.id)}
                                >
                                  Edit
                                </button>
                                <button
                                  className="button secondary"
                                  type="button"
                                  onClick={() => removeHoldingMutation.mutate(holding.ticker)}
                                >
                                  Remove
                                </button>
                              </div>
                            )}
                          </td>
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
