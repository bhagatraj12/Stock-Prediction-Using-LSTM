"""
watchlist_routes.py - Watchlist CRUD API

GET    /api/watchlist          - Get user's saved stocks
POST   /api/watchlist          - Add a stock to watchlist
DELETE /api/watchlist/{symbol} - Remove a stock from watchlist
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db, Watchlist
from auth import get_current_user
import yfinance as yf

router = APIRouter(prefix="/api", tags=["Watchlist"])


class WatchlistRequest(BaseModel):
    symbol: str


@router.get("/watchlist")
def get_watchlist(user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Returns all stocks in the user's watchlist."""
    items = (
        db.query(Watchlist)
        .filter(Watchlist.user_id == user["user_id"])
        .order_by(Watchlist.added_at.desc())
        .all()
    )
    return [
        {
            "id": w.id,
            "symbol": w.symbol,
            "company_name": w.company_name,
            "added_at": w.added_at.strftime("%Y-%m-%d"),
        }
        for w in items
    ]


@router.post("/watchlist")
def add_to_watchlist(req: WatchlistRequest, user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Add a stock to the user's watchlist."""
    symbol = req.symbol.upper().strip()

    # Check if already in watchlist
    exists = (
        db.query(Watchlist)
        .filter(Watchlist.user_id == user["user_id"], Watchlist.symbol == symbol)
        .first()
    )
    if exists:
        raise HTTPException(status_code=400, detail="Stock already in watchlist")

    # Try to get the company name from Yahoo Finance
    try:
        ticker = yf.Ticker(symbol)
        company_name = ticker.info.get("shortName", symbol)
    except Exception:
        company_name = symbol

    item = Watchlist(
        user_id=user["user_id"],
        symbol=symbol,
        company_name=company_name,
    )
    db.add(item)
    db.commit()
    return {"message": f"{symbol} added to watchlist"}


@router.delete("/watchlist/{symbol}")
def remove_from_watchlist(symbol: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Remove a stock from the user's watchlist."""
    item = (
        db.query(Watchlist)
        .filter(Watchlist.user_id == user["user_id"], Watchlist.symbol == symbol.upper())
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Stock not found in watchlist")

    db.delete(item)
    db.commit()
    return {"message": f"{symbol.upper()} removed from watchlist"}
