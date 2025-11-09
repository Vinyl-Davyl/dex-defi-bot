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
from src.utils.helpers import (
    format_percentage, format_currency, get_cached_result, 
    cache_result, calculate_risk_score
)

# Setup logger
logger = setup_logger(__name__)

async def get_top_yields(limit=10, min_tvl=1000000, chain=None):
    """Get top yield opportunities from DeFiLlama"""
    # Check cache first
    cache_key = f"top_yields_{limit}_{min_tvl}_{chain}"
    cached_data = get_cached_result(cache_key)
    if cached_data:
        return cached_data
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(Config.DEFILLAMA_API_URL) as response:
                if response.status == 200:
                    data = await response.json()
                    pools = data.get('data', [])
                    
                    # Filter pools
                    filtered_pools = []
                    for pool in pools:
                        # Skip if TVL is too low
                        if pool.get('tvlUsd', 0) < min_tvl:
                            continue
                        
                        # Skip if chain doesn't match (if specified)
                        if chain and pool.get('chain') != chain:
                            continue
                        
                        # Add to filtered pools
                        filtered_pools.append(pool)
                    
                    # Sort by APY (descending)
                    sorted_pools = sorted(filtered_pools, key=lambda x: x.get('apy', 0), reverse=True)
                    
                    # Take top N
                    top_pools = sorted_pools[:limit]
                    
                    # Format results
                    results = []
                    for pool in top_pools:
                        # Calculate risk score
                        volatility = pool.get('volatility', 0.5)  # Default medium volatility
                        liquidity = pool.get('tvlUsd', 0)
                        protocol_age = 365  # Default 1 year in days
                        risk_score = calculate_risk_score(volatility, liquidity, protocol_age)
                        
                        results.append({
                            'name': pool.get('name', 'Unknown'),
                            'protocol': pool.get('project', 'Unknown'),
                            'chain': pool.get('chain', 'Unknown'),
                            'apy': format_percentage(pool.get('apy', 0)),
                            'tvl': format_currency(pool.get('tvlUsd', 0)),
                            'risk_score': f"{risk_score:.1f}/10",
                            'url': f"https://defillama.com/yields?project={pool.get('project', '')}"
                        })
                    
                    # Cache results
                    cache_result(cache_key, results, Config.CACHE_TIMEOUT)
                    
                    return results
                else:
                    logger.error(f"Error fetching yields: {response.status}")
                    return []
    except Exception as e:
        logger.exception(f"Error in get_top_yields: {e}")
        return []

async def get_yield_by_protocol(protocol_name, limit=5):
    """Get yield opportunities for a specific protocol"""
    # Check cache first
    cache_key = f"protocol_yields_{protocol_name}_{limit}"
    cached_data = get_cached_result(cache_key)
    if cached_data:
        return cached_data
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(Config.DEFILLAMA_API_URL) as response:
                if response.status == 200:
                    data = await response.json()
                    pools = data.get('data', [])
                    
                    # Filter pools by protocol
                    protocol_pools = [p for p in pools if p.get('project', '').lower() == protocol_name.lower()]
                    
                    # Sort by APY (descending)
                    sorted_pools = sorted(protocol_pools, key=lambda x: x.get('apy', 0), reverse=True)
                    
                    # Take top N
                    top_pools = sorted_pools[:limit]
                    
                    # Format results
                    results = []
                    for pool in top_pools:
                        results.append({
                            'name': pool.get('name', 'Unknown'),
                            'chain': pool.get('chain', 'Unknown'),
                            'apy': format_percentage(pool.get('apy', 0)),
                            'tvl': format_currency(pool.get('tvlUsd', 0)),
                            'url': f"https://defillama.com/yields?project={protocol_name}"
                        })
                    
                    # Cache results
                    cache_result(cache_key, results, Config.CACHE_TIMEOUT)
                    
                    return results
                else:
                    logger.error(f"Error fetching protocol yields: {response.status}")
                    return []
    except Exception as e:
        logger.exception(f"Error in get_yield_by_protocol: {e}")
        return []

