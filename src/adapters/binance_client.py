"""
Cliente para integração com Binance API
Documentação: https://binance-docs.github.io/apidocs/spot/en/#kline-candlestick-data
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


class BinanceError(Exception):
    """Exceção personalizada para erros da Binance"""

    pass


class BinanceClient:
    """Cliente para API da Binance"""

    def __init__(self, base_url: str = "https://api.binance.com"):
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
        Busca dados OHLCV do mercado spot da Binance

        Args:
            symbol: Par de trading (ex: BTCUSDT)
            interval: Intervalo (1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M)
            limit: Limite de dados (máx 1000)
            from_timestamp: Timestamp inicial (opcional)
            to_timestamp: Timestamp final (opcional)
        """
        if not self.session:
            raise BinanceError("Cliente não inicializado. Use async with.")

        # Converter símbolo: BTC -> BTCUSDT
        symbol = symbol.upper()
        if not symbol.endswith("USDT"):
            symbol = f"{symbol}USDT"

        url = f"{self.base_url}/api/v3/klines"
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": min(limit, 1000),
        }

        if from_timestamp:
            params["startTime"] = from_timestamp
        if to_timestamp:
            params["endTime"] = to_timestamp

        try:
            logger.info(f"Buscando OHLCV para {symbol} com intervalo {interval}")
            logger.info(f"URL: {url} com parâmetros: {params}")
            response = await self.session.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            # Debug: mostrar dados brutos da Binance
            if data:
                logger.info(f"Primeiros 3 itens da Binance (raw): {data[:3]}")

            # Binance retorna array de arrays com 12 elementos:
            # [openTime, open, high, low, close, volume, closeTime, quoteAssetVolume, numberOfTrades, takerBuyBaseAssetVolume, takerBuyQuoteAssetVolume, ignore]
            ohlcv_data = []

            for item in data:
                try:
                    # Verificar se o item tem pelo menos 6 elementos (essenciais)
                    if len(item) < 6:
                        logger.warning(f"Item OHLCV inválido: {item}")
                        continue

                    # Extrair dados essenciais
                    (
                        open_time,
                        open_price,
                        high_price,
                        low_price,
                        close_price,
                        volume,
                    ) = item[:6]

                    # Converter timestamp (Binance usa milissegundos)
                    timestamp = datetime.fromtimestamp(int(open_time) / 1000)

                    # Converter valores para Decimal
                    open_val = Decimal(str(open_price))
                    high_val = Decimal(str(high_price))
                    low_val = Decimal(str(low_price))
                    close_val = Decimal(str(close_price))
                    volume_val = Decimal(str(volume))

                    # Validar que os valores são números válidos
                    for val in [open_val, high_val, low_val, close_val, volume_val]:
                        if val.is_nan() or val.is_infinite():
                            raise ValueError(f"Valor inválido: {val}")

                    ohlcv = OHLCVData(
                        symbol=symbol,
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

            # Debug: mostrar últimos preços de fechamento
            if ohlcv_data:
                closes = [float(item.close) for item in ohlcv_data[-5:]]
                logger.info(f"Últimos 5 preços de fechamento: {closes}")

            logger.info(
                f"OHLCV obtido com sucesso: {len(ohlcv_data)} valores para {symbol}"
            )
            return ohlcv_data

        except httpx.HTTPError as e:
            error_msg = f"Erro HTTP ao buscar OHLCV: {e}"
            logger.error(error_msg)
            raise BinanceError(error_msg)
        except Exception as e:
            error_msg = f"Erro inesperado ao buscar OHLCV: {e}"
            logger.error(error_msg)
            raise BinanceError(error_msg)

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
            logger.info(
                f"Buscando {total_periods} períodos para RSI (window={period} + histórico={100})"
            )
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
                # Atualizar source para indicar que veio da Binance
                rsi_data.source = "binance_calculated"
                return rsi_data
            return None

        except BinanceError:
            raise
        except Exception as e:
            raise BinanceError(f"Erro ao buscar RSI mais recente: {e}")
