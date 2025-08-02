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
                "User-Agent": "CryptoHunter/1.0",
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
            logger.info(f"Buscando OHLCV para {symbol} com intervalo {interval}")
            response = await self.session.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            # Gate.io retorna array de arrays com 8 elementos:
            # [timestamp, volume_quote, close, high, low, open, volume_base, is_closed]
            # Formato: [[timestamp_str, volume_quote_str, close_str, high_str, low_str, open_str, volume_base_str, is_closed_str], ...]
            ohlcv_data = []

            for item in data:
                try:
                    # Verificar se o item tem pelo menos 6 elementos (mínimo necessário)
                    if len(item) < 6:
                        logger.warning(
                            f"Item OHLCV inválido (menos de 6 elementos): {item}"
                        )
                        continue

                    # Extrair os 6 primeiros elementos (essenciais para OHLCV)
                    (
                        timestamp_str,
                        volume_quote_str,  # Volume em moeda de cotação (ex: USDT)
                        close_str,
                        high_str,
                        low_str,
                        open_str,
                    ) = item[:6]

                    # Converter timestamp
                    timestamp = datetime.fromtimestamp(int(timestamp_str))

                    # Converter valores para Decimal
                    open_val = Decimal(str(open_str))
                    high_val = Decimal(str(high_str))
                    low_val = Decimal(str(low_str))
                    close_val = Decimal(str(close_str))
                    volume_val = Decimal(str(volume_quote_str))

                    # Validar que os valores são números válidos
                    for val in [open_val, high_val, low_val, close_val, volume_val]:
                        if val.is_nan() or val.is_infinite():
                            raise ValueError(f"Valor inválido: {val}")

                    ohlcv = OHLCVData(
                        symbol=symbol.replace(
                            "_", ""
                        ),  # Remove underscore para padronizar
                        timestamp=timestamp,
                        open=open_val,
                        high=high_val,
                        low=low_val,
                        close=close_val,
                        volume=volume_val,
                        timespan=interval,
                    )
                    ohlcv_data.append(ohlcv)

                except (ValueError, TypeError, IndexError) as e:
                    logger.warning(f"Erro ao processar item OHLCV: {e}, item: {item}")
                    continue

            # Ordenar por timestamp (mais antigo primeiro)
            ohlcv_data.sort(key=lambda x: x.timestamp)

            logger.info(
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
                logger.error(f"Erro ao buscar OHLCV para {symbol}: {result}")
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
