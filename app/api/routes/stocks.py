from datetime import date, timedelta
from decimal import Decimal
from enum import Enum

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


class StockListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[StockListItem]


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
    timeframe: Timeframe | None
    start_date: date | None
    end_date: date | None
    total: int
    limit: int
    offset: int
    items: list[StockPricePoint]


def _to_float(value: Decimal) -> float:
    return float(value)


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
        items=[StockListItem(ticker=row.ticker, company_name=row.company_name) for row in rows],
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
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Use either timeframe or start_date/end_date filters, not both",
        )

    max_available_date = db.scalar(
        select(func.max(StockPrice.date)).where(StockPrice.ticker == normalized_ticker)
    )

    if not max_available_date:
        return StockHistoryResponse(
            ticker=normalized_ticker,
            company_name=stock.company_name,
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
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
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
