import { Suspense, lazy, useEffect, useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'

import { fetchStockDetail, fetchStockHistory, fetchStockLive, fetchStockNews } from '../lib/api'

const StockHistoryChart = lazy(() =>
  import('../components/StockHistoryChart').then((module) => ({
    default: module.StockHistoryChart,
  })),
)

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
  const [newsTimeframe, setNewsTimeframe] = useState<'1w' | '1m' | '3m' | '6m' | '1y' | '5y' | 'max'>('1w')
  const [liveRange, setLiveRange] = useState<'1d' | '5d' | '1mo'>('1d')
  const [liveInterval, setLiveInterval] = useState<'1m' | '2m' | '5m' | '15m' | '30m' | '60m'>('5m')

  const liveIntervalOptions = useMemo(() => {
    if (liveRange === '1d') return ['1m', '2m', '5m', '15m', '30m', '60m'] as const
    if (liveRange === '5d') return ['5m', '15m', '30m', '60m'] as const
    return ['15m', '30m', '60m'] as const
  }, [liveRange])

  useEffect(() => {
    const isAllowed = liveIntervalOptions.some((intervalOption) => intervalOption === liveInterval)
    if (!isAllowed) {
      setLiveInterval(liveIntervalOptions[0])
    }
  }, [liveInterval, liveIntervalOptions])

  const detailQuery = useQuery({
    queryKey: ['stock-detail', ticker],
    queryFn: () => fetchStockDetail(ticker),
    enabled: Boolean(ticker),
  })

  const historyQuery = useQuery({
    queryKey: ['stock-history', ticker, timeframe],
    queryFn: () => fetchStockHistory(ticker, timeframe),
    enabled: Boolean(ticker),
    placeholderData: (previous) => previous,
  })

  const newsQuery = useQuery({
    queryKey: ['stock-news', ticker, newsTimeframe],
    queryFn: () => fetchStockNews(ticker, newsTimeframe, 10),
    enabled: Boolean(ticker),
    placeholderData: (previous) => previous,
  })

  const liveQuery = useQuery({
    queryKey: ['stock-live', ticker, liveRange, liveInterval],
    queryFn: () => fetchStockLive(ticker, liveRange, liveInterval),
    enabled: Boolean(ticker),
    placeholderData: (previous) => previous,
    refetchInterval: 60_000,
  })

  const detail = detailQuery.data ?? null
  const history = historyQuery.data?.items ?? []
  const newsItems = newsQuery.data?.items ?? []
  const liveItems = liveQuery.data?.items ?? []
  const initialLoading = detailQuery.isPending || (historyQuery.isPending && !historyQuery.data)
  const updatingChart = historyQuery.isFetching && !historyQuery.isPending
  const updatingNews = newsQuery.isFetching && !newsQuery.isPending
  const updatingLive = liveQuery.isFetching && !liveQuery.isPending
  const error =
    (detailQuery.error as Error | null)?.message ??
    (historyQuery.error as Error | null)?.message ??
    null

  const chartData = useMemo(
    () => history.map((point) => ({ date: point.date.slice(2), close: point.close })),
    [history],
  )

  const liveChartData = useMemo(() => {
    return liveItems
      .filter((point) => point.close !== null)
      .map((point) => {
        const parsed = new Date(point.timestamp)
        const label =
          liveRange === '1d'
            ? parsed.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            : `${parsed.getMonth() + 1}/${parsed.getDate()} ${parsed
                .toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`
        return {
          date: label,
          close: point.close as number,
        }
      })
  }, [liveItems, liveRange])

  return (
    <section className="grid" style={{ gap: '1rem' }}>
      <div>
        <Link to="/" className="back-link">
          ← Back to discover
        </Link>
      </div>

      {initialLoading && <div className="empty-state">Loading stock detail...</div>}
      {error && <div className="card negative">{error}</div>}

      {!initialLoading && !error && detail && (
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
              <div style={{ display: 'flex', gap: '0.6rem', alignItems: 'center' }}>
                {updatingChart && <span className="chip">Updating chart...</span>}
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
            </div>

            <div className="chart-shell" style={{ width: '100%', height: 360 }}>
              <Suspense fallback={<div className="empty-state">Loading chart...</div>}>
                <StockHistoryChart data={chartData} />
              </Suspense>
            </div>
          </div>

          <div className="card">
            <div className="panel-header">
              <div>
                <h3 className="section-title">Live Market Activity</h3>
                <div className="muted">Intraday chart auto-refreshes every 60 seconds.</div>
              </div>
              <div style={{ display: 'flex', gap: '0.55rem', alignItems: 'center', flexWrap: 'wrap' }}>
                {updatingLive && <span className="chip">Refreshing...</span>}
                <select
                  className="select"
                  value={liveRange}
                  onChange={(event) => setLiveRange(event.target.value as typeof liveRange)}
                  style={{ maxWidth: '110px' }}
                >
                  <option value="1d">1D</option>
                  <option value="5d">5D</option>
                  <option value="1mo">1MO</option>
                </select>
                <select
                  className="select"
                  value={liveInterval}
                  onChange={(event) => setLiveInterval(event.target.value as typeof liveInterval)}
                  style={{ maxWidth: '110px' }}
                >
                  {liveIntervalOptions.map((intervalOption) => (
                    <option key={intervalOption} value={intervalOption}>
                      {intervalOption}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="hero-meta" style={{ marginTop: 0, marginBottom: '0.85rem' }}>
              <span className="chip">Points: {liveQuery.data?.total ?? 0}</span>
              <span className="chip">Latest: ${formatNumber(liveQuery.data?.latest_close ?? null)}</span>
              {liveQuery.data?.latest_timestamp && (
                <span className="chip">
                  Updated: {new Date(liveQuery.data.latest_timestamp).toLocaleString()}
                </span>
              )}
            </div>

            {liveQuery.isPending ? (
              <div className="empty-state">Loading live chart...</div>
            ) : liveQuery.error ? (
              <div className="empty-state negative">{(liveQuery.error as Error).message}</div>
            ) : !liveChartData.length ? (
              <div className="empty-state">No live points returned for this range/interval.</div>
            ) : (
              <div className="chart-shell" style={{ width: '100%', height: 320 }}>
                <Suspense fallback={<div className="empty-state">Loading chart...</div>}>
                  <StockHistoryChart data={liveChartData} />
                </Suspense>
              </div>
            )}

            {liveQuery.data?.provider_error && (
              <div className="muted" style={{ marginTop: '0.8rem' }}>
                Provider note: {liveQuery.data.provider_error}
              </div>
            )}
          </div>

          <div className="card">
            <div className="panel-header">
              <div>
                <h3 className="section-title">Latest News</h3>
                <div className="muted">Headline stream filtered by selected timeframe.</div>
              </div>
              <div style={{ display: 'flex', gap: '0.6rem', alignItems: 'center' }}>
                {updatingNews && <span className="chip">Updating news...</span>}
                <select
                  className="select"
                  value={newsTimeframe}
                  onChange={(event) => setNewsTimeframe(event.target.value as typeof newsTimeframe)}
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
            </div>

            {newsQuery.isPending ? (
              <div className="empty-state">Loading news...</div>
            ) : newsQuery.error ? (
              <div className="empty-state negative">{(newsQuery.error as Error).message}</div>
            ) : !newsItems.length ? (
              <div className="empty-state">No news found for the selected timeframe.</div>
            ) : (
              <div className="news-list">
                {newsItems.map((item) => (
                  <a
                    key={`${item.url}-${item.published_at ?? 'na'}`}
                    href={item.url}
                    target="_blank"
                    rel="noreferrer"
                    className="news-item"
                  >
                    <div style={{ fontWeight: 700 }}>{item.title}</div>
                    <div className="muted" style={{ fontSize: '0.9rem' }}>
                      {item.source ?? 'Unknown source'}
                      {item.published_at
                        ? ` · ${new Date(item.published_at).toLocaleString()}`
                        : ''}
                    </div>
                  </a>
                ))}
              </div>
            )}

            {newsQuery.data?.provider_error && (
              <div className="muted" style={{ marginTop: '0.8rem' }}>
                Provider note: {newsQuery.data.provider_error}
              </div>
            )}
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
