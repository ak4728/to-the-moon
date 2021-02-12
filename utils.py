# helper functions will go here
import requests

symbol_url = "https://symbol-search.tradingview.com/symbol_search/?text={}"

def get_market_exchange(ticker):
    r = requests.get(symbol_url.format(ticker))
    for el in r.json():
        if el['symbol'] == ticker.upper():
            if el['exchange'] in ['NYSE', 'NASDAQ', 'BINANCE', 'BITTREX']:
                response = el
    if response['exchange'] in ['NYSE', 'NASDAQ']:
        screener = "america"
    else:
        screener = "crypto"
    return(screener, response['exchange'])
