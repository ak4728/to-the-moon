# helper functions will go here
import requests

symbol_url = "https://symbol-search.tradingview.com/symbol_search/?text={}"

def get_market_exchange(ticker):
    r = requests.get(symbol_url.format(ticker))
    for el in r.json():
        if el['symbol'] == ticker.upper():
            if el['exchange'] in ['NYSE', 'NASDAQ', 'BINANCE', 'BITTREX', "NYSE ARCA & MKT"]:
                response = el
                if el['exchange'] == "NYSE ARCA & MKT":
                    response['exchange'] = "AMEX"
    if response['exchange'] in ['NYSE', 'NASDAQ', 'ARCA',"AMEX"]:
        screener = "america"
    else:
        screener = "crypto"
    return(screener, response['exchange'])
