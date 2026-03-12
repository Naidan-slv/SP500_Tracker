import type {
  HoldingPublic,
  LoginResponse,
  MessageResponse,
  PortfolioHoldingsResponse,
  PortfolioListResponse,
  PortfolioPublic,
  RegisterResponse,
  StockDetailResponse,
  StockHistoryResponse,
  StockListResponse,
  UserPublic,
  WatchlistInsightsResponse,
  WatchlistItemsResponse,
  WatchlistListResponse,
  WatchlistPublic,
  WatchlistItem,
} from './types'

const API_BASE_URL = import.meta.env.DEV
  ? '/api'
  : import.meta.env.VITE_API_BASE_URL ?? 'https://sp500-tracker.onrender.com'

type RequestOptions = {
  method?: 'GET' | 'POST' | 'DELETE'
  token?: string
  body?: unknown
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', token, body } = options

  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers: {
        ...(body ? { 'Content-Type': 'application/json' } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      ...(body ? { body: JSON.stringify(body) } : {}),
    })
  } catch {
    throw new Error(
      `Network/CORS error. Could not reach API at ${API_BASE_URL}. ` +
        'Check backend CORS settings and that the API URL is correct.',
    )
  }

  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`
    try {
      const payload = (await response.json()) as { detail?: string }
      if (payload.detail) {
        detail = payload.detail
      }
    } catch {
      detail = `${response.status} ${response.statusText}`
    }
    throw new Error(detail)
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

export async function registerUser(email: string, password: string): Promise<RegisterResponse> {
  return request<RegisterResponse>('/auth/register', {
    method: 'POST',
    body: { email, password },
  })
}

export async function verifyEmailToken(token: string): Promise<MessageResponse> {
  return request<MessageResponse>('/auth/verify-email', {
    method: 'POST',
    body: { token },
  })
}

export async function loginUser(email: string, password: string): Promise<LoginResponse> {
  return request<LoginResponse>('/auth/login', {
    method: 'POST',
    body: { email, password },
  })
}

export async function fetchMe(token: string): Promise<UserPublic> {
  return request<UserPublic>('/auth/me', { token })
}

export async function fetchWatchlists(token: string): Promise<WatchlistListResponse> {
  return request<WatchlistListResponse>('/watchlists?limit=100', { token })
}

export async function createWatchlist(token: string, name: string): Promise<WatchlistPublic> {
  return request<WatchlistPublic>('/watchlists', {
    method: 'POST',
    token,
    body: { name },
  })
}

export async function deleteWatchlist(token: string, watchlistId: number): Promise<MessageResponse> {
  return request<MessageResponse>(`/watchlists/${watchlistId}`, {
    method: 'DELETE',
    token,
  })
}

export async function fetchWatchlistItems(token: string, watchlistId: number): Promise<WatchlistItemsResponse> {
  return request<WatchlistItemsResponse>(`/watchlists/${watchlistId}/items?limit=200`, { token })
}

export async function addWatchlistItem(
  token: string,
  watchlistId: number,
  ticker: string,
): Promise<WatchlistItem> {
  return request<WatchlistItem>(`/watchlists/${watchlistId}/items`, {
    method: 'POST',
    token,
    body: { ticker },
  })
}

export async function removeWatchlistItem(
  token: string,
  watchlistId: number,
  ticker: string,
): Promise<MessageResponse> {
  return request<MessageResponse>(`/watchlists/${watchlistId}/items/${encodeURIComponent(ticker)}`, {
    method: 'DELETE',
    token,
  })
}

export async function fetchWatchlistInsights(
  token: string,
  watchlistId: number,
): Promise<WatchlistInsightsResponse> {
  return request<WatchlistInsightsResponse>(`/watchlists/${watchlistId}/insights`, { token })
}

export async function fetchPortfolios(token: string): Promise<PortfolioListResponse> {
  return request<PortfolioListResponse>('/portfolios?limit=100', { token })
}

export async function createPortfolio(token: string, name: string): Promise<PortfolioPublic> {
  return request<PortfolioPublic>('/portfolios', {
    method: 'POST',
    token,
    body: { name },
  })
}

export async function deletePortfolio(token: string, portfolioId: number): Promise<MessageResponse> {
  return request<MessageResponse>(`/portfolios/${portfolioId}`, {
    method: 'DELETE',
    token,
  })
}

export async function fetchPortfolioHoldings(
  token: string,
  portfolioId: number,
): Promise<PortfolioHoldingsResponse> {
  return request<PortfolioHoldingsResponse>(`/portfolios/${portfolioId}/holdings?limit=200`, {
    token,
  })
}

export async function addPortfolioHolding(
  token: string,
  portfolioId: number,
  payload: { ticker: string; quantity: number; avg_cost?: number | null },
): Promise<HoldingPublic> {
  return request<HoldingPublic>(`/portfolios/${portfolioId}/holdings`, {
    method: 'POST',
    token,
    body: payload,
  })
}

export async function removePortfolioHolding(
  token: string,
  portfolioId: number,
  ticker: string,
): Promise<MessageResponse> {
  return request<MessageResponse>(`/portfolios/${portfolioId}/holdings/${encodeURIComponent(ticker)}`, {
    method: 'DELETE',
    token,
  })
}
