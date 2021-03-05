# helper functions will go here
import requests, random, json
import pandas as pd
import snscrape.modules.twitter as sntwitter
from datetime import datetime, timedelta, timezone
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


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
    if "USD" in ticker.upper():
        ticker = ticker.upper().split("USD")[0]+"-USD"
    elif ticker.upper() == 'IXIC':
        ticker = "%5EIXIC"
    r = requests.get(json_data['api_url'].format(ticker.upper()))
    return(r.json()['quoteResponse']['result'][0]['regularMarketPrice'])



def labeler(f):
    if f > 0.05:
        lbl = 'pos'
    elif f < -0.05:
        lbl = 'neg'
    else:
        lbl = 'neu'
    return (lbl)


def get_sentiment(keyword="TSLA", dollar=True):
    keyword = keyword.upper()
    if dollar:
        keyword = "$" + keyword
    if "USDT" in keyword:
        keyword = keyword.rstrip("USDT")
    # Configuration
    tweets = pd.DataFrame(columns=['id', 'date', 'content'])
    timenow = (datetime.now(timezone.utc) - timedelta(hours=8))
    analyzer = SentimentIntensityAnalyzer()

    # Tweets within the last hour
    for i, tweet in enumerate(sntwitter.TwitterSearchScraper(
            keyword + ' lang:en since:2021-03-04 -filter:links -filter:replies').get_items()):
        date = (tweet.date - timedelta(hours=7))
        if date < timenow:
            break
        tweets.loc[i] = [tweet.id, tweet.date, tweet.content]

    # Data engineering
    tweets['compound'] = [analyzer.polarity_scores(x)['compound'] for x in tweets['content']]
    tweets['neg'] = [analyzer.polarity_scores(x)['neg'] for x in tweets['content']]
    tweets['neu'] = [analyzer.polarity_scores(x)['neu'] for x in tweets['content']]
    tweets['pos'] = [analyzer.polarity_scores(x)['pos'] for x in tweets['content']]
    tweets['label'] = [x for x in map(labeler, tweets['compound'])]

    pos = tweets[tweets['label'] == 'pos'].count()['pos']
    neg = tweets[tweets['label'] == 'neg'].count()['neg']
    neu = tweets[tweets['label'] == 'neu'].count()['neu']

    return (tweets, pos, neg, neu)


def sentiment_response(stock="TSLA"):
    tweets, pos, neg, neu = get_sentiment(stock, dollar=True)
    count = len(tweets['id'])
    pos_rate = pos / len(tweets['id'])
    print(tweets)
    image = "https://www.shareicon.net/data/512x512/2015/09/04/95557_twitter_512x512.png"
    embed = discord.Embed(color=1146986)
    embed.set_thumbnail(url=image)
    embed.add_field(name="{}".format(stock),
                    value='> Positive Tweets: {}\n> Negative Tweets: {}\n> Neutral Tweets: {}\n> Positivity Rate: {}'.format(
                        pos,
                        neg,
                        neu,
                        pos_rate), inline=False)
    hook.send(embed=embed)

