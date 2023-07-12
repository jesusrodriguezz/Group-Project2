
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from datetime import datetime, timedelta

def graph_individual_stock_info(stockName):
    # Define the ticker symbol
    ticker_symbol = 'AAPL' # TODO: Replace APPL with stockName to let stock info be gathered for any stock.

    # Create empty lists to store data
    timestamps = []
    prices = []

    # Retrieve historical stock price data for the last day
    end = datetime.now()
    start = end - timedelta(days=1)
    ticker = yf.Ticker(ticker_symbol)
    historical_data = ticker.history(start=start, end=end, interval='1m')
    timestamps = historical_data.index.tolist()
    prices = historical_data['Close'].tolist()

    # Function to update the graph with new data
    def update_graph(i):
        # Retrieve the latest intraday price data
        latest_data = ticker.history(period='1d', interval='1m').tail(1)
        
        # Extract the closing price and timestamp of the latest data point
        latest_timestamp = latest_data.index[0]
        latest_price = latest_data['Close'][0]

        # Check if new data is available
        if latest_timestamp not in timestamps:
            # Append the latest data to the lists
            timestamps.append(latest_timestamp)
            prices.append(latest_price)

        # Limit the number of data points to display on the graph
        max_data_points = 1440  # Display data points for the last day
        timestamps_display = timestamps[-max_data_points:]
        prices_display = prices[-max_data_points:]

        # Plot the graph with updated data
        ax.clear()

        # Check if market is open or closed
        if len(timestamps_display) > 0 and timestamps_display[-1].date() != datetime.today().date():
            ax.plot(timestamps_display[:-1], prices_display[:-1], 'b-')  # Exclude the last point
            ax.plot(timestamps_display[-2:], prices_display[-2:], 'b.-')  # Separate line for market close and open
        else:
            ax.plot(timestamps_display, prices_display, 'b-')
        

        ax.plot(timestamps_display, prices_display)
        ax.set_xlabel('Time (EST)')
        ax.set_ylabel('Stock Price ($ USD)')
        ax.set_title(f'Real-Time Stock Price ({ticker_symbol})\nCurrent Price: {latest_price}')
        ax.tick_params(axis='x', rotation=45)

    # Set up the figure and axis for the graph
    fig, ax = plt.subplots()

    # Set the animation update interval (in milliseconds)
    update_interval = 60000  # 1 minute

    # Create the animation
    ani = animation.FuncAnimation(fig, update_graph, interval=update_interval, cache_frame_data=False)

    # Display the graph
    plt.show()


import sqlite3 # to use a database

def setup_portfolio():
    """Creates a holdings table if it doesn't exist yet"""
    # Create connection to portfolio database
    db = sqlite3.connect('portfolio.db')
    c = db.cursor()

    # Create leaderboard table inside our database if it doesn't exist yet   
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

def calculate_portfolio_value(userID):
    holdings = get_user_holdings(userID)
    # TODO: Finish implementing method to grab stock data from holdings table in database and sum total value of portfolio


def graph_portfolio_value_history(userID):
    # TODO: using calculate_portfolio_value, graph realtime portfolio value (1-day history maybe?)
    return 0


# Code to get most updated stock value
stockName = 'AMD'
stockData = yf.Ticker(stockName)
todayData = stockData.history(period='1d')
print(todayData['Close'][0]) # prints out 

