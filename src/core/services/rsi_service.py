"""
Serviço principal para operações com RSI
"""

from typing import Dict, List, Optional

from src.adapters.binance_client import BinanceClient, BinanceError
from src.adapters.gate_client import GateClient, GateError
from src.adapters.mexc_client import MEXCClient, MEXCError
from src.core.models.crypto import RSIData, RSILevels, OHLCVData
from src.core.models.signals import SignalStrength
from src.core.services.rsi_calculator import RSICalculator
from src.core.services.confluence_analyzer import ConfluenceAnalyzer, ConfluenceResult
from src.utils.logger import get_logger
from src.utils.trading_coins import trading_coins

logger = get_logger(__name__)


class RSIService:
    """Serviço para análise de RSI usando múltiplas fontes de dados"""

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
        interval: str = "1d",
        window: int = 14,
        source: str = "binance",
    ) -> Optional[RSIData]:
        """Busca RSI de uma exchange específica"""
        if source.lower() == "binance":
            return await self.get_rsi_from_binance(symbol, interval, window)
        elif source.lower() == "mexc":
            return await self.get_rsi_from_mexc(symbol, interval, window)
        elif source.lower() == "gate":
            return await self.get_rsi_from_gate(symbol, interval, window)
        else:
            logger.error(f"❌ Exchange não suportada: {source}")
            return None

    async def get_rsi_from_gate(
        self, symbol: str, interval: str = "1d", window: int = 14
    ) -> Optional[RSIData]:
        """
        Busca OHLCV da Gate.io e calcula RSI

        Args:
            symbol: Símbolo da crypto (BTC, ETH, etc.)
            interval: Intervalo (10s, 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1M)
            window: Janela de cálculo RSI
        """
        try:
            async with GateClient() as client:
                rsi_data = await client.get_latest_rsi(symbol, interval, window)

            if rsi_data:
                logger.debug(f"RSI calculado para {symbol}: {rsi_data.value}")
                return rsi_data
            else:
                logger.warning(f"Nenhum dado RSI calculado para {symbol}")
                return None

        except GateError as e:
            logger.error(f"❌ Erro da Gate.io para {symbol}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Erro inesperado ao buscar RSI para {symbol}: {e}")
            return None

    async def get_rsi_from_mexc(
        self, symbol: str, interval: str = "1d", window: int = 14
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

    async def get_rsi_from_binance(
        self, symbol: str, interval: str = "1d", window: int = 14
    ) -> Optional[RSIData]:
        """
        Busca OHLCV da Binance e calcula RSI

        Args:
            symbol: Símbolo da crypto (BTC, ETH, etc.)
            interval: Intervalo (1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M)
            window: Janela de cálculo RSI
        """
        try:
            async with BinanceClient() as client:
                rsi_data = await client.get_latest_rsi(symbol, interval, window)

            if rsi_data:
                logger.debug(f"RSI Binance: {symbol} = {rsi_data.value}")
                return rsi_data
            else:
                logger.warning(f"Nenhum dado RSI Binance calculado para {symbol}")
                return None

        except BinanceError as e:
            logger.error(f"❌ Erro da Binance para {symbol}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Erro inesperado ao buscar RSI Binance para {symbol}: {e}")
            return None

    def calculate_rsi_from_ohlcv(
        self,
        ohlcv_data: List[dict],
        symbol: str,
        interval: str = "1d",
        window: int = 14,
    ) -> Optional[RSIData]:
        """
        Calcula RSI a partir de dados OHLCV de qualquer fonte

        Args:
            ohlcv_data: Lista de dicionários com dados OHLCV
            symbol: Símbolo da crypto
            interval: Intervalo dos dados
            window: Janela de cálculo RSI

        Returns:
            RSIData calculado ou None se não conseguir calcular
        """
        try:
            rsi_data = RSICalculator.get_latest_rsi(
                ohlcv_data, window, symbol, interval
            )

            if rsi_data:
                logger.debug(f"RSI calculado para {symbol}: {rsi_data.value}")
                return rsi_data
            else:
                logger.warning(f"Nenhum dado RSI calculado para {symbol}")
                return None

        except Exception as e:
            logger.error(f"❌ Erro ao calcular RSI para {symbol}: {e}")
            return None

    async def get_multiple_rsi(
        self, symbols: List[str], interval: str = "1d", window: int = 14
    ) -> Dict[str, Optional[RSIData]]:
        """Busca RSI para múltiplas cryptos em paralelo"""
        try:
            # Buscar RSI para cada símbolo
            results = {}
            async with GateClient() as client:
                for symbol in symbols:
                    try:
                        rsi_data = await client.get_latest_rsi(symbol, interval, window)
                        results[symbol] = rsi_data
                    except GateError as e:
                        logger.error(f"❌ Erro ao buscar RSI para {symbol}: {e}")
                        results[symbol] = None

            # Log resultados
            successful = sum(1 for v in results.values() if v is not None)
            logger.info(f"RSI calculado para {successful}/{len(symbols)} símbolos")

            return results

        except Exception as e:
            logger.error(f"❌ Erro ao buscar RSI múltiplo: {e}")
            return {symbol: None for symbol in symbols}

    def get_curated_symbols(self, limit: int = 200) -> List[str]:
        """
        Retorna lista curada de símbolos para trading
        """
        return trading_coins.get_trading_symbols(limit)

    def get_symbols_by_exchange(self, exchange: str) -> List[str]:
        """
        Retorna símbolos disponíveis em uma exchange específica
        """
        return trading_coins.get_coins_by_exchange(exchange)

    async def analyze_rsi_with_confluence(
        self,
        symbol: str,
        interval: str = "15m",
        window: int = 14,
        source: str = "binance",
    ) -> Optional[ConfluenceResult]:
        """
        Analisa RSI com sistema de confluência de indicadores

        Args:
            symbol: Símbolo da crypto (BTC, ETH, etc.)
            interval: Intervalo (15m, 1h, 4h, 1d)
            window: Janela de cálculo RSI
            source: Fonte dos dados (binance, gate, mexc)

        Returns:
            ConfluenceResult com análise completa ou None se não conseguir calcular
        """
        try:
            logger.info(f"Iniciando análise com confluência para {symbol} ({interval})")

            # Obter dados OHLCV da exchange
            ohlcv_data = await self._get_ohlcv_data(
                symbol, interval, source, window + 50
            )

            if not ohlcv_data:
                logger.error(f"❌ Não foi possível obter dados OHLCV para {symbol}")
                return None

            # Calcular RSI
            rsi_data = await self.get_rsi(symbol, interval, window, source)

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
        self, symbol: str, interval: str, source: str, limit: int = 100
    ) -> Optional[List[dict]]:
        """
        Obtém dados OHLCV da exchange especificada

        Args:
            symbol: Símbolo da crypto
            interval: Intervalo dos dados
            source: Exchange fonte
            limit: Quantidade de pontos a buscar

        Returns:
            Lista de dados OHLCV ou None se erro
        """
        try:
            if source.lower() == "binance":
                async with BinanceClient() as client:
                    return await client.get_ohlcv(symbol, interval, limit)

            elif source.lower() == "mexc":
                async with MEXCClient() as client:
                    return await client.get_ohlcv(symbol, interval, limit)

            elif source.lower() == "gate":
                async with GateClient() as client:
                    return await client.get_ohlcv(symbol, interval, limit)

            else:
                logger.error(f"❌ Exchange não suportada: {source}")
                return None

        except Exception as e:
            logger.error(f"❌ Erro ao obter dados OHLCV de {source} para {symbol}: {e}")
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
        source: str = "binance",
    ) -> Optional[ConfluenceResult]:
        """
        Método principal para análise de sinais usando confluência de indicadores

        Args:
            symbol: Símbolo da crypto (BTC, ETH, etc.)
            interval: Intervalo (15m, 1h, 4h, 1d)
            window: Janela de cálculo RSI
            source: Fonte dos dados (binance, gate, mexc)

        Returns:
            ConfluenceResult com análise completa ou None se não conseguir calcular
        """
        return await self.analyze_rsi_with_confluence(symbol, interval, window, source)

    def should_notify(self, confluence_result: ConfluenceResult) -> bool:
        """
        Determina se um resultado de confluência deve gerar notificação

        Args:
            confluence_result: Resultado da análise de confluência

        Returns:
            True se deve notificar, False caso contrário
        """
        if not confluence_result.signal:
            return False

        # Sinais STRONG sempre notificam
        if confluence_result.signal.strength == SignalStrength.STRONG:
            return True

        # Sinais MODERATE com score alto
        if confluence_result.signal.strength == SignalStrength.MODERATE:
            score_percentage = (
                confluence_result.confluence_score.total_score
                / confluence_result.confluence_score.max_possible_score
            ) * 100
            return score_percentage >= 70  # 70% ou mais

        # WEAK não notifica
        return False
