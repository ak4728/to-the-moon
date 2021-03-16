import discord
import json, logging, requests

import asyncio

from tradingview_ta import TA_Handler, Interval, Exchange
from dhooks import Webhook
from discord.ext import commands, tasks
from utils import *
from pretty_help import PrettyHelp

# Configuration
logger = logging.getLogger('discord')
logger.setLevel(logging.ERROR)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)
# bot = commands.Bot(command_prefix='!')

with open('config.json') as json_file:
    json_data = json.load(json_file)

hook = Webhook(json_data['webhook_url'])

image = "https://nineplanets.org/wp-content/uploads/2019/09/moon.png"
user_agent = json_data['user_agent']
selected = json_data['default_int']

intervals = {"1-minute": Interval.INTERVAL_1_MINUTE,
             "5-minutes": Interval.INTERVAL_5_MINUTES,
             "15-minutes": Interval.INTERVAL_15_MINUTES,
             "1-hour": Interval.INTERVAL_1_HOUR,
             "4-hours": Interval.INTERVAL_4_HOURS,
             "1-day": Interval.INTERVAL_1_DAY,
             "1-week": Interval.INTERVAL_1_WEEK,
             "1-month": Interval.INTERVAL_1_MONTH,
             }

client = commands.Bot(command_prefix="!", help_command=PrettyHelp())  # discord.Client()


async def color_text(recommendation):
    if "BUY" in recommendation:
        rec_text = """```diff\n+{}```""".format(recommendation)
    elif "SELL" in recommendation:
        rec_text = """```diff\n-{}```""".format(recommendation)
    else:
        rec_text = """```fix\n{}```""".format(recommendation)
    return rec_text



async def get_ma_osc(embed, stock, method='ma'):
    method = method
    analyzed = stock.get_analysis()
    text = "```"
    if method == 'ma':
        d = analyzed.moving_averages
        for k, v in d.items():
            if k == "RECOMMENDATION":

                embed.add_field(name="Moving Avgs Recommendation",
                                value='{}'.format(await color_text(d['RECOMMENDATION'])), inline=False)
            if k == "COMPUTE":
                compute = d['COMPUTE']
                for x, y in compute.items():
                    text = text + str(x) + " : " + str(y) + "\n"
                text = text + "```"
                embed.add_field(name="Indicators", value="{}".format(text), inline=True)
    if method == 'osc':
        d = analyzed.oscillators
        for k, v in d.items():
            if k == "RECOMMENDATION":
                embed.add_field(name="Oscillators Recommendation",
                                value="{}".format(await color_text(d['RECOMMENDATION'])), inline=False)
            if k == "COMPUTE":
                compute = d['COMPUTE']
                for x, y in compute.items():
                    text = text + str(x) + " : " + str(y) + "\n"
                text = text + "```"
                embed.add_field(name="Indicators", value="{}".format(text), inline=True)


async def watchlist(ticker, fun="add"):
    '''
    Adds/removes the stock to the watchlist dictionary
    E.g. watchlist("TSLA", "add")
    '''
    if fun == "add":
        screener, exchange = get_market_exchange(ticker)
        with open("watchlist.txt", "r") as f:
            data = json.load(f)
            f.close()
            if ticker.upper() not in list(data.keys()):
                with open("watchlist.txt", "w") as f:
                    data[ticker.upper()] = {"screener": screener, "exchange": exchange}
                    json.dump(data, f)
                f.close()
    if fun == "remove":
        with open("watchlist.txt", "r") as f:
            data = json.load(f)
            f.close()
            if ticker.upper() in list(data.keys()):
                with open("watchlist.txt", "w") as f:
                    data.pop(ticker.upper(), None)
                    json.dump(data, f)
                f.close()


async def get_ticker(ticker="TSLA", interval=Interval.INTERVAL_4_HOURS, screener=None, exc=None):
    if screener == None and exc == None:
        screener, exc = get_market_exchange(ticker)
    try:
        stock = TA_Handler(
            symbol=ticker,
            screener=screener,
            exchange=exc,
            interval=interval
        )
    except Exception as e:
        print(ticker, exc, screener, e)
    return (stock)


