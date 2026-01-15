import discord
import asyncio
from discord.ext import commands
from typing import List, Optional
from utils import get_ticker, get_ticker_price, get_ma_osc, color_text, validate_ticker
from config_manager import config_manager
from http_client import http_client
from tradingview_ta import Interval

config = config_manager.config


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
        help="Retrieves indicators for a given stock or cryptocoin. [] = required, {} = optional",
        brief="Retrieves stock indicators including moving avgs and oscillators."
    )
    async def ticker(self, ctx, *args):
        """Get ticker analysis with proper error handling and validation."""
        async with ctx.channel.typing():
            await asyncio.sleep(0.01)
            embed = discord.Embed(color=config.ticker_color)
            
            if len(args) == 0:
                embed.set_thumbnail(
                    url="https://cdn2.iconfinder.com/data/icons/mix-color-5/100/Mix_color_5__info-512.png")
                embed.add_field(
                    name="Missing Arguments",
                    value="```!ticker [ticker_name] [indicator_name] \n!ticker ixic \n!ticker ixic osc```",
                    inline=True
                )
                embed.set_footer(text="Indicator names, Oscillators/Moving Averages, [osc, ma] are optional.")
            else:
                embed.set_thumbnail(url=config.image)
                
                # Parse arguments
                args_list = [x.upper() for x in args]
                moving_avgs = "MA" in args_list[-2:]
                oscillators = "OSC" in args_list[-2:]
                
                # Remove indicator flags from ticker list
                if "MA" in args_list:
                    args_list.remove("MA")
                if "OSC" in args_list:
                    args_list.remove("OSC")
                
                # Process each ticker
                for arg in args_list:
                    try:
                        ticker_name = validate_ticker(arg)
                        
                        # Get stock data
                        selected_interval = config_manager.get_selected_interval()
                        stock = await get_ticker(ticker_name, selected_interval)
                        
                        if not stock:
                            embed.add_field(
                                name="Error",
                                value=f"```Failed to get data for {ticker_name}```",
                                inline=False
                            )
                            continue
                        
                        price = await get_ticker_price(ticker_name)
                        if not price:
                            embed.add_field(
                                name="Error", 
                                value=f"```Failed to get price for {ticker_name}```",
                                inline=False
                            )
                            continue
                        
                        analyzed = stock.get_analysis()
                        
                        # Add main ticker info
                        embed.add_field(
                            name=f"```[${analyzed.symbol}]```",
                            value=await color_text(f"{analyzed.summary['RECOMMENDATION']} : ${price:.2f}"),
                            inline=False
                        )
                        
                        embed.add_field(
                            name="Buy/Sell/Neutral",
                            value=f"```{analyzed.summary['BUY']}/{analyzed.summary['SELL']}/{analyzed.summary['NEUTRAL']}```",
                            inline=True
                        )
                        
                        # Add detailed indicators if requested
                        if moving_avgs:
                            await get_ma_osc(embed, stock, "ma")
                        
                        if oscillators:
                            await get_ma_osc(embed, stock, "osc")
                            
                    except ValueError as e:
                        embed.add_field(
                            name="Validation Error",
                            value=f"```{str(e)}```",
                            inline=False
                        )
                    except Exception as e:
                        embed.add_field(
                            name="Error",
                            value=f"```Failed to process {arg}: {str(e)[:100]}```",
                            inline=False
                        )

        await ctx.channel.send(embed=embed)

    @commands.command(
        help="Retrieves latest ARK trades. [] = required, {} = optional",
        brief="Retrieves latest ARK trades."
    )
    async def trades(self, ctx, *args):
        """
        Latest ARK trades with improved error handling.
        !trades ARKK
        """
        embed = discord.Embed(color=3426654)
        async with ctx.channel.typing():
            await asyncio.sleep(0.01)
            
            if len(args) == 0:
                embed.add_field(
                    name="Missing Arguments.",
                    value="```!trades [ARK symbol] \n!trades ARKK```",
                    inline=True
                )
                msg_image = "https://cdn2.iconfinder.com/data/icons/mix-color-5/100/Mix_color_5__info-512.png"
            else:
                valid_symbols = ["ARKK", "ARKQ", "ARKF", "ARKW"]
                
                for arg in args:
                    symbol = arg.upper()
                    
                    if symbol in valid_symbols:
                        msg_image = "https://upload.wikimedia.org/wikipedia/en/thumb/c/c1/Ark-logo-1-1.svg/1200px-Ark-logo-1-1.svg.png"
                        
                        try:
                            # Start HTTP client
                            await http_client.start()
                            
                            # Get ARK trades data
                            response_data = await http_client.get_json(
                                config.ark_url.format(symbol, '1d')
                            )
                            
                            bought = ""
                            sold = ""
                            
                            trades = response_data.get('trades', [])
                            if not trades:
                                embed.add_field(
                                    name="No Data",
                                    value=f"```No trades found for {symbol}```",
                                    inline=False
                                )
                                continue
                            
                            for trade in trades:
                                shares = trade.get('shares', 'Unknown')
                                ticker = trade.get('ticker', 'Unknown')
                                direction = trade.get('direction', 'Unknown')
                                
                                if direction == 'Buy':
                                    bought += f"```{shares} shares of {ticker}.```"
                                else:
                                    sold += f"```{shares} shares of {ticker}.```"
                            
                            embed.set_thumbnail(url=msg_image)
                            
                            if bought:
                                embed.add_field(
                                    name="Direction",
                                    value=f'{await color_text("Bought")} \u200b',
                                    inline=False
                                )
                                embed.add_field(
                                    name="Trades",
                                    value=f'{bought} \u200b',
                                    inline=False
                                )
                            
                            if sold:
                                embed.add_field(
                                    name="Direction",
                                    value=f'{await color_text("Sold")} \u200b',
                                    inline=False
                                )
                                embed.add_field(
                                    name="Trades",
                                    value=f'{sold} \u200b',
                                    inline=False
                                )
                                
                        except Exception as e:
                            embed.add_field(
                                name="Error",
                                value=f"```Failed to get ARK data for {symbol}: {str(e)[:100]}```",
                                inline=False
                            )
                            msg_image = "https://cdn2.iconfinder.com/data/icons/mix-color-5/100/Mix_color_5__info-512.png"
                    else:
                        embed.add_field(
                            name="Invalid Symbol",
                            value=f"```Wrong symbol: {symbol}. Please use one of: {', '.join(valid_symbols)}```",
                            inline=True
                        )
                        msg_image = "https://cdn2.iconfinder.com/data/icons/mix-color-5/100/Mix_color_5__info-512.png"
                        
            embed.set_thumbnail(url=msg_image)

        await ctx.channel.send(embed=embed)
