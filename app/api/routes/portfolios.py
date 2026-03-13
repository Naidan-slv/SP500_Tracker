from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.routes.auth import get_current_user
from app.database.dependencies import get_db
from app.database.models import Portfolio, PortfolioHolding, Stock, User

router = APIRouter(prefix="/portfolios", tags=["portfolios"])


class PortfolioCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class HoldingAddRequest(BaseModel):
    ticker: str = Field(min_length=1, max_length=16)
    quantity: float = Field(gt=0)
    avg_cost: float | None = Field(default=None, gt=0)


class PortfolioPublic(BaseModel):
    id: int
    name: str
    created_at: datetime
    holdings_count: int


class PortfolioListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[PortfolioPublic]


class HoldingPublic(BaseModel):
    id: int
    ticker: str
    quantity: float
    avg_cost: float | None


class PortfolioHoldingsResponse(BaseModel):
    portfolio_id: int
    total: int
    limit: int
    offset: int
    items: list[HoldingPublic]


class MessageResponse(BaseModel):
    message: str


def _to_float_or_none(value) -> float | None:
    return float(value) if value is not None else None


def _compact_sql_text(expression):
    compact = func.upper(func.coalesce(expression, ""))
    for token in (" ", ".", "-", "_", "/", "&", "'", ","):
        compact = func.replace(compact, token, "")
    return compact


def _compact_input_text(value: str) -> str:
    return "".join(char for char in value.upper() if char.isalnum())


def _resolve_stock_from_input(db: Session, raw_input: str) -> Stock | None:
    normalized_ticker = raw_input.strip().upper()
    if not normalized_ticker:
        return None

    exact_match = db.get(Stock, normalized_ticker)
    if exact_match:
        return exact_match

    compact_search = _compact_input_text(raw_input)
    if not compact_search:
        return None

    compact_pattern = f"%{compact_search}%"
    return db.scalar(
        select(Stock)
        .where(
            or_(
                _compact_sql_text(Stock.ticker).like(compact_pattern),
                _compact_sql_text(Stock.company_name).like(compact_pattern),
            )
        )
        .order_by(Stock.ticker.asc())
        .limit(1)
    )


def _get_user_portfolio_or_404(db: Session, portfolio_id: int, user_id: int) -> Portfolio:
    portfolio = db.scalar(
        select(Portfolio).where(Portfolio.id == portfolio_id, Portfolio.user_id == user_id)
    )
    if not portfolio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")
    return portfolio


@router.post("", response_model=PortfolioPublic, status_code=status.HTTP_201_CREATED)
def create_portfolio(
    payload: PortfolioCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    portfolio = Portfolio(user_id=current_user.id, name=payload.name.strip())
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)

    return PortfolioPublic(
        id=portfolio.id,
        name=portfolio.name,
        created_at=portfolio.created_at,
        holdings_count=0,
    )


@router.get("", response_model=PortfolioListResponse)
def list_portfolios(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    base_query = select(Portfolio).where(Portfolio.user_id == current_user.id)
    total = db.scalar(select(func.count()).select_from(base_query.subquery())) or 0

    rows = db.scalars(base_query.order_by(Portfolio.created_at.desc()).offset(offset).limit(limit)).all()

    portfolio_ids = [row.id for row in rows]
    holding_counts: dict[int, int] = {}
    if portfolio_ids:
        counts_rows = db.execute(
            select(PortfolioHolding.portfolio_id, func.count(PortfolioHolding.id))
            .where(PortfolioHolding.portfolio_id.in_(portfolio_ids))
            .group_by(PortfolioHolding.portfolio_id)
        ).all()
        holding_counts = {portfolio_id: count for portfolio_id, count in counts_rows}

    return PortfolioListResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=[
            PortfolioPublic(
                id=row.id,
                name=row.name,
                created_at=row.created_at,
                holdings_count=holding_counts.get(row.id, 0),
            )
            for row in rows
        ],
    )


@router.delete("/{portfolio_id}", response_model=MessageResponse)
def delete_portfolio(
    portfolio_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    portfolio = _get_user_portfolio_or_404(db, portfolio_id, current_user.id)
    db.delete(portfolio)
    db.commit()
    return MessageResponse(message="Portfolio deleted successfully")


@router.get("/{portfolio_id}/holdings", response_model=PortfolioHoldingsResponse)
def list_holdings(
    portfolio_id: int,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_user_portfolio_or_404(db, portfolio_id, current_user.id)

    base_query = select(PortfolioHolding).where(PortfolioHolding.portfolio_id == portfolio_id)
    total = db.scalar(select(func.count()).select_from(base_query.subquery())) or 0
    rows = db.scalars(
        base_query.order_by(PortfolioHolding.id.asc()).offset(offset).limit(limit)
    ).all()

    return PortfolioHoldingsResponse(
        portfolio_id=portfolio_id,
        total=total,
        limit=limit,
        offset=offset,
        items=[
            HoldingPublic(
                id=row.id,
                ticker=row.ticker,
                quantity=float(row.quantity),
                avg_cost=_to_float_or_none(row.avg_cost),
            )
            for row in rows
        ],
    )


@router.post("/{portfolio_id}/holdings", response_model=HoldingPublic, status_code=status.HTTP_201_CREATED)
def add_holding(
    portfolio_id: int,
    payload: HoldingAddRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_user_portfolio_or_404(db, portfolio_id, current_user.id)

    stock = _resolve_stock_from_input(db, payload.ticker)
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticker not found. Use a valid ticker or company name.",
        )

    normalized_ticker = stock.ticker

    holding = PortfolioHolding(
        portfolio_id=portfolio_id,
        ticker=normalized_ticker,
        quantity=payload.quantity,
        avg_cost=payload.avg_cost,
    )
    db.add(holding)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ticker already exists in this portfolio",
        ) from exc

    db.refresh(holding)
    return HoldingPublic(
        id=holding.id,
        ticker=holding.ticker,
        quantity=float(holding.quantity),
        avg_cost=_to_float_or_none(holding.avg_cost),
    )


@router.delete("/{portfolio_id}/holdings/{ticker}", response_model=MessageResponse)
def remove_holding(
    portfolio_id: int,
    ticker: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_user_portfolio_or_404(db, portfolio_id, current_user.id)

    normalized_ticker = ticker.strip().upper()
    holding = db.scalar(
        select(PortfolioHolding).where(
            PortfolioHolding.portfolio_id == portfolio_id,
            PortfolioHolding.ticker == normalized_ticker,
        )
    )
    if not holding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Holding not found")

    db.delete(holding)
    db.commit()
    return MessageResponse(message="Holding removed successfully")
