# helper functions will go here
import re
import asyncpraw
import asyncio
import discord
import pandas as pd
# import snscrape.modules.twitter as sntwitter  # Temporarily disabled due to compatibility issues
from datetime import datetime, timedelta, timezone
from pathlib import Path
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from tradingview_ta import TA_Handler, Interval, Exchange
from typing import Optional, Tuple, Dict, Any, List

# Import our new modules
from config_manager import config_manager
from http_client import http_client, RetryConfig
from cache import cached, global_cache
from file_manager import file_manager

# Get config instance
config = config_manager.config



async def color_text(recommendation: str) -> str:
    """
    Format recommendation text with appropriate colors.
    
    Args:
        recommendation: The recommendation text to format
        
    Returns:
        Formatted text string with Discord color codes
    """
    recommendation_upper = recommendation.upper()
    
    if "BUY" in recommendation_upper or "BOUGHT" in recommendation_upper:
        rec_text = f"```diff\n+{recommendation}```"
    elif "SELL" in recommendation_upper or "SOLD" in recommendation_upper:
        rec_text = f"```diff\n-{recommendation}```"
    else:
        rec_text = f"```fix\n{recommendation}```"
    
    return rec_text



async def get_ma_osc(embed: discord.Embed, stock: TA_Handler, method: str = 'ma') -> None:
    """
    Add moving averages or oscillators data to Discord embed.
    
    Args:
        embed: Discord embed to modify
        stock: TradingView TA_Handler instance
        method: 'ma' for moving averages, 'osc' for oscillators
    """
    try:
        analyzed = stock.get_analysis()
        text = "```"
        
        if method == 'ma':
            d = analyzed.moving_averages
            title = "Moving Avgs Recommendation"
            indicator_title = "Moving Average Indicators"
        elif method == 'osc':
            d = analyzed.oscillators
            title = "Oscillators Recommendation"
            indicator_title = "Oscillator Indicators"
        else:
            raise ValueError(f"Invalid method: {method}. Use 'ma' or 'osc'")
        
        # Add recommendation
        if 'RECOMMENDATION' in d:
            embed.add_field(
                name=title,
                value=await color_text(d['RECOMMENDATION']),
                inline=False
            )
        
        # Add compute indicators
        if 'COMPUTE' in d:
            compute = d['COMPUTE']
            for key, value in compute.items():
                text += f"{key}: {value}\n"
            text += "```"
            embed.add_field(name=indicator_title, value=text, inline=True)
            
    except Exception as e:
        embed.add_field(
            name="Error",
            value=f"```Failed to get {method} data: {str(e)[:100]}```",
            inline=False
        )


async def watchlist(ticker: str, action: str = "add") -> Dict[str, Any]:
    """
    Add or remove stock from watchlist with proper error handling and locking.
    
    Args:
        ticker: Stock symbol to add/remove
        action: "add" or "remove"
        
    Returns:
        Dict with status and message
        
    Raises:
        ValueError: If action is invalid
    """
    if action not in ["add", "remove"]:
        raise ValueError(f"Invalid action: {action}. Use 'add' or 'remove'")
    
    ticker = validate_ticker(ticker)
    watchlist_file = "watchlist.txt"
    
    async with file_manager.locked_file_operation(watchlist_file):
        try:
            # Load existing watchlist
            data = await file_manager.read_json_file(watchlist_file, default={})
            
            if action == "add":
                if ticker not in data:
                    try:
                        screener, exchange = await get_market_exchange(ticker)
                        data[ticker] = {"screener": screener, "exchange": exchange}
                        await file_manager.write_json_file(watchlist_file, data)
                        return {"status": "success", "message": f"Added {ticker} to watchlist"}
                    except Exception as e:
                        return {"status": "error", "message": f"Failed to add {ticker}: {str(e)}"}
                else:
                    return {"status": "info", "message": f"{ticker} already in watchlist"}
            
            else:  # remove
                if ticker in data:
                    data.pop(ticker, None)
                    await file_manager.write_json_file(watchlist_file, data)
                    return {"status": "success", "message": f"Removed {ticker} from watchlist"}
                else:
                    return {"status": "info", "message": f"{ticker} not found in watchlist"}
                    
        except Exception as e:
            return {"status": "error", "message": f"Failed to {action} {ticker}: {str(e)}"}


