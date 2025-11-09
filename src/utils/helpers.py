import re
import json
import time
from urllib.parse import urlparse
from datetime import datetime

# Cache for API responses
_cache = {}

def is_valid_url(url):
    """Check if a string is a valid URL"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def format_message(message, max_length=4000):
    """Format message to ensure it doesn't exceed Telegram's message length limit"""
    if len(message) <= max_length:
        return message
    
    # Truncate and add ellipsis
    return message[:max_length-3] + "..."

def format_currency(amount, decimals=2):
    """Format currency amount with commas and specified decimal places"""
    if amount is None:
        return "N/A"
    
    try:
        return f"${amount:,.{decimals}f}"
    except (ValueError, TypeError):
        return str(amount)

def format_percentage(value, decimals=2):
    """Format percentage value with specified decimal places"""
    if value is None:
        return "N/A"
    
    try:
        return f"{value:.{decimals}f}%"
    except (ValueError, TypeError):
        return str(value)

def format_timestamp(timestamp):
    """Format Unix timestamp to human-readable date"""
    if not timestamp:
        return "N/A"
    
    try:
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return str(timestamp)

def cache_result(key, result, timeout=300):
    """Cache a result with expiration"""
    _cache[key] = {
        'data': result,
        'expires': time.time() + timeout
    }

def get_cached_result(key):
    """Get a cached result if it exists and hasn't expired"""
    if key in _cache:
        cache_entry = _cache[key]
        if time.time() < cache_entry['expires']:
            return cache_entry['data']
        # Remove expired entry
        del _cache[key]
    return None

def clean_text(text):
    """Clean text by removing extra whitespace and normalizing line breaks"""
    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)
    # Replace multiple newlines with a double newline
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    return text.strip()

def calculate_apy_difference(apy1, apy2):
    """Calculate the difference between two APY values"""
    try:
        return apy1 - apy2
    except (TypeError, ValueError):
        return None

def calculate_risk_score(volatility, liquidity, protocol_age):
    """Calculate a simple risk score based on volatility, liquidity, and protocol age"""
    try:
        # Normalize inputs to 0-10 scale
        vol_score = min(10, volatility * 10)  # Higher volatility = higher risk
        liq_score = max(0, 10 - (liquidity / 1000000))  # Lower liquidity = higher risk
        age_score = max(0, 10 - (protocol_age / 30))  # Newer protocol = higher risk
        
        # Weighted average (volatility has highest weight)
        risk_score = (vol_score * 0.5) + (liq_score * 0.3) + (age_score * 0.2)
        
        return min(10, max(0, risk_score))
    except (TypeError, ValueError):
        return 5  # Default medium risk