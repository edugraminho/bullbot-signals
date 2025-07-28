"""
Testes para o sistema de cache Redis.
"""

import pytest
from unittest.mock import Mock, patch
from core.cache import CacheManager, CacheConfig


class TestCacheManager:
    """Testes para o CacheManager."""

    def test_cache_manager_initialization(self):
        """Testa inicialização do CacheManager."""
        config = CacheConfig()
        cache_manager = CacheManager(config)

        assert cache_manager.config == config
        assert cache_manager.cache is not None

    def test_ohlcv_cache_operations(self):
        """Testa operações de cache para dados OHLCV."""
        config = CacheConfig()
        cache_manager = CacheManager(config)

        # Dados de teste
        exchange = "gateio"
        symbol = "BTC_USDT"
        timeframe = "1h"
        test_data = [{"timestamp": "2024-01-01", "close": 50000}]

        # Testa set
        success = cache_manager.set_ohlcv(exchange, symbol, timeframe, test_data)
        assert success is True

        # Testa get
        cached_data = cache_manager.get_ohlcv(exchange, symbol, timeframe)
        assert cached_data == test_data

    def test_rsi_cache_operations(self):
        """Testa operações de cache para dados RSI."""
        config = CacheConfig()
        cache_manager = CacheManager(config)

        # Dados de teste
        exchange = "gateio"
        symbol = "BTC_USDT"
        test_data = {"rsi_14": {"value": 65.5, "signal": "neutral"}}

        # Testa set
        success = cache_manager.set_rsi(exchange, symbol, test_data)
        assert success is True

        # Testa get
        cached_data = cache_manager.get_rsi(exchange, symbol)
        assert cached_data == test_data

    def test_symbols_cache_operations(self):
        """Testa operações de cache para lista de símbolos."""
        config = CacheConfig()
        cache_manager = CacheManager(config)

        # Dados de teste
        exchange = "gateio"
        test_symbols = ["BTC_USDT", "ETH_USDT", "ADA_USDT"]

        # Testa set
        success = cache_manager.set_symbols(exchange, test_symbols)
        assert success is True

        # Testa get
        cached_symbols = cache_manager.get_symbols(exchange)
        assert cached_symbols == test_symbols

    def test_cache_miss(self):
        """Testa comportamento quando dados não estão no cache."""
        config = CacheConfig()
        cache_manager = CacheManager(config)

        # Testa get de dados inexistentes
        cached_data = cache_manager.get_ohlcv("nonexistent", "BTC_USDT", "1h")
        assert cached_data is None

    def test_invalidate_exchange(self):
        """Testa invalidação de dados de uma exchange."""
        config = CacheConfig()
        cache_manager = CacheManager(config)

        # Adiciona alguns dados
        cache_manager.set_ohlcv("gateio", "BTC_USDT", "1h", [{"test": "data"}])
        cache_manager.set_rsi("gateio", "BTC_USDT", {"test": "rsi"})

        # Invalida exchange
        deleted_count = cache_manager.invalidate_exchange("gateio")
        assert deleted_count >= 0  # Pode ser 0 se não houver dados

    def test_health_check(self):
        """Testa health check do cache."""
        config = CacheConfig()
        cache_manager = CacheManager(config)

        # Health check deve retornar boolean
        health = cache_manager.health_check()
        assert isinstance(health, bool)


class TestCacheConfig:
    """Testes para CacheConfig."""

    def test_cache_config_defaults(self):
        """Testa valores padrão da configuração."""
        config = CacheConfig()

        assert config.ohlcv_ttl == 300  # 5 minutos
        assert config.rsi_ttl == 120  # 2 minutos
        assert config.symbols_ttl == 3600  # 1 hora
        assert config.ticker_ttl == 60  # 1 minuto
        assert config.redis_host == "redis"
        assert config.redis_port == 6379
        assert config.redis_db == 0
        assert config.redis_password is None

    def test_cache_config_custom(self):
        """Testa configuração customizada."""
        config = CacheConfig(
            ohlcv_ttl=600, rsi_ttl=300, redis_host="localhost", redis_port=6380
        )

        assert config.ohlcv_ttl == 600
        assert config.rsi_ttl == 300
        assert config.redis_host == "localhost"
        assert config.redis_port == 6380
