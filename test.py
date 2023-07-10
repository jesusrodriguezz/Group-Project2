import requests
    
key = 'W626K7TKR5CCR5UT'
url = 'https://www.alphavantage.co/query?function=MARKET_STATUS&apikey=demo'
response = requests.get(url)
data = response.json()

print(response)
print(data)
