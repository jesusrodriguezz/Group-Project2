from flask import Flask, render_template, redirect, request, url_for, jsonify
import pandas as pd
import json
import plotly
import plotly.express as px
import yfinance as yf


app = Flask(__name__)
@app.route('/', methods=['GET', 'POST'])

def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != 'admin' or request.form['password'] != 'admin':
            error = 'Invalid username or password. Please try again.'
        else:
            return render_template('index.html') 
    return render_template('login.html', error=error)


@app.route('/login')
def logout():
    return redirect(url_for('login'))

@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/forum')
def forum():
    # Your forum route logic here
    return render_template('forum.html')


@app.route('/callback/<endpoint>')
def cb(endpoint):   
    if endpoint == "getStock":
        return gm(request.args.get('data'),request.args.get('period'),request.args.get('interval'))
    elif endpoint == "getInfo":
        stock = request.args.get('data')
        st = yf.Ticker(stock)
        return json.dumps(st.info)
    else:
        return "Bad endpoint", 400

# Return the JSON data for the Plotly graph
def gm(stock,period, interval):
    st = yf.Ticker(stock)
  
    # Create a line graph
    df = st.history(period=(period), interval=interval)
    df=df.reset_index()
    df.columns = ['Date-Time']+list(df.columns[1:])
    max = (df['Open'].max())
    min = (df['Open'].min())
    range = max - min
    margin = range * 0.05
    max = max + margin
    min = min - margin
    fig = px.area(df, x='Date-Time', y="Open",
        hover_data=("Open","Close","Volume"), 
        range_y=(min,max), template="seaborn" )

    # Create a JSON representation of the graph
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return graphJSON


@app.route('/callback/getInfo')
def get_stock_info():
    stock = request.args.get('data')
    st = yf.Ticker(stock)
    stock_info = st.info
    current_price = stock_info.get('currentPrice')
    net_change = stock_info.get('regularMarketChange')
    twenty_four_hour_change = stock_info.get('regularMarketChangePercent')
    return jsonify(current_price=current_price, net_change=net_change, twenty_four_hour_change=twenty_four_hour_change)

if __name__ == '__main__':
    app.run(debug=True)
