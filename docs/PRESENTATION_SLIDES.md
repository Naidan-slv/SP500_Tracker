# SP500 Tracker — Presentation Slides

> **Instructions:** This Markdown file contains the content for each slide in the 5-minute presentation.
> Convert to PPTX using any Markdown-to-PPTX tool, or copy each slide's content into PowerPoint/Google Slides.
> Each `---` divider marks a new slide.

---

## Slide 1 — Title

# SP500 Tracker
### A Full-Stack S&P 500 Stock Tracking Application

**COMP3011 — Web-Based Application Development**  
**Naidan Salvador**  
**March 2025**

- Live API: https://sp500-tracker.onrender.com
- GitHub: https://github.com/naidansalvador/SP500_Tracker

---

## Slide 2 — Project Overview

### What is SP500 Tracker?

A web application that lets users:

- 🔍 **Browse & search** all S&P 500 stocks with fuzzy search
- 📈 **View historical charts** with configurable timeframes (1W – 5Y)
- ⚡ **Monitor live prices** with intraday candlestick data
- 📰 **Read latest news** aggregated from Google News RSS
- 📋 **Create watchlists** with computed analytics & insights
- 💼 **Manage portfolios** with holdings, cost tracking & allocation pie chart
- 🔐 **User authentication** via JWT (register → login)

**23 API endpoints | 127 automated tests | Deployed on Render**

---

## Slide 3 — Technology Stack

### Tech Stack

| Layer | Technology | Why? |
|-------|-----------|------|
| **Backend** | FastAPI + Python 3.12 | Auto-docs, async, Pydantic validation |
| **Database** | PostgreSQL (Supabase) | 230k+ price rows, concurrent access |
| **ORM** | SQLAlchemy 2.0 + Alembic | Type-safe queries, versioned migrations |
| **Frontend** | React 18 + TypeScript + Vite | Component model, type safety, fast HMR |
| **State** | TanStack Query v5 | Caching, background refetch, stale-while-revalidate |
| **Charts** | Recharts | React-native composable chart components |
| **Auth** | JWT (python-jose) | Stateless, scalable, no session storage |
| **Deployment** | Render | Backend web service + frontend static site |

---

## Slide 4 — System Architecture

### Architecture Diagram

```
┌──────────────┐            ┌──────────────┐           ┌──────────────┐
│   React SPA  │───HTTPS───▶│  FastAPI API  │───SQL────▶│  PostgreSQL  │
│  (Static)    │◀──JSON─────│  (Render)     │◀──Rows───│  (Supabase)  │
└──────────────┘            └──────┬───────┘           └──────────────┘
                                   │
                         ┌─────────┼─────────┐
                         ▼         ▼         ▼
                     Finnhub    Yahoo     Google
                     (Live)    (Fallback)  (News)
```

**Key design decisions:**
- Three-tier separation (SPA → API → Database)
- Multi-provider fallback cascade for live data reliability
- Two-tier caching (backend in-memory + frontend TanStack Query)

---

## Slide 5 — API Overview

### 23 RESTful Endpoints

| Group | Endpoints | Key Features |
|-------|-----------|-------------|
| **Auth** (3) | Register, Login, Me | JWT tokens, password hashing |
| **Stocks** (5) | List, Detail, History, News, Live | Fuzzy search, OHLCV data, 3-provider cascade |
| **Watchlists** (7) | CRUD + Items + Insights | Analytics: volatility, % change, top gainer/loser |
| **Portfolios** (8) | CRUD + Holdings CRUD | Quantity, avg cost, allocation breakdown |

- Full API documentation with example requests/responses
- Interactive Swagger UI at `/docs`
- Consistent error handling with clear HTTP status codes

---

## Slide 6 — Key Features Demo

### Feature Highlights

1. **Fuzzy Stock Search** — type "Berkshire" → resolves to `BRK.B`
   - SQL normalisation + override map + Yahoo fallback

2. **Live Chart with 3-Layer Fallback**
   - Finnhub → Yahoo Finance → Database History → Stale Cache
   - Chart always renders, even when external APIs fail

3. **Watchlist Insights**
   - 1W/1M/1Y price change, 30-day volatility, average volume
   - Top gainer, top loser, most/least volatile summary

4. **Portfolio Allocation Pie Chart**
   - Interactive donut chart with hover highlighting
   - Total portfolio value displayed in centre
   - Colour-coded legend with sync hover

---

## Slide 7 — Version Control & Deployment

### Git & Deployment Practices

**Version Control:**
- Meaningful commit messages following conventional format
- Frequent, atomic commits (feature-by-feature)
- Full history from project scaffold to final fixes

**Deployment Pipeline:**
- `render.yaml` Infrastructure-as-Code configuration
- Backend: Python web service with Gunicorn + Uvicorn workers
- Frontend: Static site with SPA redirect rules
- Environment variables managed via Render dashboard

**Live URLs:**
- API: `https://sp500-tracker.onrender.com`
- Docs: `https://sp500-tracker.onrender.com/docs`

---

## Slide 8 — Testing Strategy

### 127 Automated Tests

| Category | Count | Description |
|----------|-------|-------------|
| Auth | 15 | Register, login, token validation |
| Stocks | 20 | Search, detail, history, pagination |
| Watchlists | 11 | CRUD, duplicate prevention |
| Portfolios | 42 | Full CRUD + holdings edge cases |
| Contract | 10 | Response schema validation |
| E2E Journey | 7 | Full user flow: register → insights |
| Insights | 21 | Analytics accuracy, summary labels |

**Testing approach:**
- In-memory SQLite for complete isolation
- FastAPI dependency injection overrides
- No external API calls during tests
- All 127 tests pass in ~4 seconds

---

## Slide 9 — Challenges & GenAI Usage

### Key Challenges

1. **External API instability** → solved with 3-layer fallback + stale cache
2. **Fuzzy search edge cases** (BRK.B, special chars) → normalisation pipeline
3. **CSS stacking conflicts** → z-index management across layout layers

### GenAI Usage (GitHub Copilot)

- Used as a **pair programming assistant**
- Code scaffolding, test generation, debugging, documentation
- **All code reviewed and understood** before integration
- AI accelerated velocity but required continuous human oversight
- AI occasionally addressed symptoms over root causes (CSS issues needed multiple rounds)

---

## Slide 10 — Limitations & Future Work

### Current Limitations

- REST polling for live data (no WebSocket push)
- In-memory cache (not shared across server instances)
- No refresh token rotation
- Equal-weight watchlist analytics only

### Future Improvements

- ⚡ **WebSocket** real-time price streaming
- 🗄️ **Redis caching** for horizontal scaling
- 🔐 **OAuth 2.0** social login (Google, GitHub)
- 📊 **Portfolio P&L tracking** with benchmark comparison
- 📱 **Mobile-responsive** redesign
- 🔔 **Price alerts** via notifications

---

## Slide 11 — Summary & Deliverables

### Deliverables Checklist

| Deliverable | Status |
|-------------|--------|
| ✅ Working API (23 endpoints) | Deployed on Render |
| ✅ React Frontend (4 pages) | Deployed on Render |
| ✅ API Documentation | Complete with examples |
| ✅ Technical Report (5 pages) | Stack, design, testing, GenAI |
| ✅ 127 Automated Tests | All passing |
| ✅ Version Control (Git) | Full commit history |
| ✅ GenAI Declaration | Documented in report & dev log |
| ✅ Presentation Slides | This presentation |
| ✅ AI Development Log | 19 entries, full interaction history |
| ✅ README.md | Setup, API reference, deployment |

### Thank you! Questions?
