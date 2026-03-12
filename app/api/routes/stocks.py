from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from email.utils import parsedate_to_datetime
from enum import Enum
from urllib.parse import quote_plus
from xml.etree import ElementTree

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.database.models import Stock, StockPrice

router = APIRouter(prefix="/stocks", tags=["stocks"])


class Timeframe(str, Enum):
    one_week = "1w"
    one_month = "1m"
    three_months = "3m"
    six_months = "6m"
    one_year = "1y"
    five_years = "5y"
    max = "max"


_TIMEFRAME_DAYS = {
    Timeframe.one_week: 7,
    Timeframe.one_month: 30,
    Timeframe.three_months: 90,
    Timeframe.six_months: 180,
    Timeframe.one_year: 365,
    Timeframe.five_years: 365 * 5,
}


class StockListItem(BaseModel):
    ticker: str
    company_name: str | None
    logo_url: str | None


class StockListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[StockListItem]


class StockDetailResponse(BaseModel):
    ticker: str
    company_name: str | None
    logo_url: str | None
    latest_date: date | None
    latest_close: float | None
    latest_open: float | None
    latest_volume: int | None
    change_pct_1d: float | None   # vs previous trading day
    change_pct_1w: float | None   # vs ~5 trading days ago
    change_pct_1m: float | None   # vs ~21 trading days ago
    change_pct_1y: float | None   # vs ~252 trading days ago
    week_52_high: float | None
    week_52_low: float | None
    avg_volume_30d: float | None


class StockPricePoint(BaseModel):
    date: date
    open: float
    high: float
    low: float
    close: float
    adj_close: float
    volume: int


class StockHistoryResponse(BaseModel):
    ticker: str
    company_name: str | None
    logo_url: str | None
    timeframe: Timeframe | None
    start_date: date | None
    end_date: date | None
    total: int
    limit: int
    offset: int
    items: list[StockPricePoint]


class StockNewsItem(BaseModel):
    title: str
    url: str
    source: str | None
    published_at: datetime | None


class StockNewsResponse(BaseModel):
    ticker: str
    company_name: str | None
    logo_url: str | None
    timeframe: Timeframe
    total: int
    limit: int
    provider: str
    provider_error: str | None
    items: list[StockNewsItem]


class LiveRange(str, Enum):
    one_day = "1d"
    five_days = "5d"
    one_month = "1mo"


class LiveInterval(str, Enum):
    one_minute = "1m"
    two_minutes = "2m"
    five_minutes = "5m"
    fifteen_minutes = "15m"
    thirty_minutes = "30m"
    sixty_minutes = "60m"


class StockLivePoint(BaseModel):
    timestamp: datetime
    open: float | None
    high: float | None
    low: float | None
    close: float | None
    volume: int | None


class StockLiveResponse(BaseModel):
    ticker: str
    company_name: str | None
    logo_url: str | None
    range: LiveRange
    interval: LiveInterval
    provider: str
    provider_error: str | None
    total: int
    latest_timestamp: datetime | None
    latest_close: float | None
    items: list[StockLivePoint]


def _to_float(value: Decimal) -> float:
    return float(value)


def _safe_pct(current: float | None, prior: float | None) -> float | None:
    if current is None or prior is None or prior == 0:
        return None
    return round((current - prior) / prior * 100, 4)


async def _fetch_company_logo_url(ticker: str) -> str | None:
    """
    Fetch company logo URL from Finnhub's free endpoint.
    Returns a logo URL or None if unavailable.
    """
    try:
        # Finnhub free endpoint - no key required for basic profile data
        response = httpx.get(
            f"https://finnhub.io/api/v1/stock/profile2?symbol={ticker}",
            timeout=5.0,
        )
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict) and "logo" in data:
            logo = data["logo"]
            if logo and isinstance(logo, str):
                return logo
    except Exception:
        pass
    
    # Fallback: construct a generic logo URL using a reliable service
    # Using clearbit logo service as fallback
    return f"https://logo.clearbit.com/{ticker.lower().replace('.', '')}.com"


