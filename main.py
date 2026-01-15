import discord
import logging
import asyncio
from typing import Dict, List

from dhooks import Webhook
from discord.ext import commands, tasks
from pretty_help import PrettyHelp

# Import our improved modules
from config_manager import config_manager
from http_client import http_client
from file_manager import file_manager
from utils import get_ticker, get_ticker_price, validate_ticker

# Cogs
from cogs.market import MarketCommands
from cogs.config import Configuration
from cogs.social_media import SocialMedia

# Get configuration
config = config_manager.config
json_data = config  # For backward compatibility

# Configuration
logger = logging.getLogger('discord')
logger.setLevel(logging.ERROR)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)
hook = Webhook(config.webhook_url)
user_agent = config.user_agent

# Configure intents for proper bot functionality (non-privileged)
intents = discord.Intents.default()
intents.guilds = True          # Required for guild information
intents.guild_messages = True   # Required for receiving messages
# intents.message_content = True  # Privileged intent - must be enabled in Discord Developer Portal

client = commands.Bot(command_prefix="!", help_command=PrettyHelp(), intents=intents)

@tasks.loop(seconds=900.0)
async def signal_alarm():
    """Monitor watchlist and send trading signals."""
    await client.wait_until_ready()
    logger.info("Signal alarm loop started")
    
    try:
        # Load watchlist with proper error handling
        watchlist_data = await file_manager.read_json_file("watchlist.txt", default={})
        tickers = list(watchlist_data.keys())
        
        if not tickers:
            logger.info("No tickers in watchlist")
            return
        
        # Start HTTP client
        await http_client.start()
        
        # Process each ticker with improved error handling
        for ticker in tickers:
            try:
                ticker = validate_ticker(ticker)
                selected_interval = config_manager.get_selected_interval()
                
                # Get stock data
                stock = await get_ticker(ticker, selected_interval)
                if not stock:
                    logger.warning(f"Failed to get stock data for {ticker}")
                    continue
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.1)
                
                # Get analysis data
                analyzed = stock.get_analysis()
                ind = analyzed.indicators
                osc = analyzed.oscillators
                price = await get_ticker_price(ticker)
                
                if not price:
                    logger.warning(f"Failed to get price for {ticker}")
                    continue
                
                # Calculate indicators with safe access
                rsi = {
                    "rec": osc.get('COMPUTE', {}).get('RSI', 'NEUTRAL'),
                    "value": ind.get('RSI', 0)
                }
                
                # Override RSI recommendation based on value
                if rsi['value'] < 50:
                    rsi['rec'] = 'BUY'
                else:
                    rsi['rec'] = 'SELL'
                
                macd = {
                    "rec": osc.get('COMPUTE', {}).get('MACD', 'NEUTRAL'),
                    "value": ind.get('MACD.macd', 0),
                    "signal": ind.get('MACD.signal', 0)
                }
                
                mom = {
                    "rec": osc.get('COMPUTE', {}).get('STOCH.K', 'NEUTRAL'),
                    "value": ind.get('Stoch.K', 0)
                }
                
                recs = [rsi['rec'], macd['rec'], mom['rec']]
                
                # Send BUY signal
                if recs.count("BUY") == 3:
                    await send_trading_signal("BUY", ticker, price, rsi, macd, mom)
                    logger.info(f"BUY signal sent for {ticker}")
                
                # Send SELL signal
                elif recs.count("SELL") == 3:
                    await send_trading_signal("SELL", ticker, price, rsi, macd, mom)
                    logger.info(f"SELL signal sent for {ticker}")
                    
            except Exception as e:
                logger.error(f"Error processing ticker {ticker}: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Signal alarm error: {e}")


async def send_trading_signal(
    signal_type: str, 
    ticker: str, 
    price: float, 
    rsi: dict, 
    macd: dict, 
    mom: dict
) -> None:
    """Send trading signal via webhook."""
    try:
        if signal_type == "BUY":
            embed = discord.Embed(color=config.buy_color)
            embed.set_thumbnail(url="https://reveregolf.com/wp-content/uploads/2019/10/Thumbs-Up-icon-2.png")
        else:  # SELL
            embed = discord.Embed(color=config.sell_color)
            embed.set_thumbnail(url="https://hotemoji.com/images/dl/r/money-with-wings-emoji-by-google.png")
        
        embed.add_field(name=signal_type, value=f"```{ticker}```", inline=False)
        embed.add_field(name="Price", value=f"${price:.2f}", inline=False)
        embed.add_field(name="RSI", value=f"{rsi['value']:.2f}", inline=True)
        embed.add_field(name="MACD", value=f"{macd['value']:.4f}", inline=True)
        embed.add_field(name="Stochastic", value=f"{mom['value']:.2f}", inline=True)
        
        hook.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Failed to send {signal_type} signal for {ticker}: {e}")


@client.event
async def on_ready():
    """Event handler for bot ready state."""
    print(f'{client.user.name} Logged In!')
    logger.info(f"Bot {client.user.name} is ready")

# Initialize HTTP client and start bot
async def main():
    """Main function to start the bot with proper cleanup."""
    try:
        # Add cogs
        await client.add_cog(MarketCommands())
        await client.add_cog(Configuration())
        await client.add_cog(SocialMedia())
        
        # Start signal alarm
        signal_alarm.start()
        
        # Run bot
        await client.start(config.discord_token)
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise
    finally:
        # Cleanup
        await http_client.close()

if __name__ == "__main__":
    asyncio.run(main())
