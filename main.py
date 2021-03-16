import discord
import json, logging, requests, os

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

from cogs.market import MarketCommands
from cogs.config import Configuration
from cogs.social_media import SocialMedia

client.add_cog(MarketCommands())
client.add_cog(Configuration())
client.add_cog(SocialMedia())

#signalAlarm.start()
client.run(json_data['discord_token'])
