"""
analytics_routes.py - Analytics & Stats API

GET /api/analytics - Returns aggregated prediction stats for the user
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db, Prediction
from auth import get_current_user

router = APIRouter(prefix="/api", tags=["Analytics"])


@router.get("/analytics")
def get_analytics(user=Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Returns analytics data for the logged-in user:
    - Total predictions made
    - Most predicted stock
    - Average predicted price
    - Recent predictions for charting
    """
    user_id = user["user_id"]

    # Total number of predictions
    total = db.query(Prediction).filter(Prediction.user_id == user_id).count()

    # Most predicted stock symbol
    most_predicted = (
        db.query(Prediction.symbol, func.count(Prediction.symbol).label("count"))
        .filter(Prediction.user_id == user_id)
        .group_by(Prediction.symbol)
        .order_by(func.count(Prediction.symbol).desc())
        .first()
    )

    # Get last 20 predictions for chart display
    recent = (
        db.query(Prediction)
        .filter(Prediction.user_id == user_id)
        .order_by(Prediction.created_at.desc())
        .limit(20)
        .all()
    )

    recent_data = [
        {
            "symbol": p.symbol,
            "predicted_price": p.predicted_price,
            "current_price": p.current_price,
            "date": p.created_at.strftime("%Y-%m-%d"),
        }
        for p in reversed(recent)  # oldest first for chart
    ]

    # Per-stock breakdown
    stock_breakdown = (
        db.query(
            Prediction.symbol,
            func.count(Prediction.id).label("count"),
            func.avg(Prediction.predicted_price).label("avg_predicted"),
        )
        .filter(Prediction.user_id == user_id)
        .group_by(Prediction.symbol)
        .all()
    )

    breakdown = [
        {
            "symbol": s.symbol,
            "count": s.count,
            "avg_predicted": round(float(s.avg_predicted), 2),
        }
        for s in stock_breakdown
    ]

    return {
        "total_predictions": total,
        "most_predicted_stock": most_predicted[0] if most_predicted else "N/A",
        "most_predicted_count": most_predicted[1] if most_predicted else 0,
        "recent_predictions": recent_data,
        "stock_breakdown": breakdown,
    }
