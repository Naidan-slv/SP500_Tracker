import type {
  StockDetailResponse,
  StockHistoryResponse,
  StockListResponse,
} from './types'

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? 'https://sp500-tracker.onrender.com'

async function request<T>(path: string): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${path}`)
  } catch {
    throw new Error(
      `Network/CORS error. Could not reach API at ${API_BASE_URL}. ` +
        'Check backend CORS settings and that the API URL is correct.',
    )
  }

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status} ${response.statusText}`)
  }
  return (await response.json()) as T
}

export function getApiBaseUrl(): string {
  return API_BASE_URL
}

export async function fetchStocks(search: string, limit = 25, offset = 0): Promise<StockListResponse> {
  const query = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  })

  if (search.trim()) {
    query.set('search', search.trim())
  }

  return request<StockListResponse>(`/stocks?${query.toString()}`)
}

export async function fetchStockDetail(ticker: string): Promise<StockDetailResponse> {
  return request<StockDetailResponse>(`/stocks/${encodeURIComponent(ticker)}`)
}

export async function fetchStockHistory(
  ticker: string,
  timeframe: '1w' | '1m' | '3m' | '6m' | '1y' | '5y' | 'max' = '6m',
): Promise<StockHistoryResponse> {
  return request<StockHistoryResponse>(
    `/stocks/${encodeURIComponent(ticker)}/history?timeframe=${timeframe}&limit=500`,
  )
}
