import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
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

  const detailQuery = useQuery({
    queryKey: ['stock-detail', ticker],
    queryFn: () => fetchStockDetail(ticker),
    enabled: Boolean(ticker),
  })

  const historyQuery = useQuery({
    queryKey: ['stock-history', ticker, timeframe],
    queryFn: () => fetchStockHistory(ticker, timeframe),
    enabled: Boolean(ticker),
  })

  const detail = detailQuery.data ?? null
  const history = historyQuery.data?.items ?? []
  const loading = detailQuery.isLoading || historyQuery.isLoading
  const error =
    (detailQuery.error as Error | null)?.message ??
    (historyQuery.error as Error | null)?.message ??
    null

  const chartData = useMemo(
    () => history.map((point) => ({ date: point.date.slice(2), close: point.close })),
    [history],
  )

  return (
    <section className="grid" style={{ gap: '1rem' }}>
      <div>
        <Link to="/" className="back-link">
          ← Back to discover
        </Link>
      </div>

      {loading && <div className="empty-state">Loading stock detail...</div>}
      {error && <div className="card negative">{error}</div>}

      {!loading && !error && detail && (
        <>
          <div className="card hero-card">
            <div className="eyebrow">Ticker deep dive</div>
            <h1 className="hero-title" style={{ fontSize: 'clamp(1.8rem, 3vw, 2.7rem)' }}>
              {detail.ticker} {detail.company_name ? `— ${detail.company_name}` : ''}
            </h1>
            <div className="hero-meta">
              <span className="chip">As of: {detail.latest_date ?? '—'}</span>
              <span className="chip">Latest close: ${formatNumber(detail.latest_close)}</span>
              <span className="chip">Avg 30d volume: {formatNumber(detail.avg_volume_30d, 0)}</span>
            </div>

            <div className="stats-grid" style={{ marginTop: '1.1rem' }}>
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
            <div className="panel-header">
              <div>
                <h3 className="section-title">Price History</h3>
                <div className="muted">Switch timeframes to explore momentum.</div>
              </div>
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

            <div className="chart-shell" style={{ width: '100%', height: 360 }}>
              <ResponsiveContainer>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(191, 205, 224, 0.12)" />
                  <XAxis dataKey="date" tick={{ fill: '#BFCDE0', fontSize: 12 }} />
                  <YAxis tick={{ fill: '#BFCDE0', fontSize: 12 }} domain={['auto', 'auto']} />
                  <Tooltip
                    contentStyle={{
                      background: '#3B3355',
                      border: '1px solid rgba(191, 205, 224, 0.18)',
                      color: '#FEFCFD',
                      borderRadius: 12,
                    }}
                  />
                  <Line type="monotone" dataKey="close" stroke="#BFCDE0" dot={false} strokeWidth={3} />
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
    <div className="stat-card">
      <div className="stat-label">{label}</div>
      <div className={`stat-value ${className ?? ''}`}>
        {value}
        {suffix}
      </div>
    </div>
  )
}
