# Stock Intelligence API

FastAPI + PostgreSQL backend for COMP3011 Web Services coursework.

**Live API:** https://sp500-tracker.onrender.com  
**Interactive docs:** https://sp500-tracker.onrender.com/docs

> ⚠️ Hosted on Render's free tier — first request after inactivity may take ~30s to cold-start.

---

## What It Does

- Historical OHLCV data for 49 tickers (230,111 rows, 2006–2026)
- JWT authentication with email verification
- Watchlist and portfolio CRUD (ownership-scoped)
- Watchlist analytics: price change %, volatility, concentration
- Stock summary cards: latest price, 52-week high/low, % changes

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

---

## Tests

```bash
pytest tests/
# 114 tests, ~3 seconds, in-memory SQLite (no network required)
```

---

## Deployment (Render)

Configured via `render.yaml`. Set these env vars in the Render dashboard:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | Supabase session pooler URI |
| `JWT_SECRET_KEY` | Long random secret (generate: `openssl rand -hex 32`) |

All other env vars are defined in `render.yaml` with safe defaults.

---

## Stack

- **FastAPI** — web framework
- **SQLAlchemy 2 + Alembic** — ORM and migrations
- **Supabase PostgreSQL** — hosted database
- **python-jose** — JWT tokens
- **pytest** — test suite (114 tests)
- **Render** — deployment platform
