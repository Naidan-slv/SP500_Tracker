# SP500 Tracker — Technical Report

**Module:** COMP3011 — Web-Based Application Development  
**Student:** Naidan Salvador  
**Date:** March 2025

---

## 1. Introduction

The SP500 Tracker is a full-stack web application that enables users to browse S&P 500 stocks, view historical and live price charts, track watchlists with computed analytics, and manage investment portfolios. This report details the technology choices, architectural design, development challenges, testing strategy, and areas for future improvement.

---

## 2. Technology Stack Justification

### 2.1 Backend — FastAPI + SQLAlchemy

**FastAPI** was chosen over Flask or Django for several reasons:

- **Automatic OpenAPI documentation** — every endpoint is immediately explorable via Swagger UI at `/docs`, reducing the need for manual documentation and accelerating frontend integration.
- **Pydantic validation** — request and response schemas are declared as Python type-annotated models, providing automatic input validation, serialisation, and clear error messages without boilerplate code.
- **Async support** — native `async/await` enables non-blocking calls to external APIs (Finnhub, Yahoo Finance) without thread pool overhead, critical for a data aggregation service.
- **Performance** — benchmarks consistently show FastAPI outperforming Flask by 2–5× on JSON response throughput, important for serving real-time chart data.

**SQLAlchemy 2.0** with the modern `select()` API provides type-safe query construction. **Alembic** handles schema migrations, ensuring database changes are versioned alongside application code.

**PostgreSQL** (via Supabase) was selected over SQLite for production because it handles concurrent connections, supports advanced indexing, and scales to the 230,000+ OHLCV price rows stored in the application.

### 2.2 Frontend — React + TypeScript + Vite

**React 18** was chosen for its component model and ecosystem maturity. **TypeScript** catches type errors at compile time, which was particularly valuable when modelling the 23-endpoint API surface with strongly-typed request/response interfaces.

**Vite** provides sub-second hot module replacement during development and optimised production builds. **TanStack Query v5** manages all server state — providing automatic caching, background refetching, stale-while-revalidate, and loading/error state management without manual `useEffect` data-fetching patterns.

**Recharts** was selected for charting (area charts, donut pie charts) because it is a React-native composable charting library — each axis, tooltip, and data series is a React component, making it straightforward to build interactive, responsive charts.

### 2.3 Authentication — JWT

JSON Web Tokens (via `python-jose`) provide stateless authentication. The token is stored in frontend `localStorage` and attached to requests via the `Authorization: Bearer` header. This approach avoids server-side session storage, simplifies horizontal scaling, and integrates naturally with the RESTful API design.

### 2.4 External Data Providers

A **multi-provider cascade** ensures data resilience:

1. **Finnhub** (primary live data) — provides real-time candles and company profiles.
2. **Yahoo Finance** (fallback) — used when Finnhub is unavailable or rate-limited.
3. **Database history** (guaranteed fallback) — stored OHLCV data ensures the live chart always renders, even when both external providers fail.
4. **Google News RSS** — provides ticker-specific news articles with time-scoped queries.

---

## 3. Design & Architecture

### 3.1 System Architecture

The application follows a **three-tier architecture**:

```
┌──────────────┐     HTTPS      ┌──────────────┐     SQL       ┌──────────────┐
│   React SPA  │ ──────────────▶│  FastAPI API  │ ────────────▶│  PostgreSQL  │
│   (Render    │                │  (Render Web  │              │  (Supabase)  │
│    Static)   │◀──────────────│   Service)    │◀────────────│              │
└──────────────┘     JSON       └──────┬───────┘     Rows      └──────────────┘
                                       │
                              ┌────────┼────────┐
                              ▼        ▼        ▼
                          Finnhub   Yahoo    Google
                          Finance   Finance   News
```

### 3.2 Backend Structure

The backend uses a **modular router pattern**:

- `app/api/routes/auth.py` — registration, login, user profile (3 endpoints)
- `app/api/routes/stocks.py` — search, detail, history, news, live (5 endpoints)
- `app/api/routes/watchlists.py` — CRUD + insights (7 endpoints)
- `app/api/routes/portfolios.py` — CRUD + holdings management (8 endpoints)
- `app/database/models.py` — SQLAlchemy ORM models (User, Stock, StockPrice, Watchlist, WatchlistItem, Portfolio, PortfolioHolding)
- `app/auth/` — JWT token creation, hashing, verification

### 3.3 Frontend Structure

The frontend follows a **page-component-hook** pattern:

- **Pages** (`src/pages/`) — top-level route components that orchestrate data fetching and layout.
- **Components** (`src/components/`) — reusable UI pieces (charts, modals, navigation).
- **API layer** (`src/lib/api.ts`) — centralised HTTP client with typed request/response functions.
- **Auth context** (`src/context/AuthContext.tsx`) — React context providing login state and token management to all components.

### 3.4 Caching Strategy

A **two-tier caching** approach minimises external API calls:

| Layer | Implementation | TTL |
|-------|---------------|-----|
| Backend | Python dict (`_LIVE_CACHE`, `_NEWS_CACHE`) | 45s live, 5min news |
| Frontend | TanStack Query | 30s–10min per resource |

---

## 4. Challenges & Lessons Learned

### 4.1 External API Reliability

