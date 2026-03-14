# SP500 Tracker — API Documentation

**Base URL (Production):** `https://sp500-tracker.onrender.com`  
**Base URL (Local):** `http://localhost:8000`  
**Interactive Swagger UI:** `https://sp500-tracker.onrender.com/docs`  
**OpenAPI JSON:** `https://sp500-tracker.onrender.com/openapi.json`

---

## Table of Contents

1. [Overview](#1-overview)
2. [Authentication](#2-authentication)
3. [Error Handling](#3-error-handling)
4. [Endpoints — Auth](#4-endpoints--auth)
5. [Endpoints — Stocks](#5-endpoints--stocks)
6. [Endpoints — Watchlists](#6-endpoints--watchlists)
7. [Endpoints — Portfolios](#7-endpoints--portfolios)
8. [Pagination](#8-pagination)
9. [Rate Limiting & Caching](#9-rate-limiting--caching)
10. [Environment Variables](#10-environment-variables)

---

## 1. Overview

The SP500 Tracker API is a RESTful web service built with **FastAPI** that provides:

- **Real-time & historical S&P 500 stock data** sourced from Finnhub, Yahoo Finance, and a local PostgreSQL database.
- **User authentication** via JWT tokens (register → login → access protected resources).
- **Watchlist management** — create named watchlists, add/remove tickers, and retrieve computed analytics/insights.
- **Portfolio management** — create portfolios, track holdings with quantity and average cost, and update/remove holdings.
- **News aggregation** — fetch recent news articles for any S&P 500 ticker via Google News RSS.

All responses are JSON. The API follows standard HTTP methods (GET, POST, PATCH, DELETE) and returns appropriate HTTP status codes.

---

## 2. Authentication

The API uses **Bearer Token (JWT)** authentication.

### Workflow

1. **Register** — `POST /auth/register` → creates an account.
2. **Login** — `POST /auth/login` → returns an `access_token`.
3. **Authenticated requests** — include the header:

```
Authorization: Bearer <access_token>
```

Tokens expire after **60 minutes** by default (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`).

### Protected Endpoints

All `/watchlists/*` and `/portfolios/*` endpoints require authentication.  
All `/stocks/*` endpoints are **public** (no token required).

---

## 3. Error Handling

The API returns standard HTTP status codes with JSON error bodies:

| Status Code | Meaning | Example |
|-------------|---------|---------|
| `200` | Success | Successful GET, PATCH, DELETE |
| `201` | Created | Successful POST |
| `401` | Unauthorized | Invalid or missing token |
| `403` | Forbidden | Account inactive |
| `404` | Not Found | Resource does not exist |
| `409` | Conflict | Duplicate resource (e.g. duplicate email, duplicate ticker in watchlist) |
| `422` | Unprocessable Entity | Validation error (missing/invalid fields) |

**Error response format:**

```json
{
  "detail": "Human-readable error message"
}
```

**Validation error format (422):**

```json
{
  "detail": [
    {
      "loc": ["body", "password"],
      "msg": "String should have at least 8 characters",
      "type": "string_too_short"
    }
  ]
}
```

---

## 4. Endpoints — Auth

### 4.1 Register

**`POST /auth/register`** — Create a new user account.

**Request Body:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `email` | string | ✅ | Valid email address |
| `password` | string | ✅ | 8–128 characters |

**Example Request:**

```bash
curl -X POST https://sp500-tracker.onrender.com/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "securepass123"}'
```

**Example Response (201 Created):**

```json
{
  "message": "Registration successful. You can now log in.",
  "user_id": 42
}
```

**Error Responses:**
- `409 Conflict` — Email already registered.
- `422 Unprocessable Entity` — Password too short.

---

### 4.2 Login

**`POST /auth/login`** — Authenticate and receive a JWT token.

**Request Body:**

| Field | Type | Required |
|-------|------|----------|
| `email` | string | ✅ |
| `password` | string | ✅ |

**Example Request:**

```bash
curl -X POST https://sp500-tracker.onrender.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "securepass123"}'
```

**Example Response (200 OK):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 42,
    "email": "user@example.com",
    "is_email_verified": true,
    "is_active": true,
    "created_at": "2025-02-15T10:30:00"
  }
}
```

**Error Responses:**
- `401 Unauthorized` — Invalid email or password.
- `403 Forbidden` — Account is inactive.

---

### 4.3 Get Current User

**`GET /auth/me`** 🔒 — Return the authenticated user's profile.

**Headers:** `Authorization: Bearer <token>`

**Example Request:**

```bash
curl https://sp500-tracker.onrender.com/auth/me \
  -H "Authorization: Bearer eyJhbG..."
```

**Example Response (200 OK):**

```json
{
  "id": 42,
  "email": "user@example.com",
  "is_email_verified": true,
  "is_active": true,
  "created_at": "2025-02-15T10:30:00"
}
```

---

## 5. Endpoints — Stocks

All stock endpoints are **public** — no authentication required.

### 5.1 List / Search Stocks

**`GET /stocks`** — List S&P 500 stocks with optional fuzzy search.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `search` | string | — | Search ticker or company name (fuzzy, case-insensitive) |
| `limit` | int | 50 | Results per page (1–200) |
| `offset` | int | 0 | Pagination offset |

**Example Request:**

```bash
curl "https://sp500-tracker.onrender.com/stocks?search=apple&limit=5"
```

**Example Response (200 OK):**

```json
{
  "total": 1,
  "limit": 5,
  "offset": 0,
  "items": [
    {
      "ticker": "AAPL",
      "company_name": "Apple Inc",
      "logo_url": "https://static2.finnhub.io/file/publicdatany/finnhubimage/stock_logo/AAPL.png"
    }
  ]
}
```

**Search behaviour:**
1. Exact ticker match and SQL LIKE on `ticker` and `company_name`.
2. Normalised fuzzy search (strips spaces, punctuation) on both fields.
3. Fallback to a hardcoded company-name override map (handles edge cases like `BRK.B`).
4. Final fallback to Yahoo Finance search API to resolve uncommon queries.

---

### 5.2 Stock Detail

**`GET /stocks/{ticker}`** — Return a summary card with latest price and key metrics.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `ticker` | string | S&P 500 ticker symbol (e.g. `AAPL`, `MSFT`) |

**Example Request:**

```bash
curl https://sp500-tracker.onrender.com/stocks/AAPL
```

**Example Response (200 OK):**

```json
{
  "ticker": "AAPL",
  "company_name": "Apple Inc",
  "logo_url": "https://static2.finnhub.io/file/publicdatany/finnhubimage/stock_logo/AAPL.png",
  "latest_date": "2025-03-07",
  "latest_close": 241.84,
  "latest_open": 240.155,
  "latest_volume": 38065373,
  "change_pct_1d": -0.5432,
  "change_pct_1w": -2.1876,
  "change_pct_1m": -8.3451,
  "change_pct_1y": 37.8912,
  "week_52_high": 260.1,
  "week_52_low": 164.075,
  "avg_volume_30d": 52340875.67
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `latest_close` | float\|null | Most recent closing price |
| `change_pct_1d` | float\|null | % change vs previous trading day |
| `change_pct_1w` | float\|null | % change vs ~5 trading days ago |
| `change_pct_1m` | float\|null | % change vs ~21 trading days ago |
| `change_pct_1y` | float\|null | % change vs ~252 trading days ago |
| `week_52_high` | float\|null | Highest price in last 252 trading days |
| `week_52_low` | float\|null | Lowest price in last 252 trading days |
| `avg_volume_30d` | float\|null | Average daily volume over last 30 trading days |

---

### 5.3 Stock History (OHLCV)

**`GET /stocks/{ticker}/history`** — Return historical OHLCV price data.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `timeframe` | enum | — | Preset: `1w`, `1m`, `3m`, `6m`, `1y`, `5y`, `max` |
| `start_date` | date | — | ISO date (e.g. `2024-01-01`). Cannot combine with `timeframe`. |
| `end_date` | date | — | ISO date. Cannot combine with `timeframe`. |
| `limit` | int | 500 | Results per page (1–5000) |
| `offset` | int | 0 | Pagination offset |

> **Note:** Use either `timeframe` OR `start_date`/`end_date`, not both.

**Example Request:**

```bash
curl "https://sp500-tracker.onrender.com/stocks/AAPL/history?timeframe=1m&limit=5"
```

**Example Response (200 OK):**

```json
{
  "ticker": "AAPL",
  "company_name": "Apple Inc",
  "logo_url": "https://...",
  "timeframe": "1m",
  "start_date": "2025-02-05",
  "end_date": "2025-03-07",
  "total": 22,
  "limit": 5,
  "offset": 0,
  "items": [
    {
      "date": "2025-02-05",
      "open": 229.23,
      "high": 232.89,
      "low": 228.97,
      "close": 232.47,
      "adj_close": 232.47,
      "volume": 42618530
    }
  ]
}
```

---

### 5.4 Stock News

**`GET /stocks/{ticker}/news`** — Fetch recent news articles for a ticker.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `timeframe` | enum | `1w` | Recency window: `1w`, `1m`, `3m`, `6m`, `1y`, `5y`, `max` |
| `limit` | int | 20 | Max articles (1–100) |

**Example Request:**

```bash
curl "https://sp500-tracker.onrender.com/stocks/AAPL/news?timeframe=1w&limit=3"
```

**Example Response (200 OK):**

```json
{
  "ticker": "AAPL",
  "company_name": "Apple Inc",
  "logo_url": "https://...",
  "timeframe": "1w",
  "total": 3,
  "limit": 3,
  "provider": "google_news_rss",
  "provider_error": null,
  "items": [
    {
      "title": "Apple launches new AI features for iPhone 16",
      "url": "https://news.google.com/rss/articles/...",
      "source": "Reuters",
      "published_at": "2025-03-06T14:22:00Z"
    }
  ]
}
```

**Provider:** Google News RSS feed. The `provider_error` field indicates if the feed was unavailable.

---

### 5.5 Live / Intraday Data

**`GET /stocks/{ticker}/live`** — Fetch live intraday candle data.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `range` | enum | `1d` | Time range: `1d`, `5d`, `1mo` |
| `interval` | enum | `5m` | Candle interval: `1m`, `2m`, `5m`, `15m`, `30m`, `60m` |

**Example Request:**

```bash
curl "https://sp500-tracker.onrender.com/stocks/AAPL/live?range=1d&interval=5m"
```

**Example Response (200 OK):**

```json
{
  "ticker": "AAPL",
  "company_name": "Apple Inc",
  "logo_url": "https://...",
  "range": "1d",
  "interval": "5m",
  "provider": "finnhub_candle",
  "provider_error": null,
  "total": 78,
  "latest_timestamp": "2025-03-07T20:55:00Z",
  "latest_close": 241.84,
  "items": [
    {
      "timestamp": "2025-03-07T14:30:00Z",
      "open": 240.12,
      "high": 240.89,
      "low": 239.95,
      "close": 240.65,
      "volume": 523400
    }
  ]
}
```

**Provider cascade:**
1. **Finnhub** candle API (primary, requires `FINNHUB_API_KEY`).
2. **Yahoo Finance** chart API (secondary fallback).
3. **Database history** — stored daily OHLCV data (guaranteed fallback).
4. **Stale cache** — returns cached data up to 5 minutes old.

**Caching:** Fresh results are cached in-memory for **45 seconds**. Stale cache is valid for up to **300 seconds**.

---

## 6. Endpoints — Watchlists

All watchlist endpoints require authentication 🔒.

### 6.1 Create Watchlist

**`POST /watchlists`** 🔒

**Request Body:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `name` | string | ✅ | 1–120 characters |

**Example Request:**

```bash
curl -X POST https://sp500-tracker.onrender.com/watchlists \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Tech Giants"}'
```

**Example Response (201 Created):**

```json
{
  "id": 5,
  "name": "Tech Giants",
  "created_at": "2025-03-07T15:00:00",
  "items_count": 0
}
```

---

### 6.2 List Watchlists

**`GET /watchlists`** 🔒

**Query Parameters:**

| Parameter | Type | Default |
|-----------|------|---------|
| `limit` | int | 50 |
| `offset` | int | 0 |

**Example Response (200 OK):**

```json
{
  "total": 2,
  "limit": 50,
  "offset": 0,
  "items": [
    {
      "id": 5,
      "name": "Tech Giants",
      "created_at": "2025-03-07T15:00:00",
      "items_count": 3
    }
  ]
}
```

---

### 6.3 Delete Watchlist

**`DELETE /watchlists/{watchlist_id}`** 🔒

**Example Response (200 OK):**

```json
{
  "message": "Watchlist deleted successfully"
}
```

---

### 6.4 List Watchlist Items

**`GET /watchlists/{watchlist_id}/items`** 🔒

**Query Parameters:**

| Parameter | Type | Default |
|-----------|------|---------|
| `limit` | int | 100 |
| `offset` | int | 0 |

**Example Response (200 OK):**

```json
{
  "watchlist_id": 5,
  "total": 3,
  "limit": 100,
  "offset": 0,
  "items": [
    {
      "id": 12,
      "ticker": "AAPL",
      "company_name": "Apple Inc",
      "added_at": "2025-03-07T15:05:00"
    },
    {
      "id": 13,
      "ticker": "MSFT",
      "company_name": "Microsoft Corporation",
      "added_at": "2025-03-07T15:06:00"
    }
  ]
}
```

---

### 6.5 Add Ticker to Watchlist

**`POST /watchlists/{watchlist_id}/items`** 🔒

**Request Body:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `ticker` | string | ✅ | 1–16 chars. Accepts ticker symbol or company name (fuzzy resolved). |

**Example Request:**

```bash
curl -X POST https://sp500-tracker.onrender.com/watchlists/5/items \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"ticker": "GOOGL"}'
```

**Example Response (201 Created):**

```json
{
  "id": 14,
  "ticker": "GOOGL",
  "company_name": "Alphabet Inc",
  "added_at": "2025-03-07T15:10:00"
}
```

**Error Responses:**
- `404 Not Found` — Ticker not found in S&P 500.
- `409 Conflict` — Ticker already in this watchlist.

---

### 6.6 Remove Ticker from Watchlist

**`DELETE /watchlists/{watchlist_id}/items/{ticker}`** 🔒

**Example Response (200 OK):**

```json
{
  "message": "Watchlist item removed successfully"
}
```

---

### 6.7 Watchlist Insights / Analytics

**`GET /watchlists/{watchlist_id}/insights`** 🔒

Returns computed analytics for every ticker in the watchlist.

**Example Response (200 OK):**

```json
{
  "watchlist_id": 5,
  "watchlist_name": "Tech Giants",
  "ticker_count": 3,
  "as_of_date": "2025-03-07",
  "tickers": [
    {
      "ticker": "AAPL",
      "company_name": "Apple Inc",
      "latest_close": 241.84,
      "change_pct_1w": -2.19,
      "change_pct_1m": -8.35,
      "change_pct_1y": 37.89,
      "avg_volume_30d": 52340875.67,
      "volatility_30d": 28.45,
      "weight_pct": 33.3333
    }
  ],
  "top_gainer_1w": "MSFT",
  "top_loser_1w": "AAPL",
  "top_gainer_1m": "GOOGL",
  "top_loser_1m": "AAPL",
  "highest_volatility": "AAPL",
  "lowest_volatility": "MSFT"
}
```

**Insight Fields:**

| Field | Description |
|-------|-------------|
| `change_pct_1w` | % price change vs 5 trading days ago |
| `change_pct_1m` | % price change vs 21 trading days ago |
| `change_pct_1y` | % price change vs 252 trading days ago |
| `avg_volume_30d` | Average daily trading volume over 30 days |
| `volatility_30d` | Annualised standard deviation of daily returns (30 days), expressed as % |
| `weight_pct` | Equal-weight allocation percentage |

---

## 7. Endpoints — Portfolios

All portfolio endpoints require authentication 🔒.

### 7.1 Create Portfolio

**`POST /portfolios`** 🔒

**Request Body:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `name` | string | ✅ | 1–120 characters |

**Example Response (201 Created):**

```json
{
  "id": 3,
  "name": "Growth Portfolio",
  "created_at": "2025-03-07T16:00:00",
  "holdings_count": 0
}
```

---

### 7.2 List Portfolios

**`GET /portfolios`** 🔒

**Query Parameters:** `limit` (default 50), `offset` (default 0).

**Example Response (200 OK):**

```json
{
  "total": 1,
  "limit": 50,
  "offset": 0,
  "items": [
    {
      "id": 3,
      "name": "Growth Portfolio",
      "created_at": "2025-03-07T16:00:00",
      "holdings_count": 5
    }
  ]
}
```

---

### 7.3 Update Portfolio Name

**`PATCH /portfolios/{portfolio_id}`** 🔒

**Request Body:**

| Field | Type | Required |
|-------|------|----------|
| `name` | string | ✅ |

**Example Response (200 OK):**

```json
{
  "id": 3,
  "name": "Renamed Portfolio",
  "created_at": "2025-03-07T16:00:00",
  "holdings_count": 5
}
```

---

### 7.4 Delete Portfolio

**`DELETE /portfolios/{portfolio_id}`** 🔒

**Example Response (200 OK):**

```json
{
  "message": "Portfolio deleted successfully"
}
```

---

### 7.5 List Holdings

**`GET /portfolios/{portfolio_id}/holdings`** 🔒

**Query Parameters:** `limit` (default 100), `offset` (default 0).

**Example Response (200 OK):**

```json
{
  "portfolio_id": 3,
  "total": 2,
  "limit": 100,
  "offset": 0,
  "items": [
    {
      "id": 8,
      "ticker": "AAPL",
      "company_name": "Apple Inc",
      "quantity": 10.0,
      "avg_cost": 185.50
    },
    {
      "id": 9,
      "ticker": "MSFT",
      "company_name": "Microsoft Corporation",
      "quantity": 5.0,
      "avg_cost": 420.00
    }
  ]
}
```

---

### 7.6 Add Holding

**`POST /portfolios/{portfolio_id}/holdings`** 🔒

**Request Body:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `ticker` | string | ✅ | 1–16 chars. Accepts ticker or company name (fuzzy resolved). |
| `quantity` | float | ✅ | Must be > 0 |
| `avg_cost` | float | ❌ | Must be > 0 if provided |

**Example Request:**

```bash
curl -X POST https://sp500-tracker.onrender.com/portfolios/3/holdings \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"ticker": "NVDA", "quantity": 15, "avg_cost": 875.25}'
```

**Example Response (201 Created):**

```json
{
  "id": 10,
  "ticker": "NVDA",
  "company_name": "NVIDIA Corporation",
  "quantity": 15.0,
  "avg_cost": 875.25
}
```

**Error Responses:**
- `404 Not Found` — Ticker not found.
- `409 Conflict` — Ticker already in this portfolio.

---

### 7.7 Update Holding

**`PATCH /portfolios/{portfolio_id}/holdings/{ticker}`** 🔒

**Request Body (partial update):**

| Field | Type | Required |
|-------|------|----------|
| `quantity` | float | ❌ |
| `avg_cost` | float | ❌ |

> At least one field must be provided.

**Example Request:**

```bash
curl -X PATCH https://sp500-tracker.onrender.com/portfolios/3/holdings/NVDA \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"quantity": 20}'
```

**Example Response (200 OK):**

```json
{
  "id": 10,
  "ticker": "NVDA",
  "company_name": "NVIDIA Corporation",
  "quantity": 20.0,
  "avg_cost": 875.25
}
```

---

### 7.8 Remove Holding

**`DELETE /portfolios/{portfolio_id}/holdings/{ticker}`** 🔒

**Example Response (200 OK):**

```json
{
  "message": "Holding removed successfully"
}
```

---

## 8. Pagination

All list endpoints support offset-based pagination:

| Parameter | Description |
|-----------|-------------|
| `limit` | Maximum number of items to return |
| `offset` | Number of items to skip |

Every paginated response includes `total`, `limit`, and `offset` fields so the client can compute total pages.

**Example:** To get page 3 with 20 items per page:

```
GET /stocks?limit=20&offset=40
```

---

## 9. Rate Limiting & Caching

### Backend Caching

| Cache | TTL | Scope |
|-------|-----|-------|
| Live data (in-memory) | 45 seconds | Per ticker + range + interval |
| Live data stale fallback | 300 seconds | Same key, used only when live providers fail |
| News (in-memory) | 5 minutes | Per ticker + timeframe |

### External Provider Rate Limits

| Provider | Limit | Notes |
|----------|-------|-------|
| Finnhub | 60 calls/min (free tier) | Used for live candles and company profiles |
| Yahoo Finance | Unofficial, no strict limit | Used as fallback for live candles and search |
| Google News RSS | No strict limit | Used for news articles |

### Frontend Caching (TanStack Query)

| Resource | `staleTime` |
|----------|-------------|
| Stock list/search | 2 minutes |
| Stock detail | 5 minutes |
| Stock history | 10 minutes |
| Live chart | 30 seconds |
| News | 2 minutes |
| Watchlists / Portfolios | 2 minutes |

---

## 10. Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | ✅ |
| `JWT_SECRET_KEY` | Secret key for JWT signing | ✅ |
| `JWT_ALGORITHM` | JWT algorithm (default: `HS256`) | ❌ |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime (default: `60`) | ❌ |
| `APP_BASE_URL` | Backend public URL | ❌ |
| `FRONTEND_URL` | Frontend URL for CORS | ❌ |
| `FINNHUB_API_KEY` | Finnhub API key for live data | ❌ |

---

## Endpoint Summary Table

| # | Method | Path | Auth | Description |
|---|--------|------|------|-------------|
| 1 | POST | `/auth/register` | ❌ | Register a new user |
| 2 | POST | `/auth/login` | ❌ | Log in and receive JWT |
| 3 | GET | `/auth/me` | 🔒 | Get current user profile |
| 4 | GET | `/stocks` | ❌ | List/search S&P 500 stocks |
| 5 | GET | `/stocks/{ticker}` | ❌ | Stock detail with key metrics |
| 6 | GET | `/stocks/{ticker}/history` | ❌ | Historical OHLCV data |
| 7 | GET | `/stocks/{ticker}/news` | ❌ | Recent news articles |
| 8 | GET | `/stocks/{ticker}/live` | ❌ | Live/intraday candle data |
| 9 | POST | `/watchlists` | 🔒 | Create a watchlist |
| 10 | GET | `/watchlists` | 🔒 | List user's watchlists |
| 11 | DELETE | `/watchlists/{id}` | 🔒 | Delete a watchlist |
| 12 | GET | `/watchlists/{id}/items` | 🔒 | List watchlist tickers |
| 13 | POST | `/watchlists/{id}/items` | 🔒 | Add ticker to watchlist |
| 14 | DELETE | `/watchlists/{id}/items/{ticker}` | 🔒 | Remove ticker from watchlist |
| 15 | GET | `/watchlists/{id}/insights` | 🔒 | Watchlist analytics & insights |
| 16 | POST | `/portfolios` | 🔒 | Create a portfolio |
| 17 | GET | `/portfolios` | 🔒 | List user's portfolios |
| 18 | PATCH | `/portfolios/{id}` | 🔒 | Rename a portfolio |
| 19 | DELETE | `/portfolios/{id}` | 🔒 | Delete a portfolio |
| 20 | GET | `/portfolios/{id}/holdings` | 🔒 | List portfolio holdings |
| 21 | POST | `/portfolios/{id}/holdings` | 🔒 | Add a holding |
| 22 | PATCH | `/portfolios/{id}/holdings/{ticker}` | 🔒 | Update holding qty/cost |
| 23 | DELETE | `/portfolios/{id}/holdings/{ticker}` | 🔒 | Remove a holding |

**Total: 23 endpoints** across 4 resource groups.

---

## Data Source

Historical OHLCV stock data sourced from:

> Shahrukh, I. (2025) *Top 50 S&P 500 Companies Dataset*. Available at: https://www.kaggle.com/datasets/ibrahimshahrukh/top-50-companies-dataset (Accessed: 9 March 2025).

Live and intraday data provided by [Finnhub](https://finnhub.io/) and [Yahoo Finance](https://finance.yahoo.com/).  
News articles aggregated via [Google News RSS](https://news.google.com/).