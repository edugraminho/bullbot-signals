"""
Cliente para API da MEXC (Spot)
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

import httpx

from src.core.models.crypto import OHLCVData, RSIData
from src.core.services.rsi_calculator import RSICalculator
from src.utils.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class MEXCError(Exception):
    """Exceção personalizada para erros da MEXC"""

    pass


class MEXCClient:
    """Cliente para API da MEXC (Spot)"""

    def __init__(self, base_url: str = "https://api.mexc.com"):
        self.base_url = base_url
        self.session: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Context manager entry"""
        self.session = httpx.AsyncClient(timeout=30.0)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.session:
            await self.session.aclose()

    async def get_ohlcv(
        self,
        symbol: str,
        interval: str = "4h",
        limit: int = 50,
        from_timestamp: Optional[int] = None,
        to_timestamp: Optional[int] = None,
    ) -> List[OHLCVData]:
        """
        Busca dados OHLCV da MEXC (Spot)

        Args:
            symbol: Símbolo do par (ex: BTCUSDT)
            interval: Intervalo de tempo (1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1M)
            limit: Quantidade de candles (máx 1000)
            from_timestamp: Timestamp inicial (opcional)
            to_timestamp: Timestamp final (opcional)

        Returns:
            Lista de dados OHLCV

        Raises:
            MEXCError: Em caso de erro na API
        """
        try:
            # Converter símbolo: BTC -> BTCUSDT (formato spot)
            symbol = symbol.upper()
            if not symbol.endswith("USDT"):
                symbol = f"{symbol}USDT"

            # Construir URL e parâmetros (API spot)
            url = f"{self.base_url}/api/v3/klines"
            params = {
                "symbol": symbol,
                "interval": interval,
                "limit": min(limit, 1000),
            }

            # Adicionar timestamps se fornecidos
            if from_timestamp:
                params["start"] = from_timestamp
            if to_timestamp:
                params["end"] = to_timestamp

            logger.debug(f"Buscando OHLCV para {symbol} com intervalo {interval}")
            response = await self.session.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            # MEXC retorna array de arrays com 6 elementos:
            # [timestamp, open, high, low, close, volume]
            ohlcv_data = []

            for item in data:
                try:
                    # MEXC retorna timestamp em milissegundos (13 dígitos)
                    timestamp_raw = int(item[0])
                    timestamp = datetime.fromtimestamp(timestamp_raw / 1000)

                    # Converter valores para Decimal
                    open_val = Decimal(str(item[1]))
                    high_val = Decimal(str(item[2]))
                    low_val = Decimal(str(item[3]))
                    close_val = Decimal(str(item[4]))
                    volume_val = Decimal(str(item[5]))

                    ohlcv_data.append(
                        OHLCVData(
                            symbol=symbol,
                            timestamp=timestamp,
                            open=open_val,
                            high=high_val,
                            low=low_val,
                            close=close_val,
                            volume=volume_val,
                            timespan=interval,
                        )
                    )
                except (ValueError, IndexError, OSError) as e:
                    logger.warning(f"Erro ao processar item OHLCV: {e}")
                    continue

            logger.debug(
                f"OHLCV obtido com sucesso: {len(ohlcv_data)} valores para {symbol}"
            )
            return ohlcv_data

        except httpx.HTTPError as e:
            error_msg = f"Erro HTTP ao buscar OHLCV: {e}"
            logger.error(error_msg)
            raise MEXCError(error_msg)
        except Exception as e:
            error_msg = f"Erro ao buscar OHLCV para {symbol}: {e}"
            logger.error(error_msg)
            raise MEXCError(error_msg)

    async def get_multiple_ohlcv(
        self,
        symbols: List[str],
        interval: str = "4h",
        limit: int = 50,
    ) -> Dict[str, List[OHLCVData]]:
        """
        Busca dados OHLCV para múltiplos símbolos

        Args:
            symbols: Lista de símbolos
            interval: Intervalo de tempo
            limit: Quantidade de candles

        Returns:
            Dicionário com dados OHLCV por símbolo
        """
        results = {}

        for symbol in symbols:
            try:
                ohlcv_data = await self.get_ohlcv(symbol, interval, limit)
                results[symbol] = ohlcv_data
            except MEXCError as e:
                logger.error(f"❌ Erro ao buscar OHLCV para {symbol}: {e}")
                results[symbol] = []

        return results

    async def get_latest_rsi(
        self,
        symbol: str,
        interval: str = "4h",
        period: int = 14,
    ) -> Optional[RSIData]:
        """Busca OHLCV e calcula o RSI mais recente"""
        try:
            # Buscar dados suficientes para calcular RSI usando configuração
            total_periods = period + 100
            logger.debug(f"Buscando RSI MEXC: {symbol} {interval}")
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

            # Calcular RSI usando o calculador independente
            rsi_data = RSICalculator.get_latest_rsi(
                ohlcv_dict, period, symbol, interval
            )

            if rsi_data:
                # Adicionar preço atual (último preço de fechamento)
                rsi_data.current_price = ohlcv_data[-1].close
                rsi_data.source = "mexc"
                logger.info(f"RSI MEXC calculado para {symbol}: {rsi_data.value}")
                logger.info(f"Preço atual MEXC: {rsi_data.current_price}")
                return rsi_data
            else:
                logger.warning(f"Nenhum dado RSI MEXC calculado para {symbol}")
                return None

        except MEXCError as e:
            logger.error(f"❌ Erro da MEXC para {symbol}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Erro ao calcular RSI MEXC para {symbol}: {e}")
            return None