The most significant challenge was **external API instability**. Finnhub rate limits (60 calls/min on the free tier) and Yahoo Finance's unofficial API occasionally returning empty responses caused the live chart to break in production. The solution was a three-layer fallback cascade (Finnhub → Yahoo → Database history) with stale cache as a final safety net, ensuring the chart always renders meaningful data.

### 4.2 Fuzzy Search Resolution

Supporting both ticker symbols and company names as input (e.g., typing "Berkshire" should resolve to `BRK.B`) required a normalisation pipeline that strips punctuation, spaces, and special characters before performing SQL LIKE queries. A hardcoded `COMPANY_NAME_OVERRIDES` map handles edge cases where database names don't match common queries.

### 4.3 CSS Layering & Overflow

The autocomplete suggestion dropdown on the Watchlist and Portfolio pages had z-index stacking conflicts with adjacent cards. Resolving this required careful management of `overflow`, `position`, and `z-index` across the layout shell, grid containers, and individual cards — a reminder that CSS stacking contexts must be considered holistically.

---

## 5. Testing Approach

### 5.1 Strategy

The project has **127 automated tests** using `pytest` with an **in-memory SQLite** database for isolation. Tests are organised into focused modules:

| Module | Tests | Coverage |
|--------|-------|----------|
| Auth (register, login, /me) | 15 | Registration, login, token validation, error cases |
| Stocks (list, detail, history, news, live) | 20 | Search, pagination, timeframe validation, 404 handling |
| Watchlists (CRUD + insights) | 11 | Create, list, delete, add/remove items, duplicate prevention |
| Portfolios (CRUD + holdings) | 42 | Full CRUD, holding add/update/remove, edge cases |
| Contracts (API schema validation) | 10 | Response structure matches Pydantic models |
| E2E (user journey) | 7 | Register → login → create watchlist → add items → insights |
| Insights analytics | 21 | Volatility calculation, change %, summary labels |

### 5.2 Key Testing Decisions

- **In-memory SQLite** — each test function gets a fresh database via `pytest` fixtures, ensuring complete isolation without network dependencies.
- **Dependency injection override** — FastAPI's `app.dependency_overrides` replaces the production database session with a test session, avoiding any production data access.
- **No mocking of external APIs in unit tests** — external provider calls (Finnhub, Yahoo) are not hit during tests; the stock data endpoints operate on seeded test data.

---

## 6. Limitations & Future Improvements

### 6.1 Current Limitations

- **No real-time WebSocket streaming** — the live chart polls via REST; true real-time push would reduce latency.
- **In-memory caching only** — the Python dict cache is not shared across multiple server instances; a Redis-based cache would support horizontal scaling.
- **No refresh token rotation** — JWT tokens expire after 60 minutes with no silent refresh mechanism.
- **Equal-weight insights only** — watchlist analytics assume equal weighting; market-cap or custom weighting would be more useful.

### 6.2 Future Improvements

- **WebSocket integration** for push-based live price updates.
- **Redis caching** to support multi-instance deployments.
- **OAuth 2.0** social login (Google, GitHub) alongside email/password.
- **Portfolio performance tracking** — historical value charting, P&L calculations, benchmark comparison.
- **Mobile-responsive redesign** using CSS container queries.
- **Alerting system** — price threshold notifications via email or push.

---

## 7. GenAI Declaration & Analysis

### 7.1 Tools Used

| Tool | Purpose |
|------|---------|
| GitHub Copilot (Claude) | Code generation, debugging, architecture design, test writing, documentation |

### 7.2 How GenAI Was Used

Generative AI was used as a **pair programming assistant** throughout the project. Key use cases:

1. **Code scaffolding** — initial endpoint structures, Pydantic models, and SQLAlchemy schemas were generated and then reviewed/modified.
2. **Test generation** — test cases were collaboratively designed, with AI generating boilerplate and the developer specifying edge cases and assertions.
3. **Debugging** — CSS stacking issues, external API integration failures, and database query optimisation were iteratively debugged with AI assistance.
4. **Documentation** — API documentation, this technical report, and the development log were drafted with AI and refined by the developer.

### 7.3 Critical Analysis

**Benefits:**
- Significantly accelerated development velocity — the 23-endpoint API with 127 tests was built faster than would have been possible manually.
- Caught subtle bugs (e.g., timezone-naive datetime comparisons, SQL injection vectors in LIKE queries) that might have been missed in manual review.
- Provided consistent code style and idiomatic patterns across the codebase.

**Limitations:**
- AI-generated CSS fixes sometimes addressed symptoms rather than root causes, requiring multiple iterations (e.g., the dropdown overlay issue needed two rounds of fixes).
- Generated test cases occasionally tested implementation details rather than behaviour, requiring manual refactoring.
- Required careful review — AI suggestions were not blindly accepted; each was evaluated for correctness and relevance.

**Conclusion:** GenAI was a valuable productivity tool but required continuous human oversight. The developer maintained architectural decision-making authority while leveraging AI for implementation speed. All generated code was reviewed, tested, and understood before integration.

---

## References

- FastAPI documentation: https://fastapi.tiangolo.com/
- SQLAlchemy 2.0: https://docs.sqlalchemy.org/en/20/
- React documentation: https://react.dev/
- TanStack Query v5: https://tanstack.com/query/latest
- Recharts: https://recharts.org/
- Finnhub API: https://finnhub.io/docs/api
- Yahoo Finance (unofficial): https://query1.finance.yahoo.com/
