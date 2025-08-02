"""
Serviço principal para operações com RSI
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

from src.adapters.gate_client import GateClient, GateError
from src.adapters.binance_client import BinanceClient, BinanceError
from src.adapters.mexc_client import MEXCClient, MEXCError
from src.core.models.crypto import RSIData, RSILevels
from src.core.services.rsi_calculator import RSICalculator
from src.core.models.signals import (
    TradingSignal,
    SignalType,
    SignalStrength,
)
from src.utils.logger import get_logger
from src.utils.trading_coins import trading_coins

logger = get_logger(__name__)


@dataclass
class RSIAnalysis:
    """Resultado da análise de RSI"""

    rsi_data: RSIData
    signal: TradingSignal
    interpretation: str
    risk_level: str


class RSIService:
    """Serviço para análise de RSI usando múltiplas fontes de dados"""

    def __init__(self):
        self.rsi_levels = RSILevels()

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

    def analyze_rsi(self, rsi_data: RSIData) -> RSIAnalysis:
        """
        Analisa o RSI e gera sinal de trading

        Lógica baseada nos níveis clássicos:
        - RSI > 70: Sobrecompra (possível venda)
        - RSI < 30: Sobrevenda (possível compra)
        - RSI > 80: Sobrecompra extrema
        - RSI < 20: Sobrevenda extrema
        """
        rsi_value = rsi_data.value

        # Determinar tipo e força do sinal
        if rsi_value >= self.rsi_levels.extreme_overbought:
            signal_type = SignalType.STRONG_SELL
            strength = SignalStrength.STRONG
            interpretation = f"RSI {rsi_value} indica sobrecompra EXTREMA"
            risk_level = "ALTO"
            message = f"🔴 Sobrecompra extrema! RSI em {rsi_value}. Considere venda."

        elif rsi_value >= self.rsi_levels.overbought:
            signal_type = SignalType.SELL
            strength = SignalStrength.MODERATE
            interpretation = f"RSI {rsi_value} indica sobrecompra"
            risk_level = "MÉDIO"
            message = (
                f"📉 Sobrecompra detectada. RSI em {rsi_value}. Possível reversão."
            )

        elif rsi_value <= self.rsi_levels.extreme_oversold:
            signal_type = SignalType.STRONG_BUY
            strength = SignalStrength.STRONG
            interpretation = f"RSI {rsi_value} indica sobrevenda EXTREMA"
            risk_level = "ALTO"
            message = f"🚀 Sobrevenda extrema! RSI em {rsi_value}. Forte oportunidade de compra."

        elif rsi_value <= self.rsi_levels.oversold:
            signal_type = SignalType.BUY
            strength = SignalStrength.MODERATE
            interpretation = f"RSI {rsi_value} indica sobrevenda"
            risk_level = "MÉDIO"
            message = f"📈 Sobrevenda detectada. RSI em {rsi_value}. Possível reversão de alta."

        else:
            signal_type = SignalType.HOLD
            strength = SignalStrength.WEAK
            interpretation = f"RSI {rsi_value} em zona neutra"
            risk_level = "BAIXO"
            message = f"⏸️ RSI neutro em {rsi_value}. Aguardar melhor oportunidade."

        # Criar sinal
        signal = TradingSignal(
            symbol=rsi_data.symbol,
            signal_type=signal_type,
            strength=strength,
            rsi_value=rsi_value,
            timestamp=rsi_data.timestamp,
            timeframe=rsi_data.timespan,
            message=message,
        )

        return RSIAnalysis(
            rsi_data=rsi_data,
            signal=signal,
            interpretation=interpretation,
            risk_level=risk_level,
        )

    def should_notify(self, analysis: RSIAnalysis) -> bool:
        """
        Determina se um sinal deve gerar notificação

        Critérios:
        - Sinais STRONG sempre notificam
        - Sinais MODERATE em níveis extremos
        """
        if analysis.signal.strength == SignalStrength.STRONG:
            return True

        if analysis.signal.strength == SignalStrength.MODERATE:
            rsi = analysis.rsi_data.value
            # Notificar se está próximo dos extremos
            return rsi <= 35 or rsi >= 65

        return False

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
