import discord
import json, logging, requests

import asyncio

from discord.ext.commands import Bot
from tradingview_ta import TA_Handler, Interval, Exchange
from dhooks import Webhook
from discord.ext import commands, tasks
from itertools import cycle
from utils import *

# Configuration
logger = logging.getLogger('discord')
logger.setLevel(logging.ERROR)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

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

client = discord.Client()


async def get_ma_osc(embed, stock, method='ma'):
    method = method
    analyzed = stock.get_analysis()
    if method == 'ma':
        d = analyzed.moving_averages
        for k, v in d.items():
            if k == "RECOMMENDATION":
                embed.add_field(name="Moving Avgs Recommendation",
                                value='{}'.format(d['RECOMMENDATION']), inline=False)
            if k == "COMPUTE":
                compute = d['COMPUTE']
                for x, y in compute.items():
                    embed.add_field(name=str(x), value="{}".format(y), inline=True)
    if method == 'osc':
        d = analyzed.oscillators
        for k, v in d.items():
            if k == "RECOMMENDATION":
                embed.add_field(name="Oscillators Recommendation",
                                value="{}".format(d['RECOMMENDATION']), inline=False)
            if k == "COMPUTE":
                compute = d['COMPUTE']
                for x, y in compute.items():
                    embed.add_field(name=str(x), value="{}".format(y), inline=True)


async def watchlist(ticker, fun="add"):
    '''
    Adds/removes the stock to the watchlist dictionary
    E.g. watchlist("TSLA", "add")
    '''
    if fun == "add":
        screener, exchange = get_market_exchange(ticker)
        with open("watchlist2.txt", "r") as f:
            data = json.load(f)
            f.close()
            if ticker.upper() not in list(data.keys()):
                with open("watchlist2.txt", "w") as f:
                    data[ticker] = {"screener": screener, "exchange": exchange}
                    json.dump(data, f)
                f.close()
    if fun == "remove":
        screener, exchange = get_market_exchange(ticker)
        with open("watchlist2.txt", "r") as f:
            data = json.load(f)
            f.close()
            if ticker.upper() in list(data.keys()):
                with open("watchlist2.txt", "w") as f:
                    data.pop(ticker, None)
                    json.dump(data, f)
                f.close()


async def get_ticker(ticker="TSLA", interval=Interval.INTERVAL_4_HOURS, screener = None, exc = None):
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


@client.event
async def on_message(message):
    if message.content.startswith('!ticker '):
        embed = discord.Embed(color=json_data['ticker_color'])
        embed.set_thumbnail(url=image)
        try:
            ticker = message.content.split('!ticker')[1].split(" ")[1]
            stock = await get_ticker(ticker, intervals[selected])
            analyzed = stock.get_analysis()
            embed.add_field(name="Stock", value="${}".format(analyzed.symbol.upper()), inline=False)
            embed.add_field(name="Recommendation", value="{}".format(analyzed.summary['RECOMMENDATION']), inline=False)
            embed.add_field(name="Buy", value="{}".format(analyzed.summary['BUY']), inline=True)
            embed.add_field(name="Sell", value="{}".format(analyzed.summary['SELL']), inline=True)
            embed.add_field(name="Neutral", value="{}".format(analyzed.summary['NEUTRAL']), inline=True)
            try:
                ma = message.content.split('!ticker')[1].split(" ")[2]
                if ma == "ma":
                    await get_ma_osc(embed, stock, "ma")
                if ma == "osc":
                    await get_ma_osc(embed, stock, "osc")
            except Exception as e:
                print("Exception in MA {}".format(e))
                pass
            try:
                osc = message.content.split('!ticker')[1].split(" ")[3]
                if osc == "osc":
                    await get_ma_osc(embed, stock, "osc")
            except Exception as e:
                print("Exception in OSC {}".format(e))
                pass
        except Exception as e:
            print("Try block exception Stock Rec: ", e)
            embed.add_field(name="Exception", value="{}".format("Ticker not found."), inline=True)

        await message.channel.send(embed=embed)

    if message.content.startswith('!watchlist '):
        embed = discord.Embed(color=json_data['watchlist_color'])
        embed.set_thumbnail(url=image)
        try:
            fun = message.content.split('!watchlist ')[1].split(" ")[0]
            stock = message.content.split('!watchlist ')[1].split(" ")[1]
            embed.add_field(name="Watchlist is updated. Function: {}.".format(fun.upper()),
                            value="${}".format(stock.upper()), inline=True)
            await watchlist(str(stock), str(fun))
        except Exception as e:
            print("Exception in Watchlist {}".format(e))
        await message.channel.send(embed=embed)

    if message.content.startswith('!watchlist'):
        embed = discord.Embed(color=json_data['watchlist_color'])
        embed.set_thumbnail(url=image)
        with open("watchlist2.txt", "r") as f:
            tickers = list(json.load(f).keys())
        f.close()
        await message.channel.send(tickers)

    if message.content.startswith('!interval '):
        print(intervals[selected])
        embed = discord.Embed(color=json_data['watchlist_color'])
        embed.set_thumbnail(url=image)
        globals()['selected'] = message.content.split('!interval ')[1].split(" ")[0]
        embed.add_field(name="Interval setting is updated.", value=intervals[selected], inline=True)
        print(intervals[selected])
        await message.channel.send(embed=embed)


@tasks.loop(seconds=1500.0)
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
            ma = analyzed.moving_averages
            rsi = {"rec": osc['COMPUTE']['RSI'], "value": ind['RSI']}
            macd = {"rec": osc['COMPUTE']['MACD'], "value": ind['MACD.macd'], "signal": ind['MACD.signal']}
            mom = {"rec": osc['COMPUTE']['Mom'], "value": ind['Mom']}

            recs = [rsi['rec'], macd['rec'], mom['rec']]

            if recs.count("BUY") == 3:
                embed = discord.Embed(color=json_data['buy_color'])
                embed.set_thumbnail(url="https://reveregolf.com/wp-content/uploads/2019/10/Thumbs-Up-icon-2.png")
                embed.add_field(name="Recommendation", value="{}".format("BUY"), inline=False)
                embed.add_field(name="Stock", value="${}".format(ticker), inline=False)
                embed.add_field(name="RSI", value="{}".format(rsi['value']), inline=True)
                embed.add_field(name="MACD", value="{}".format(macd['value']), inline=True)
                embed.add_field(name="MOM", value="{}".format(mom['value']), inline=True)
                hook.send(embed=embed)

            if recs.count("SELL") == 3:
                embed = discord.Embed(color=json_data['sell_color'])
                embed.set_thumbnail(url="https://hotemoji.com/images/dl/r/money-with-wings-emoji-by-google.png")
                embed.add_field(name="Recommendation", value="{}".format("SELL"), inline=False)
                embed.add_field(name="Stock", value="${}".format(ticker), inline=False)
                embed.add_field(name="RSI", value="{}".format(rsi['value']), inline=True)
                embed.add_field(name="MACD", value="{}".format(macd['value']), inline=True)
                embed.add_field(name="MOM", value="{}".format(mom['value']), inline=True)
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


signalAlarm.start()
client.run(json_data['discord_token'])
