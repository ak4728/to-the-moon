# helper functions will go here
import re
import asyncpraw
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
    time_now = (datetime.now(timezone.utc) - timedelta(hours=8))
    analyzer = SentimentIntensityAnalyzer()

    # Tweets within the last hour
    for i, tweet in enumerate(sntwitter.TwitterSearchScraper(
            keyword + ' lang:en since:' + time_now.strftime("%Y-%m-%d") + ' -filter:replies').get_items()):
        date = (tweet.date - timedelta(hours=7))
        if date < time_now:
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

async def get_reddit_stocks(sr_limit=100):
    reddit = asyncpraw.Reddit(
        client_id = json_data['client_id'],
        client_secret = json_data['client_secret'],
        user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36"
    )

    subreddit = await reddit.subreddit("wallstreetbets")

    df = {}
    async for submission in subreddit.hot(limit=sr_limit):
        df[submission.title] = submission.selftext

    regex = re.compile('[^a-zA-Z ]')
    word_dict = {}

    for (k, v) in df.items():
        title = k
        title = regex.sub('', title)
        title_words = title.split(' ')
        content = v
        content = regex.sub('', content)
        content_words = content.split(' ')
        words = title_words + content_words
        for x in words:
            if x in ['A', 'B', 'GO', 'ARE', 'ON', 'IT', 'ALL', 'NEXT', 'PUMP', 'AT', 'NOW', 'FOR', 'TD', 'CEO', 'AM', 'K', 'BIG', 'BY', 'LOVE', 'CAN', 'BE', 'SO', 'OUT', 'STAY', 'OR', 'NEW','RH','EDIT','ONE','ANY']:
                pass
            elif x in word_dict:
                word_dict[x] += 1
            else:
                word_dict[x] = 1
    wordbag = pd.DataFrame.from_dict(list(word_dict.items())).rename(columns = {0:"Term", 1:"Frequency"})
    tickers = pd.read_csv('tickers.csv').rename(columns = {"Symbol":"Term", "Name":"Company_Name"})
    stocks = pd.merge(tickers, wordbag, on="Term").sort_values(by="Frequency", ascending = False).head(20)
    return(stocks)