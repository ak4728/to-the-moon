import discord
import asyncio
from discord.ext import commands
from utils import *


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
            text = "```" + text + "```"
            embed.add_field(name="Top Reddit Stocks - Limit:{}".format(sr_limit), value='{}'.format(text),
                            inline=False)

            await ctx.channel.send(embed=embed)