def _timeframe_start_datetime(timeframe: Timeframe, now_utc: datetime) -> datetime:
    if timeframe == Timeframe.max:
        return datetime(1970, 1, 1, tzinfo=timezone.utc)
    return now_utc - timedelta(days=_TIMEFRAME_DAYS[timeframe])


def _fetch_google_news_items(
    ticker: str,
    company_name: str | None,
    limit: int,
) -> tuple[list[StockNewsItem], str | None]:
    query_terms = [ticker]
    if company_name:
        query_terms.append(company_name)
    query_terms.append("stock")
    query = quote_plus(" ".join(query_terms))
    feed_url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"

    try:
        response = httpx.get(feed_url, timeout=10.0)
        response.raise_for_status()
        root = ElementTree.fromstring(response.text)
    except Exception as exc:
        return [], f"News provider unavailable: {exc}"

    items: list[StockNewsItem] = []
    for node in root.findall(".//item"):
        if len(items) >= limit:
            break

        title = (node.findtext("title") or "").strip()
        link = (node.findtext("link") or "").strip()
        source = node.findtext("source")
        pub_date_text = (node.findtext("pubDate") or "").strip()

        published_at: datetime | None = None
        if pub_date_text:
            try:
                parsed = parsedate_to_datetime(pub_date_text)
                published_at = parsed.astimezone(timezone.utc)
            except Exception:
                published_at = None

        if not title or not link:
            continue

        items.append(
            StockNewsItem(
                title=title,
                url=link,
                source=source,
                published_at=published_at,
            )
        )

    return items, None


def _fetch_yahoo_live_points(
    ticker: str,
    data_range: LiveRange,
    interval: LiveInterval,
) -> tuple[list[StockLivePoint], str | None]:
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        f"?range={data_range.value}&interval={interval.value}&includePrePost=false&events=div%2Csplits"
    )

    try:
        response = httpx.get(url, timeout=10.0)
        response.raise_for_status()
        payload = response.json()
    except Exception as exc:
        return [], f"Live market provider unavailable: {exc}"

    chart = payload.get("chart", {})
    results = chart.get("result") or []
    if not results:
        return [], "Live market provider returned no chart data"

    result = results[0]
    timestamps = result.get("timestamp") or []
    quote_entries = ((result.get("indicators") or {}).get("quote") or [])
    quote = quote_entries[0] if quote_entries else {}

    opens = quote.get("open") or []
    highs = quote.get("high") or []
    lows = quote.get("low") or []
    closes = quote.get("close") or []
    volumes = quote.get("volume") or []

    items: list[StockLivePoint] = []
    for idx, ts in enumerate(timestamps):
        try:
            timestamp = datetime.fromtimestamp(int(ts), tz=timezone.utc)
        except Exception:
            continue

        open_value = opens[idx] if idx < len(opens) else None
        high_value = highs[idx] if idx < len(highs) else None
        low_value = lows[idx] if idx < len(lows) else None
        close_value = closes[idx] if idx < len(closes) else None
        volume_value = volumes[idx] if idx < len(volumes) else None

        if close_value is None:
            continue

        items.append(
            StockLivePoint(
                timestamp=timestamp,
                open=float(open_value) if open_value is not None else None,
                high=float(high_value) if high_value is not None else None,
                low=float(low_value) if low_value is not None else None,
                close=float(close_value) if close_value is not None else None,
                volume=int(volume_value) if volume_value is not None else None,
            )
        )

    return items, None