class MarketCommands(commands.Cog):
    """
    !ticker [stock_name] {indicator_name}
        > !ticker TSLA
        > !ticker TSLA osc
    """
    @commands.command(
        ticker="Retrieves indicators for a given stock or cryptocoin. [] = required, {} = optional",
        brief="Retrieves stock indicators including moving avgs and oscillators."
    )
    async def ticker(self, ctx, *args):
        async with ctx.channel.typing():
            await asyncio.sleep(0.01)
            embed = discord.Embed(color=json_data['ticker_color'])
            if len(args) == 0:
                embed.set_thumbnail(
                    url="https://cdn2.iconfinder.com/data/icons/mix-color-5/100/Mix_color_5__info-512.png")
                embed.add_field(name="Missing Arguments",
                                value="```!ticker [ticker_name] [indicator_name] \n!ticker ixic \n!ticker ixic osc```",
                                inline=True)
                embed.set_footer(text="Indicator names, Oscillators/Moving Averages, [osc, ma] are optional. ")
            else:
                embed.set_thumbnail(url=json_data['image'])
                args_list = [x.upper() for x in args]
                moving_avgs = False
                oscillators = False
                if "MA" in args_list[-2:]:
                    args_list.remove("MA")
                    moving_avgs = True
                if "OSC" in args_list[-2:]:
                    args_list.remove("OSC")
                    oscillators = True
                for arg in args_list:
                    ticker_name = arg
                    stock = await get_ticker(ticker_name, intervals[selected])
                    price = await get_ticker_price(ticker_name)
                    analyzed = stock.get_analysis()
                    embed.add_field(name="```[${}]```".format(analyzed.symbol), value="{}".format(await color_text(analyzed.summary['RECOMMENDATION'] + " : $" + str(price))), inline=False)
                    embed.add_field(name="Buy/Sell/Neutral", value="```{}/{}/{}```".format(analyzed.summary['BUY'], analyzed.summary['SELL'],analyzed.summary['NEUTRAL']), inline=True)
                    if moving_avgs == True:
                        await get_ma_osc(embed, stock, "ma")
                        if oscillators == True:
                            await get_ma_osc(embed, stock, "osc")
                        print('ma')
                    elif oscillators == True:
                        await get_ma_osc(embed, stock, "osc")
                        if moving_avgs == True:
                            await get_ma_osc(embed, stock, "ma")
                        print('osc')

        await ctx.channel.send(embed=embed)


class Configuration(commands.Cog):
    """
    !interval [interval]
        > !interval 1-minute

    !watchlist {add/remove}
        > !watchlist
        > !watchlist add TSLA
        > !watchlist remove TSLA
    """

    @commands.command(
        watchlist="Adds or removes a stock or shows the watchlist.",
        brief="See or change stocks in the watchlist."
    )
    async def watchlist(self, ctx, *args):
        """
        Bring the existing watchlist
            !watchlist
        Add a stock to the watchlist
            !watchlist add TSLA
        Remove a stock from the watchlist
            !watchlist remove TSLA
        """
        embed = discord.Embed(color=json_data['watchlist_color'])
        embed.set_thumbnail(url="https://dl3.pushbulletusercontent.com/v3GAmZvD2FtVZ2SK9IY1YppLLZYoJuca/bookmark.png")
        if len(args) > 1:
            fun = args[0]
            for stock in args[1:]:
                embed.add_field(name="Watchlist is updated. Function: {}.".format(fun.upper()),
                                value="${}".format(stock.upper()), inline=True)
                await watchlist(str(stock), str(fun))
        else:
            with open("watchlist.txt", "r") as f:
                tickers = list(json.load(f).keys())
            f.close()
            embed.add_field(name="Watchlist",
                            value="{}".format(tickers), inline=True)
        await ctx.channel.send(embed=embed)

    @commands.command(
        interval="Shows or changes the interval.",
        brief="See or change candle intervals."
    )
    async def interval(self, ctx, *args):
        """
        See or change candle intervals.

        Existing interval
        !interval

        Set interval
        !interval 15-minutes

        Intervals
        1-minute, 5-minutes, 15-minutes, 1-hour,
        4-hours, 1-day, 1-week, 1-month

        """
        print(intervals[selected])
        embed = discord.Embed(color=json_data['watchlist_color'])
        embed.set_thumbnail(url=image)
        try:
            globals()['selected'] = args[0]
            embed.add_field(name="Interval setting is updated.", value=intervals[selected], inline=True)
            print(intervals[selected])
        except:
            embed.add_field(name="Existing interval.", value=intervals[selected], inline=True)
        await ctx.channel.send(embed=embed)


