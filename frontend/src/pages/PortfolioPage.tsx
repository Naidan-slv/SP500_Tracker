import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'

import { useAuth } from '../auth/AuthContext'
import {
  addPortfolioHolding,
  createPortfolio,
  deletePortfolio,
  fetchPortfolioHoldings,
  fetchPortfolios,
  removePortfolioHolding,
} from '../lib/api'

export function PortfolioPage() {
  const queryClient = useQueryClient()
  const { token, user } = useAuth()
  const [newPortfolioName, setNewPortfolioName] = useState('')
  const [holdingTicker, setHoldingTicker] = useState('')
  const [quantity, setQuantity] = useState('')
  const [avgCost, setAvgCost] = useState('')
  const [selectedPortfolioId, setSelectedPortfolioId] = useState<number | null>(null)
  const [pageError, setPageError] = useState<string | null>(null)

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
                <input
                  className="input"
                  value={holdingTicker}
                  onChange={(event) => setHoldingTicker(event.target.value)}
                  placeholder="Ticker or company"
                />
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
                          </td>
                          <td>{holding.quantity.toFixed(4)}</td>
                          <td>{holding.avg_cost ? `$${holding.avg_cost.toFixed(2)}` : '—'}</td>
                          <td>
                            <button
                              className="button secondary"
                              type="button"
                              onClick={() => removeHoldingMutation.mutate(holding.ticker)}
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
