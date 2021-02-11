# helper functions will go here
import requests

symbol_url = "https://symbol-search.tradingview.com/symbol_search/?text={}"

def get_market_exchange(ticker):
    r = requests.get(symbol_url.format(ticker))
    for el in r.json():
        if el['exchange'] in ['NYSE', 'NASDAQ', 'BINANCE', 'BITTREX']:
            if el['symbol'] == ticker.upper():
                response = el
    screener = response['type']
    exc = response['exchange']
    if exc in ['NYSE', 'NASDAQ']:
        screener = "america"
    return(screener, exc)
