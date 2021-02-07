import discord
import json, logging, requests
from itertools import cycle
from discord.ext.commands import Bot
from tradingview_ta import TA_Handler, Interval, Exchange
from dhooks import Webhook
from discord.ext import commands, tasks
import asyncio


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


client = discord.Client()


async def getAnalysis(embed, stock, method = 'ma'):
    method = method
    if method == 'ma':
        d = stock.get_analysis().moving_averages
        for k,v in d.items():
            if k == "RECOMMENDATION":
                embed.add_field(name="Moving Avgs Recommendation", value="{}".format(stock.get_analysis().moving_averages['RECOMMENDATION']), inline=False)
            if k == "COMPUTE":
                compute = stock.get_analysis().moving_averages['COMPUTE']
                for x,y in compute.items():
                    embed.add_field(name=str(x), value="{}".format(y), inline=True)
    if method == 'osc':
        d = stock.get_analysis().oscillators
        for k,v in d.items():
            if k == "RECOMMENDATION":
                embed.add_field(name="Oscillators Recommendation", value="{}".format(stock.get_analysis().moving_averages['RECOMMENDATION']), inline=False)
            if k == "COMPUTE":
                compute = stock.get_analysis().oscillators['COMPUTE']
                for x,y in compute.items():
                    embed.add_field(name=str(x), value="{}".format(y), inline=True)

async def watchlist(stock, fun="add"):
    if fun == "add":
        with open("watchlist.txt", "r") as f:
            lines = f.readlines()
            tickers = [x.strip() for x in lines] 
            f.close()
            if stock.upper() not in tickers:
                with open("watchlist.txt", "a") as f:
                    f.write(stock.upper()+"\n")
    elif fun == "remove":
        with open("watchlist.txt", "r") as f:
            lines = f.readlines()
            tickers = [x.strip() for x in lines]
            f.close()
            if stock.upper() in tickers: 
                with open("watchlist.txt", "w") as f:
                    for line in lines:
                        if line.strip("\n") != stock.upper():
                            f.write(line.upper())
    f.close()




@client.event
async def on_message(message):
    if message.content.startswith('!ticker '):
        ticker = message.content.split('!ticker')[1].split(" ")[1]
        exchange = cycle(["NYSE", "NASDAQ", "BINANCE", "BITTREX"]) 
        exc = "NYSE"
        while True:
            try:
                if exc in ["BINANCE", "BITTREX"]:
                    screener = "crypto"
                else:
                    screener = "america"
                stock = TA_Handler(
                    symbol=ticker,
                    screener=screener,
                    exchange=exc,
                    interval=Interval.INTERVAL_4_HOURS
                )
                stock.get_analysis().indicators
                break
            except Exception as e:
                print(ticker,exc, screener, e)
                exc = next(exchange)
                continue

        embed = discord.Embed(color=json_data['ticker_color'])
        embed.set_thumbnail(url=image)
        try:
            embed.add_field(name="Stock", value="${}".format(stock.get_analysis().symbol.upper()), inline=False)
            embed.add_field(name="Recommendation", value="{}".format(stock.get_analysis().summary['RECOMMENDATION']), inline=False)
            embed.add_field(name="Buy", value="{}".format(stock.get_analysis().summary['BUY']), inline=True)
            embed.add_field(name="Sell", value="{}".format(stock.get_analysis().summary['SELL']), inline=True)
            embed.add_field(name="Neutral", value="{}".format(stock.get_analysis().summary['NEUTRAL']), inline=True)
            try:
                ma = message.content.split('!ticker')[1].split(" ")[2]
                if ma == "ma":
                    await getAnalysis(embed,stock,"ma")
                if ma == "osc":
                    await getAnalysis(embed,stock,"osc")
            except Exception as e:
                print("Exception in MA {}".format(e))
                pass
            try:
                osc = message.content.split('!ticker')[1].split(" ")[3]
                if osc == "osc":
                    await getAnalysis(embed,stock,"osc")
            except Exception as e:
                print("Exception in OSC {}".format(e))
                pass
        except Exception as e:
            print("Try block exception Stock Rec: ",e)
            embed.add_field(name="Exception", value="{}".format("Ticker not found."), inline=True)

        await message.channel.send(embed=embed)

    if message.content.startswith('!watchlist '):
        embed = discord.Embed(color=json_data['watchlist_color'])
        embed.set_thumbnail(url=image)
        try:
            fun = message.content.split('!watchlist ')[1].split(" ")[0]
            stock = message.content.split('!watchlist ')[1].split(" ")[1]
            embed.add_field(name="Watchlist is updated. Function: {}.".format(fun.upper()), value="${}".format(stock.upper()), inline=True)
            await watchlist(str(stock), str(fun))   
        except Exception as e:
            print("Exception in Watchlist {}".format(e))
        await message.channel.send(embed=embed)

    if message.content.startswith('!watchlist'):
        embed = discord.Embed(color=json_data['watchlist_color'])
        embed.set_thumbnail(url=image)
        with open("watchlist.txt", "r") as f:
            tickers = f.readlines()
        f.close()               
        tickers = [x.strip() for x in tickers]
        await message.channel.send(tickers)
        





@tasks.loop(seconds=1500.0)
async def signalAlarm():
    await client.wait_until_ready()
    print("Loop started.")


    with open("watchlist.txt", "r") as f:
        tickers = f.readlines()
    f.close()               
    tickers = [x.strip() for x in tickers]
    

    for ticker in tickers:
        exchange = cycle(["NYSE", "NASDAQ", "BINANCE", "BITTREX"])
        exc = "NYSE"
        while True:
            try:
                if exc in ["BINANCE", "BITTREX"]:
                    screener = "crypto"
                else:
                    screener = "america"
                stock = TA_Handler(
                    symbol=ticker,
                    screener=screener,
                    exchange=exc,
                    interval=Interval.INTERVAL_4_HOURS
                )
                stock.get_analysis().indicators
                break
            except Exception as e:
                print(ticker,exc, screener, e)
                exc = next(exchange)
                continue

        try:
            ind = stock.get_analysis().indicators
            osc = stock.get_analysis().oscillators
            ma = stock.get_analysis().moving_averages
            rsi = {"rec": osc['COMPUTE']['RSI'], "value":ind['RSI']}
            macd = {"rec": osc['COMPUTE']['MACD'], "value":ind['MACD.macd'], "signal":ind['MACD.signal']}
            mom = {"rec": osc['COMPUTE']['Mom'], "value":ind['Mom']}

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
            print("Handler exception: ",e)
            pass



@signalAlarm.before_loop
async def signalAlarm_before():
    await client.wait_until_ready()

@client.event
async def on_ready():
    print('{} Logged In!'.format(client.user.name))


signalAlarm.start()
client.run(json_data['discord_token'])