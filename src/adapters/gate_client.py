"""
Cliente para integração com Gate.io API
Documentação: https://www.gate.io/docs/apiv4/
"""

import asyncio
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

import httpx

from src.core.models.crypto import OHLCVData, RSIData
from src.core.services.rsi_calculator import RSICalculator
from src.utils.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class GateError(Exception):
    """Exceção personalizada para erros da Gate.io"""

    pass


class GateClient:
    """Cliente para API da Gate.io"""

    def __init__(self, base_url: str = "https://api.gateio.ws"):
        self.base_url = base_url
        self.session: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Context manager entry"""
        self.session = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "BullBotSignals/1.0",
                "Accept": "application/json",
            },
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.session:
            await self.session.aclose()

    async def get_ohlcv(
        self,
        symbol: str,
        interval: str = "1d",
        limit: int = 50,
        from_timestamp: Optional[int] = None,
        to_timestamp: Optional[int] = None,
    ) -> List[OHLCVData]:
        """
        Busca dados OHLCV do mercado spot da Gate.io

        Args:
            symbol: Par de trading (ex: BTC_USDT)
            interval: Intervalo (10s, 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1M)
            limit: Limite de dados (máx 1000)
            from_timestamp: Timestamp inicial (opcional)
            to_timestamp: Timestamp final (opcional)
        """
        if not self.session:
            raise GateError("Cliente não inicializado. Use async with.")

        # Padronizar formato do símbolo para Gate.io
        if "_" not in symbol:
            symbol = f"{symbol.upper()}_USDT"

        url = f"{self.base_url}/api/v4/spot/candlesticks"
        params = {
            "currency_pair": symbol,
            "interval": interval,
            "limit": min(limit, 1000),  # Gate.io limita a 1000
        }

        if from_timestamp:
            params["from"] = from_timestamp
        if to_timestamp:
            params["to"] = to_timestamp

        try:
            logger.debug(f"Buscando OHLCV para {symbol} com intervalo {interval}")
            response = await self.session.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            # Gate.io retorna array de arrays com 8 elementos:
            # [timestamp, volume_quote, close, high, low, open, volume_base, is_closed]
            # Formato: [[timestamp_str, volume_quote_str, close_str, high_str, low_str, open_str, volume_base_str, is_closed_str], ...]
            ohlcv_data = []

            for item in data:
                try:
                    # Converter strings para valores numéricos
                    timestamp = int(item[0]) / 1000  # Gate.io usa milissegundos
                    volume_quote = float(item[1])  # Volume em quote currency
                    close = float(item[2])
                    high = float(item[3])
                    low = float(item[4])
                    open_price = float(item[5])
                    volume_base = float(item[6])

                    ohlcv_data.append(
                        OHLCVData(
                            symbol=symbol,
                            timestamp=datetime.fromtimestamp(timestamp),
                            open=Decimal(str(open_price)),
                            high=Decimal(str(high)),
                            low=Decimal(str(low)),
                            close=Decimal(str(close)),
                            volume=Decimal(str(volume_quote)),
                            timespan=interval,
                        )
                    )
                except (ValueError, IndexError) as e:
                    logger.warning(f"Erro ao processar item OHLCV: {e}")
                    continue

            logger.debug(
                f"OHLCV obtido com sucesso: {len(ohlcv_data)} valores para {symbol}"
            )
            return ohlcv_data

        except httpx.HTTPError as e:
            error_msg = f"Erro HTTP ao buscar OHLCV: {e}"
            logger.error(error_msg)
            raise GateError(error_msg)
        except Exception as e:
            error_msg = f"Erro inesperado ao buscar OHLCV: {e}"
            logger.error(error_msg)
            raise GateError(error_msg)

    async def get_multiple_ohlcv(
        self,
        symbols: List[str],
        interval: str = "1d",
        limit: int = 50,
    ) -> Dict[str, List[OHLCVData]]:
        """
        Busca OHLCV para múltiplos símbolos em paralelo
        """
        tasks = []
        for symbol in symbols:
            task = self.get_ohlcv(symbol, interval, limit)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        response_dict = {}
        for symbol, result in zip(symbols, results):
            if isinstance(result, Exception):
                logger.error(f"❌ Erro ao buscar OHLCV para {symbol}: {result}")
                response_dict[symbol] = []
            else:
                response_dict[symbol] = result

        return response_dict

    async def get_latest_rsi(
        self,
        symbol: str,
        interval: str = "1d",
        period: int = 14,
    ) -> Optional[RSIData]:
        """Busca OHLCV e calcula o RSI mais recente"""
        try:
            # Buscar dados suficientes para calcular RSI usando configuração
            total_periods = period + 100
            logger.debug(f"Buscando RSI Gate.io: {symbol} {interval}")
            ohlcv_data = await self.get_ohlcv(symbol, interval, total_periods)

            if not ohlcv_data:
                return None

            # Converter OHLCVData para formato genérico para o calculador
            ohlcv_dict = [
                {
                    "timestamp": item.timestamp,
                    "close": float(item.close),
                    "open": float(item.open),
                    "high": float(item.high),
                    "low": float(item.low),
                    "volume": float(item.volume),
                }
                for item in ohlcv_data
            ]

            # Usar o calculador independente
            rsi_data = RSICalculator.get_latest_rsi(
                ohlcv_dict, period, symbol, interval
            )

            if rsi_data:
                # Atualizar source para indicar que veio da Gate.io
                rsi_data.source = "gate_calculated"
                return rsi_data
            return None

        except GateError:
            raise
        except Exception as e:
            raise GateError(f"Erro ao buscar RSI mais recente: {e}")
