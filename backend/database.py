"""
database.py - SQLite Database Setup using SQLAlchemy

Creates three tables:
  - users: stores registered user accounts
  - predictions: stores every prediction made by a user
  - watchlist: stores stocks a user has saved to watch
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# SQLite database file - will be auto-created in the backend/ folder
DATABASE_URL = "sqlite:///./stock_app.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ==================== DATABASE MODELS ====================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    symbol = Column(String, index=True)
    company_name = Column(String)
    predicted_price = Column(Float)
    current_price = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


class Watchlist(Base):
    __tablename__ = "watchlist"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    symbol = Column(String)
    company_name = Column(String)
    added_at = Column(DateTime, default=datetime.utcnow)


# Create all tables when this module is imported
Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency function - gives a database session to each request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
