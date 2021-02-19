# helper functions will go here
import requests

symbol_url = "https://symbol-search.tradingview.com/symbol_search/?text={}"

def get_market_exchange(ticker):
    r = requests.get(symbol_url.format(ticker))
    for el in r.json():
        if el['symbol'] == ticker.upper():
            if el['exchange'] in ['NYSE', 'NASDAQ', 'BINANCE', 'BITTREX', "ARCA"]:
                response = el
            else:
                print(el['symbol'])
    if response['exchange'] in ['NYSE', 'NASDAQ', 'ARCA']:
        screener = "america"
    else:
        screener = "crypto"
    return(screener, response['exchange'])
