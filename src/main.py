import asyncio
import os
import sys
import logging

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))  
from src.bot.bot import setup_bot
from src.config.config import Config
from src.utils.logger import setup_logger

# Setup logger
logger = setup_logger(__name__)

async def main():
    """Start the bot."""
    try:
        # Setup and start the bot
        logger.info("Starting DeFi Yield Finder Bot...")
        application = setup_bot(request_timeout=30)
        
        # Start the bot without using run_polling which manages its own event loop
        await application.initialize()
        
        # Log startup information
        logger.info(f"Bot started successfully as @{application.bot.username}")
        logger.info("Press Ctrl+C to stop the bot")
        
        # Use start_polling instead of run_polling to avoid event loop conflicts
        await application.updater.start_polling()
        
        # Keep the main task running
        while True:
            await asyncio.sleep(1)
    except Exception as e:
        logger.exception(f"Error in main: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        # Check if required environment variables are set
        if not Config.TELEGRAM_BOT_TOKEN:
            logger.error("TELEGRAM_BOT_TOKEN is not set in environment variables")
            sys.exit(1)
        
        # Run the bot
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.exception(f"Unhandled exception: {e}")
        sys.exit(1)