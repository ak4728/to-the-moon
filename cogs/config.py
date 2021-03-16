import discord
import asyncio
from discord.ext import commands
from utils import *
from tradingview_ta import TA_Handler, Interval, Exchange

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
        embed.set_thumbnail(url=json_data['interval_image'])
        try:
            globals()['selected'] = args[0]
            embed.add_field(name="Interval setting is updated.", value=intervals[selected], inline=True)
            print(intervals[selected])
        except:
            embed.add_field(name="Existing interval.", value=intervals[selected], inline=True)
        await ctx.channel.send(embed=embed)


