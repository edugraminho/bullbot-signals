"""
Gerenciador de cache simples para o Crypto Hunter.

Implementa cache-aside básico com TTL para dados de trading.
"""

import logging
from typing import Any, Optional, Dict
from functools import wraps
from .redis_cache import RedisCache, CacheConfig

logger = logging.getLogger(__name__)


class CacheManager:
    """Gerenciador de cache simples."""

    def __init__(self, config: CacheConfig):
        self.cache = RedisCache(config)
        self.config = config

    def get_ohlcv(self, exchange: str, symbol: str, timeframe: str) -> Optional[Dict]:
        """Obtém dados OHLCV do cache."""
        key = f"ohlcv:{exchange}:{symbol}:{timeframe}"
        return self.cache.get(key)

    def set_ohlcv(self, exchange: str, symbol: str, timeframe: str, data: Dict) -> bool:
        """Armazena dados OHLCV no cache."""
        key = f"ohlcv:{exchange}:{symbol}:{timeframe}"
        return self.cache.set(key, data, self.config.ohlcv_ttl)

    def get_rsi(self, exchange: str, symbol: str) -> Optional[Dict]:
        """Obtém dados RSI do cache."""
        key = f"rsi:{exchange}:{symbol}"
        return self.cache.get(key)

    def set_rsi(self, exchange: str, symbol: str, data: Dict) -> bool:
        """Armazena dados RSI no cache."""
        key = f"rsi:{exchange}:{symbol}"
        return self.cache.set(key, data, self.config.rsi_ttl)

    def get_symbols(self, exchange: str) -> Optional[list]:
        """Obtém lista de símbolos do cache."""
        key = f"symbols:{exchange}"
        return self.cache.get(key)

    def set_symbols(self, exchange: str, symbols: list) -> bool:
        """Armazena lista de símbolos no cache."""
        key = f"symbols:{exchange}"
        return self.cache.set(key, symbols, self.config.symbols_ttl)

    def invalidate_exchange(self, exchange: str) -> int:
        """Invalida todos os dados de uma exchange."""
        pattern = f"{exchange}:*"
        return self.cache.invalidate_pattern(pattern)

    def health_check(self) -> bool:
        """Verifica saúde do cache."""
        return self.cache.health_check()


def cache_result(ttl: Optional[int] = None):
    """Decorator para cache automático."""

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Gera chave baseada na função e argumentos
            key = f"{func.__name__}:{':'.join(map(str, args))}"

            # Tenta obter do cache
            cached = self.cache.get(key)
            if cached is not None:
                return cached

            # Executa função e armazena resultado
            result = func(self, *args, **kwargs)
            if result is not None:
                self.cache.set(key, result, ttl)

            return result

        return wrapper

    return decorator
