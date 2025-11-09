import asyncio
import sys
import os.path
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.config.config import Config
from src.utils.logger import setup_logger
from src.utils.helpers import is_valid_url, format_message, clean_text
from src.services.yield_service import (
    get_top_yields, get_yield_by_protocol, get_yield_by_chain,
    get_yield_comparison, get_yield_recommendations
)
from src.services.trading_service import (
    get_token_price, get_market_sentiment, get_token_sentiment,
    get_trading_signals, get_yield_entry_recommendation
)
from src.services.ai_service import (
    analyze_yield_opportunity, generate_trading_insight,
    explain_yield_comparison, summarize_market_sentiment,
    explain_yield_entry_recommendation
)

# Setup logger
logger = setup_logger(__name__)

# Command descriptions
COMMAND_DESCRIPTIONS = {
    "start": "Start the bot and get welcome message",
    "help": "Show available commands and their descriptions",
    "top_yields": "Get top yield opportunities (e.g., /top_yields 10)",
    "yield_by_protocol": "Get yields for a specific protocol (e.g., /yield_by_protocol aave)",
    "yield_by_chain": "Get yields for a specific blockchain (e.g., /yield_by_chain ethereum)",
    "compare_yields": "Compare yields between protocols (e.g., /compare_yields aave,compound)",
    "recommend_yields": "Get personalized yield recommendations (e.g., /recommend_yields stable)",
    "token_price": "Get current price of a token (e.g., /token_price bitcoin)",
    "market_sentiment": "Get overall market sentiment",
    "token_sentiment": "Get sentiment analysis for a token (e.g., /token_sentiment ethereum)",
    "trading_signals": "Get trading signals for a token (e.g., /trading_signals bitcoin)",
    "yield_entry": "Check if it's a good time to enter a yield position (e.g., /yield_entry ethereum)"
}

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome message when the command /start is issued."""
    user = update.effective_user
    welcome_message = (
        f"👋 Hello {user.first_name}! Welcome to the DeFi Yield Finder Bot.\n\n"
        f"I can help you find the best yield opportunities in DeFi and provide market insights.\n\n"
        f"Use /help to see all available commands."
    )
    await update.message.reply_text(welcome_message)
    logger.info(f"User {user.id} started the bot")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message with all available commands when the command /help is issued."""
    help_text = "🤖 **Available Commands:**\n\n"
    
    for command, description in COMMAND_DESCRIPTIONS.items():
        help_text += f"/{command} - {description}\n"
    
    await update.message.reply_text(help_text, parse_mode="Markdown")
    logger.info(f"User {update.effective_user.id} requested help")

