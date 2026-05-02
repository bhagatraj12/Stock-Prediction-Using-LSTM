"""
main.py - FastAPI Application Entry Point

This is the main file that runs the Stock Prediction API server.
It loads the LSTM model and registers all route handlers.

Run with: py -3.11 -m uvicorn main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from model_loader import StockPredictor

# Import all route modules
from routes.auth_routes import router as auth_router
from routes.predict_routes import router as predict_router
from routes.history_routes import router as history_router
from routes.watchlist_routes import router as watchlist_router
from routes.analytics_routes import router as analytics_router

# Create the FastAPI app
app = FastAPI(title="Stock Prediction API", version="1.0.0")

# Allow the React frontend (localhost:5173) to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load the LSTM model once at startup (shared across all requests)
predictor = StockPredictor()

# Register all route files
app.include_router(auth_router)
app.include_router(predict_router)
app.include_router(history_router)
app.include_router(watchlist_router)
app.include_router(analytics_router)


@app.get("/")
def root():
    return {"message": "Stock Prediction API is running"}
