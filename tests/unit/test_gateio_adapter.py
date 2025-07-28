"""
Testes unitários para o adapter da Gate.io.

Testa as funcionalidades básicas do adapter sem depender
de conexão real com a API.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from core.exchanges.gateio import GateIOAdapter
from core.exchanges.base import OHLCV, SymbolInfo


class TestGateIOAdapter:
    """Testes para o adapter da Gate.io."""

    @pytest.fixture
    def mock_config(self):
        """Configuração mock para testes."""
        return {
            "name": "gateio",
            "api_key": "test_key",
            "api_secret": "test_secret",
            "rate_limit": 100,
            "timeframes": ["1m", "5m", "15m", "1h", "4h", "1d"],
            "symbols": ["BTC_USDT", "ETH_USDT"],
        }

    @pytest.fixture
    def adapter(self, mock_config):
        """Adapter mock para testes."""
        with patch("core.exchanges.gateio.gate_api"):
            return GateIOAdapter(mock_config)

    def test_init(self, mock_config):
        """Testa inicialização do adapter."""
        with patch("core.exchanges.gateio.gate_api"):
            adapter = GateIOAdapter(mock_config)

            assert adapter.name == "gateio"
            assert adapter.api_key == "test_key"
            assert adapter.api_secret == "test_secret"
            assert adapter.rate_limit == 100

    def test_normalize_timeframe(self, adapter):
        """Testa normalização de timeframes."""
        assert adapter._normalize_timeframe("1h") == "1h"
        assert adapter._normalize_timeframe("4h") == "4h"
        assert adapter._normalize_timeframe("1d") == "1d"
        assert adapter._normalize_timeframe("unknown") == "unknown"

    @pytest.mark.asyncio
    async def test_test_connection_success(self, adapter):
        """Testa conexão bem-sucedida."""
        # Mock da API
        mock_spot_api = Mock()
        mock_spot_api.list_currency_pairs.return_value = []
        adapter.spot_api = mock_spot_api

        # Mock do rate limit
        with patch.object(adapter, "_rate_limit_check", new_callable=AsyncMock):
            result = await adapter.test_connection()
            assert result is True

    @pytest.mark.asyncio
    async def test_test_connection_failure(self, adapter):
        """Testa falha na conexão."""
        # Mock da API com erro
        mock_spot_api = Mock()
        mock_spot_api.list_currency_pairs.side_effect = Exception("Connection error")
        adapter.spot_api = mock_spot_api

        # Mock do rate limit
        with patch.object(adapter, "_rate_limit_check", new_callable=AsyncMock):
            result = await adapter.test_connection()
            assert result is False

    @pytest.mark.asyncio
    async def test_get_symbols(self, adapter):
        """Testa busca de símbolos."""
        # Mock da resposta da API
        mock_pair = Mock()
        mock_pair.id = "BTC_USDT"
        mock_pair.base = "BTC"
        mock_pair.quote = "USDT"
        mock_pair.trade_status = "tradable"
        mock_pair.min_amount = "0.001"
        mock_pair.max_amount = "1000"
        mock_pair.precision = "0.0001"
        mock_pair.min_base_amount = "10"

        mock_spot_api = Mock()
        mock_spot_api.list_currency_pairs.return_value = [mock_pair]
        adapter.spot_api = mock_spot_api

        # Mock do rate limit
        with patch.object(adapter, "_rate_limit_check", new_callable=AsyncMock):
            symbols = await adapter.get_symbols()

            assert len(symbols) == 1
            assert symbols[0].symbol == "BTC_USDT"
            assert symbols[0].base_asset == "BTC"
            assert symbols[0].quote_asset == "USDT"
            assert symbols[0].is_active is True

    @pytest.mark.asyncio
    async def test_get_ohlcv(self, adapter):
        """Testa busca de dados OHLCV."""
        # Mock da resposta da API
        mock_candle = Mock()
        mock_candle.t = int(datetime.now().timestamp())
        mock_candle.o = "50000.0"
        mock_candle.h = "51000.0"
        mock_candle.l = "49000.0"
        mock_candle.c = "50500.0"
        mock_candle.v = "100.0"

        mock_spot_api = Mock()
        mock_spot_api.list_candlesticks.return_value = [mock_candle]
        adapter.spot_api = mock_spot_api

        # Mock do rate limit e asyncio
        with (
            patch.object(adapter, "_rate_limit_check", new_callable=AsyncMock),
            patch("asyncio.get_event_loop") as mock_loop,
        ):
            # Mock do executor para retornar uma coroutine
            async def mock_run_in_executor(*args, **kwargs):
                return [mock_candle]

            mock_loop.return_value.run_in_executor = mock_run_in_executor

            ohlcv_data = await adapter.get_ohlcv("BTC_USDT", "1h", limit=1)

            assert len(ohlcv_data) == 1
            assert isinstance(ohlcv_data[0], OHLCV)
            assert ohlcv_data[0].symbol == "BTC_USDT"
            assert ohlcv_data[0].timeframe == "1h"
            assert ohlcv_data[0].open == 50000.0
            assert ohlcv_data[0].high == 51000.0
            assert ohlcv_data[0].low == 49000.0
            assert ohlcv_data[0].close == 50500.0
            assert ohlcv_data[0].volume == 100.0

    @pytest.mark.asyncio
    async def test_get_ticker(self, adapter):
        """Testa busca de ticker."""
        # Mock da resposta da API
        mock_ticker = Mock()
        mock_ticker.currency_pair = "BTC_USDT"
        mock_ticker.last = "50500.0"
        mock_ticker.lowest_ask = "50501.0"
        mock_ticker.highest_bid = "50499.0"
        mock_ticker.quote_volume = "1000000.0"
        mock_ticker.change_percentage = "2.5"
        mock_ticker.high_24h = "51000.0"
        mock_ticker.low_24h = "49000.0"

        mock_spot_api = Mock()
        mock_spot_api.get_ticker.return_value = mock_ticker
        adapter.spot_api = mock_spot_api

        # Mock do rate limit
        with patch.object(adapter, "_rate_limit_check", new_callable=AsyncMock):
            ticker = await adapter.get_ticker("BTC_USDT")

            assert ticker["symbol"] == "BTC_USDT"
            assert ticker["last_price"] == 50500.0
            assert ticker["bid"] == 50501.0
            assert ticker["ask"] == 50499.0
            assert ticker["volume_24h"] == 1000000.0
            assert ticker["change_24h"] == 2.5
            assert ticker["high_24h"] == 51000.0
            assert ticker["low_24h"] == 49000.0

    @pytest.mark.asyncio
    async def test_get_all_tickers(self, adapter):
        """Testa busca de todos os tickers."""
        # Mock da resposta da API
        mock_ticker = Mock()
        mock_ticker.currency_pair = "BTC_USDT"
        mock_ticker.last = "50500.0"
        mock_ticker.lowest_ask = "50501.0"
        mock_ticker.highest_bid = "50499.0"
        mock_ticker.quote_volume = "1000000.0"
        mock_ticker.change_percentage = "2.5"
        mock_ticker.high_24h = "51000.0"
        mock_ticker.low_24h = "49000.0"

        mock_spot_api = Mock()
        mock_spot_api.list_tickers.return_value = [mock_ticker]
        adapter.spot_api = mock_spot_api

        # Mock do rate limit
        with patch.object(adapter, "_rate_limit_check", new_callable=AsyncMock):
            tickers = await adapter.get_all_tickers()

            assert len(tickers) == 1
            assert "BTC_USDT" in tickers
            assert tickers["BTC_USDT"]["symbol"] == "BTC_USDT"
            assert tickers["BTC_USDT"]["last_price"] == 50500.0

    @pytest.mark.asyncio
    async def test_error_handling(self, adapter):
        """Testa tratamento de erros."""
        # Mock da API com erro
        mock_spot_api = Mock()
        mock_spot_api.list_currency_pairs.side_effect = Exception("API Error")
        adapter.spot_api = mock_spot_api

        # Mock do rate limit
        with patch.object(adapter, "_rate_limit_check", new_callable=AsyncMock):
            # Testar get_symbols com erro
            symbols = await adapter.get_symbols()
            assert symbols == []

            # Testar get_ohlcv com erro
            ohlcv_data = await adapter.get_ohlcv("BTC_USDT", "1h")
            assert ohlcv_data == []

            # Testar get_ticker com erro
            ticker = await adapter.get_ticker("BTC_USDT")
            assert ticker == {}

            # Testar get_all_tickers com erro
            tickers = await adapter.get_all_tickers()
            assert tickers == {}

    def test_rate_limit_configuration(self, mock_config):
        """Testa configuração de rate limiting."""
        with patch("core.exchanges.gateio.gate_api"):
            adapter = GateIOAdapter(mock_config)

            # Testar rate limit padrão
            assert adapter.rate_limit == 100

            # Testar com rate limit personalizado
            custom_config = mock_config.copy()
            custom_config["rate_limit"] = 50
            adapter_custom = GateIOAdapter(custom_config)
            assert adapter_custom.rate_limit == 50


if __name__ == "__main__":
    pytest.main([__file__])
