"""
model_loader.py - LSTM Model Integration

This module:
  - Loads the pre-trained LSTM model (.h5 file)
  - Fetches stock data from Yahoo Finance
  - Normalizes data using MinMaxScaler
  - Predicts the next-day closing price
  - Returns chart data and company metrics
"""

import yfinance as yf
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import load_model
import os

MODEL_PATH = os.path.join(os.path.dirname(__file__), "long_model_lstm.h5")


class StockPredictor:
    def __init__(self):
        """Load the LSTM model once when the server starts."""
        self.model = load_model(MODEL_PATH)

    def _get_recent_data(self, symbol: str, period: str = "1y"):
        """Download historical stock data from Yahoo Finance."""
        data = yf.download(symbol, period=period, progress=False)
        if data.empty:
            raise ValueError(f"No data found for symbol: {symbol}")
        return data

    def predict_next_day(self, symbol: str) -> dict:
        """
        Main prediction function. Returns a dictionary with:
          - predicted_price: float
          - current_price: float
          - chart_data: list of {day, price} for the last 100 days
          - company_info: dict of key financial metrics
        """
        # Fetch full stock data
        full_data = self._get_recent_data(symbol)
        close_data = full_data[["Close"]].copy()

        # Normalize closing prices (scale between 0 and 1 for the LSTM)
        scaler = MinMaxScaler()
        scaled_prices = scaler.fit_transform(close_data)

        # Take last 100 days as input to the model
        last_100 = scaled_prices[-100:].reshape(1, 100, 1)

        # Run prediction through the LSTM model
        prediction_scaled = self.model.predict(last_100, verbose=0)
        predicted_price = float(scaler.inverse_transform(prediction_scaled)[0][0])

        # Get the current (latest) closing price
        current_price = float(close_data.iloc[-1].values[0])

        # Calculate the next trading day (skip weekends)
        from datetime import datetime, timedelta
        last_date = full_data.index[-1]
        # Convert to Python datetime if it's a pandas Timestamp
        if hasattr(last_date, 'to_pydatetime'):
            last_date = last_date.to_pydatetime()
        next_day = last_date + timedelta(days=1)
        # Skip Saturday (5) and Sunday (6)
        while next_day.weekday() >= 5:
            next_day = next_day + timedelta(days=1)
        prediction_date = next_day.strftime("%B %d, %Y")  # e.g. "March 12, 2026"

        # Prepare chart data: last 100 days of closing prices as a list
        prices_list = close_data.values[-100:].flatten().tolist()
        chart_data = [
            {"day": i + 1, "price": round(p, 2)}
            for i, p in enumerate(prices_list)
        ]
        # Add the predicted point
        chart_data.append({"day": 101, "price": round(predicted_price, 2), "predicted": True})

        # Fetch company info from Yahoo Finance
        company_info = self._get_company_info(symbol)

        return {
            "predicted_price": round(predicted_price, 2),
            "current_price": round(current_price, 2),
            "prediction_date": prediction_date,
            "chart_data": chart_data,
            "company_info": company_info,
        }

    def _get_company_info(self, symbol: str) -> dict:
        """Fetch key financial data about the company."""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            return {
                "company_name": info.get("shortName", symbol),
                "sector": info.get("sector", "N/A"),
                "day_high": info.get("dayHigh", "N/A"),
                "day_low": info.get("dayLow", "N/A"),
                "volume": info.get("volume", "N/A"),
                "week_52_high": info.get("fiftyTwoWeekHigh", "N/A"),
                "week_52_low": info.get("fiftyTwoWeekLow", "N/A"),
                "fifty_day_avg": info.get("fiftyDayAverage", "N/A"),
                "two_hundred_day_avg": info.get("twoHundredDayAverage", "N/A"),
                "market_cap": info.get("marketCap", "N/A"),
            }
        except Exception:
            return {"company_name": symbol}
