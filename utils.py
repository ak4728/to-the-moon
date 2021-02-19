# helper functions will go here
import requests, random, json

with open('config.json') as json_file:
    json_data = json.load(json_file)

def get_market_exchange(ticker):
    r = requests.get(json_data['symbol_url'].format(ticker))
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


def get_ticker_price(ticker):
    if "usd" in ticker:
        ticker = ticker.split("usd")[0]+"-usd"
    r = requests.get(json_data['api_url'].format(ticker.upper()))
    return(r.json()['quoteResponse']['result'][0]['regularMarketPrice'])