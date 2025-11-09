import aiohttp
import json
import asyncio
import sys
import os.path

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.config.config import Config
from src.utils.logger import setup_logger

# Setup logger
logger = setup_logger(__name__)

async def generate_ai_response(prompt, model=Config.DEFAULT_MODEL):
    """Generate AI response using Fireworks API"""
    try:
        url = Config.FIREWORKS_API_URL
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {Config.FIREWORKS_API_KEY}"
        }
        
        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant specializing in DeFi, cryptocurrency trading, and yield farming. Provide concise, accurate information and analysis."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    if 'choices' in result and len(result['choices']) > 0:
                        return result['choices'][0]['message']['content']
                    else:
                        logger.error(f"Unexpected response format from Fireworks API: {result}")
                        return "Sorry, I couldn't generate a response at this time."
                else:
                    error_text = await response.text()
                    logger.error(f"Error from Fireworks API: {response.status} - {error_text}")
                    return "Sorry, there was an error generating a response. Please try again later."
    except Exception as e:
        logger.exception(f"Error in generate_ai_response: {e}")
        return "Sorry, an unexpected error occurred. Please try again later."

async def analyze_yield_opportunity(yield_data):
    """Analyze a yield opportunity using AI"""
    try:
        # Format yield data for the prompt
        prompt = f"""Analyze this DeFi yield opportunity and provide insights:

Protocol: {yield_data.get('project', 'Unknown')}
Chain: {yield_data.get('chain', 'Unknown')}
APY: {yield_data.get('apy', 'Unknown')}%
TVL: ${yield_data.get('tvl', 'Unknown')}
Pool: {yield_data.get('pool', 'Unknown')}
IlRisk: {yield_data.get('ilRisk', 'Unknown')}

Please provide:
1. A brief analysis of this yield opportunity
2. Potential risks to be aware of
3. A recommendation on whether this is a good opportunity for:
   a) Conservative investors
   b) Moderate risk investors
   c) High risk investors

Keep your response concise and focused on the most important factors."""
        
        return await generate_ai_response(prompt)
    except Exception as e:
        logger.exception(f"Error in analyze_yield_opportunity: {e}")
        return "Sorry, I couldn't analyze this yield opportunity at this time."

async def generate_trading_insight(token_data, market_sentiment=None):
    """Generate trading insights for a token using AI"""
    try:
        # Format token data for the prompt
        prompt = f"""Provide trading insights for {token_data.get('name', 'this token')} ({token_data.get('symbol', '')}):

Current price: {token_data.get('price', 'Unknown')}
24h change: {token_data.get('change_24h', 'Unknown')}
7d change: {token_data.get('change_7d', 'Unknown')}
30d change: {token_data.get('change_30d', 'Unknown')}
Market cap: {token_data.get('market_cap', 'Unknown')}
24h volume: {token_data.get('volume_24h', 'Unknown')}
Overall sentiment: {token_data.get('sentiment', 'Unknown')}
"""
        
        # Add market sentiment if available
        if market_sentiment:
            prompt += f"""\nMarket context:\nOverall market sentiment: {market_sentiment.get('sentiment', 'Unknown')}\nMarket 24h average change: {market_sentiment.get('avg_change_24h', 'Unknown')}\n"""
        
        prompt += """\nPlease provide:\n1. A brief technical analysis based on the price movements\n2. Key factors that might be influencing this token's price\n3. Short-term outlook (24-48 hours)\n4. Medium-term outlook (1-2 weeks)\n\nKeep your response concise and focused on actionable insights."""
        
        return await generate_ai_response(prompt)
    except Exception as e:
        logger.exception(f"Error in generate_trading_insight: {e}")
        return "Sorry, I couldn't generate trading insights at this time."

async def explain_yield_comparison(comparison_data):
    """Explain the comparison between yield opportunities using AI"""
    try:
        # Format comparison data for the prompt
        protocols = [item.get('project', 'Unknown') for item in comparison_data]
        chains = [item.get('chain', 'Unknown') for item in comparison_data]
        apys = [f"{item.get('apy', 'Unknown')}%" for item in comparison_data]
        tvls = [f"${item.get('tvl', 'Unknown')}" for item in comparison_data]
        
        prompt = """Compare these DeFi yield opportunities and explain the key differences:\n\n"""
        
        for i in range(len(comparison_data)):
            prompt += f"Option {i+1}:\nProtocol: {protocols[i]}\nChain: {chains[i]}\nAPY: {apys[i]}\nTVL: {tvls[i]}\n\n"
        
        prompt += """Please provide:\n1. A comparison of the risk-reward profiles\n2. Which option might be better for different investor types\n3. Any notable advantages or disadvantages of each option\n\nKeep your response concise and focused on helping the user make an informed decision."""
        
        return await generate_ai_response(prompt)
    except Exception as e:
        logger.exception(f"Error in explain_yield_comparison: {e}")
        return "Sorry, I couldn't generate a comparison explanation at this time."

async def summarize_market_sentiment(sentiment_data):
    """Summarize market sentiment using AI"""
    try:
        # Format sentiment data for the prompt
        top_gainers = "\n".join([f"{coin.get('name', 'Unknown')} ({coin.get('symbol', 'Unknown')}): {coin.get('change_24h', 'Unknown')}" 
                               for coin in sentiment_data.get('top_gainers', [])])
        top_losers = "\n".join([f"{coin.get('name', 'Unknown')} ({coin.get('symbol', 'Unknown')}): {coin.get('change_24h', 'Unknown')}" 
                              for coin in sentiment_data.get('top_losers', [])])
        
        prompt = f"""Summarize the current crypto market sentiment based on this data:\n\nOverall market sentiment: {sentiment_data.get('sentiment', 'Unknown')}\nAverage 24h change: {sentiment_data.get('avg_change_24h', 'Unknown')}\n\nTop gainers:\n{top_gainers}\n\nTop losers:\n{top_losers}\n\nPlease provide:\n1. A brief summary of the current market conditions\n2. What this might mean for traders and investors\n3. Key trends or patterns to watch\n\nKeep your response concise and focused on actionable insights."""
        
        return await generate_ai_response(prompt)
    except Exception as e:
        logger.exception(f"Error in summarize_market_sentiment: {e}")
        return "Sorry, I couldn't summarize market sentiment at this time."

async def explain_yield_entry_recommendation(recommendation_data):
    """Explain a yield entry recommendation using AI"""
    try:
        # Format recommendation data for the prompt
        reasoning = "\n".join([f"- {reason}" for reason in recommendation_data.get('reasoning', [])])
        
        prompt = f"""Explain this yield entry recommendation for {recommendation_data.get('name', 'Unknown')} ({recommendation_data.get('symbol', 'Unknown')}):\n\nCurrent price: {recommendation_data.get('price', 'Unknown')}\nRecommendation: {"Enter now" if recommendation_data.get('enter_now', False) else "Wait"}\nConfidence: {recommendation_data.get('confidence', 'Unknown')}\n\nReasoning:\n{reasoning}\n\nPlease provide:\n1. An explanation of this recommendation in simple terms\n2. What factors are most important in this decision\n3. What the user should watch for if they decide to wait\n\nKeep your response conversational and easy to understand for someone new to DeFi."""
        
        return await generate_ai_response(prompt)
    except Exception as e:
        logger.exception(f"Error in explain_yield_entry_recommendation: {e}")
        return "Sorry, I couldn't explain this recommendation at this time."