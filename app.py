

from flask import Flask, render_template, redirect, request, jsonify
import yfinance as yf
import sqlite3
import pandas as pd
from datetime import timedelta

app = Flask(__name__)

def get_user_holdings(userID):
    """Retrieve stock holdings for a specific user"""
    db = sqlite3.connect('portfolio.db')
    cursor = db.cursor()

    # Execute the SELECT query with a WHERE clause to filter by user_id
    cursor.execute("SELECT stock_symbol, quantity FROM holdings WHERE user_id = ?", (userID,))

    # Fetch all the rows returned by the query
    holdings = cursor.fetchall()

    # Close the database connection
    db.close()

    return holdings

def combine_individual_stock_totals(userID): # NOTE: i grabbed this code from calculate_portfolio_value
    """This function takes in the list of stocks a user owns, and gets the totals of each stock owned"""
    stockList = get_user_holdings(userID)
    stock_totals = {} # calculate how much of each stock is owned so we can grab value of a single stock all at once instead of at different times.
    #                   Example: stockList = [('AAPL', 5), ('AAPL', 5)] will become [('AAPL', 10)] so we can calculate Apple stock value all at once.
    # Keep track of stocks in a dictionary and iterate through stockList-- updating the total quantity of each stock owned in the dictionary
    for stock, quantity in stockList:
        stock_totals[stock] = stock_totals.get(stock, 0) + quantity
    
    updatedStockList = [(stock, quantity) for stock, quantity in stock_totals.items()]
    return updatedStockList


def get_portfolio_value_history(userID):
    """Grabs history of every single stock for the past 24 hours, and adds up all stock values"""
    #Initialize list with 388 "0" elements since we are epecting 388 total values from (9:30am to 4:00pm) (not inclusive) if we sample every minute 
    portfolioValue_everyMinute_past24hrs = []
    stockList = combine_individual_stock_totals(userID)

    for stock, quantity in stockList:
        # Define the ticker symbol
        ticker_symbol = stock
        # Retrieve historical stock price data for the last day
        ticker = yf.Ticker(ticker_symbol)
        historical_data = ticker.history(period='1d', interval='1m')
     
        timestamps = historical_data.index.tolist()
        prices = historical_data['Close'].tolist()
        # portfolio_value_per_minute = [quantity * price for price in prices]
        portfolio_value_per_minute = [quantity * price for price in prices]
        # print(f'last stock value: {portfolio_value_per_minute[-1]}')
        # print(len(portfolio_value_per_minute))
        # for value in range(len(timestamps)):
        # print(f'length of timestamps = {len(timestamps)}')
        # print(f'length of portfolio value entries = {len(portfolioValue_everyMinute_past24hrs)}')
        if len(timestamps) - 1 == len(portfolioValue_everyMinute_past24hrs):
            for value in range(len(timestamps) - 1):
                portfolioValue_everyMinute_past24hrs[value] += (portfolio_value_per_minute[value])
        else:
            portfolioValue_everyMinute_past24hrs.extend(portfolio_value_per_minute)
    portfolioValue_everyMinute_past24hrs.extend([portfolio_value_per_minute[-1]])
    # print(f'timestamps is equal to {timestamps} and it has a length of {len(timestamps)}')
    # print(f'timestamps has a length of {len(timestamps)}')
    # print(f'portfolioValue_everyMinute_past24hrs is equal to {portfolioValue_everyMinute_past24hrs} and it has a length of {len(portfolioValue_everyMinute_past24hrs)}')
    #print(f'portfolioValue_everyMinute_past24hrs has a length of {len(portfolioValue_everyMinute_past24hrs)}')
    return timestamps, portfolioValue_everyMinute_past24hrs


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != 'admin' or request.form['password'] != 'admin':
            error = 'Invalid username or password. Please try again.'
        else:
            return redirect(url_for('login')) 
    return render_template('login.html', error=error)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/get_portfolio_value')
def get_portfolio_value():
    userID = 999  # TODO: Replace with the actual user ID
    timestamps, portfolio_values = get_portfolio_value_history(userID)

    # print(f"timestamps: {timestamps}")
    # print(f"portfolio_values: {portfolio_values}")


    # Convert timestamps to datetime objects with timezone offset adjustment
    x_axis_values = [pd.to_datetime(ts) - timedelta(hours=4) for ts in timestamps]
    data = [{'x': x_axis_values, 'y': portfolio_values}]

    return jsonify({'x': x_axis_values[:-1], 'y': portfolio_values[:-1]})
    # return jsonify(data)

    
if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
