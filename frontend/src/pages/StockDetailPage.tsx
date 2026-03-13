import { Suspense, lazy, useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'

import { useAuth } from '../auth/AuthContext'
import {
  addPortfolioHolding,
  addWatchlistItem,
  fetchPortfolios,
  fetchStockDetail,
  fetchStockHistory,
  fetchStockLive,
  fetchStockNews,
  fetchWatchlists,
} from '../lib/api'

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
  const queryClient = useQueryClient()
  const { token, user } = useAuth()

  const [activePanel, setActivePanel] = useState<'overview' | 'live' | 'news'>('overview')
  const [timeframe, setTimeframe] = useState<'1w' | '1m' | '3m' | '6m' | '1y' | '5y' | 'max'>('6m')
  const [newsTimeframe, setNewsTimeframe] = useState<'1w' | '1m' | '3m' | '6m' | '1y' | '5y' | 'max'>('1w')
  const [liveRange, setLiveRange] = useState<'1d' | '5d' | '1mo'>('1d')
  const [liveInterval, setLiveInterval] = useState<'1m' | '2m' | '5m' | '15m' | '30m' | '60m'>('5m')
  const [selectedWatchlistId, setSelectedWatchlistId] = useState<number | ''>('')
  const [selectedPortfolioId, setSelectedPortfolioId] = useState<number | ''>('')
  const [quickActionMessage, setQuickActionMessage] = useState<string | null>(null)

  const liveIntervalOptions = useMemo(() => {
    if (liveRange === '1d') return ['1m', '2m', '5m', '15m', '30m', '60m'] as const
    if (liveRange === '5d') return ['5m', '15m', '30m', '60m'] as const
    return ['15m', '30m', '60m'] as const
  }, [liveRange])

  const watchlistsQuery = useQuery({
    queryKey: ['watchlists-stock-detail', token],
    queryFn: () => fetchWatchlists(token!),
    enabled: Boolean(token),
  })

  const portfoliosQuery = useQuery({
    queryKey: ['portfolios-stock-detail', token],
    queryFn: () => fetchPortfolios(token!),
    enabled: Boolean(token),
  })

  useEffect(() => {
    if (!selectedWatchlistId && watchlistsQuery.data?.items.length) {
      setSelectedWatchlistId(watchlistsQuery.data.items[0].id)
    }
  }, [selectedWatchlistId, watchlistsQuery.data])

  useEffect(() => {
    if (!selectedPortfolioId && portfoliosQuery.data?.items.length) {
      setSelectedPortfolioId(portfoliosQuery.data.items[0].id)
    }
  }, [selectedPortfolioId, portfoliosQuery.data])

  const addToWatchlistMutation = useMutation({
    mutationFn: () => addWatchlistItem(token!, Number(selectedWatchlistId), ticker),
    onSuccess: async () => {
      setQuickActionMessage('Added to watchlist.')
      await queryClient.invalidateQueries({ queryKey: ['watchlist-items'] })
    },
    onError: (error: Error) => setQuickActionMessage(error.message),
  })

  const addToPortfolioMutation = useMutation({
    mutationFn: () =>
      addPortfolioHolding(token!, Number(selectedPortfolioId), {
        ticker,
        quantity: 1,
      }),
    onSuccess: async () => {
      setQuickActionMessage('Added to portfolio (qty 1).')
      await queryClient.invalidateQueries({ queryKey: ['portfolio-holdings'] })
    },
    onError: (error: Error) => setQuickActionMessage(error.message),
  })

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
    enabled: Boolean(ticker) && activePanel === 'news',
    placeholderData: (previous) => previous,
  })

  const liveQuery = useQuery({
    queryKey: ['stock-live', ticker, liveRange, liveInterval],
    queryFn: () => fetchStockLive(ticker, liveRange, liveInterval),
    enabled: Boolean(ticker) && activePanel === 'live',
    placeholderData: (previous) => previous,
    refetchInterval: activePanel === 'live' ? 60_000 : false,
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
    <section className="grid page-section" style={{ gap: '1rem' }}>
      <div>
        <Link to="/discover" className="back-link">
          ← Back to discover
        </Link>
      </div>

      {initialLoading && <div className="empty-state">Loading stock detail...</div>}
      {error && <div className="card negative">{error}</div>}

      {!initialLoading && !error && detail && (
        <>
          <div className="card hero-card smooth-enter">
            <div className="eyebrow">📌 Investment Snapshot</div>
            <div className="detail-hero">
              {detail.logo_url ? (
                <img
                  src={detail.logo_url}
                  alt={detail.ticker}
                  className="detail-logo"
                  onError={(e) => {
                    (e.target as HTMLImageElement).style.display = 'none'
                  }}
                />
              ) : (
                <div className="detail-logo-placeholder">{detail.ticker.slice(0, 3)}</div>
              )}

              <div className="detail-hero-text">
                <h1 className="hero-title" style={{ fontSize: 'clamp(1.8rem, 3vw, 2.7rem)', margin: 0 }}>
                  {detail.ticker}
                </h1>
                <p className="detail-company">{detail.company_name ?? 'Company name unavailable'}</p>

                <div className="detail-price-row">
                  <div className="detail-price">${formatNumber(detail.latest_close)}</div>
                  <span className={`change-pill ${detail.change_pct_1d === null ? 'neutral' : detail.change_pct_1d >= 0 ? 'positive' : 'negative'}`}>
                    {detail.change_pct_1d === null ? 'No daily move data' : `${detail.change_pct_1d >= 0 ? '+' : ''}${formatNumber(detail.change_pct_1d)}% today`}
                  </span>
                </div>
              </div>
            </div>
            <div className="hero-meta">
              <span className="chip">As of: {detail.latest_date ?? '—'}</span>
              <span className="chip">Latest close: ${formatNumber(detail.latest_close)}</span>
              <span className="chip">Avg 30d volume: {formatNumber(detail.avg_volume_30d, 0)}</span>
              <span className="chip">52W range: ${formatNumber(detail.week_52_low)} → ${formatNumber(detail.week_52_high)}</span>
            </div>

            {user && token && (
              <div className="grid" style={{ gap: '0.75rem', marginTop: '0.9rem' }}>
                <div className="search-row" style={{ alignItems: 'center' }}>
                  <select
                    className="select"
                    value={selectedWatchlistId}
                    onChange={(event) => setSelectedWatchlistId(Number(event.target.value))}
                    disabled={!watchlistsQuery.data?.items.length}
                    style={{ minWidth: '220px' }}
                  >
                    {!watchlistsQuery.data?.items.length ? (
                      <option value="">No watchlists</option>
                    ) : (
                      watchlistsQuery.data.items.map((watchlist) => (
                        <option key={watchlist.id} value={watchlist.id}>
                          {watchlist.name}
                        </option>
                      ))
                    )}
                  </select>
                  <button
                    className="button secondary"
                    type="button"
                    disabled={!selectedWatchlistId || addToWatchlistMutation.isPending}
                    onClick={() => addToWatchlistMutation.mutate()}
                  >
                    {addToWatchlistMutation.isPending ? 'Adding...' : 'Add to watchlist'}
                  </button>
                </div>

                <div className="search-row" style={{ alignItems: 'center' }}>
                  <select
                    className="select"
                    value={selectedPortfolioId}
                    onChange={(event) => setSelectedPortfolioId(Number(event.target.value))}
                    disabled={!portfoliosQuery.data?.items.length}
                    style={{ minWidth: '220px' }}
                  >
                    {!portfoliosQuery.data?.items.length ? (
                      <option value="">No portfolios</option>
                    ) : (
                      portfoliosQuery.data.items.map((portfolio) => (
                        <option key={portfolio.id} value={portfolio.id}>
                          {portfolio.name}
                        </option>
                      ))
                    )}
                  </select>
                  <button
                    className="button secondary"
                    type="button"
                    disabled={!selectedPortfolioId || addToPortfolioMutation.isPending}
                    onClick={() => addToPortfolioMutation.mutate()}
                  >
                    {addToPortfolioMutation.isPending ? 'Adding...' : 'Add to portfolio'}
                  </button>
                </div>

                {quickActionMessage && (
                  <div className={quickActionMessage.includes('Added') ? 'muted' : 'negative'}>
                    {quickActionMessage}
                  </div>
                )}
              </div>
            )}

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

            <div className="section-tabs" style={{ marginTop: '1rem' }}>
              <button
                type="button"
                className={`section-tab ${activePanel === 'overview' ? 'active' : ''}`}
                onClick={() => setActivePanel('overview')}
              >
                Overview
              </button>
              <button
                type="button"
                className={`section-tab ${activePanel === 'live' ? 'active' : ''}`}
                onClick={() => setActivePanel('live')}
              >
                Live Market
              </button>
              <button
                type="button"
                className={`section-tab ${activePanel === 'news' ? 'active' : ''}`}
                onClick={() => setActivePanel('news')}
              >
                News
              </button>
            </div>
          </div>

          {activePanel === 'overview' && <div className="card smooth-enter">
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
          </div>}

          {activePanel === 'live' && <div className="card smooth-enter">
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
              {liveQuery.data?.provider && (
                <span className="chip">
                  Source: {liveQuery.data.provider === 'database_history' ? '📊 Stored History' : liveQuery.data.provider.replace('_', ' ')}
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
          </div>}

          {activePanel === 'news' && <div className="card smooth-enter">
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
          </div>}
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