async def get_yield_by_chain(chain_name, limit=5):
    """Get top yield opportunities for a specific blockchain"""
    # Check cache first
    cache_key = f"chain_yields_{chain_name}_{limit}"
    cached_data = get_cached_result(cache_key)
    if cached_data:
        return cached_data
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(Config.DEFILLAMA_API_URL) as response:
                if response.status == 200:
                    data = await response.json()
                    pools = data.get('data', [])
                    
                    # Filter pools by chain
                    chain_pools = [p for p in pools if p.get('chain', '').lower() == chain_name.lower()]
                    
                    # Sort by APY (descending)
                    sorted_pools = sorted(chain_pools, key=lambda x: x.get('apy', 0), reverse=True)
                    
                    # Take top N
                    top_pools = sorted_pools[:limit]
                    
                    # Format results
                    results = []
                    for pool in top_pools:
                        results.append({
                            'name': pool.get('name', 'Unknown'),
                            'protocol': pool.get('project', 'Unknown'),
                            'apy': format_percentage(pool.get('apy', 0)),
                            'tvl': format_currency(pool.get('tvlUsd', 0)),
                            'url': f"https://defillama.com/yields?chain={chain_name}"
                        })
                    
                    # Cache results
                    cache_result(cache_key, results, Config.CACHE_TIMEOUT)
                    
                    return results
                else:
                    logger.error(f"Error fetching chain yields: {response.status}")
                    return []
    except Exception as e:
        logger.exception(f"Error in get_yield_by_chain: {e}")
        return []

async def get_yield_comparison(protocol1, protocol2):
    """Compare yields between two protocols"""
    # Get yields for both protocols
    protocol1_yields = await get_yield_by_protocol(protocol1)
    protocol2_yields = await get_yield_by_protocol(protocol2)
    
    # Calculate average APY for each protocol
    try:
        protocol1_avg_apy = sum([float(p['apy'].replace('%', '')) for p in protocol1_yields]) / len(protocol1_yields) if protocol1_yields else 0
        protocol2_avg_apy = sum([float(p['apy'].replace('%', '')) for p in protocol2_yields]) / len(protocol2_yields) if protocol2_yields else 0
        
        return {
            'protocol1': protocol1,
            'protocol1_avg_apy': format_percentage(protocol1_avg_apy),
            'protocol1_pools': len(protocol1_yields),
            'protocol2': protocol2,
            'protocol2_avg_apy': format_percentage(protocol2_avg_apy),
            'protocol2_pools': len(protocol2_yields),
            'difference': format_percentage(protocol1_avg_apy - protocol2_avg_apy),
            'winner': protocol1 if protocol1_avg_apy > protocol2_avg_apy else protocol2
        }
    except Exception as e:
        logger.exception(f"Error in get_yield_comparison: {e}")
        return {
            'protocol1': protocol1,
            'protocol2': protocol2,
            'error': str(e)
        }

async def get_yield_recommendations(risk_tolerance='medium', min_tvl=1000000, limit=5):
    """Get yield recommendations based on risk tolerance"""
    # Map risk tolerance to filter parameters
    risk_params = {
        'low': {'min_tvl': 10000000, 'max_volatility': 0.3},  # $10M TVL, low volatility
        'medium': {'min_tvl': 1000000, 'max_volatility': 0.6},  # $1M TVL, medium volatility
        'high': {'min_tvl': 100000, 'max_volatility': 1.0}      # $100K TVL, any volatility
    }
    
    # Use parameters based on risk tolerance, default to medium
    params = risk_params.get(risk_tolerance.lower(), risk_params['medium'])
    
    # Get all yields
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(Config.DEFILLAMA_API_URL) as response:
                if response.status == 200:
                    data = await response.json()
                    pools = data.get('data', [])
                    
                    # Filter pools based on risk parameters
                    filtered_pools = []
                    for pool in pools:
                        # Skip if TVL is too low
                        if pool.get('tvlUsd', 0) < params['min_tvl']:
                            continue
                        
                        # Skip if volatility is too high
                        if pool.get('volatility', 0.5) > params['max_volatility']:
                            continue
                        
                        # Calculate risk score
                        volatility = pool.get('volatility', 0.5)
                        liquidity = pool.get('tvlUsd', 0)
                        protocol_age = 365  # Default 1 year in days
                        risk_score = calculate_risk_score(volatility, liquidity, protocol_age)
                        
                        # Add risk score to pool data
                        pool['risk_score'] = risk_score
                        
                        # Add to filtered pools
                        filtered_pools.append(pool)
                    
                    # Sort by APY (descending)
                    sorted_pools = sorted(filtered_pools, key=lambda x: x.get('apy', 0), reverse=True)
                    
                    # Take top N
                    top_pools = sorted_pools[:limit]
                    
                    # Format results
                    results = []
                    for pool in top_pools:
                        results.append({
                            'name': pool.get('name', 'Unknown'),
                            'protocol': pool.get('project', 'Unknown'),
                            'chain': pool.get('chain', 'Unknown'),
                            'apy': format_percentage(pool.get('apy', 0)),
                            'tvl': format_currency(pool.get('tvlUsd', 0)),
                            'risk_score': f"{pool.get('risk_score', 5):.1f}/10",
                            'url': f"https://defillama.com/yields?project={pool.get('project', '')}"
                        })
                    
                    return results
                else:
                    logger.error(f"Error fetching yield recommendations: {response.status}")
                    return []
    except Exception as e:
        logger.exception(f"Error in get_yield_recommendations: {e}")
        return []