@router.get("", response_model=StockListResponse)
def list_stocks(
    search: str | None = Query(default=None, min_length=1, max_length=64),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    base_query = select(Stock)

    if search:
        pattern = f"%{search.strip().upper()}%"
        base_query = base_query.where(
            or_(
                func.upper(Stock.ticker).like(pattern),
                func.upper(func.coalesce(Stock.company_name, "")).like(pattern),
            )
        )

    total = db.scalar(select(func.count()).select_from(base_query.subquery())) or 0
    rows = db.scalars(base_query.order_by(Stock.ticker.asc()).limit(limit).offset(offset)).all()

    return StockListResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=[StockListItem(ticker=row.ticker, company_name=row.company_name, logo_url=row.logo_url) for row in rows],
    )


@router.get("/{ticker}", response_model=StockDetailResponse)
async def get_stock_detail(
    ticker: str,
    db: Session = Depends(get_db),
):
    """
    Return a summary card for a single ticker:
    latest price, 1d/1w/1m/1y % change, 52-week high/low, 30-day avg volume.
    Uses the last 260 trading-day rows (approx 1 year + buffer).
    """
    normalized_ticker = ticker.strip().upper()
    stock = db.get(Stock, normalized_ticker)
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticker '{normalized_ticker}' was not found",
        )

    rows = db.execute(
        select(
            StockPrice.date,
            StockPrice.open,
            StockPrice.close,
            StockPrice.high,
            StockPrice.low,
            StockPrice.volume,
        )
        .where(StockPrice.ticker == normalized_ticker)
        .order_by(StockPrice.date.desc())
        .limit(260)
    ).all()

    # Fetch logo URL from external API
    logo_url = await _fetch_company_logo_url(normalized_ticker)

    if not rows:
        return StockDetailResponse(
            ticker=normalized_ticker,
            company_name=stock.company_name,
            logo_url=logo_url,
            latest_date=None,
            latest_close=None,
            latest_open=None,
            latest_volume=None,
            change_pct_1d=None,
            change_pct_1w=None,
            change_pct_1m=None,
            change_pct_1y=None,
            week_52_high=None,
            week_52_low=None,
            avg_volume_30d=None,
        )

    closes = [float(r.close) for r in rows]
    highs = [float(r.high) for r in rows]
    lows = [float(r.low) for r in rows]
    volumes = [int(r.volume) for r in rows]

    latest = rows[0]

    def _at(n: int) -> float | None:
        return closes[n] if len(closes) > n else None

    recent_252_highs = highs[:252]
    recent_252_lows = lows[:252]
    recent_30_volumes = volumes[:30]

    return StockDetailResponse(
        ticker=normalized_ticker,
        company_name=stock.company_name,
        logo_url=logo_url,
        latest_date=latest.date,
        latest_close=round(closes[0], 4),
        latest_open=round(float(latest.open), 4),
        latest_volume=int(latest.volume),
        change_pct_1d=_safe_pct(closes[0], _at(1)),
        change_pct_1w=_safe_pct(closes[0], _at(5)),
        change_pct_1m=_safe_pct(closes[0], _at(21)),
        change_pct_1y=_safe_pct(closes[0], _at(252)),
        week_52_high=round(max(recent_252_highs), 4) if recent_252_highs else None,
        week_52_low=round(min(recent_252_lows), 4) if recent_252_lows else None,
        avg_volume_30d=round(sum(recent_30_volumes) / len(recent_30_volumes), 2) if recent_30_volumes else None,
    )


