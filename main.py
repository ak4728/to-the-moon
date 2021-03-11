import discord
import json, logging, requests

import asyncio

from discord.ext.commands import Bot
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
    Functions regarding the market, ticker price, and indicators. [] = required, {} = optional"
    !ticker [stock_name] {indicator_name}
    """

    @commands.command(
        sa="Selam ulan nesini anlamadin?",
        brief="Selamini alir.")
    async def sa(self, ctx):
        response = "Aleykum selam reyiz."
        await ctx.channel.send(response)

    @commands.command(
        ticker="Retrieves indicators for a given stock or cryptocoin. [] = required, {} = optional",
        brief="Retrieves stock indicators. \n  !ticker [ixic] \n  !ticker ixic ma"
    )
    async def ticker(self, ctx, *args):
        async with ctx.channel.typing():
            await asyncio.sleep(0.01)
            embed = discord.Embed(color=json_data['ticker_color'])
            embed.set_thumbnail(url="https://cdn2.iconfinder.com/data/icons/mix-color-5/100/Mix_color_5__info-512.png")
            try:
                ticker_name = args[0]
                stock = await get_ticker(ticker_name, intervals[selected])
                analyzed = stock.get_analysis()
                embed.add_field(name="Stock", value="${}".format(analyzed.symbol.upper()), inline=False)
                embed.add_field(name="Price", value="${}".format(get_ticker_price(ticker_name.upper())), inline=False)
                embed.add_field(name="Recommendation", value="{}".format(analyzed.summary['RECOMMENDATION']),
                                inline=False)
                embed.add_field(name="Buy", value="{}".format(analyzed.summary['BUY']), inline=True)
                embed.add_field(name="Sell", value="{}".format(analyzed.summary['SELL']), inline=True)
                embed.add_field(name="Neutral", value="{}".format(analyzed.summary['NEUTRAL']), inline=True)
                if len(args) > 1:
                    if args[1] == "ma":
                        await get_ma_osc(embed, stock, "ma")
                    if args[1] == "osc":
                        await get_ma_osc(embed, stock, "osc")
            except Exception as e:
                print(e)
                embed.add_field(name="Missing Arguments",
                                value="\n > !ticker [ticker_name] [indicator_name] \n > !ticker ixic \n > !ticker ixic osc",
                                inline=True)
                embed.set_footer(text="Indicator names, Oscillators/Moving Averages, [osc, ma] are optional. ")

        await ctx.channel.send(embed=embed)


class Configuration(commands.Cog):
    """
    Configuration functions. [] = required, {} = optional
    !interval [interval]
        !interval 1-minute

    Intervals:
        1-minute
        5-minutes
        15-minutes
        1-hour
        4-hours
        1-day
        1-week
        1-month

    !watchlist {add/remove}
        !watchlist
        !watchlist add TSLA
        !watchlist remove TSLA

    """

    @commands.command()
    async def watchlist(self, ctx, *args):
        response = "Aleykum selam reyiz."
        embed = discord.Embed(color=json_data['watchlist_color'])
        embed.set_thumbnail(url="https://dl3.pushbulletusercontent.com/v3GAmZvD2FtVZ2SK9IY1YppLLZYoJuca/bookmark.png")
        if len(args) > 1:
            fun = args[0]
            stock = args[1]
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

    @commands.command()
    async def interval(self, ctx, *args):
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
            ma = analyzed.moving_averages
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
                embed.add_field(name="Recommendation", value="{}".format("BUY"), inline=False)
                embed.add_field(name="Stock", value="${}".format(ticker), inline=False)
                embed.add_field(name="RSI", value="{}".format(rsi['value']), inline=True)
                embed.add_field(name="MACD", value="{}".format(macd['value']), inline=True)
                embed.add_field(name="Stochastic", value="{}".format(mom['value']), inline=True)
                hook.send(embed=embed)

            if recs.count("SELL") == 3:
                embed = discord.Embed(color=json_data['sell_color'])
                embed.set_thumbnail(url="https://hotemoji.com/images/dl/r/money-with-wings-emoji-by-google.png")
                embed.add_field(name="Recommendation", value="{}".format("SELL"), inline=False)
                embed.add_field(name="Stock", value="${}".format(ticker), inline=False)
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
signalAlarm.start()
client.run(json_data['discord_token'])
