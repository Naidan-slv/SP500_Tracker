# Stock Intelligence API

Full-stack stock tracking platform for COMP3011 Web Services coursework.

**Live API:** https://sp500-tracker.onrender.com  
**Interactive docs:** https://sp500-tracker.onrender.com/docs

> ⚠️ The backend is hosted on Render's free tier — the first request after inactivity may take ~30s to cold-start.

---

## What It Does

- Historical OHLCV data for 49 tickers (230,111 rows, 2006–2026)
- JWT authentication with email verification
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
| POST | `/auth/verify-email` | — | Verify email token |
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
| DELETE | `/portfolios/{id}` | ✅ | Delete portfolio |
| GET | `/portfolios/{id}/holdings` | ✅ | List holdings |
| POST | `/portfolios/{id}/holdings` | ✅ | Add holding (quantity + avg cost) |
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

## Tests

```bash
pytest tests/
# 120 tests, in-memory SQLite, no network required
```

Latest verified local checks:

- `pytest -q` → `120 passed in 2.76s`
- `cd frontend && npm run build` → production build succeeded

---

## Deployment (Render)

Configured via `render.yaml`. Set these env vars in the Render dashboard:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | Supabase session pooler URI |
| `JWT_SECRET_KEY` | Long random secret (generate: `openssl rand -hex 32`) |
| `FRONTEND_URL` | Public frontend URL used in verification links (e.g. `https://sp500-tracker-frontend.onrender.com`) |
| `SMTP_HOST` | SMTP server host (e.g. `smtp.gmail.com`) |
| `SMTP_USERNAME` | SMTP username/login |
| `SMTP_PASSWORD` | SMTP password or app password |
| `SMTP_FROM_EMAIL` | Sender address for verification emails |

`SMTP_ENABLED=true` is set in `render.yaml`; keep `SMTP_USE_TLS=true` unless your provider requires another mode.

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
- **pytest** — backend test suite (`120` tests)
- **Render** — backend deployment platform
