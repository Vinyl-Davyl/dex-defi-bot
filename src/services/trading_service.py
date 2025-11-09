import aiohttp
import json
import asyncio
from datetime import datetime
import sys
import os.path

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.config.config import Config
from src.utils.logger import setup_logger
from src.utils.helpers import format_percentage, format_currency, get_cached_result, cache_result

# Setup logger
logger = setup_logger(__name__)

async def get_token_price(token_id):
    """Get current price and 24h change for a token from CoinGecko"""
    # Check cache first
    cache_key = f"token_price_{token_id}"
    cached_data = get_cached_result(cache_key)
    if cached_data:
        return cached_data
    
    try:
        url = f"{Config.COINGECKO_API_URL}/simple/price?ids={token_id}&vs_currencies=usd&include_24hr_change=true"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if token_id in data:
                        token_data = data[token_id]
                        result = {
                            'price': format_currency(token_data.get('usd', 0)),
                            'change_24h': format_percentage(token_data.get('usd_24h_change', 0))
                        }
                        
                        # Cache result
                        cache_result(cache_key, result, 300)  # Cache for 5 minutes
                        
                        return result
                    else:
                        logger.error(f"Token {token_id} not found in CoinGecko response")
                        return None
                else:
                    logger.error(f"Error fetching token price: {response.status}")
                    return None
    except Exception as e:
        logger.exception(f"Error in get_token_price: {e}")
        return None

async def get_market_sentiment():
    """Get overall market sentiment based on top tokens"""
    # Check cache first
    cache_key = "market_sentiment"
    cached_data = get_cached_result(cache_key)
    if cached_data:
        return cached_data
    
    try:
        # Get top 10 tokens by market cap
        url = f"{Config.COINGECKO_API_URL}/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=10&page=1&sparkline=false&price_change_percentage=24h"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Calculate average 24h change
                    total_change = sum(coin.get('price_change_percentage_24h', 0) for coin in data)
                    avg_change = total_change / len(data) if data else 0
                    
                    # Determine sentiment
                    sentiment = "neutral"
                    if avg_change > 5:
                        sentiment = "very bullish"
                    elif avg_change > 2:
                        sentiment = "bullish"
                    elif avg_change < -5:
                        sentiment = "very bearish"
                    elif avg_change < -2:
                        sentiment = "bearish"
                    
                    # Format top gainers and losers
                    sorted_by_change = sorted(data, key=lambda x: x.get('price_change_percentage_24h', 0), reverse=True)
                    top_gainers = sorted_by_change[:3]
                    top_losers = sorted_by_change[-3:]
                    
                    result = {
                        'sentiment': sentiment,
                        'avg_change_24h': format_percentage(avg_change),
                        'top_gainers': [
                            {
                                'name': coin.get('name', 'Unknown'),
                                'symbol': coin.get('symbol', 'Unknown').upper(),
                                'change_24h': format_percentage(coin.get('price_change_percentage_24h', 0))
                            } for coin in top_gainers
                        ],
                        'top_losers': [
                            {
                                'name': coin.get('name', 'Unknown'),
                                'symbol': coin.get('symbol', 'Unknown').upper(),
                                'change_24h': format_percentage(coin.get('price_change_percentage_24h', 0))
                            } for coin in top_losers
                        ]
                    }
                    
                    # Cache result
                    cache_result(cache_key, result, 1800)  # Cache for 30 minutes
                    
                    return result
                else:
                    logger.error(f"Error fetching market data: {response.status}")
                    return None
    except Exception as e:
        logger.exception(f"Error in get_market_sentiment: {e}")
        return None

async def get_token_sentiment(token_id):
    """Get sentiment analysis for a specific token"""
    # Check cache first
    cache_key = f"token_sentiment_{token_id}"
    cached_data = get_cached_result(cache_key)
    if cached_data:
        return cached_data
    
    try:
        # Get token data
        url = f"{Config.COINGECKO_API_URL}/coins/{token_id}?localization=false&tickers=false&market_data=true&community_data=true&developer_data=false"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Extract relevant data
                    market_data = data.get('market_data', {})
                    community_data = data.get('community_data', {})
                    
                    # Calculate sentiment score (simple algorithm)
                    sentiment_score = 0
                    
                    # Price change factors
                    price_change_24h = market_data.get('price_change_percentage_24h', 0)
                    price_change_7d = market_data.get('price_change_percentage_7d', 0)
                    price_change_30d = market_data.get('price_change_percentage_30d', 0)
                    
                    # Weight recent changes more heavily
                    sentiment_score += price_change_24h * 0.5
                    sentiment_score += price_change_7d * 0.3
                    sentiment_score += price_change_30d * 0.2
                    
                    # Community factors
                    reddit_subscribers = community_data.get('reddit_subscribers', 0)
                    twitter_followers = community_data.get('twitter_followers', 0)
                    
                    # Normalize and add community factors (very basic)
                    if reddit_subscribers > 100000 or twitter_followers > 500000:
                        sentiment_score += 1
                    
                    # Determine sentiment label
                    sentiment = "neutral"
                    if sentiment_score > 10:
                        sentiment = "very bullish"
                    elif sentiment_score > 5:
                        sentiment = "bullish"
                    elif sentiment_score < -10:
                        sentiment = "very bearish"
                    elif sentiment_score < -5:
                        sentiment = "bearish"
                    
                    result = {
                        'name': data.get('name', 'Unknown'),
                        'symbol': data.get('symbol', 'Unknown').upper(),
                        'sentiment': sentiment,
                        'price': format_currency(market_data.get('current_price', {}).get('usd', 0)),
                        'change_24h': format_percentage(price_change_24h),
                        'change_7d': format_percentage(price_change_7d),
                        'change_30d': format_percentage(price_change_30d),
                        'market_cap': format_currency(market_data.get('market_cap', {}).get('usd', 0)),
                        'volume_24h': format_currency(market_data.get('total_volume', {}).get('usd', 0))
                    }
                    
                    # Cache result
                    cache_result(cache_key, result, 1800)  # Cache for 30 minutes
                    
                    return result
                else:
                    logger.error(f"Error fetching token data: {response.status}")
                    return None
    except Exception as e:
        logger.exception(f"Error in get_token_sentiment: {e}")
        return None

