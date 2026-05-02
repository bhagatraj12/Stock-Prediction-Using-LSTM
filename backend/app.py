import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.preprocessing import MinMaxScaler
from keras.models import load_model

lstm_model = load_model('long_model_lstm.h5')

def predict_next_day_price(ticker="GOOGL"):
    """
   Returns the predicted closing price for the next day
   using the pre-trained LSTM model and last 100 days of data
    """
    #Fetch recent 6 months of stock data
    stock_data = yf.download(ticker, period='6mo')
    # Keep only the closing prices
    closing = stock_data[['Close']].copy()
    
    #Normalize the data for LSTM
    scaler = MinMaxScaler(feature_range=(0,1))
    scaled_close = scaler.fit_transform(closing)
    
    #Prepare input array for model: last 100 days
    last_100 = scaled_close[-100:]
    x_input = last_100.reshape(1,100,1)
    
    #Now predict the next day's
    next_scaled = lstm_model.predict(x_input)
    next_price = scaler.inverse_transform(next_scaled)
    
    #Return as single float value
    return next_price[0][0]


if __name__ == "__main__":
    stock_symbol = "GOOGL"
    prediction = predict_next_day_price(stock_symbol)
    print(f"Next Day Predicted Closing Price for {stock_symbol}:${prediction:.2f}")