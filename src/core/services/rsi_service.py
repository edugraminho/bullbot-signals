"""
Serviço principal para operações com RSI usando MEXC Exchange
"""

from typing import List, Optional

from src.core.models.crypto import OHLCVData, RSIData, RSILevels
from src.core.services.confluence_analyzer import ConfluenceAnalyzer, ConfluenceResult
from src.services.mexc_client import MEXCClient, MEXCError
from src.utils.logger import get_logger

logger = get_logger(__name__)


class RSIService:
    """Serviço para análise de RSI usando MEXC Exchange"""

    def __init__(self, custom_rsi_levels: Optional[RSILevels] = None):
        from src.utils.config import settings

        if custom_rsi_levels:
            self.rsi_levels = custom_rsi_levels
        else:
            # Usar configurações padrão do config.py
            self.rsi_levels = RSILevels(
                oversold=settings.rsi_oversold,
                overbought=settings.rsi_overbought,
            )

        # Inicializar analisador de confluência
        self.confluence_analyzer = ConfluenceAnalyzer()

    async def get_rsi(
        self,
        symbol: str,
        interval: str = "4h",
        window: int = 14,
    ) -> Optional[RSIData]:
        """Busca RSI da MEXC Exchange"""
        return await self.get_rsi_from_mexc(symbol, interval, window)

    async def get_rsi_from_mexc(
        self, symbol: str, interval: str = "4h", window: int = 14
    ) -> Optional[RSIData]:
        """
        Busca OHLCV da MEXC e calcula RSI

        Args:
            symbol: Símbolo da crypto (BTC, ETH, etc.)
            interval: Intervalo (1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1M)
            window: Janela de cálculo RSI
        """
        try:
            async with MEXCClient() as client:
                rsi_data = await client.get_latest_rsi(symbol, interval, window)

            if rsi_data:
                logger.debug(f"RSI MEXC: {symbol} = {rsi_data.value}")
                return rsi_data
            else:
                logger.warning(f"Nenhum dado RSI MEXC calculado para {symbol}")
                return None

        except MEXCError as e:
            logger.error(f"❌ Erro da MEXC para {symbol}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Erro inesperado ao buscar RSI MEXC para {symbol}: {e}")
            return None

    async def analyze_rsi_with_confluence(
        self,
        symbol: str,
        interval: str = "15m",
        window: int = 14,
    ) -> Optional[ConfluenceResult]:
        """
        Analisa RSI com sistema de confluência de indicadores usando MEXC

        Args:
            symbol: Símbolo da crypto (BTC, ETH, etc.)
            interval: Intervalo (15m, 1h, 4h, 1d)
            window: Janela de cálculo RSI

        Returns:
            ConfluenceResult com análise completa ou None se não conseguir calcular
        """
        try:
            logger.info(f"Iniciando análise com confluência para {symbol} ({interval})")

            # Obter dados OHLCV da MEXC
            ohlcv_data = await self._get_ohlcv_data(symbol, interval, window + 50)

            if not ohlcv_data:
                logger.error(f"❌ Não foi possível obter dados OHLCV para {symbol}")
                return None

            # Calcular RSI
            rsi_data = await self.get_rsi(symbol, interval, window)

            if not rsi_data:
                logger.error(f"❌ Não foi possível calcular RSI para {symbol}")
                return None

            # Converter OHLCVData para dict (os calculadores esperam dict)
            ohlcv_dict_data = self._convert_ohlcv_to_dict(ohlcv_data)

            # Executar análise de confluência
            confluence_result = self.confluence_analyzer.analyze_confluence(
                ohlcv_dict_data, rsi_data, symbol, interval
            )

            logger.info(
                f"Confluência {symbol}: Score {confluence_result.confluence_score.total_score}/"
                f"{confluence_result.confluence_score.max_possible_score} | "
                f"Sinal: {confluence_result.signal.signal_type.value if confluence_result.signal else 'None'}"
            )

            return confluence_result

        except Exception as e:
            logger.error(f"❌ Erro na análise de confluência para {symbol}: {e}")
            return None

    async def _get_ohlcv_data(
        self, symbol: str, interval: str, limit: int = 100
    ) -> Optional[List[dict]]:
        """
        Obtém dados OHLCV da MEXC

        Args:
            symbol: Símbolo da crypto
            interval: Intervalo dos dados
            limit: Quantidade de pontos a buscar

        Returns:
            Lista de dados OHLCV ou None se erro
        """
        try:
            async with MEXCClient() as client:
                return await client.get_ohlcv(symbol, interval, limit)

        except Exception as e:
            logger.error(f"❌ Erro ao obter dados OHLCV da MEXC para {symbol}: {e}")
            return None

    def _convert_ohlcv_to_dict(self, ohlcv_data: List[OHLCVData]) -> List[dict]:
        """
        Converte lista de OHLCVData para lista de dicionários

        Args:
            ohlcv_data: Lista de objetos OHLCVData

        Returns:
            Lista de dicionários com formato esperado pelos calculadores
        """
        dict_data = []
        for ohlcv in ohlcv_data:
            dict_data.append(
                {
                    "symbol": ohlcv.symbol,
                    "timestamp": ohlcv.timestamp,
                    "open": float(ohlcv.open),
                    "high": float(ohlcv.high),
                    "low": float(ohlcv.low),
                    "close": float(ohlcv.close),
                    "volume": float(ohlcv.volume),
                    "timespan": ohlcv.timespan,
                }
            )
        return dict_data

    async def analyze_signal(
        self,
        symbol: str,
        interval: str = "15m",
        window: int = 14,
    ) -> Optional[ConfluenceResult]:
        """
        Método principal para análise de sinais usando confluência de indicadores

        Args:
            symbol: Símbolo da crypto (BTC, ETH, etc.)
            interval: Intervalo (15m, 1h, 4h, 1d)
            window: Janela de cálculo RSI

        Returns:
            ConfluenceResult com análise completa ou None se não conseguir calcular
        """
        return await self.analyze_rsi_with_confluence(symbol, interval, window)
