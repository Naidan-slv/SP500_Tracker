import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { fetchStockDetail, fetchStockHistory } from '../lib/api'
import type { StockDetailResponse, StockHistoryPoint } from '../lib/types'

function formatNumber(value: number | null, digits = 2): string {
  if (value === null) return '—'
  return value.toLocaleString(undefined, {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })
}

function pctClass(value: number | null): string {
  if (value === null) return ''
  return value >= 0 ? 'positive' : 'negative'
}

export function StockDetailPage() {
  const { ticker = '' } = useParams<{ ticker: string }>()

  const [timeframe, setTimeframe] = useState<'1w' | '1m' | '3m' | '6m' | '1y' | '5y' | 'max'>('6m')
  const [detail, setDetail] = useState<StockDetailResponse | null>(null)
  const [history, setHistory] = useState<StockHistoryPoint[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let isCancelled = false

    async function load() {
      setLoading(true)
      setError(null)
      try {
        const [detailResult, historyResult] = await Promise.all([
          fetchStockDetail(ticker),
          fetchStockHistory(ticker, timeframe),
        ])

        if (!isCancelled) {
          setDetail(detailResult)
          setHistory(historyResult.items)
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

    if (ticker) {
      void load()
    }

    return () => {
      isCancelled = true
    }
  }, [ticker, timeframe])

  const chartData = useMemo(
    () => history.map((point) => ({ date: point.date.slice(2), close: point.close })),
    [history],
  )

  return (
    <section className="grid" style={{ gap: '1rem' }}>
      <div>
        <Link to="/" className="muted">
          ← Back to discover
        </Link>
      </div>

      {loading && <div className="card">Loading stock detail...</div>}
      {error && <div className="card negative">{error}</div>}

      {!loading && !error && detail && (
        <>
          <div className="card">
            <h2 style={{ marginTop: 0 }}>
              {detail.ticker} {detail.company_name ? `— ${detail.company_name}` : ''}
            </h2>
            <div className="muted">As of: {detail.latest_date ?? '—'}</div>

            <div className="grid grid-4" style={{ marginTop: '1rem' }}>
              <Stat label="Latest Close" value={`$${formatNumber(detail.latest_close)}`} />
              <Stat label="52W High" value={`$${formatNumber(detail.week_52_high)}`} />
              <Stat label="52W Low" value={`$${formatNumber(detail.week_52_low)}`} />
              <Stat label="Avg Vol (30d)" value={formatNumber(detail.avg_volume_30d, 0)} />
              <Stat label="1D Change" value={formatNumber(detail.change_pct_1d)} suffix="%" className={pctClass(detail.change_pct_1d)} />
              <Stat label="1W Change" value={formatNumber(detail.change_pct_1w)} suffix="%" className={pctClass(detail.change_pct_1w)} />
              <Stat label="1M Change" value={formatNumber(detail.change_pct_1m)} suffix="%" className={pctClass(detail.change_pct_1m)} />
              <Stat label="1Y Change" value={formatNumber(detail.change_pct_1y)} suffix="%" className={pctClass(detail.change_pct_1y)} />
            </div>
          </div>

          <div className="card">
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '0.8rem',
              }}
            >
              <h3 style={{ margin: 0 }}>Price History</h3>
              <select
                className="select"
                value={timeframe}
                onChange={(event) => setTimeframe(event.target.value as typeof timeframe)}
                style={{ maxWidth: '130px' }}
              >
                <option value="1w">1W</option>
                <option value="1m">1M</option>
                <option value="3m">3M</option>
                <option value="6m">6M</option>
                <option value="1y">1Y</option>
                <option value="5y">5Y</option>
                <option value="max">MAX</option>
              </select>
            </div>

            <div style={{ width: '100%', height: 360 }}>
              <ResponsiveContainer>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                  <XAxis dataKey="date" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                  <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} domain={['auto', 'auto']} />
                  <Tooltip
                    contentStyle={{
                      background: '#0f172a',
                      border: '1px solid #334155',
                      borderRadius: 8,
                    }}
                  />
                  <Line type="monotone" dataKey="close" stroke="#3b82f6" dot={false} strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      )}
    </section>
  )
}

function Stat({
  label,
  value,
  suffix,
  className,
}: {
  label: string
  value: string
  suffix?: string
  className?: string
}) {
  return (
    <div className="card" style={{ padding: '0.7rem' }}>
      <div className="muted" style={{ fontSize: '0.84rem' }}>
        {label}
      </div>
      <div className={className} style={{ fontSize: '1.05rem', fontWeight: 700 }}>
        {value}
        {suffix}
      </div>
    </div>
  )
}