async def top_yields_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get top yield opportunities."""
    try:
        # Get limit from args or default to 5
        limit = 5
        if context.args and context.args[0].isdigit():
            limit = min(int(context.args[0]), 20)  # Cap at 20 to avoid huge messages
        
        # Send typing action
        await update.message.chat.send_action(action="typing")
        
        # Get top yields
        yields = await get_top_yields(limit)
        
        if not yields or len(yields) == 0:
            await update.message.reply_text("Sorry, I couldn't find any yield opportunities at the moment.")
            return
        
        # Format response
        response = f"🔝 **Top {len(yields)} Yield Opportunities**\n\n"
        
        for i, yield_data in enumerate(yields, 1):
            response += (
                f"{i}. **{yield_data['project']} on {yield_data['chain']}**\n"
                f"   Pool: {yield_data['pool']}\n"
                f"   APY: {yield_data['apy']}%\n"
                f"   TVL: ${yield_data['tvl']}\n"
                f"   IL Risk: {yield_data['ilRisk']}\n\n"
            )
        
        # Add analyze button for the first yield
        keyboard = [
            [InlineKeyboardButton("🔍 Analyze Top Opportunity", callback_data=f"analyze_yield_{0}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(response, parse_mode="Markdown", reply_markup=reply_markup)
        logger.info(f"User {update.effective_user.id} requested top {limit} yields")
    except Exception as e:
        logger.exception(f"Error in top_yields_command: {e}")
        await update.message.reply_text("Sorry, an error occurred while fetching yield opportunities.")

async def yield_by_protocol_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get yields for a specific protocol."""
    try:
        if not context.args or not context.args[0]:
            await update.message.reply_text("Please specify a protocol name. Example: /yield_by_protocol aave")
            return
        
        protocol = context.args[0].lower()
        
        # Send typing action
        await update.message.chat.send_action(action="typing")
        
        # Get yields by protocol
        yields = await get_yield_by_protocol(protocol)
        
        if not yields or len(yields) == 0:
            await update.message.reply_text(f"Sorry, I couldn't find any yield opportunities for {protocol}.")
            return
        
        # Format response
        response = f"📊 **Yield Opportunities on {protocol.capitalize()}**\n\n"
        
        for i, yield_data in enumerate(yields, 1):
            response += (
                f"{i}. **{yield_data['pool']} on {yield_data['chain']}**\n"
                f"   APY: {yield_data['apy']}%\n"
                f"   TVL: ${yield_data['tvl']}\n"
                f"   IL Risk: {yield_data['ilRisk']}\n\n"
            )
        
        # Add analyze buttons for the first 3 yields (or fewer if less available)
        keyboard = []
        for i in range(min(3, len(yields))):
            keyboard.append([InlineKeyboardButton(f"🔍 Analyze Option {i+1}", callback_data=f"analyze_yield_{i}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(response, parse_mode="Markdown", reply_markup=reply_markup)
        logger.info(f"User {update.effective_user.id} requested yields for protocol {protocol}")
    except Exception as e:
        logger.exception(f"Error in yield_by_protocol_command: {e}")
        await update.message.reply_text("Sorry, an error occurred while fetching yield opportunities.")

async def yield_by_chain_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get yields for a specific blockchain."""
    try:
        if not context.args or not context.args[0]:
            await update.message.reply_text("Please specify a blockchain name. Example: /yield_by_chain ethereum")
            return
        
        chain = context.args[0].lower()
        
        # Send typing action
        await update.message.chat.send_action(action="typing")
        
        # Get yields by chain
        yields = await get_yield_by_chain(chain)
        
        if not yields or len(yields) == 0:
            await update.message.reply_text(f"Sorry, I couldn't find any yield opportunities on {chain}.")
            return
        
        # Format response
        response = f"⛓️ **Yield Opportunities on {chain.capitalize()}**\n\n"
        
        for i, yield_data in enumerate(yields, 1):
            response += (
                f"{i}. **{yield_data['project']} - {yield_data['pool']}**\n"
                f"   APY: {yield_data['apy']}%\n"
                f"   TVL: ${yield_data['tvl']}\n"
                f"   IL Risk: {yield_data['ilRisk']}\n\n"
            )
        
        # Add analyze buttons for the first 3 yields (or fewer if less available)
        keyboard = []
        for i in range(min(3, len(yields))):
            keyboard.append([InlineKeyboardButton(f"🔍 Analyze Option {i+1}", callback_data=f"analyze_yield_{i}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(response, parse_mode="Markdown", reply_markup=reply_markup)
        logger.info(f"User {update.effective_user.id} requested yields for chain {chain}")
    except Exception as e:
        logger.exception(f"Error in yield_by_chain_command: {e}")
        await update.message.reply_text("Sorry, an error occurred while fetching yield opportunities.")

async def compare_yields_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Compare yields between protocols."""
    try:
        if not context.args or not context.args[0]:
            await update.message.reply_text("Please specify protocols to compare. Example: /compare_yields aave,compound")
            return
        
        # Parse protocols from comma-separated list
        protocols = [p.strip().lower() for p in context.args[0].split(',')]
        
        if len(protocols) < 2:
            await update.message.reply_text("Please specify at least two protocols to compare.")
            return
        
        # Send typing action
        await update.message.chat.send_action(action="typing")
        
        # Get yield comparison
        comparison = await get_yield_comparison(protocols)
        
        if not comparison or len(comparison) == 0:
            await update.message.reply_text(f"Sorry, I couldn't find comparable yield opportunities for these protocols.")
            return
        
        # Format response
        response = f"🔄 **Yield Comparison**\n\n"
        
        for i, yield_data in enumerate(comparison, 1):
            response += (
                f"{i}. **{yield_data['project']} on {yield_data['chain']}**\n"
                f"   Pool: {yield_data['pool']}\n"
                f"   APY: {yield_data['apy']}%\n"
                f"   TVL: ${yield_data['tvl']}\n"
                f"   IL Risk: {yield_data['ilRisk']}\n\n"
            )
        
        # Add explain comparison button
        keyboard = [
            [InlineKeyboardButton("🧠 Explain Comparison", callback_data="explain_comparison")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Store comparison data in context for callback
        context.user_data['comparison_data'] = comparison
        
        await update.message.reply_text(response, parse_mode="Markdown", reply_markup=reply_markup)
        logger.info(f"User {update.effective_user.id} compared yields for protocols: {', '.join(protocols)}")
    except Exception as e:
        logger.exception(f"Error in compare_yields_command: {e}")
        await update.message.reply_text("Sorry, an error occurred while comparing yield opportunities.")

async def recommend_yields_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get personalized yield recommendations."""
    try:
        # Default to 'all' if no preference specified
        preference = 'all'
        if context.args and context.args[0]:
            preference = context.args[0].lower()
        
        # Send typing action
        await update.message.chat.send_action(action="typing")
        
        # Get yield recommendations
        recommendations = await get_yield_recommendations(preference)
        
        if not recommendations or len(recommendations) == 0:
            await update.message.reply_text(f"Sorry, I couldn't find any yield recommendations for '{preference}'.")
            return
        
        # Format response
        response = f"🎯 **Recommended Yield Opportunities for '{preference}'**\n\n"
        
        for i, yield_data in enumerate(recommendations, 1):
            response += (
                f"{i}. **{yield_data['project']} on {yield_data['chain']}**\n"
                f"   Pool: {yield_data['pool']}\n"
                f"   APY: {yield_data['apy']}%\n"
                f"   TVL: ${yield_data['tvl']}\n"
                f"   IL Risk: {yield_data['ilRisk']}\n"
                f"   Risk Score: {yield_data.get('risk_score', 'N/A')}/10\n\n"
            )
        
        # Add analyze buttons for the first 3 recommendations (or fewer if less available)
        keyboard = []
        for i in range(min(3, len(recommendations))):
            keyboard.append([InlineKeyboardButton(f"🔍 Analyze Option {i+1}", callback_data=f"analyze_yield_{i}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Store yield data in context for callback
        context.user_data['yield_data'] = recommendations
        
        await update.message.reply_text(response, parse_mode="Markdown", reply_markup=reply_markup)
        logger.info(f"User {update.effective_user.id} requested yield recommendations for '{preference}'")
    except Exception as e:
        logger.exception(f"Error in recommend_yields_command: {e}")
        await update.message.reply_text("Sorry, an error occurred while fetching yield recommendations.")

async def token_price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get current price of a token."""
    try:
        if not context.args or not context.args[0]:
            await update.message.reply_text("Please specify a token. Example: /token_price bitcoin")
            return
        
        token_id = context.args[0].lower()
        
        # Send typing action
        await update.message.chat.send_action(action="typing")
        
        # Get token price
        price_data = await get_token_price(token_id)
        
        if not price_data:
            await update.message.reply_text(f"Sorry, I couldn't find price data for {token_id}.")
            return
        
        # Format response
        response = f"💰 **{token_id.capitalize()} Price**\n\n"
        response += f"Current Price: {price_data['price']}\n"
        response += f"24h Change: {price_data['change_24h']}\n"
        
        # Add sentiment analysis button
        keyboard = [
            [InlineKeyboardButton("🧠 Get Sentiment Analysis", callback_data=f"token_sentiment_{token_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(response, parse_mode="Markdown", reply_markup=reply_markup)
        logger.info(f"User {update.effective_user.id} requested price for {token_id}")
    except Exception as e:
        logger.exception(f"Error in token_price_command: {e}")
        await update.message.reply_text("Sorry, an error occurred while fetching token price.")

async def market_sentiment_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get overall market sentiment."""
    try:
        # Send typing action
        await update.message.chat.send_action(action="typing")
        
        # Get market sentiment
        sentiment_data = await get_market_sentiment()
        
        if not sentiment_data:
            await update.message.reply_text("Sorry, I couldn't fetch market sentiment data at the moment.")
            return
        
        # Format response
        response = f"📊 **Market Sentiment**\n\n"
        response += f"Overall: {sentiment_data['sentiment'].capitalize()}\n"
        response += f"24h Average Change: {sentiment_data['avg_change_24h']}\n\n"
        
        # Add top gainers
        response += "**Top Gainers:**\n"
        for coin in sentiment_data['top_gainers']:
            response += f"- {coin['name']} ({coin['symbol']}): {coin['change_24h']}\n"
        
        response += "\n**Top Losers:**\n"
        for coin in sentiment_data['top_losers']:
            response += f"- {coin['name']} ({coin['symbol']}): {coin['change_24h']}\n"
        
        # Add AI analysis button
        keyboard = [
            [InlineKeyboardButton("🧠 Get AI Analysis", callback_data="analyze_market_sentiment")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Store sentiment data in context for callback
        context.user_data['market_sentiment'] = sentiment_data
        
        await update.message.reply_text(response, parse_mode="Markdown", reply_markup=reply_markup)
        logger.info(f"User {update.effective_user.id} requested market sentiment")
    except Exception as e:
        logger.exception(f"Error in market_sentiment_command: {e}")
        await update.message.reply_text("Sorry, an error occurred while fetching market sentiment.")

async def token_sentiment_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get sentiment analysis for a token."""
    try:
        if not context.args or not context.args[0]:
            await update.message.reply_text("Please specify a token. Example: /token_sentiment ethereum")
            return
        
        token_id = context.args[0].lower()
        
        # Send typing action
        await update.message.chat.send_action(action="typing")
        
        # Get token sentiment
        sentiment_data = await get_token_sentiment(token_id)
        
        if not sentiment_data:
            await update.message.reply_text(f"Sorry, I couldn't find sentiment data for {token_id}.")
            return
        
        # Format response
        response = f"🔍 **{sentiment_data['name']} ({sentiment_data['symbol']}) Sentiment**\n\n"
        response += f"Current Price: {sentiment_data['price']}\n"
        response += f"Sentiment: {sentiment_data['sentiment'].capitalize()}\n\n"
        
        response += "**Price Changes:**\n"
        response += f"24h: {sentiment_data['change_24h']}\n"
        response += f"7d: {sentiment_data['change_7d']}\n"
        response += f"30d: {sentiment_data['change_30d']}\n\n"
        
        response += f"Market Cap: {sentiment_data['market_cap']}\n"
        response += f"24h Volume: {sentiment_data['volume_24h']}\n"
        
        # Add trading signals and AI analysis buttons
        keyboard = [
            [InlineKeyboardButton("📈 Trading Signals", callback_data=f"trading_signals_{token_id}")],
            [InlineKeyboardButton("🧠 AI Analysis", callback_data=f"analyze_token_{token_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Store sentiment data in context for callback
        context.user_data['token_sentiment'] = sentiment_data
        
        await update.message.reply_text(response, parse_mode="Markdown", reply_markup=reply_markup)
        logger.info(f"User {update.effective_user.id} requested sentiment for {token_id}")
    except Exception as e:
        logger.exception(f"Error in token_sentiment_command: {e}")
        await update.message.reply_text("Sorry, an error occurred while fetching token sentiment.")

async def trading_signals_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get trading signals for a token."""
    try:
        if not context.args or not context.args[0]:
            await update.message.reply_text("Please specify a token. Example: /trading_signals bitcoin")
            return
        
        token_id = context.args[0].lower()
        
        # Send typing action
        await update.message.chat.send_action(action="typing")
        
        # Get trading signals
        signals_data = await get_trading_signals(token_id)
        
        if not signals_data:
            await update.message.reply_text(f"Sorry, I couldn't find trading signals for {token_id}.")
            return
        
        # Format response
        response = f"📈 **{signals_data['name']} ({signals_data['symbol']}) Trading Signals**\n\n"
        response += f"Current Price: {signals_data['price']}\n\n"
        
        response += "**Signals:**\n"
        for signal in signals_data['signals']:
            signal_emoji = "🟢" if signal['signal'] in ['strong_buy', 'buy', 'buy_dip'] else \
                          "🔴" if signal['signal'] in ['strong_sell', 'sell', 'sell_rally'] else "⚪️"
            
            signal_text = signal['signal'].replace('_', ' ').capitalize()
            response += f"{signal_emoji} {signal['type'].capitalize()}: {signal_text}\n"
            response += f"   Reason: {signal['reason']}\n\n"
        
        # Add yield entry recommendation button
        keyboard = [
            [InlineKeyboardButton("🌾 Yield Entry Recommendation", callback_data=f"yield_entry_{token_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(response, parse_mode="Markdown", reply_markup=reply_markup)
        logger.info(f"User {update.effective_user.id} requested trading signals for {token_id}")
    except Exception as e:
        logger.exception(f"Error in trading_signals_command: {e}")
        await update.message.reply_text("Sorry, an error occurred while fetching trading signals.")

async def yield_entry_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check if it's a good time to enter a yield position."""
    try:
        if not context.args or not context.args[0]:
            await update.message.reply_text("Please specify a token. Example: /yield_entry ethereum")
            return
        
        token_id = context.args[0].lower()
        
        # Send typing action
        await update.message.chat.send_action(action="typing")
        
        # Get yield entry recommendation
        recommendation = await get_yield_entry_recommendation(token_id)
        
        if not recommendation:
            await update.message.reply_text(f"Sorry, I couldn't generate a yield entry recommendation for {token_id}.")
            return
        
        # Format response
        response = f"🌾 **{recommendation['name']} ({recommendation['symbol']}) Yield Entry Recommendation**\n\n"
        response += f"Current Price: {recommendation['price']}\n"
        response += f"Recommendation: {'✅ Enter now' if recommendation['enter_now'] else '⏳ Wait'}\n"
        response += f"Confidence: {recommendation['confidence'].capitalize()}\n\n"
        
        response += "**Reasoning:**\n"
        for reason in recommendation['reasoning']:
            response += f"- {reason}\n"
        
        # Add AI explanation button
        keyboard = [
            [InlineKeyboardButton("🧠 Get Detailed Explanation", callback_data=f"explain_yield_entry")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Store recommendation data in context for callback
        context.user_data['yield_entry_recommendation'] = recommendation
        
        await update.message.reply_text(response, parse_mode="Markdown", reply_markup=reply_markup)
        logger.info(f"User {update.effective_user.id} requested yield entry recommendation for {token_id}")
    except Exception as e:
        logger.exception(f"Error in yield_entry_command: {e}")
        await update.message.reply_text("Sorry, an error occurred while generating yield entry recommendation.")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()
    
    try:
        callback_data = query.data
        
        # Send typing action
        await query.message.chat.send_action(action="typing")
        
        if callback_data.startswith("analyze_yield_"):
            # Extract yield index
            index = int(callback_data.split("_")[-1])
            
            # Get yield data from context
            yield_data = context.user_data.get('yield_data', [])
            if not yield_data or index >= len(yield_data):
                await query.message.reply_text("Sorry, I couldn't find the yield data to analyze.")
                return
            
            # Analyze yield opportunity
            analysis = await analyze_yield_opportunity(yield_data[index])
            
            await query.message.reply_text(f"🧠 **AI Analysis**\n\n{analysis}", parse_mode="Markdown")
        
        elif callback_data == "explain_comparison":
            # Get comparison data from context
            comparison_data = context.user_data.get('comparison_data', [])
            if not comparison_data:
                await query.message.reply_text("Sorry, I couldn't find the comparison data to explain.")
                return
            
            # Explain yield comparison
            explanation = await explain_yield_comparison(comparison_data)
            
            await query.message.reply_text(f"🧠 **Comparison Explanation**\n\n{explanation}", parse_mode="Markdown")
        
        elif callback_data.startswith("token_sentiment_"):
            # Extract token id
            token_id = callback_data.split("_")[-1]
            
            # Get token sentiment
            sentiment_data = await get_token_sentiment(token_id)
            if not sentiment_data:
                await query.message.reply_text(f"Sorry, I couldn't find sentiment data for {token_id}.")
                return
            
            # Format response
            response = f"🔍 **{sentiment_data['name']} ({sentiment_data['symbol']}) Sentiment**\n\n"
            response += f"Current Price: {sentiment_data['price']}\n"
            response += f"Sentiment: {sentiment_data['sentiment'].capitalize()}\n\n"
            
            response += "**Price Changes:**\n"
            response += f"24h: {sentiment_data['change_24h']}\n"
            response += f"7d: {sentiment_data['change_7d']}\n"
            response += f"30d: {sentiment_data['change_30d']}\n\n"
            
            response += f"Market Cap: {sentiment_data['market_cap']}\n"
            response += f"24h Volume: {sentiment_data['volume_24h']}\n"
            
            await query.message.reply_text(response, parse_mode="Markdown")
        
        elif callback_data == "analyze_market_sentiment":
            # Get market sentiment data from context
            sentiment_data = context.user_data.get('market_sentiment', None)
            if not sentiment_data:
                await query.message.reply_text("Sorry, I couldn't find the market sentiment data to analyze.")
                return
            
            # Summarize market sentiment
            summary = await summarize_market_sentiment(sentiment_data)
            
            await query.message.reply_text(f"🧠 **Market Analysis**\n\n{summary}", parse_mode="Markdown")
        
        elif callback_data.startswith("analyze_token_"):
            # Extract token id
            token_id = callback_data.split("_")[-1]
            
            # Get token sentiment
            token_data = await get_token_sentiment(token_id)
            if not token_data:
                await query.message.reply_text(f"Sorry, I couldn't find data for {token_id}.")
                return
            
            # Get market sentiment for context
            market_sentiment = await get_market_sentiment()
            
            # Generate trading insight
            insight = await generate_trading_insight(token_data, market_sentiment)
            
            await query.message.reply_text(f"🧠 **Trading Insights**\n\n{insight}", parse_mode="Markdown")
        
        elif callback_data.startswith("trading_signals_"):
            # Extract token id
            token_id = callback_data.split("_")[-1]
            
            # Get trading signals
            signals_data = await get_trading_signals(token_id)
            if not signals_data:
                await query.message.reply_text(f"Sorry, I couldn't find trading signals for {token_id}.")
                return
            
            # Format response
            response = f"📈 **{signals_data['name']} ({signals_data['symbol']}) Trading Signals**\n\n"
            response += f"Current Price: {signals_data['price']}\n\n"
            
            response += "**Signals:**\n"
            for signal in signals_data['signals']:
                signal_emoji = "🟢" if signal['signal'] in ['strong_buy', 'buy', 'buy_dip'] else \
                              "🔴" if signal['signal'] in ['strong_sell', 'sell', 'sell_rally'] else "⚪️"
                
                signal_text = signal['signal'].replace('_', ' ').capitalize()
                response += f"{signal_emoji} {signal['type'].capitalize()}: {signal_text}\n"
                response += f"   Reason: {signal['reason']}\n\n"
            
            await query.message.reply_text(response, parse_mode="Markdown")
        
        elif callback_data.startswith("yield_entry_"):
            # Extract token id
            token_id = callback_data.split("_")[-1]
            
            # Get yield entry recommendation
            recommendation = await get_yield_entry_recommendation(token_id)
            if not recommendation:
                await query.message.reply_text(f"Sorry, I couldn't generate a yield entry recommendation for {token_id}.")
                return
            
            # Format response
            response = f"🌾 **{recommendation['name']} ({recommendation['symbol']}) Yield Entry Recommendation**\n\n"
            response += f"Current Price: {recommendation['price']}\n"
            response += f"Recommendation: {'✅ Enter now' if recommendation['enter_now'] else '⏳ Wait'}\n"
            response += f"Confidence: {recommendation['confidence'].capitalize()}\n\n"
            
            response += "**Reasoning:**\n"
            for reason in recommendation['reasoning']:
                response += f"- {reason}\n"
            
            # Store recommendation data in context for callback
            context.user_data['yield_entry_recommendation'] = recommendation
            
            # Add AI explanation button
            keyboard = [
                [InlineKeyboardButton("🧠 Get Detailed Explanation", callback_data="explain_yield_entry")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.message.reply_text(response, parse_mode="Markdown", reply_markup=reply_markup)
        
        elif callback_data == "explain_yield_entry":
            # Get yield entry recommendation from context
            recommendation = context.user_data.get('yield_entry_recommendation', None)
            if not recommendation:
                await query.message.reply_text("Sorry, I couldn't find the yield entry recommendation to explain.")
                return
            
            # Explain yield entry recommendation
            explanation = await explain_yield_entry_recommendation(recommendation)
            
            await query.message.reply_text(f"🧠 **Detailed Explanation**\n\n{explanation}", parse_mode="Markdown")
        
        else:
            await query.message.reply_text("Sorry, I couldn't process that request.")
        
        logger.info(f"User {update.effective_user.id} clicked button: {callback_data}")
    except Exception as e:
        logger.exception(f"Error in button_callback: {e}")
        await query.message.reply_text("Sorry, an error occurred while processing your request.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle non-command messages."""
    message_text = update.message.text
    user_id = update.effective_user.id
    
    # Log the message with more details for debugging
    logger.info(f"Received message from user {user_id}: {message_text}")
    logger.info(f"Full update object: {update}")
    
    # For now, just provide help message for non-command messages
    await update.message.reply_text(
        "I can help you find the best yield opportunities in DeFi and provide market insights. "
        "Use /help to see all available commands."
    )

def setup_bot(request_timeout=None):
    """Setup and return the bot application."""
    # Create the Application
    if request_timeout:
        application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).request_timeout(request_timeout).build()
    else:
        application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("top_yields", top_yields_command))
    application.add_handler(CommandHandler("yield_by_protocol", yield_by_protocol_command))
    application.add_handler(CommandHandler("yield_by_chain", yield_by_chain_command))
    application.add_handler(CommandHandler("compare_yields", compare_yields_command))
    application.add_handler(CommandHandler("recommend_yields", recommend_yields_command))
    application.add_handler(CommandHandler("token_price", token_price_command))
    application.add_handler(CommandHandler("market_sentiment", market_sentiment_command))
    application.add_handler(CommandHandler("token_sentiment", token_sentiment_command))
    application.add_handler(CommandHandler("trading_signals", trading_signals_command))
    application.add_handler(CommandHandler("yield_entry", yield_entry_command))
    
    # Add callback query handler for buttons
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Add message handler for non-command messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    return application