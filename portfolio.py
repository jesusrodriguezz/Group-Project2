# FILE:         portfolio.py
# AUTHOR:       Dimitri Avila      davila@g.hmc.edu
# DATE:         July 9th, 2023     last updated: July 12th, 2023
# DESCRIPTION:  The program below uses the Yahoo! Finance (yfinance) python package to access 
#               live stock data in order to allow for the creation of an investment portfolio.
#               We create a "holdings" table within the portfolio.db database to store all user
#               stock holdings infromation via their unique ID number. Helper functions gather stock
#               information in real time which allows for a user to add stocks to their portfolio and
#               ultimately visualize value trends within their portfolio through a graph that displays
#               their portfolio value over the past 24 hours.

import sqlite3 # to use a database
import yfinance as yf # to gather stock information
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.dates as mdates 
import pandas as pd
from datetime import datetime, timedelta

def setup_portfolio():
    """Creates a holdings table inside the portfolio.db database if it doesn't exist yet"""
    # Create connection to portfolio database
    db = sqlite3.connect('portfolio.db')
    c = db.cursor()

    # Create holdings table inside our database if it doesn't exist yet   
    c.execute('''
        CREATE TABLE IF NOT EXISTS holdings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            stock_symbol TEXT,
            quantity INTEGER,
            purchase_price REAL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # NOTE for above: the table "holdings" in the portfolio.db database will communicate with the "user" table Jesus is working on. This is done 
    #       using a foreign key and a reference to the "users" table. See below for more information...
    # FOREIGN KEY (user_id): Specifies that the user_id column in the "holdings" table will be a foreign key. 
    #                        It references the id column of another table.
    # REFERENCES users(id): Indicates that the foreign key column, user_id, from the "holdings" table references 
    #                       the id column in the "users" table. So the "users" table Jesus makes should have an "id" column for us to
    #                       match holdings information to the proper user.

    db.close()


def update_holdings(userID, stockName, stockQuantity, purchasePrice):
    """This function inputs new information into our holdings table within the portfolio.db database"""
    # Create connection to portfolio database
    db = sqlite3.connect('portfolio.db')
    c = db.cursor()
    c.execute("INSERT INTO holdings (user_id, stock_symbol, quantity, purchase_price) VALUES (?, ?, ?, ?)",
             (userID, stockName, stockQuantity, purchasePrice))
    db.commit()
    db.close()


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

def view_holdings_table():
    """View the contents of the holdings table (holdings content of every user)"""
    db = sqlite3.connect('portfolio.db')
    cursor = db.cursor()

    # Execute the SELECT query to fetch all rows from the holdings table
    cursor.execute("SELECT * FROM holdings")

    # Fetch all the rows returned by the query
    rows = cursor.fetchall()

    # Print the column names
    column_names = [description[0] for description in cursor.description]
    print(column_names)

    # Print each row of the holdings table
    for row in rows:
        print(row)

    # Close the database connection
    db.close()


# Code to get most updated stock value
def get_stock_value(stockName):
    """Get most recent value for specified stock"""
    stockData = yf.Ticker(stockName)
    todayData = stockData.history(period='1d', prepost = True)
   # print(todayData)
    # print(todayData['Close'][0]) # prints out current stock value
    return todayData['Close'][0]


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


def calculate_portfolio_value(userID):
    """Returns the value of all stocks in a user's portfolio based on current stock values"""
    stockList = get_user_holdings(userID)
    stock_totals = {} # calculate how much of each stock is owned so we can grab value of a single stock all at once instead of at different times.
    #                   Example: stockList = [('AAPL', 5), ('AAPL', 5)] will become [('AAPL', 10)] so we can calculate Apple stock value all at once.
    # Keep track of stocks in a dictionary and iterate through stockList-- updating the total quantity of each stock owned in the dictionary
    for stock, quantity in stockList:
        stock_totals[stock] = stock_totals.get(stock, 0) + quantity
    
    updatedStockList = [(stock, quantity) for stock, quantity in stock_totals.items()]

    portfolioValue = 0
    for stock, quantity in updatedStockList:
        stockValue = get_stock_value(stock) * quantity
        portfolioValue += stockValue
    return portfolioValue


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
        print(f'length of timestamps = {len(timestamps)}')
        print(f'portfolio val per minute past 24hrs = {len(portfolioValue_everyMinute_past24hrs)}')
        if len(timestamps) == len(portfolioValue_everyMinute_past24hrs):
            for value in range(len(timestamps)):
                portfolioValue_everyMinute_past24hrs[value] += (portfolio_value_per_minute[value])
        else:
            portfolioValue_everyMinute_past24hrs.extend(portfolio_value_per_minute)
    print(f'timestamps is equal to {timestamps} and it has a length of {len(timestamps)}')
    print(f'portfolioValue_everyMinute_past24hrs is equal to {portfolioValue_everyMinute_past24hrs} and it has a length of {len(portfolioValue_everyMinute_past24hrs)}')
    return timestamps, portfolioValue_everyMinute_past24hrs


def graph_portfolio_value_history(userID):
    """This function graphs the portfolio value live. Working! 7/13/2023 @ 8:57PST"""
    fig, ax = plt.subplots()
    line, = ax.plot([], [])
    timestamps, portfolio_values = get_portfolio_value_history(userID)

    def update_graph(i):
        timestamps, portfolio_values = get_portfolio_value_history(userID)
        
        # Convert timestamps to datetime objects with timezone offset adjustment
        x_axis_values = [pd.to_datetime(ts) - timedelta(hours=4) for ts in timestamps]
        
        line.set_data(x_axis_values, portfolio_values)
        ax.relim()
        ax.autoscale_view()
        ax.set_title(f'Investment Portfolio Performance\nCurrent Value: {calculate_portfolio_value(userID)}')
        ax.set_xlabel('Time (EST)')
        ax.set_ylabel('Portfolio Value')
        ax.tick_params(axis='x', rotation=45)

        # Adjust x-axis limits
        ax.set_xlim(x_axis_values[0], x_axis_values[-1] + timedelta(hours=4))

        return line,

    ani = animation.FuncAnimation(fig, update_graph, interval=1000)  # Update every second

    # Configure x-axis formatting
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))

    # plt.xlabel('Time (EST)')
    # plt.ylabel('Portfolio Value')
    # plt.xticks(rotation=45)
    # plt.tight_layout()
    plt.show()


graph_portfolio_value_history(999)
get_portfolio_value_history(999)
print(get_stock_value('AAPL'))
print(get_stock_value('AMD'))