class SocialMedia(commands.Cog):
    """
    !sentiment [ticker_name]
        > !sentiment TSLA

    !reddit {#_of_posts}
        > !reddit
        > !reddit 100
    """
    @commands.command(
        sentiment="Sentiment analysis of a given ticker on Twitter.",
        brief="Sentiment analysis of a given ticker on Twitter."
    )
    async def sentiment(self, ctx, *args):
        """
        Sentiment analysis of a given ticker on Twitter.
        !sentiment TSLA
        """
        async with ctx.channel.typing():
            await asyncio.sleep(0.1)
            embed = discord.Embed(color=1146986)
            if len(args) == 0:
                embed.add_field(name="Missing Arguments",
                                value="```!sentiment [ticker_name] \n!sentiment THETA```",
                                inline=True)
                msg_image = "https://cdn2.iconfinder.com/data/icons/mix-color-5/100/Mix_color_5__info-512.png"
            else:
                msg_image = "https://www.shareicon.net/data/512x512/2015/09/04/95557_twitter_512x512.png"
                for arg in args:
                    stock = arg
                    tweets, pos, neg, neu = get_sentiment(stock, dollar=True)
                    count = len(tweets['id'])
                    pos_rate = pos / len(tweets['id'])

                    embed.add_field(name="{} Tweets within the last hour".format(stock.upper()),
                                    value='> Positive Tweets: {}\n> Negative Tweets: {}\n> Neutral Tweets: {}\n> Positivity Rate: {:2.2%}'.format(
                                        pos,
                                        neg,
                                        neu,
                                    pos_rate), inline=False)
            embed.set_thumbnail(url=msg_image)
            await ctx.channel.send(embed=embed)

    @commands.command(
        reddit="# of stock mentions in r/wallstreetbets",
        brief="# of stock mentions in r/wallstreetbets. default limit: 100"
    )
    async def reddit(self, ctx, *args):
        """
        # of stock mentions in r/wallstreetbets. default limit: 100
        !reddit 100
        """
        msg_image = "https://www.redditinc.com/assets/images/site/reddit-logo.png"
        embed = discord.Embed(color=11027200)
        embed.set_thumbnail(url=msg_image)
        async with ctx.channel.typing():
            await asyncio.sleep(0.01)
            try:
                sr_limit = args[0]
            except:
                sr_limit = 100
            df = await get_reddit_stocks(sr_limit)
            text = ""
            for x, y in df.iloc[0:10].iterrows():
                text = text + "{}:{} \n".format(y[0], y[2])
            text = "```"+text+"```"
            embed.add_field(name="Top Reddit Stocks - Limit:{}".format(sr_limit), value='{}'.format(text),
                            inline=False)

            await ctx.channel.send(embed=embed)



@tasks.loop(seconds=900.0)
async def signalAlarm():
    await client.wait_until_ready()
    print("Loop started.")

    with open("watchlist.txt", "r") as f:
        tickers = list(json.load(f).keys())
    f.close()

    for ticker in tickers:
        stock = await get_ticker(ticker, intervals[selected])
        await asyncio.sleep(0.01)
        try:
            analyzed = stock.get_analysis()
            ind = analyzed.indicators
            osc = analyzed.oscillators
            price = await get_ticker_price(ticker.upper())
            rsi = {"rec": osc['COMPUTE']['RSI'], "value": ind['RSI']}

            if rsi['value'] < 50:
                rsi['rec'] = 'BUY'
            else:
                rsi['rec'] = 'SELL'

            macd = {"rec": osc['COMPUTE']['MACD'], "value": ind['MACD.macd'], "signal": ind['MACD.signal']}
            mom = {"rec": osc['COMPUTE']['STOCH.K'], "value": ind['Stoch.K']}

            recs = [rsi['rec'], macd['rec'], mom['rec']]

            if recs.count("BUY") == 3:
                embed = discord.Embed(color=json_data['buy_color'])
                embed.set_thumbnail(url="https://reveregolf.com/wp-content/uploads/2019/10/Thumbs-Up-icon-2.png")
                embed.add_field(name="{}".format("BUY"), value="```{}```".format(ticker), inline=False)
                embed.add_field(name="Price", value="${}".format(price), inline=False)
                embed.add_field(name="RSI", value="{}".format(rsi['value']), inline=True)
                embed.add_field(name="MACD", value="{}".format(macd['value']), inline=True)
                embed.add_field(name="Stochastic", value="{}".format(mom['value']), inline=True)
                hook.send(embed=embed)

            if recs.count("SELL") == 3:
                embed = discord.Embed(color=json_data['sell_color'])
                embed.set_thumbnail(url="https://hotemoji.com/images/dl/r/money-with-wings-emoji-by-google.png")
                embed.add_field(name="{}".format("SELL"), value="```{}```".format(ticker), inline=False)
                embed.add_field(name="Price", value="${}".format(price), inline=False)
                embed.add_field(name="RSI", value="{}".format(rsi['value']), inline=True)
                embed.add_field(name="MACD", value="{}".format(macd['value']), inline=True)
                embed.add_field(name="Stochastic", value="{}".format(mom['value']), inline=True)
                hook.send(embed=embed)
        except Exception as e:
            print("Handler exception: ", e)
            pass


@signalAlarm.before_loop
async def signalAlarm_before():
    await client.wait_until_ready()


@client.event
async def on_ready():
    print('{} Logged In!'.format(client.user.name))


client.add_cog(MarketCommands())
client.add_cog(Configuration())
client.add_cog(SocialMedia())
signalAlarm.start()
client.run(json_data['discord_token'])
