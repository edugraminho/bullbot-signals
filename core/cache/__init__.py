"""
Sistema de cache Redis para o Crypto Hunter.

Implementa cache-aside híbrido com TTL para diferentes
tipos de dados (OHLCV, RSI, símbolos, etc.).
"""

from .redis_cache import RedisCache, CacheConfig
from .cache_manager import CacheManager

__all__ = ["RedisCache", "CacheManager", "CacheConfig"]
