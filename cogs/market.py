import discord
import asyncio
from discord.ext import commands
from utils import *
from tradingview_ta import TA_Handler, Interval, Exchange


class MarketCommands(commands.Cog):
    """
    !ticker [stock_name] {indicator_name}
        > !ticker TSLA
        > !ticker TSLA osc

    !trades [ARK symbol]
        > !trades ARKK
        > !trades ARKQ
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
                    embed.add_field(name="```[${}]```".format(analyzed.symbol), value="{}".format(
                        await color_text(analyzed.summary['RECOMMENDATION'] + " : $" + str(price))), inline=False)
                    embed.add_field(name="Buy/Sell/Neutral",
                                    value="```{}/{}/{}```".format(analyzed.summary['BUY'], analyzed.summary['SELL'],
                                                                  analyzed.summary['NEUTRAL']), inline=True)
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

    @commands.command(
        ticker="Retrieves latest ARK trades. [] = required, {} = optional",
        brief="Retrieves latest ARK trades."
    )
    async def trades(self, ctx, *args):
        """
        Latest ARK trades. default symbol: ARKK, period:1d
        !reddit 100
        """
        embed = discord.Embed(color=3426654)
        async with ctx.channel.typing():
            await asyncio.sleep(0.01)
            if len(args) == 0:
                embed.add_field(name="Missing Arguments",
                                value="```!trades [ARK name] \n!trades ARKK```",
                                inline=True)
                msg_image = "https://cdn2.iconfinder.com/data/icons/mix-color-5/100/Mix_color_5__info-512.png"
            else:
                msg_image = "https://upload.wikimedia.org/wikipedia/en/thumb/c/c1/Ark-logo-1-1.svg/1200px-Ark-logo-1-1.svg.png"
            for arg in args:
                symbol = arg
                r = requests.get(json_data['ark_url'].format(symbol, '1d'))
                text = ""
                for el in r.json()['trades']:
                    if el['direction'] == 'Buy':
                        text += "{} bought {} shares of {} \n".format(symbol, el['shares'], el['ticker'])
                    else:
                        text += "{} sold {} shares of {}\n".format(symbol, el['shares'], el['ticker'])
                embed.set_thumbnail(url=msg_image)
                embed.add_field(name="Latest {} Trades within {}".format(symbol, '1d'), value='{}'.format(text),
                                    inline=False)

        await ctx.channel.send(embed=embed)
