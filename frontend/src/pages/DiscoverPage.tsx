import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { fetchStocks, getApiBaseUrl } from '../lib/api'
import type { StockListResponse } from '../lib/types'

const PAGE_SIZE = 25

export function DiscoverPage() {
  const apiBaseUrl = getApiBaseUrl()
  const [searchInput, setSearchInput] = useState('')
  const [search, setSearch] = useState('')
  const [offset, setOffset] = useState(0)
  const [data, setData] = useState<StockListResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let isCancelled = false

    async function load() {
      setLoading(true)
      setError(null)
      try {
        const result = await fetchStocks(search, PAGE_SIZE, offset)
        if (!isCancelled) {
          setData(result)
        }
      } catch (err) {
        if (!isCancelled) {
          setError(err instanceof Error ? err.message : 'Unknown error')
        }
      } finally {
        if (!isCancelled) {
          setLoading(false)
        }
      }
    }

    void load()
    return () => {
      isCancelled = true
    }
  }, [search, offset])

  const currentPage = useMemo(() => Math.floor(offset / PAGE_SIZE) + 1, [offset])

  return (
    <section className="grid" style={{ gap: '1rem' }}>
      <div className="card">
        <h2 style={{ marginTop: 0 }}>Discover Stocks</h2>
        <p className="muted" style={{ marginTop: '-0.2rem' }}>
          Search across tickers and open any stock detail page.
        </p>
        <p className="muted" style={{ marginTop: '-0.4rem', fontSize: '0.86rem' }}>
          API: {apiBaseUrl}
        </p>

        <div style={{ display: 'flex', gap: '0.6rem', flexWrap: 'wrap' }}>
          <input
            className="input"
            placeholder="Search ticker/company (e.g. AAPL, Microsoft)"
            value={searchInput}
            onChange={(event) => setSearchInput(event.target.value)}
            style={{ maxWidth: '430px' }}
          />
          <button
            className="button"
            type="button"
            onClick={() => {
              setOffset(0)
              setSearch(searchInput)
            }}
          >
            Search
          </button>
          <button
            className="button secondary"
            type="button"
            onClick={() => {
              setSearchInput('')
              setSearch('')
              setOffset(0)
            }}
          >
            Reset
          </button>
        </div>
      </div>

      <div className="card table-wrap">
        {loading && <p>Loading stocks...</p>}
        {error && (
          <div className="card" style={{ borderColor: '#7f1d1d', marginBottom: '0.8rem' }}>
            <strong className="negative">Could not load stocks</strong>
            <p className="negative" style={{ marginBottom: 0 }}>{error}</p>
          </div>
        )}

        {!loading && !error && data && (
          <>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '0.6rem',
              }}
            >
              <strong>{data.total} total stocks</strong>
              <span className="muted">Page {currentPage}</span>
            </div>

            <table>
              <thead>
                <tr>
                  <th>Ticker</th>
                  <th>Company</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((stock) => (
                  <tr key={stock.ticker}>
                    <td>
                      <strong>{stock.ticker}</strong>
                    </td>
                    <td>{stock.company_name ?? '—'}</td>
                    <td>
                      <Link to={`/stocks/${stock.ticker}`} className="button secondary">
                        Open
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            <div style={{ display: 'flex', gap: '0.6rem', marginTop: '0.9rem' }}>
              <button
                className="button secondary"
                type="button"
                onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
                disabled={offset === 0}
              >
                Previous
              </button>
              <button
                className="button"
                type="button"
                onClick={() => setOffset(offset + PAGE_SIZE)}
                disabled={offset + PAGE_SIZE >= data.total}
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