@router.get("/{ticker}/history", response_model=StockHistoryResponse)
def get_stock_history(
    ticker: str,
    timeframe: Timeframe | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    limit: int = Query(default=500, ge=1, le=5000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    normalized_ticker = ticker.strip().upper()
    stock = db.get(Stock, normalized_ticker)
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticker '{normalized_ticker}' was not found",
        )

    if timeframe and (start_date or end_date):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Use either timeframe or start_date/end_date filters, not both",
        )

    max_available_date = db.scalar(
        select(func.max(StockPrice.date)).where(StockPrice.ticker == normalized_ticker)
    )

    if not max_available_date:
        return StockHistoryResponse(
            ticker=normalized_ticker,
            company_name=stock.company_name,
            logo_url=stock.logo_url,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            total=0,
            limit=limit,
            offset=offset,
            items=[],
        )

    effective_end_date = end_date or max_available_date
    effective_start_date = start_date

    if timeframe:
        if timeframe == Timeframe.max:
            effective_start_date = None
            effective_end_date = max_available_date
        else:
            effective_end_date = max_available_date
            effective_start_date = effective_end_date - timedelta(days=_TIMEFRAME_DAYS[timeframe])

    if effective_start_date and effective_end_date and effective_start_date > effective_end_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start_date cannot be after end_date",
        )

    filtered_query = select(StockPrice).where(StockPrice.ticker == normalized_ticker)
    if effective_start_date:
        filtered_query = filtered_query.where(StockPrice.date >= effective_start_date)
    if effective_end_date:
        filtered_query = filtered_query.where(StockPrice.date <= effective_end_date)

    total = db.scalar(select(func.count()).select_from(filtered_query.subquery())) or 0
    rows = db.scalars(
        filtered_query.order_by(StockPrice.date.asc()).offset(offset).limit(limit)
    ).all()

    return StockHistoryResponse(
        ticker=normalized_ticker,
        company_name=stock.company_name,
        logo_url=stock.logo_url,
        timeframe=timeframe,
        start_date=effective_start_date,
        end_date=effective_end_date,
        total=total,
        limit=limit,
        offset=offset,
        items=[
            StockPricePoint(
                date=row.date,
                open=_to_float(row.open),
                high=_to_float(row.high),
                low=_to_float(row.low),
                close=_to_float(row.close),
                adj_close=_to_float(row.adj_close),
                volume=row.volume,
            )
            for row in rows
        ],
    )


@router.get("/{ticker}/news", response_model=StockNewsResponse)
def get_stock_news(
    ticker: str,
    timeframe: Timeframe = Query(default=Timeframe.one_week),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    normalized_ticker = ticker.strip().upper()
    stock = db.get(Stock, normalized_ticker)
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticker '{normalized_ticker}' was not found",
        )

    raw_items, provider_error = _fetch_google_news_items(
        ticker=normalized_ticker,
        company_name=stock.company_name,
        limit=max(limit * 3, 30),
    )

    since = _timeframe_start_datetime(timeframe, datetime.now(timezone.utc))
    filtered_items = [
        item for item in raw_items if item.published_at is not None and item.published_at >= since
    ][:limit]

    return StockNewsResponse(
        ticker=normalized_ticker,
        company_name=stock.company_name,
        logo_url=stock.logo_url,
        timeframe=timeframe,
        total=len(filtered_items),
        limit=limit,
        provider="google_news_rss",
        provider_error=provider_error,
        items=filtered_items,
    )


@router.get("/{ticker}/live", response_model=StockLiveResponse)
def get_stock_live_data(
    ticker: str,
    data_range: LiveRange = Query(default=LiveRange.one_day, alias="range"),
    interval: LiveInterval = Query(default=LiveInterval.five_minutes),
    db: Session = Depends(get_db),
):
    normalized_ticker = ticker.strip().upper()
    stock = db.get(Stock, normalized_ticker)
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticker '{normalized_ticker}' was not found",
        )

    items, provider_error = _fetch_yahoo_live_points(
        ticker=normalized_ticker,
        data_range=data_range,
        interval=interval,
    )

    latest_item = items[-1] if items else None

    return StockLiveResponse(
        ticker=normalized_ticker,
        company_name=stock.company_name,
        logo_url=stock.logo_url,
        range=data_range,
        interval=interval,
        provider="yahoo_chart",
        provider_error=provider_error,
        total=len(items),
        latest_timestamp=latest_item.timestamp if latest_item else None,
        latest_close=latest_item.close if latest_item else None,
        items=items,
    )
