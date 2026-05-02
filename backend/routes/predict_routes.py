"""
predict_routes.py - Stock Prediction API Endpoint

POST /api/predict - Predict next-day closing price using the LSTM model
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db, Prediction
from auth import get_current_user

router = APIRouter(prefix="/api", tags=["Prediction"])


class PredictRequest(BaseModel):
    symbol: str


@router.post("/predict")
def predict_stock(req: PredictRequest, user=Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Takes a stock symbol, runs it through the LSTM model,
    and returns the predicted price + chart data + company info.
    Also saves the prediction to the database.
    """
    from main import predictor  # Import the shared model instance

    symbol = req.symbol.upper().strip()
    if not symbol:
        raise HTTPException(status_code=400, detail="Stock symbol is required")

    try:
        result = predictor.predict_next_day(symbol)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

    # Save prediction to database
    prediction_record = Prediction(
        user_id=user["user_id"],
        symbol=symbol,
        company_name=result["company_info"].get("company_name", symbol),
        predicted_price=result["predicted_price"],
        current_price=result["current_price"],
    )
    db.add(prediction_record)
    db.commit()

    return {
        "symbol": symbol,
        "predicted_price": result["predicted_price"],
        "current_price": result["current_price"],
        "prediction_date": result["prediction_date"],
        "chart_data": result["chart_data"],
        "company_info": result["company_info"],
    }
