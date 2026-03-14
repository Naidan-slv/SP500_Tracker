# Stock Intelligence API

Full-stack stock tracking platform for COMP3011 Web Services coursework.

**Live API:** https://sp500-tracker-frontend.onrender.com  
**Interactive docs:** https://sp500-tracker.onrender.com/docs

> ⚠️ The backend is hosted on Render's free tier — the first request after inactivity may take ~30s to cold-start.

---

## Documentation

| Document | Location |
|----------|----------|
| API Documentation (PDF) | [`docs/SP500_Tracker_API_Documentation.pdf`](docs/SP500_Tracker_API_Documentation.pdf) |
| API Documentation (Markdown) | [`docs/API_DOCUMENTATION.md`](docs/API_DOCUMENTATION.md) |
| AI Development Log | [`AI_DEVELOPMENT_LOG.md`](AI_DEVELOPMENT_LOG.md) |

---

## What It Does

- Historical OHLCV data for 49 tickers (230,111 rows, 2006–2026)
- JWT authentication (register + login)
- Watchlist and portfolio CRUD (ownership-scoped)
- Watchlist analytics: price change %, volatility, concentration
- Stock summary cards: latest price, 52-week high/low, % changes
- Stock news feeds filtered by user-selected timeframe
- Live intraday market chart data with selectable range and interval
- Full React frontend with Discover, Stock Detail, Watchlists, and Portfolio pages
- Search autocomplete, cached queries, lazy route loading, and chart chunk-splitting for smoother UX

---

## Frontend Features

- **Discover page:** Search tickers and companies, use market filters, browse paginated results, and jump into stock detail pages
- **Autocomplete search:** Live dropdown suggestions using cached stock universe data
- **Stock detail page:** Summary card, historical price chart, live intraday chart, and timeframe-filtered news panel
- **Watchlists page:** Create/delete watchlists, add/remove tickers, and review insight summaries
- **Portfolio page:** Create/delete portfolios, manage holdings, and inspect cost basis and gain/loss values
- **Client performance:** TanStack Query caching, placeholder data for non-blocking refetches, lazy-loaded routes, and `Recharts` isolated into its own async chunk

---

## API Endpoints

### Auth
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/register` | — | Create account |
| POST | `/auth/login` | — | Get JWT access token |
| GET | `/auth/me` | ✅ | Current user profile |

### Stocks
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/stocks` | — | Discover/search tickers (paginated) |
| GET | `/stocks/{ticker}` | — | Summary card: price, % changes, 52w high/low |
| GET | `/stocks/{ticker}/history` | — | OHLCV history (timeframe or date range) |
| GET | `/stocks/{ticker}/news` | — | News feed filtered by timeframe |
| GET | `/stocks/{ticker}/live` | — | Live/intraday chart data with range + interval |

### Watchlists
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/watchlists` | ✅ | Create watchlist |
| GET | `/watchlists` | ✅ | List user's watchlists |
| DELETE | `/watchlists/{id}` | ✅ | Delete watchlist |
| GET | `/watchlists/{id}/items` | ✅ | List tickers in watchlist |
| POST | `/watchlists/{id}/items` | ✅ | Add ticker |
| DELETE | `/watchlists/{id}/items/{ticker}` | ✅ | Remove ticker |
| GET | `/watchlists/{id}/insights` | ✅ | Analytics: movers, volatility, concentration |

### Portfolios
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/portfolios` | ✅ | Create portfolio |
| GET | `/portfolios` | ✅ | List user's portfolios |
| PATCH | `/portfolios/{id}` | ✅ | Rename portfolio |
| DELETE | `/portfolios/{id}` | ✅ | Delete portfolio |
| GET | `/portfolios/{id}/holdings` | ✅ | List holdings |
| POST | `/portfolios/{id}/holdings` | ✅ | Add holding (quantity + avg cost) |
| PATCH | `/portfolios/{id}/holdings/{ticker}` | ✅ | Update holding quantity/avg cost |
| DELETE | `/portfolios/{id}/holdings/{ticker}` | ✅ | Remove holding |

---

## Local Development

### One-command startup (recommended)

```bash
./scripts/dev.sh
```

This starts both services together and stops both on `Ctrl+C`:

- Backend: `http://127.0.0.1:8000/docs`
- Frontend: `http://127.0.0.1:5174`

Optional port/host overrides:

```bash
BACKEND_PORT=8001 FRONTEND_PORT=5175 ./scripts/dev.sh
```

### Backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
# fill in DATABASE_URL and JWT_SECRET_KEY in .env
```

Run DB migrations:
```bash
alembic upgrade head
```

Start server:
```bash
uvicorn app.main:app --reload
```

Open docs at `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5174
```

The frontend uses Vite and proxies `/api` requests to `http://127.0.0.1:8000` in development.

Create a production build with:

```bash
cd frontend
npm run build
```

---

## Caching Architecture

The app uses a **two-tier caching strategy** to keep the experience fast on free-tier hosting and avoid external provider rate limits:

### Backend (in-memory)
| Cache | Key | TTL | Purpose |
|-------|-----|-----|---------|
| Live market data | `(ticker, range, interval)` | 45 s fresh / 5 min stale fallback | Avoid re-hitting Finnhub/Yahoo on every page load |
| News feeds | `(ticker, timeframe)` | 5 min | Prevent duplicate Google News RSS calls when users toggle timeframe filters |

### Frontend (TanStack Query)
| Scope | staleTime | gcTime | Purpose |
|-------|-----------|--------|---------|
| Global default | 2 min | 5 min | All queries get basic freshness without config |
| Stock universe (Discover/Portfolio/Watchlists) | 10 min | 30 min | The ticker list rarely changes; cached aggressively |
| Detail / History queries | 5 min | default | Balance freshness vs network calls |

Both tiers work together: the backend prevents redundant external calls while the frontend prevents redundant API calls. Together, page navigations and filter changes feel instant.

---

## Tests

```bash
pytest tests/
# 127 tests, in-memory SQLite, no network required
```

Latest verified local checks:

- `pytest -q` → `127 passed in ~4s`
- `cd frontend && npm run build` → production build succeeded

---

## Deployment (Render)

Configured via `render.yaml`. Set these env vars in the Render dashboard:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | Supabase session pooler URI |
| `JWT_SECRET_KEY` | Long random secret (generate: `openssl rand -hex 32`) |
| `FRONTEND_URL` | Public frontend URL (e.g. `https://sp500-tracker-frontend.onrender.com`) |
| `FINNHUB_API_KEY` | Finnhub API key for live market data |

For the frontend, set `VITE_API_BASE_URL=https://sp500-tracker.onrender.com` when deploying to a static host such as Vercel or Netlify.

---

## Stack

- **FastAPI** — backend API framework
- **SQLAlchemy 2 + Alembic** — ORM and migrations
- **Supabase PostgreSQL** — hosted relational database
- **python-jose** — JWT tokens
- **httpx** — external provider requests
- **React 18 + TypeScript + Vite** — frontend client
- **TanStack Query** — client-side caching and async state management
- **React Router** — frontend routing
- **Recharts** — historical and live chart rendering
- **pytest** — backend test suite (`127` tests)
- **Render** — backend deployment platform

---

## Data Source

Historical OHLCV data sourced from:

> Shahrukh, I. (2025) *Top 50 S&P 500 Companies Dataset*. Available at: https://www.kaggle.com/datasets/ibrahimshahrukh/top-50-companies-dataset (Accessed: 9 March 2025).

---

## Repository

Salvador, N. (2025) *SP500 Tracker*. Available at: https://github.com/Naidan-slv/SP500_Tracker (Accessed: 13 March 2025).
