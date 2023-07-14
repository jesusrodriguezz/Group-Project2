from flask import Flask, render_template, redirect, url_for, request, jsonify
from portfolio import setup_portfolio, update_holdings, get_user_holdings, view_holdings_table, graph_portfolio_value_history, get_portfolio_value_history,calculate_portfolio_value, get_stock_value
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.dates as mdates
import pandas as pd
from datetime import datetime, timedelta
import sqlite3

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
    portfolioValue_everyMinute_past24hrs = []
    stockList = combine_individual_stock_totals(userID)

    if not stockList:
        return [], []

    for stock, quantity in stockList:
        # Define the ticker symbol
        ticker_symbol = stock
        # Retrieve historical stock price data for the last day
        ticker = yf.Ticker(ticker_symbol)
        historical_data = ticker.history(period='1d', interval='1m')

        print(f"Stock: {stock}")
        print(f"Length of Historical Data: {len(historical_data)}")

        timestamps = historical_data.index.tolist()
        prices = historical_data['Close'].tolist()
        portfolio_value_per_minute = [quantity * price for price in prices]
        portfolioValue_everyMinute_past24hrs.extend(portfolio_value_per_minute)
    
    return timestamps, portfolioValue_everyMinute_past24hrs

# Create the active_users table
def create_table():
    con = sqlite3.connect('users.db')
    cursor = con.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS active_users (
        id INTEGER PRIMARY KEY,
        username TEXT,
        password TEXT
    )''')

    con.commit()
    con.close()

# Insert a user into the active_users table
def create_user(username, password):
    con = sqlite3.connect('users.db')
    cursor = con.cursor()

    cursor.execute("SELECT id FROM active_users WHERE username = ?", (username,))
    existing_user = cursor.fetchone()
    #this should fix the bug of adding multiple users with the same username
    if existing_user:
        return "Username already exist, try a different username"

    cursor.execute("INSERT INTO active_users (username, password) VALUES (?, ?)", (username, password))

    con.commit()
    con.close()

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/get_portfolio_value')
def get_portfolio_value():
    userID = 2 # TODO: Replace with the actual user ID
    timestamps, portfolio_values = get_portfolio_value_history(userID)

    print(f"timestamps: {timestamps}")
    # print(f"portfolio_values: {portfolio_values}")


    # Convert timestamps to datetime objects with timezone offset adjustment
    x_axis_values = [pd.to_datetime(ts) - timedelta(hours=4) for ts in timestamps]
    data = [{'x': x_axis_values, 'y': portfolio_values}]

    return jsonify({'x': x_axis_values[:-1], 'y': portfolio_values[:-1]})
    #return jsonify(data)


# Route for users
@app.route('/users', methods=['GET', 'POST'])
def get_users():
    con = sqlite3.connect('users.db')
    cursor = con.cursor()

    cursor.execute("SELECT id, username FROM active_users")
    users = cursor.fetchall()

    con.close()

    return render_template('users.html', users=users)
# deletes users, I thought maybe this could be helpful
def delete_user(username):
    con = sqlite3.connect('users.db')
    cursor = con.cursor()

    cursor.execute("DELETE FROM active_users WHERE username = ?", (username,))

    con.commit()
    con.close()

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        con = sqlite3.connect('users.db')
        cursor = con.cursor()

        name = request.form['username']
        password = request.form['password']

        # Check if the username already exists in the database
        query = "SELECT * FROM active_users WHERE username = ?"
        cursor.execute(query, (name,))
        result = cursor.fetchone()
        if result is not None:
            error = "Username already exists. Please choose a different username."
        else:
            # Insert the new user into the active_users table
            query = "INSERT INTO active_users (username, password) VALUES (?, ?)"
            cursor.execute(query, (name, password))
            con.commit()

            # Redirect the user to the login page after successful registration
            return redirect(url_for('login'))

    return render_template('register.html', error=error)



# Route for login
@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        con = sqlite3.connect('users.db')
        cursor = con.cursor()

        name = request.form['name']
        password = request.form['password']

        query = "SELECT username, password FROM active_users WHERE username= ? and password= ?"
        cursor.execute(query, (name, password))

        results = cursor.fetchall()

        if len(results) == 0:
            error = "Invalid username or password. Please try again."
        else:
            # Retrieve the required data for displaying on the home page
            userID = 2  # Replace with the actual user ID
            timestamps, portfolio_values = get_portfolio_value_history(userID)
            portfolio_total = calculate_portfolio_value(userID)

            # Pre-zip the data
            zipped_data = list(zip(timestamps, portfolio_values))

            # Pass the data to the home.html template
            return render_template('home.html', zipped_data=zipped_data, portfolio_total=portfolio_total)
    
    return render_template('login.html', error=error)

@app.route('/home')
def home():
    # Retrieve the required data for displaying on the home page
    userID = 2  # Replace with the actual user ID
    timestamps, portfolio_values = get_portfolio_value_history(userID)
    portfolio_total = calculate_portfolio_value(userID)

    # Pre-zip the data
    zipped_data = list(zip(timestamps, portfolio_values))

    # Pass the data to the home.html template
    return render_template('home.html', zipped_data=zipped_data, portfolio_total=portfolio_total)


# Run program
if __name__ == '__main__':
    #create_user("bob101", "pass101")

    #delete_user("bob101")
    #setup_portfolio()
    #create_table()
    graph_portfolio_value_history(1)
    get_portfolio_value_history(1)
    print(get_stock_value('AAPL'))
    print(get_stock_value('AMD'))

    update_holdings(1, 'AAPL', 10, get_stock_value('AAPL'))
    print(get_user_holdings(1))
    print(combine_individual_stock_totals(1))
    print(calculate_portfolio_value(1))


    graph_portfolio_value_history(2)
    get_portfolio_value_history(2)
    print(get_stock_value('AAPL'))
    print(get_stock_value('AMD'))

    update_holdings(2, 'AAPL', 5, get_stock_value('AAPL'))
    print(get_user_holdings(2))
    #print(combine_individual_stock_totals(2))
    print(calculate_portfolio_value(2))

    app.run(debug=True, host="0.0.0.0")

