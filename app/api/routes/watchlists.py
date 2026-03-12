from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.routes.auth import get_current_user
from app.database.dependencies import get_db
from app.database.models import Stock, StockPrice, User, Watchlist, WatchlistItem

router = APIRouter(prefix="/watchlists", tags=["watchlists"])


class WatchlistCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class WatchlistItemAddRequest(BaseModel):
    ticker: str = Field(min_length=1, max_length=16)


class WatchlistPublic(BaseModel):
    id: int
    name: str
    created_at: datetime
    items_count: int


class WatchlistListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[WatchlistPublic]


class WatchlistItemPublic(BaseModel):
    id: int
    ticker: str
    added_at: datetime


class WatchlistItemsResponse(BaseModel):
    watchlist_id: int
    total: int
    limit: int
    offset: int
    items: list[WatchlistItemPublic]


class MessageResponse(BaseModel):
    message: str


def _get_user_watchlist_or_404(db: Session, watchlist_id: int, user_id: int) -> Watchlist:
    watchlist = db.scalar(
        select(Watchlist).where(Watchlist.id == watchlist_id, Watchlist.user_id == user_id)
    )
    if not watchlist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watchlist not found")
    return watchlist


@router.post("", response_model=WatchlistPublic, status_code=status.HTTP_201_CREATED)
def create_watchlist(
    payload: WatchlistCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    watchlist = Watchlist(user_id=current_user.id, name=payload.name.strip())
    db.add(watchlist)
    db.commit()
    db.refresh(watchlist)

    return WatchlistPublic(
        id=watchlist.id,
        name=watchlist.name,
        created_at=watchlist.created_at,
        items_count=0,
    )


@router.get("", response_model=WatchlistListResponse)
def list_watchlists(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    base_query = select(Watchlist).where(Watchlist.user_id == current_user.id)
    total = db.scalar(select(func.count()).select_from(base_query.subquery())) or 0

    rows = db.scalars(base_query.order_by(Watchlist.created_at.desc()).offset(offset).limit(limit)).all()

    watchlist_ids = [row.id for row in rows]
    item_counts: dict[int, int] = {}
    if watchlist_ids:
        counts_rows = db.execute(
            select(WatchlistItem.watchlist_id, func.count(WatchlistItem.id))
            .where(WatchlistItem.watchlist_id.in_(watchlist_ids))
            .group_by(WatchlistItem.watchlist_id)
        ).all()
        item_counts = {watchlist_id: count for watchlist_id, count in counts_rows}

    return WatchlistListResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=[
            WatchlistPublic(
                id=row.id,
                name=row.name,
                created_at=row.created_at,
                items_count=item_counts.get(row.id, 0),
            )
            for row in rows
        ],
    )


@router.delete("/{watchlist_id}", response_model=MessageResponse)
def delete_watchlist(
    watchlist_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    watchlist = _get_user_watchlist_or_404(db, watchlist_id, current_user.id)
    db.delete(watchlist)
    db.commit()
    return MessageResponse(message="Watchlist deleted successfully")


@router.get("/{watchlist_id}/items", response_model=WatchlistItemsResponse)
def list_watchlist_items(
    watchlist_id: int,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_user_watchlist_or_404(db, watchlist_id, current_user.id)

    base_query = select(WatchlistItem).where(WatchlistItem.watchlist_id == watchlist_id)
    total = db.scalar(select(func.count()).select_from(base_query.subquery())) or 0
    rows = db.scalars(
        base_query.order_by(WatchlistItem.added_at.desc()).offset(offset).limit(limit)
    ).all()

    return WatchlistItemsResponse(
        watchlist_id=watchlist_id,
        total=total,
        limit=limit,
        offset=offset,
        items=[
            WatchlistItemPublic(id=row.id, ticker=row.ticker, added_at=row.added_at)
            for row in rows
        ],
    )


@router.post("/{watchlist_id}/items", response_model=WatchlistItemPublic, status_code=status.HTTP_201_CREATED)
def add_watchlist_item(
    watchlist_id: int,
    payload: WatchlistItemAddRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_user_watchlist_or_404(db, watchlist_id, current_user.id)

    normalized_ticker = payload.ticker.strip().upper()
    stock = db.get(Stock, normalized_ticker)
    if not stock:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticker not found")

    item = WatchlistItem(watchlist_id=watchlist_id, ticker=normalized_ticker)
    db.add(item)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ticker already exists in this watchlist",
        ) from exc

    db.refresh(item)
    return WatchlistItemPublic(id=item.id, ticker=item.ticker, added_at=item.added_at)


@router.delete("/{watchlist_id}/items/{ticker}", response_model=MessageResponse)
def remove_watchlist_item(
    watchlist_id: int,
    ticker: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_user_watchlist_or_404(db, watchlist_id, current_user.id)

    normalized_ticker = ticker.strip().upper()
    item = db.scalar(
        select(WatchlistItem).where(
            WatchlistItem.watchlist_id == watchlist_id,
            WatchlistItem.ticker == normalized_ticker,
        )
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watchlist item not found")

    db.delete(item)
    db.commit()
    return MessageResponse(message="Watchlist item removed successfully")


# ── Insights ─────────────────────────────────────────────────────────────────

class TickerInsight(BaseModel):
    ticker: str
    company_name: str | None
    latest_close: float | None
    change_pct_1w: float | None   # % change vs 5 trading days ago
    change_pct_1m: float | None   # % change vs ~21 trading days ago
    change_pct_1y: float | None   # % change vs ~252 trading days ago
    avg_volume_30d: float | None
    volatility_30d: float | None  # std dev of daily returns over last 30 days
    weight_pct: float             # this ticker as % of all watchlist tickers (equal-weight)


class WatchlistInsightsResponse(BaseModel):
    watchlist_id: int
    watchlist_name: str
    ticker_count: int
    as_of_date: str              # ISO date of the most recent data used
    tickers: list[TickerInsight]
    top_gainer_1w: str | None
    top_loser_1w: str | None
    top_gainer_1m: str | None
    top_loser_1m: str | None
    highest_volatility: str | None
    lowest_volatility: str | None


def _safe_pct_change(current: float | None, prior: float | None) -> float | None:
    if current is None or prior is None or prior == 0:
        return None
    return round((current - prior) / prior * 100, 4)


def _compute_ticker_insight(
    ticker: str,
    company_name: str | None,
    ticker_count: int,
    db: Session,
) -> TickerInsight:
    """Fetch the last 260 trading-day prices for one ticker and compute analytics."""
    rows = db.execute(
        select(StockPrice.date, StockPrice.close, StockPrice.volume)
        .where(StockPrice.ticker == ticker)
        .order_by(StockPrice.date.desc())
        .limit(260)
    ).all()

    if not rows:
        return TickerInsight(
            ticker=ticker,
            company_name=company_name,
            latest_close=None,
            change_pct_1w=None,
            change_pct_1m=None,
            change_pct_1y=None,
            avg_volume_30d=None,
            volatility_30d=None,
            weight_pct=round(100.0 / ticker_count, 4) if ticker_count else 0.0,
        )

    closes = [float(r.close) for r in rows]   # index 0 = most recent
    volumes = [int(r.volume) for r in rows]

    latest_close = closes[0]

    def _close_at(n: int) -> float | None:
        return closes[n] if len(closes) > n else None

    change_pct_1w = _safe_pct_change(latest_close, _close_at(5))
    change_pct_1m = _safe_pct_change(latest_close, _close_at(21))
    change_pct_1y = _safe_pct_change(latest_close, _close_at(252))

    recent_30_volumes = volumes[:30]
    avg_volume_30d = round(sum(recent_30_volumes) / len(recent_30_volumes), 2) if recent_30_volumes else None

    # Volatility = annualised std dev of daily log-like returns over last 30 days
    recent_30_closes = closes[:30]
    volatility_30d: float | None = None
    if len(recent_30_closes) >= 2:
        daily_returns = [
            (recent_30_closes[i] - recent_30_closes[i + 1]) / recent_30_closes[i + 1]
            for i in range(len(recent_30_closes) - 1)
            if recent_30_closes[i + 1] != 0
        ]
        if len(daily_returns) >= 2:
            n = len(daily_returns)
            mean = sum(daily_returns) / n
            variance = sum((r - mean) ** 2 for r in daily_returns) / (n - 1)
            std_dev = variance ** 0.5
            volatility_30d = round(std_dev * (252 ** 0.5) * 100, 4)  # annualised %

    return TickerInsight(
        ticker=ticker,
        company_name=company_name,
        latest_close=round(latest_close, 4),
        change_pct_1w=change_pct_1w,
        change_pct_1m=change_pct_1m,
        change_pct_1y=change_pct_1y,
        avg_volume_30d=avg_volume_30d,
        volatility_30d=volatility_30d,
        weight_pct=round(100.0 / ticker_count, 4) if ticker_count else 0.0,
    )


@router.get("/{watchlist_id}/insights", response_model=WatchlistInsightsResponse)
def get_watchlist_insights(
    watchlist_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return analytics for every ticker in the watchlist:
    - price change % over 1 week, 1 month, 1 year
    - 30-day average volume
    - annualised 30-day volatility
    - equal-weight portfolio concentration
    - top gainer/loser and highest/lowest volatility labels
    """
    watchlist = _get_user_watchlist_or_404(db, watchlist_id, current_user.id)

    item_rows = db.execute(
        select(WatchlistItem.ticker)
        .where(WatchlistItem.watchlist_id == watchlist_id)
        .order_by(WatchlistItem.added_at.asc())
    ).scalars().all()

    tickers = list(item_rows)

    if not tickers:
        return WatchlistInsightsResponse(
            watchlist_id=watchlist_id,
            watchlist_name=watchlist.name,
            ticker_count=0,
            as_of_date="",
            tickers=[],
            top_gainer_1w=None,
            top_loser_1w=None,
            top_gainer_1m=None,
            top_loser_1m=None,
            highest_volatility=None,
            lowest_volatility=None,
        )

    # Resolve company names in one query
    stock_rows = db.execute(
        select(Stock.ticker, Stock.company_name).where(Stock.ticker.in_(tickers))
    ).all()
    company_map = {row.ticker: row.company_name for row in stock_rows}

    ticker_count = len(tickers)
    insights = [
        _compute_ticker_insight(t, company_map.get(t), ticker_count, db)
        for t in tickers
    ]

    # Determine as_of_date from the most recent price across all tickers
    max_date_row = db.scalar(
        select(func.max(StockPrice.date)).where(StockPrice.ticker.in_(tickers))
    )
    as_of_date = max_date_row.isoformat() if max_date_row else ""

    # Summary labels
    with_1w = [i for i in insights if i.change_pct_1w is not None]
    with_1m = [i for i in insights if i.change_pct_1m is not None]
    with_vol = [i for i in insights if i.volatility_30d is not None]

    top_gainer_1w = max(with_1w, key=lambda i: i.change_pct_1w).ticker if with_1w else None  # type: ignore[arg-type]
    top_loser_1w = min(with_1w, key=lambda i: i.change_pct_1w).ticker if with_1w else None  # type: ignore[arg-type]
    top_gainer_1m = max(with_1m, key=lambda i: i.change_pct_1m).ticker if with_1m else None  # type: ignore[arg-type]
    top_loser_1m = min(with_1m, key=lambda i: i.change_pct_1m).ticker if with_1m else None  # type: ignore[arg-type]
    highest_volatility = max(with_vol, key=lambda i: i.volatility_30d).ticker if with_vol else None  # type: ignore[arg-type]
    lowest_volatility = min(with_vol, key=lambda i: i.volatility_30d).ticker if with_vol else None  # type: ignore[arg-type]

    return WatchlistInsightsResponse(
        watchlist_id=watchlist_id,
        watchlist_name=watchlist.name,
        ticker_count=ticker_count,
        as_of_date=as_of_date,
        tickers=insights,
        top_gainer_1w=top_gainer_1w,
        top_loser_1w=top_loser_1w,
        top_gainer_1m=top_gainer_1m,
        top_loser_1m=top_loser_1m,
        highest_volatility=highest_volatility,
        lowest_volatility=lowest_volatility,
    )
