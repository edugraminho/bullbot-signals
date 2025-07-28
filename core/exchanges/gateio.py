"""
Adapter para a exchange Gate.io.

Implementa a interface ExchangeInterface para a Gate.io,
utilizando a biblioteca oficial gate-api.
"""

import asyncio
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta

import gate_api
from gate_api.rest import ApiException

from .base import ExchangeAdapter, OHLCV, SymbolInfo, Timeframe


logger = logging.getLogger(__name__)


class GateIOAdapter(ExchangeAdapter):
    """Adapter para a exchange Gate.io."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        # Configuração da API Gate.io
        self.api_key = config.get("api_key")
        self.api_secret = config.get("api_secret")

        # Configuração do cliente
        configuration = gate_api.Configuration(host="https://api.gateio.ws/api/v4")

        if self.api_key and self.api_secret:
            configuration.key = self.api_key
            configuration.secret = self.api_secret

        self.spot_api = gate_api.SpotApi(gate_api.ApiClient(configuration))
        self.futures_api = gate_api.FuturesApi(gate_api.ApiClient(configuration))

        # Mapeamento de timeframes
        self.timeframe_mapping = {
            "1m": "1m",
            "5m": "5m",
            "15m": "15m",
            "1h": "1h",
            "4h": "4h",
            "1d": "1d",
        }

    async def test_connection(self) -> bool:
        """Testa a conectividade com a Gate.io."""
        try:
            await self._rate_limit_check()

            # Tenta buscar informações básicas
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.spot_api.list_currency_pairs)

            logger.info(f"Conexão com Gate.io estabelecida com sucesso")
            return True

        except Exception as e:
            logger.error(f"Falha na conexão com Gate.io: {e}")
            return False

    async def get_symbols(self) -> List[SymbolInfo]:
        """Retorna lista de todos os símbolos disponíveis na Gate.io."""
        try:
            await self._rate_limit_check()

            loop = asyncio.get_event_loop()
            pairs = await loop.run_in_executor(None, self.spot_api.list_currency_pairs)

            symbols = []
            for pair in pairs:
                if pair.trade_status == "tradable":
                    symbol_info = SymbolInfo(
                        symbol=pair.id,
                        base_asset=pair.base,
                        quote_asset=pair.quote,
                        min_qty=0.0,  # Gate.io não fornece min_amount
                        max_qty=float("inf"),
                        step_size=0.0001,  # Valor padrão
                        min_notional=0.0,  # Gate.io não fornece min_base_amount
                        is_active=pair.trade_status == "tradable",
                    )
                    symbols.append(symbol_info)

            logger.info(f"Encontrados {len(symbols)} símbolos ativos na Gate.io")
            return symbols

        except Exception as e:
            logger.error(f"Erro ao buscar símbolos da Gate.io: {e}")
            return []

    async def get_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 500,
        since: Optional[datetime] = None,
    ) -> List[OHLCV]:
        """Retorna dados OHLCV da Gate.io."""
        try:
            await self._rate_limit_check()

            # Normaliza timeframe
            normalized_timeframe = self._normalize_timeframe(timeframe)

            # Função wrapper para chamar a API
            def fetch_candles():
                params = {
                    "interval": normalized_timeframe,
                    "limit": min(limit, 1000),  # Gate.io limita a 1000
                }
                if since:
                    params["_from"] = int(since.timestamp())
                return self.spot_api.list_candlesticks(symbol, **params)

            loop = asyncio.get_event_loop()
            candles = await loop.run_in_executor(None, fetch_candles)

            # Converte para formato padronizado
            ohlcv_data = []
            for candle in candles:
                ohlcv = OHLCV(
                    timestamp=datetime.fromtimestamp(int(candle[0])),
                    open=float(candle[4]),
                    high=float(candle[2]),
                    low=float(candle[3]),
                    close=float(candle[5]),
                    volume=float(candle[1]),
                    symbol=symbol,
                    timeframe=timeframe,
                )
                ohlcv_data.append(ohlcv)

            return ohlcv_data

        except Exception as e:
            logger.error(f"Erro ao buscar OHLCV para {symbol}: {e}")
            return []

    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Retorna informações atuais do ticker."""
        try:
            await self._rate_limit_check()

            # Busca todos os tickers e filtra pelo símbolo
            loop = asyncio.get_event_loop()
            tickers = await loop.run_in_executor(None, self.spot_api.list_tickers)

            # Encontra o ticker específico
            for ticker in tickers:
                if ticker.currency_pair == symbol:
                    return {
                        "symbol": ticker.currency_pair,
                        "last_price": float(ticker.last),
                        "bid": float(ticker.lowest_ask),
                        "ask": float(ticker.highest_bid),
                        "volume_24h": float(ticker.quote_volume),
                        "change_24h": float(ticker.change_percentage),
                        "high_24h": float(ticker.high_24h),
                        "low_24h": float(ticker.low_24h),
                    }

            logger.warning(f"Ticker não encontrado para {symbol}")
            return {}

        except Exception as e:
            logger.error(f"Erro ao buscar ticker para {symbol}: {e}")
            return {}

    async def get_all_tickers(self) -> Dict[str, Dict[str, Any]]:
        """Retorna tickers de todos os símbolos ativos."""
        try:
            await self._rate_limit_check()

            loop = asyncio.get_event_loop()
            tickers = await loop.run_in_executor(None, self.spot_api.list_tickers)

            result = {}
            for ticker in tickers:
                result[ticker.currency_pair] = {
                    "symbol": ticker.currency_pair,
                    "last_price": float(ticker.last),
                    "bid": float(ticker.lowest_ask),
                    "ask": float(ticker.highest_bid),
                    "volume_24h": float(ticker.quote_volume),
                    "change_24h": float(ticker.change_percentage),
                    "high_24h": float(ticker.high_24h),
                    "low_24h": float(ticker.low_24h),
                }

            logger.info(f"Obtidos tickers para {len(result)} símbolos")
            return result

        except Exception as e:
            logger.error(f"Erro ao buscar todos os tickers: {e}")
            return {}

    def _normalize_timeframe(self, timeframe: str) -> str:
        """Normaliza timeframe para o formato da Gate.io."""
        return self.timeframe_mapping.get(timeframe, timeframe)
