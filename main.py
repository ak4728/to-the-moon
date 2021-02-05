import discord
import json, logging, requests
from discord.ext.commands import Bot
from tradingview_ta import TA_Handler, Interval, Exchange

# Configuration
logger = logging.getLogger('discord')
logger.setLevel(logging.ERROR)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

with open('config.json') as json_file:
    json_data = json.load(json_file)

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

@client.event
async def on_ready():
    print('{} Logged In!'.format(client.user.name))


@client.event
async def on_message(message):
    if message.content.startswith('!ticker '):
        ticker = message.content.split('!ticker')[1].split(" ")[1]
        stock = TA_Handler(
            symbol=ticker,
            screener="america",
            exchange="NASDAQ",
            interval=Interval.INTERVAL_1_DAY
        )

        embed = discord.Embed(color=4500277)
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
            print(e)
            embed.add_field(name="Exception", value="{}".format("Ticker not found."), inline=True)

        await message.channel.send(embed=embed)



client.run(json_data['discord_token'])