def validate_ticker(ticker: str) -> str:
    """
    Validate and sanitize ticker symbol.
    
    Args:
        ticker: Raw ticker symbol
        
    Returns:
        Validated ticker symbol in uppercase
        
    Raises:
        ValueError: If ticker is invalid
    """
    if not ticker or not isinstance(ticker, str):
        raise ValueError("Ticker must be a non-empty string")
    
    # Clean ticker symbol
    ticker = ticker.upper().strip()
    
    # Basic validation - letters, numbers, and common characters only
    if not re.match(r'^[A-Z0-9.-]+$', ticker):
        raise ValueError(f"Invalid ticker format: {ticker}")
    
    if len(ticker) > 10:  # Most tickers are max 5-6 chars
        raise ValueError(f"Ticker too long: {ticker}")
    
    return ticker


async def get_ticker(
    ticker: str = "TSLA", 
    interval: Interval = Interval.INTERVAL_4_HOURS, 
    screener: Optional[str] = None, 
    exchange: Optional[str] = None
) -> Optional[TA_Handler]:
    """
    Get TA_Handler for a ticker with proper error handling.
    
    Args:
        ticker: Stock symbol
        interval: Trading interval
        screener: Market screener (auto-detected if None)
        exchange: Exchange (auto-detected if None)
        
    Returns:
        TA_Handler instance or None if failed
    """
    try:
        ticker = validate_ticker(ticker)
        
        if screener is None or exchange is None:
            screener, exchange = await get_market_exchange(ticker)
        
        stock = TA_Handler(
            symbol=ticker,
            screener=screener,
            exchange=exchange,
            interval=interval
        )
        
        return stock
        
    except Exception as e:
        print(f"Failed to get ticker {ticker}: {e}")
        return None


@cached(ttl=300)  # Cache for 5 minutes
async def get_market_exchange(ticker: str) -> Tuple[str, str]:
    """
    Get market screener and exchange for a ticker with caching.
    
    Args:
        ticker: Stock symbol
        
    Returns:
        Tuple of (screener, exchange)
        
    Raises:
        ValueError: If ticker not found or invalid response
    """
    ticker = validate_ticker(ticker)
    
    try:
        # Use async HTTP client
        await http_client.start()
        
        response_data = await http_client.get_json(
            config.symbol_url.format(ticker),
            retry_config=RetryConfig(max_attempts=3, base_delay=1.0)
        )
        
        exchange = None
        for item in response_data:
            if item.get('symbol') == ticker:
                raw_exchange = item.get('exchange', '')
                
                # Map exchange names
                if raw_exchange == "NYSE ARCA & MKT":
                    exchange = "AMEX"
                elif raw_exchange in ['NYSE', 'NASDAQ', 'BINANCE', 'BITTREX']:
                    exchange = raw_exchange
                else:
                    exchange = raw_exchange
                break
        
        if not exchange:
            raise ValueError(f"Ticker {ticker} not found")
        
        # Determine screener based on exchange
        if exchange in ['NYSE', 'NASDAQ', 'ARCA', 'AMEX']:
            screener = "america"
        else:
            screener = "crypto"
        
        return screener, exchange
        
    except Exception as e:
        raise ValueError(f"Failed to get market data for {ticker}: {e}")


@cached(ttl=60)  # Cache for 1 minute
async def get_ticker_price(ticker: str) -> Optional[float]:
    """
    Get current price for a ticker with caching and error handling.
    
    Args:
        ticker: Stock symbol
        
    Returns:
        Current price or None if failed
    """
    try:
        ticker = validate_ticker(ticker)
        
        # Handle special cases
        if "USD" in ticker:
            ticker = ticker.split("USD")[0] + "-USD"
        elif ticker == 'IXIC':
            ticker = "%5EIXIC"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'
        }
        
        await http_client.start()
        
        response_data = await http_client.get_json(
            config.api_url.format(ticker),
            headers=headers,
            retry_config=RetryConfig(max_attempts=3, base_delay=0.5)
        )
        
        if 'quoteResponse' in response_data and 'result' in response_data['quoteResponse']:
            results = response_data['quoteResponse']['result']
            if results and len(results) > 0:
                return results[0].get('regularMarketPrice')
        
        return None
        
    except Exception as e:
        print(f"Failed to get price for {ticker}: {e}")
        return None