async def get_trading_signals(token_id):
    """Get trading signals for a specific token"""
    # Get token sentiment first
    token_data = await get_token_sentiment(token_id)
    if not token_data:
        return None
    
    try:
        # Extract price changes
        change_24h = float(token_data['change_24h'].replace('%', ''))
        change_7d = float(token_data['change_7d'].replace('%', ''))
        change_30d = float(token_data['change_30d'].replace('%', ''))
        
        # Simple signal generation logic
        signals = []
        
        # Short-term signals (24h)
        if change_24h > 5:
            signals.append({
                'type': 'short_term',
                'signal': 'strong_buy',
                'reason': f"Price up {token_data['change_24h']} in last 24 hours"
            })
        elif change_24h > 2:
            signals.append({
                'type': 'short_term',
                'signal': 'buy',
                'reason': f"Price up {token_data['change_24h']} in last 24 hours"
            })
        elif change_24h < -5:
            signals.append({
                'type': 'short_term',
                'signal': 'strong_sell',
                'reason': f"Price down {token_data['change_24h']} in last 24 hours"
            })
        elif change_24h < -2:
            signals.append({
                'type': 'short_term',
                'signal': 'sell',
                'reason': f"Price down {token_data['change_24h']} in last 24 hours"
            })
        
        # Medium-term signals (7d vs 24h trend)
        if change_7d > 0 and change_24h < 0:
            signals.append({
                'type': 'medium_term',
                'signal': 'buy_dip',
                'reason': f"Positive 7-day trend ({token_data['change_7d']}) with recent dip ({token_data['change_24h']})"
            })
        elif change_7d < 0 and change_24h > 0:
            signals.append({
                'type': 'medium_term',
                'signal': 'sell_rally',
                'reason': f"Negative 7-day trend ({token_data['change_7d']}) with recent rally ({token_data['change_24h']})"
            })
        
        # Long-term signals (30d)
        if change_30d > 20:
            signals.append({
                'type': 'long_term',
                'signal': 'take_profit',
                'reason': f"Price up {token_data['change_30d']} in last 30 days, consider taking profits"
            })
        elif change_30d < -20:
            signals.append({
                'type': 'long_term',
                'signal': 'accumulate',
                'reason': f"Price down {token_data['change_30d']} in last 30 days, potential accumulation zone"
            })
        
        # If no signals were generated, add a neutral signal
        if not signals:
            signals.append({
                'type': 'general',
                'signal': 'neutral',
                'reason': "No clear trading signals at this time"
            })
        
        return {
            'name': token_data['name'],
            'symbol': token_data['symbol'],
            'price': token_data['price'],
            'signals': signals
        }
    except Exception as e:
        logger.exception(f"Error in get_trading_signals: {e}")
        return None

async def get_yield_entry_recommendation(token_id):
    """Get recommendation on whether it's a good time to enter a yield position"""
    # Get token sentiment and trading signals
    token_data = await get_token_sentiment(token_id)
    trading_signals = await get_trading_signals(token_id)
    
    if not token_data or not trading_signals:
        return None
    
    try:
        # Extract signals
        signals = trading_signals.get('signals', [])
        signal_types = [s['signal'] for s in signals]
        
        # Determine if it's a good time to enter yield position
        recommendation = {
            'name': token_data['name'],
            'symbol': token_data['symbol'],
            'price': token_data['price'],
            'enter_now': False,
            'confidence': 'low',
            'reasoning': []
        }
        
        # Check for buy signals
        if 'strong_buy' in signal_types or 'buy' in signal_types or 'buy_dip' in signal_types:
            recommendation['enter_now'] = True
            recommendation['confidence'] = 'medium'
            recommendation['reasoning'].append("Positive short or medium-term signals detected")
        
        # Check for accumulation signal (good for yield farming)
        if 'accumulate' in signal_types:
            recommendation['enter_now'] = True
            recommendation['confidence'] = 'high'
            recommendation['reasoning'].append("Token is in accumulation zone, good for yield positions")
        
        # Check sentiment
        if token_data['sentiment'] in ['bullish', 'very bullish']:
            if recommendation['enter_now']:
                recommendation['confidence'] = 'high'
            recommendation['reasoning'].append(f"Overall sentiment is {token_data['sentiment']}")
        elif token_data['sentiment'] in ['bearish', 'very bearish']:
            recommendation['enter_now'] = False
            recommendation['confidence'] = 'high'
            recommendation['reasoning'].append(f"Overall sentiment is {token_data['sentiment']}, consider waiting")
        
        # If no specific reasoning, add default
        if not recommendation['reasoning']:
            recommendation['reasoning'].append("No strong signals in either direction")
        
        return recommendation
    except Exception as e:
        logger.exception(f"Error in get_yield_entry_recommendation: {e}")
        return None