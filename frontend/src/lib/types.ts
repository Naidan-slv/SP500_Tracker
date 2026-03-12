export type StockListItem = {
  ticker: string
  company_name: string | null
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
  timeframe: string | null
  start_date: string | null
  end_date: string | null
  total: number
  limit: number
  offset: number
  items: StockHistoryPoint[]
}
