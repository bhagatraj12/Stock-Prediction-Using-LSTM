"""
app.py - Stock Price Prediction Web Application
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, GRU, Dense, Dropout
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, timedelta
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


# ==============================================================
# FIX FOR OLD KERAS MODEL CONFIG
# ==============================================================

#class PatchedInputLayer(InputLayer):
    #def __init__(self, *args, **kwargs):
        #kwargs.pop("batch_shape", None)
        #kwargs.pop("optional", None)
        #super().__init__(*args, **kwargs)

# Chart storage folder
CHART_DIR = os.path.join("static", "charts")

# Create folder if it doesn't exist
os.makedirs(CHART_DIR, exist_ok=True)
# ==============================================================
# APP CONFIGURATION
# ==============================================================

app = Flask(__name__)
app.secret_key = "stock-prediction-minor-project-2024"

MODEL_PATH = os.path.join(os.path.dirname(__file__), "backend", "long_model_lstm.h5")

model = Sequential()

# Input + LSTM layer
model.add(LSTM(64, return_sequences=True, input_shape=(100,1)))

# Dropout
model.add(Dropout(0.2))

# GRU layer
model.add(GRU(64))

# Dropout
model.add(Dropout(0.2))

# Output layer
model.add(Dense(1))

# Load weights
model.load_weights(MODEL_PATH)


# ==============================================================
# DATABASE SETUP
# ==============================================================

import sqlite3

def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        symbol TEXT,
        company_name TEXT,
        current_price REAL,
        predicted_price REAL,
        prediction_date TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

# Run when app starts
init_db()

DB_PATH = "stock_app.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            company_name TEXT,
            predicted_price REAL,
            current_price REAL,
            prediction_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            company_name TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()


init_db()


# ==============================================================
# LOGIN REQUIRED DECORATOR
# ==============================================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login first.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


# ==============================================================
# LSTM PREDICTION
# ==============================================================

def predict_stock(symbol):

    full_data = yf.download(symbol, period="1y", progress=False)

    if full_data.empty:
        return None

    close_data = full_data[["Close"]].copy()

    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(close_data)

    last_100 = scaled[-100:].reshape(1, 100, 1)

    pred_scaled = model.predict(last_100, verbose=0)

    predicted_price = float(scaler.inverse_transform(pred_scaled)[0][0])
    current_price = float(close_data.iloc[-1].values[0])

    last_date = full_data.index[-1]

    if hasattr(last_date, "to_pydatetime"):
        last_date = last_date.to_pydatetime()

    next_day = last_date + timedelta(days=1)

    while next_day.weekday() >= 5:
        next_day = next_day + timedelta(days=1)

    prediction_date = next_day.strftime("%B %d, %Y")

    chart_filename = f"chart_{symbol}.png"
    chart_path = os.path.join(CHART_DIR, chart_filename)

    generate_chart(close_data, predicted_price, symbol, chart_path)

    company_info = get_company_info(symbol)

    return {
        "predicted_price": round(predicted_price, 2),
        "current_price": round(current_price, 2),
        "prediction_date": prediction_date,
        "chart_path": chart_path,
        "company_info": company_info,
    }


# ==============================================================
# CHART GENERATION
# ==============================================================

def generate_chart(close_data, predicted_price, symbol, save_path):

    prices = close_data.values[-100:]

    fig, ax = plt.subplots(figsize=(10, 4.5))

    fig.patch.set_facecolor("#0d1117")
    ax.set_facecolor("#161b22")

    ax.plot(prices, color="#00ffcc", linewidth=2, label="Last 100 Days Close")

    ax.scatter(
        100,
        predicted_price,
        color="#ff6b6b",
        s=100,
        zorder=5,
        label=f"Predicted: ${predicted_price:.2f}"
    )

    ax.plot(
        [99, 100],
        [prices[-1][0], predicted_price],
        linestyle="dashed",
        color="#ff6b6b",
        linewidth=1.5
    )

    ax.grid(True, color="#30363d", linestyle="--", linewidth=0.5)

    ax.legend(
        facecolor="#161b22",
        edgecolor="#30363d",
        labelcolor="#c9d1d9"
    )

    ax.tick_params(colors="#8b949e")

    ax.set_xlabel("Days", color="#8b949e")
    ax.set_ylabel("Price (USD)", color="#8b949e")

    ax.set_title(
        f"{symbol} - Price Trend & Prediction",
        color="#c9d1d9",
        fontsize=14
    )

    for spine in ax.spines.values():
        spine.set_color("#30363d")

    plt.tight_layout()

    plt.savefig(save_path, dpi=150, facecolor=fig.get_facecolor())

    plt.close()


# ==============================================================
# COMPANY INFO
# ==============================================================

def get_company_info(symbol):

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


# ==============================================================
# FORMAT LARGE NUMBERS
# ==============================================================

def format_number(n):

    if not isinstance(n, (int, float)):
        return n

    if n >= 1_000_000_000_000:
        return f"${n / 1_000_000_000_000:.2f}T"

    elif n >= 1_000_000_000:
        return f"${n / 1_000_000_000:.2f}B"

    elif n >= 1_000_000:
        return f"{n / 1_000_000:.2f}M"

    elif n >= 1_000:
        return f"{n / 1_000:.1f}K"

    return str(n)


# ==============================================================
# ROUTES
# ==============================================================

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        username = request.form["username"].strip()
        email = request.form["email"].strip()
        password = request.form["password"]

        conn = get_db()

        try:

            conn.execute(
                "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                (username, email, generate_password_hash(password))
            )

            conn.commit()

            user = conn.execute(
                "SELECT * FROM users WHERE email = ?", (email,)
            ).fetchone()

            session["user_id"] = user["id"]
            session["username"] = user["username"]

            flash("Account created successfully!", "success")

            return redirect(url_for("dashboard"))

        except sqlite3.IntegrityError:

            flash("Username or email already exists.", "error")

        finally:

            conn.close()

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"].strip()
        password = request.form["password"]

        conn = get_db()

        user = conn.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(user["password"], password):

            session["user_id"] = user["id"]
            session["username"] = user["username"]

            return redirect(url_for("dashboard"))

        else:

            flash("Invalid email or password.", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():

    result = None
    symbol = ""

    if request.method == "POST":

        symbol = request.form["symbol"].strip().upper()

        if symbol:

            result = predict_stock(symbol)

            if result:

                conn = get_db()

                conn.execute(
                    """INSERT INTO predictions
                       (user_id, symbol, company_name, predicted_price, current_price, prediction_date)
                       VALUES (?, ?, ?, ?, ?, ?)""",

                    (
                        session["user_id"],
                        symbol,
                        result["company_info"].get("company_name", symbol),
                        result["predicted_price"],
                        result["current_price"],
                        result["prediction_date"]
                    )
                )

                conn.commit()
                conn.close()

            else:

                flash(f"Could not find data for symbol: {symbol}", "error")

    return render_template("dashboard.html", result=result, symbol=symbol)

@app.route("/history")
@login_required
def history():

    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT symbol,
               company_name,
               current_price,
               predicted_price,
               prediction_date,
               created_at
        FROM predictions
        WHERE user_id = ?
        ORDER BY created_at DESC
    """, (session["user_id"],))

    predictions = cursor.fetchall()
    conn.close()

    return render_template("history.html", predictions=predictions)

@app.route("/analytics")
@login_required
def analytics():
    return render_template("analytics.html")


# WATCHLIST PAGE
@app.route("/watchlist")
@login_required
def watchlist():

    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Create table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            symbol TEXT
        )
    """)

    cursor.execute(
        "SELECT symbol FROM watchlist WHERE user_id=?",
        (session["user_id"],)
    )

    stocks = cursor.fetchall()

    conn.close()

    return render_template("watchlist.html", stocks=stocks)


# ADD STOCK TO WATCHLIST
@app.route("/watchlist/add", methods=["POST"])
@login_required
def watchlist_add():

    symbol = request.form.get("symbol")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO watchlist (user_id, symbol) VALUES (?, ?)",
        (session["user_id"], symbol)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("watchlist"))


@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html")


# ==============================================================
# RUN APP
# ==============================================================

if __name__ == "__main__":
    app.run(debug=True)