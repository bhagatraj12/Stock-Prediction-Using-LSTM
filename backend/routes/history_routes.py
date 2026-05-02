"""
history_routes.py - Prediction History API

GET /api/history - Get all past predictions for the logged-in user
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db, Prediction
from auth import get_current_user

router = APIRouter(prefix="/api", tags=["History"])


@router.get("/history")
def get_history(user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Return all predictions made by the current user, newest first."""
    predictions = (
        db.query(Prediction)
        .filter(Prediction.user_id == user["user_id"])
        .order_by(Prediction.created_at.desc())
        .all()
    )

    return [
        {
            "id": p.id,
            "symbol": p.symbol,
            "company_name": p.company_name,
            "predicted_price": p.predicted_price,
            "current_price": p.current_price,
            "date": p.created_at.strftime("%Y-%m-%d %H:%M"),
        }
        for p in predictions
    ]
