from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.routes.auth import get_current_user
from app.database.dependencies import get_db
from app.database.models import Stock, User, Watchlist, WatchlistItem

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
