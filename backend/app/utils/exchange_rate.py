"""
汇率转换工具
使用公共API获取汇率，通过美元作为中间货币进行转换
"""
import logging
import httpx
from typing import Optional, Dict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# 汇率缓存（避免频繁请求API）
_exchange_rate_cache: Dict[str, tuple[float, datetime]] = {}
CACHE_DURATION = timedelta(hours=1)  # 缓存1小时


async def get_exchange_rate_to_cny(currency: str) -> float:
    """
    获取指定货币对人民币的汇率
    
    Args:
        currency: 货币代码（如 USD, EUR, JPY 等）
    
    Returns:
        1单位该货币等于多少人民币
    """
    if currency.upper() == "CNY":
        return 1.0
    
    # 检查缓存
    cache_key = currency.upper()
    if cache_key in _exchange_rate_cache:
        rate, cached_time = _exchange_rate_cache[cache_key]
        if datetime.now() - cached_time < CACHE_DURATION:
            return rate
    
    try:
        # 使用 exchangerate-api.com 的免费API
        # 先获取美元对人民币的汇率
        async with httpx.AsyncClient(timeout=5.0) as client:
            # 获取USD到CNY的汇率
            usd_to_cny_url = "https://api.exchangerate-api.com/v4/latest/USD"
            response = await client.get(usd_to_cny_url)
            response.raise_for_status()
            usd_rates = response.json()
            
            usd_to_cny = usd_rates["rates"].get("CNY", 7.0)  # 默认值7.0
            
            # 如果目标货币是USD，直接返回
            if currency.upper() == "USD":
                rate = usd_to_cny
                _exchange_rate_cache[cache_key] = (rate, datetime.now())
                return rate
            
            # 获取目标货币对USD的汇率
            target_currency = currency.upper()
            target_to_usd = usd_rates["rates"].get(target_currency)
            
            if target_to_usd is None:
                logger.warning(f"无法获取 {target_currency} 的汇率，使用默认值")
                # 如果无法获取，尝试使用另一个API
                return await _get_exchange_rate_fallback(currency, usd_to_cny)
            
            # 通过USD转换：1 CNY = 1/USD_to_CNY USD
            # 1 target = target_to_usd USD
            # 1 target = target_to_usd * usd_to_cny CNY
            target_to_cny = target_to_usd * usd_to_cny
            
            # 更新缓存
            _exchange_rate_cache[cache_key] = (target_to_cny, datetime.now())
            return target_to_cny
            
    except Exception as e:
        logger.error(f"获取汇率失败: {str(e)}")
        # 返回默认汇率（基于常见货币的近似值）
        return _get_default_rate(currency)


async def _get_exchange_rate_fallback(currency: str, usd_to_cny: float) -> float:
    """
    备用方案：使用fixer.io或其他API
    """
    try:
        # 可以在这里添加其他API作为备用
        # 暂时返回基于USD的估算值
        currency_upper = currency.upper()
        
        # 常见货币对USD的近似汇率（如果API失败时的备用值）
        common_rates_to_usd = {
            "EUR": 0.92,
            "GBP": 0.79,
            "JPY": 150.0,
            "AUD": 1.52,
            "CAD": 1.35,
            "CHF": 0.88,
            "HKD": 7.8,
            "SGD": 1.34,
        }
        
        if currency_upper in common_rates_to_usd:
            rate_to_usd = common_rates_to_usd[currency_upper]
            return rate_to_usd * usd_to_cny
        
        # 如果都不匹配，返回默认值
        logger.warning(f"未知货币 {currency_upper}，使用默认汇率")
        return usd_to_cny  # 假设与USD相同
        
    except Exception as e:
        logger.error(f"备用汇率获取失败: {str(e)}")
        return _get_default_rate(currency)


def _get_default_rate(currency: str) -> float:
    """
    获取默认汇率（当API失败时使用）
    """
    currency_upper = currency.upper()
    default_rates = {
        "USD": 7.0,
        "EUR": 7.6,
        "GBP": 8.8,
        "JPY": 0.047,
        "AUD": 4.6,
        "CAD": 5.1,
        "CHF": 7.8,
        "HKD": 0.9,
        "SGD": 5.2,
    }
    return default_rates.get(currency_upper, 7.0)  # 默认使用USD汇率


def convert_to_cny(amount: float, currency: str, exchange_rate: float) -> float:
    """
    将指定金额转换为人民币
    
    Args:
        amount: 金额
        currency: 货币代码
        exchange_rate: 汇率（1单位该货币等于多少人民币）
    
    Returns:
        转换后的人民币金额
    """
    if currency.upper() == "CNY":
        return amount
    return amount * exchange_rate