def labeler(f):
    if f > 0.05:
        lbl = 'pos'
    elif f < -0.05:
        lbl = 'neg'
    else:
        lbl = 'neu'
    return (lbl)


def get_sentiment(keyword="TSLA", dollar=True):
    """
    Sentiment analysis using Twitter data - TEMPORARILY DISABLED
    TODO: Fix snscrape compatibility issues
    """
    # Temporarily return dummy data due to snscrape compatibility issues
    import pandas as pd
    
    # Create empty DataFrame with expected columns
    tweets = pd.DataFrame(columns=['id', 'date', 'content', 'compound', 'neg', 'neu', 'pos', 'label'])
    
    # Return dummy sentiment data
    pos, neg, neu = 0, 0, 1  # All neutral for now
    
    return tweets, pos, neg, neu


def sentiment_response(stock="TSLA"):
    tweets, pos, neg, neu = get_sentiment(stock, dollar=True)
    count = len(tweets['id'])
    pos_rate = pos / len(tweets['id'])
    print(tweets)
    image = "https://www.shareicon.net/data/512x512/2015/09/04/95557_twitter_512x512.png"
    embed = discord.Embed(color=1146986)
    embed.set_thumbnail(url=image)
    embed.add_field(name="{}".format(stock),
                    value='> Positive Tweets: {}\n> Negative Tweets: {}\n> Neutral Tweets: {}\n> Positivity Rate: {}'.format(
                        pos,
                        neg,
                        neu,
                        pos_rate), inline=False)
    hook.send(embed=embed)

async def get_reddit_stocks(sr_limit=100):
    """Get stock mentions from r/wallstreetbets."""
    try:
        reddit = asyncpraw.Reddit(
            client_id=config.client_id,
            client_secret=config.client_secret,
            user_agent=config.user_agent
        )

        if not config.client_id or not config.client_secret:
            # Return empty DataFrame if Reddit credentials not configured
            return pd.DataFrame(columns=['Term', 'Company_Name', 'Frequency'])

        subreddit = await reddit.subreddit("wallstreetbets")

        df = {}
        async for submission in subreddit.hot(limit=sr_limit):
            df[submission.title] = submission.selftext

        regex = re.compile('[^a-zA-Z ]')
        word_dict = {}

        for (k, v) in df.items():
            title = k
            title = regex.sub('', title)
            title_words = title.split(' ')
            content = v
            content = regex.sub('', content)
            content_words = content.split(' ')
            words = title_words + content_words
            for x in words:
                if x in ['A', 'B', 'GO', 'ARE', 'ON', 'IT', 'ALL', 'NEXT', 'PUMP', 'AT', 'NOW', 'FOR', 'TD', 'CEO', 'AM', 'K', 'BIG', 'BY', 'LOVE', 'CAN', 'BE', 'SO', 'OUT', 'STAY', 'OR', 'NEW','RH','EDIT','ONE','ANY']:
                    pass
                elif x in word_dict:
                    word_dict[x] += 1
                else:
                    word_dict[x] = 1
        
        wordbag = pd.DataFrame.from_dict(list(word_dict.items())).rename(columns={0:"Term", 1:"Frequency"})
        
        # Check if tickers.csv exists
        tickers_file = Path('tickers.csv')
        if not tickers_file.exists():
            print("Warning: tickers.csv not found. Creating dummy data.")
            return wordbag.head(20)
        
        tickers = pd.read_csv('tickers.csv').rename(columns={"Symbol":"Term", "Name":"Company_Name"})
        stocks = pd.merge(tickers, wordbag, on="Term").sort_values(by="Frequency", ascending=False).head(20)
        
        await reddit.close()
        return stocks
        
    except Exception as e:
        print(f"Error getting Reddit stocks: {e}")
        return pd.DataFrame(columns=['Term', 'Company_Name', 'Frequency'])