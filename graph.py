
import sqlite3 # to use a database
import yfinance as yf # to gather stock information
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
        max_data_points = 390  # Display data points for the last day since market open
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
    update_interval = 1000  # 1 second

    # Create the animation
    ani = animation.FuncAnimation(fig, update_graph, interval=update_interval, cache_frame_data=False)

    # Display the graph
    plt.show()

def setup_portfolio():
    """Creates a holdings table if it doesn't exist yet"""
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
    stockList = get_user_holdings(userID)
    stock_totals = {} # calculate how much of each stock is owned so we can grab value of a single stock all at once instead of at different times.
    #                   Example: stockList = [('AAPL', 5), ('AAPL', 5)] will become [('AAPL', 10)] so we can calculate Apple stock value all at once.
    # Keep track of stocks in a dictionary and iterate through stockList-- updating the total quantity of each stock owned in the dictionary
    for stock, quantity in stockList:
        stock_totals[stock] = stock_totals.get(stock, 0) + quantity
    
    updatedStockList = [(stock, quantity) for stock, quantity in stock_totals.items()]
    # print(updatedStockList)

    portfolioValue = 0
    for stock, quantity in updatedStockList:
        stockValue = get_stock_value(stock) * quantity
        portfolioValue += stockValue
    return portfolioValue


# Code to get most updated stock value
def get_stock_value(stockName):
    """Get most recent value for specified stock"""
    stockName = stockName
    stockData = yf.Ticker(stockName)
    todayData = stockData.history(period='1d', prepost = True)
    # print(todayData['Close'][0]) # prints out current stock value
    return todayData['Close'][0]


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


# Testing database:
# setup_portfolio()
# update_holdings(999, 'AAPL', 5, get_stock_value('AAPL'))
# print(get_user_holdings(999))
# view_holdings_table()
# portfolioValue = calculate_portfolio_value(999)
# print(portfolioValue)

# Function to update the graph with new data
def update_graph(stockName):
    # Retrieve the latest intraday price data
    latest_data = ticker.history(period='1d', interval='1m').tail(1)
    
    # Extract the closing price and timestamp of the latest data point
    latest_timestamp = latest_data.index[0]
    latest_price = get_stock_value(stockName)

    # Check if new data is available
    if latest_timestamp not in timestamps:
        # Append the latest data to the lists
        timestamps.append(latest_timestamp)
        prices.append(latest_price)

    # Limit the number of data points to display on the graph
    max_data_points = 390  # Display data points for the last day
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


# Define the ticker symbol
ticker_symbol = 'AAPL'

# Create empty lists to store data
timestamps = []
prices = []

# Retrieve historical stock price data for the last day

end = datetime.now() + timedelta(hours=3)
start = datetime.now().replace(hour=6, minute=30, second=0, microsecond=0)
ticker = yf.Ticker(ticker_symbol)
historical_data = ticker.history(start=start, end=end, interval='1m')
timestamps = historical_data.index.tolist()
prices = historical_data['Close'].tolist()

print(historical_data)

# Set up the figure and axis for the graph
fig, ax = plt.subplots()

# Set the animation update interval (in milliseconds)
update_interval = 1000  # 1 second

# Create the animation
ani = animation.FuncAnimation(fig, update_graph(ticker_symbol), interval=update_interval, cache_frame_data=False)

# Display the graph
# plt.show()

def update_portfolio_graph(userID):
    # Retrieve the latest portfolio value
    portfolio_value = calculate_portfolio_value(userID)

    # Append the portfolio value to the list
    portfolioValue_everyMinute_past24hrs = get_portfolio_value_history(userID)
    portfolioValue_everyMinute_past24hrs.append(portfolio_value)

    # Limit the number of data points to display on the graph
    max_data_points = 1440  # Display data points for the last day
    portfolio_values_display = portfolioValue_everyMinute_past24hrs[-max_data_points:]

    # Plot the graph with updated data
    ax.clear()
    ax.plot(portfolio_values_display)
    ax.set_xlabel('Time')
    ax.set_ylabel('Portfolio Value')
    ax.set_title('Real-Time Portfolio Value')


def get_portfolio_value_history(userID):
    """Grabs history of every single stock for the past 24 hours, and adds up all stock values"""
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
        portfolio_value_per_minute = [quantity * price for price in prices]
        portfolioValue_everyMinute_past24hrs.extend(portfolio_value_per_minute)
    print(timestamps)
    print(portfolioValue_everyMinute_past24hrs)
    return timestamps, portfolioValue_everyMinute_past24hrs

#get_portfolio_value_history(999)


def graph_portfolio_value_history(userID):
    # TODO: using calculate_portfolio_value, graph realtime portfolio value (1-day history maybe?)
    timestamps, portfolio_values = get_portfolio_value_history(userID)
    fig, ax = plt.subplots()
    ax.plot(timestamps, portfolio_values)
    ax.set_xlabel('Time (EST)')
    ax.set_ylabel('Portfolio Value')
    ax.set_title('Portfolio Value over Time')
    ax.tick_params(axis='x', rotation=45)
    plt.show()




graph_individual_stock_info('test')


# # Run the script continuously
# while True:
#     # Add AMD stock to the holdings table
#     update_holdings(999, 'AMD', 1, 114.58)

#     graph_portfolio_value_history(999)

#     # Wait for a specific interval before adding the next entry
#     time.sleep(60)  # Wait for 60 seconds




# # timestamps, portfolio_values = get_portfolio_value_history(userID)

# timestamps, portfolio_values = get_portfolio_value_history(999)

# fig, ax = plt.subplots()
# ax.plot(timestamps, portfolio_values)
# ax.set_xlabel('Time (EST)')
# ax.set_ylabel('Portfolio Value')
# ax.set_title('Portfolio Value over Time')
# ax.tick_params(axis='x', rotation=45)




# def graph_portfolio_value_realtime(userID):
#     portfolioValue_everyMinute_past24hrs = []
#     stockList = combine_individual_stock_totals(userID)

#     # Set up the figure and axis for the graph
#     fig, ax = plt.subplots()

#     # Set the animation update interval (in milliseconds)
#     update_interval = 1000  # 1 second

#     # Create the animation
#     ani = animation.FuncAnimation(fig, update_graph, interval=update_interval)

#     # Display the graph
#     plt.show()

