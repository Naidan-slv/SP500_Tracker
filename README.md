# SP500_Tracker

Stock Intelligence API backend (FastAPI + PostgreSQL) for COMP3011 coursework.

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Run DB migrations:

```bash
alembic upgrade head
```

Run API server:

```bash
uvicorn app.main:app --reload
```

Open docs at `http://localhost:8000/docs`.

## Auth Endpoints

- `POST /auth/register`
- `POST /auth/verify-email`
- `POST /auth/login`
- `GET /auth/me` (Bearer token required)

## Data Ingestion

Load cleaned historical OHLCV data into PostgreSQL:

```bash
python scripts/ingest_stock_prices.py
```

## Local Auth Flow Check

```bash
python scripts/test_auth_flow.py
```
