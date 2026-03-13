export type StockListItem = {
  ticker: string
  company_name: string | null
  logo_url: string | null
}

export type StockListResponse = {
  total: number
  limit: number
  offset: number
  items: StockListItem[]
}

export type StockDetailResponse = {
  ticker: string
  company_name: string | null
  logo_url: string | null
  latest_date: string | null
  latest_close: number | null
  latest_open: number | null
  latest_volume: number | null
  change_pct_1d: number | null
  change_pct_1w: number | null
  change_pct_1m: number | null
  change_pct_1y: number | null
  week_52_high: number | null
  week_52_low: number | null
  avg_volume_30d: number | null
}

export type StockHistoryPoint = {
  date: string
  open: number
  high: number
  low: number
  close: number
  adj_close: number
  volume: number
}

export type StockHistoryResponse = {
  ticker: string
  company_name: string | null
  logo_url: string | null
  timeframe: string | null
  start_date: string | null
  end_date: string | null
  total: number
  limit: number
  offset: number
  items: StockHistoryPoint[]
}

export type StockNewsItem = {
  title: string
  url: string
  source: string | null
  published_at: string | null
}

export type StockNewsResponse = {
  ticker: string
  company_name: string | null
  logo_url: string | null
  timeframe: string
  total: number
  limit: number
  provider: string
  provider_error: string | null
  items: StockNewsItem[]
}

export type StockLivePoint = {
  timestamp: string
  open: number | null
  high: number | null
  low: number | null
  close: number | null
  volume: number | null
}

export type StockLiveResponse = {
  ticker: string
  company_name: string | null
  logo_url: string | null
  range: '1d' | '5d' | '1mo'
  interval: '1m' | '2m' | '5m' | '15m' | '30m' | '60m'
  provider: string
  provider_error: string | null
  total: number
  latest_timestamp: string | null
  latest_close: number | null
  items: StockLivePoint[]
}

export type UserPublic = {
  id: number
  email: string
  is_email_verified: boolean
  is_active: boolean
  created_at: string
}

export type RegisterResponse = {
  message: string
  user_id: number
  verification_token?: string | null
  verification_link?: string | null
}

export type LoginResponse = {
  access_token: string
  token_type: string
  user: UserPublic
}

export type MessageResponse = {
  message: string
}

export type WatchlistPublic = {
  id: number
  name: string
  created_at: string
  items_count: number
}

export type WatchlistListResponse = {
  total: number
  limit: number
  offset: number
  items: WatchlistPublic[]
}

export type WatchlistItem = {
  id: number
  ticker: string
  company_name: string | null
  added_at: string
}

export type WatchlistItemsResponse = {
  watchlist_id: number
  total: number
  limit: number
  offset: number
  items: WatchlistItem[]
}

export type TickerInsight = {
  ticker: string
  company_name: string | null
  latest_close: number | null
  change_pct_1w: number | null
  change_pct_1m: number | null
  change_pct_1y: number | null
  avg_volume_30d: number | null
  volatility_30d: number | null
  weight_pct: number
}

export type WatchlistInsightsResponse = {
  watchlist_id: number
  watchlist_name: string
  ticker_count: number
  as_of_date: string
  tickers: TickerInsight[]
  top_gainer_1w: string | null
  top_loser_1w: string | null
  top_gainer_1m: string | null
  top_loser_1m: string | null
  highest_volatility: string | null
  lowest_volatility: string | null
}

export type PortfolioPublic = {
  id: number
  name: string
  created_at: string
  holdings_count: number
}

export type PortfolioListResponse = {
  total: number
  limit: number
  offset: number
  items: PortfolioPublic[]
}

export type HoldingPublic = {
  id: number
  ticker: string
  company_name: string | null
  quantity: number
  avg_cost: number | null
}

export type PortfolioHoldingsResponse = {
  portfolio_id: number
  total: number
  limit: number
  offset: number
  items: HoldingPublic[]
}
