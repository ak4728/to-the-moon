import discord
import logging

from dhooks import Webhook
from discord.ext import commands, tasks
from utils import *
from pretty_help import PrettyHelp

# Cogs
from cogs.market import MarketCommands
from cogs.config import Configuration
from cogs.social_media import SocialMedia

with open('config.json') as json_file:
    json_data = json.load(json_file)

# Configuration
logger = logging.getLogger('discord')
logger.setLevel(logging.ERROR)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)
hook = Webhook(json_data['webhook_url'])
user_agent = json_data['user_agent']
client = commands.Bot(command_prefix="!", help_command=PrettyHelp())  # discord.Client()

@tasks.loop(seconds=900.0)
async def signal_alarm():
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


@signal_alarm.before_loop
async def signal_alarm_before():
    await client.wait_until_ready()

@client.event
async def on_ready():
    print('{} Logged In!'.format(client.user.name))

# Cogs
client.add_cog(MarketCommands())
client.add_cog(Configuration())
client.add_cog(SocialMedia())

signal_alarm.start()
client.run(json_data['discord_token'])
