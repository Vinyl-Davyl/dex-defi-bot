import os
from dotenv import load_dotenv
import sys
import os.path

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.utils.logger import setup_logger

# Setup logger
logger = setup_logger(__name__)

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for the DeFi Yield Finder application"""
    
    # Telegram Bot Token
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    
    # Fireworks API Key
    FIREWORKS_API_KEY = os.getenv("FIREWORKS_API_KEY")
    
    # Fireworks API URL
    FIREWORKS_API_URL = "https://api.fireworks.ai/inference/v1/completions"
    
    # Default AI model
    DEFAULT_MODEL = "accounts/sentientfoundation/models/dobby-unhinged-llama-3-3-70b-new"
    
    # DeFi APIs
    DEFILLAMA_API_URL = "https://yields.llama.fi/pools"
    COINGECKO_API_URL = "https://api.coingecko.com/api/v3"
    
    # Trading APIs
    TRADING_VIEW_API_URL = "https://scanner.tradingview.com/crypto/scan"
    
    # Logging level
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Maximum message length for Telegram
    MAX_MESSAGE_LENGTH = 4096
    
    # Cache timeout in seconds
    CACHE_TIMEOUT = 300  # 5 minutes
    
    @classmethod
    def validate(cls):
        """Validate configuration settings"""
        if not cls.TELEGRAM_BOT_TOKEN or cls.TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
            logger.error("TELEGRAM_BOT_TOKEN is not set properly")
            return False
        
        if not cls.FIREWORKS_API_KEY or cls.FIREWORKS_API_KEY == "YOUR_FIREWORKS_API_KEY":
            logger.warning("FIREWORKS_API_KEY is not set properly, some features may not work")
        
        return True