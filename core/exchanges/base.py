"""
Interface base para exchanges de criptomoedas.

Define a interface comum que todas as exchanges devem implementar,
permitindo abstração e padronização dos dados.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum


class Timeframe(Enum):
    """Timeframes suportados pelas exchanges."""

    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    HOUR_1 = "1h"
    HOUR_4 = "4h"
    DAY_1 = "1d"


@dataclass
class OHLCV:
    """Dados OHLCV padronizados."""

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    symbol: str
    timeframe: str


@dataclass
class SymbolInfo:
    """Informações sobre um símbolo de trading."""

    symbol: str
    base_asset: str
    quote_asset: str
    min_qty: float
    max_qty: float
    step_size: float
    min_notional: float
    is_active: bool


class ExchangeInterface(ABC):
    """Interface base para todas as exchanges."""

    @abstractmethod
    async def get_symbols(self) -> List[SymbolInfo]:
        """Retorna lista de todos os símbolos disponíveis."""
        pass

    @abstractmethod
    async def get_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 500,
        since: Optional[datetime] = None,
    ) -> List[OHLCV]:
        """Retorna dados OHLCV para um símbolo e timeframe."""
        pass

    @abstractmethod
    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Retorna informações atuais do ticker."""
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """Testa a conectividade com a exchange."""
        pass


class ExchangeAdapter(ExchangeInterface):
    """Classe base para adaptadores de exchanges."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = config.get("name", "unknown")
        self.rate_limit = config.get("rate_limit", 100)
        self._last_request_time = 0

    async def _rate_limit_check(self):
        """Implementa controle básico de rate limiting."""
        import asyncio
        import time

        current_time = time.time()
        time_since_last = current_time - self._last_request_time

        if time_since_last < (1.0 / self.rate_limit):
            await asyncio.sleep((1.0 / self.rate_limit) - time_since_last)

        self._last_request_time = time.time()

    def _normalize_timeframe(self, timeframe: str) -> str:
        """Normaliza timeframe para o formato da exchange."""
        timeframe_map = {
            "1m": "1m",
            "5m": "5m",
            "15m": "15m",
            "1h": "1h",
            "4h": "4h",
            "1d": "1d",
        }
        return timeframe_map.get(timeframe, timeframe)

    def _parse_ohlcv_data(self, data: List, symbol: str, timeframe: str) -> List[OHLCV]:
        """Converte dados OHLCV brutos para objetos padronizados."""
        ohlcv_list = []

        for item in data:
            # Formato esperado: [timestamp, open, high, low, close, volume]
            if len(item) >= 6:
                timestamp = datetime.fromtimestamp(item[0] / 1000)
                ohlcv = OHLCV(
                    timestamp=timestamp,
                    open=float(item[1]),
                    high=float(item[2]),
                    low=float(item[3]),
                    close=float(item[4]),
                    volume=float(item[5]),
                    symbol=symbol,
                    timeframe=timeframe,
                )
                ohlcv_list.append(ohlcv)

        return ohlcv_list
