"""
Serviço principal para operações com RSI
"""

from typing import Optional, List, Dict
from dataclasses import dataclass

from src.adapters.polygon_client import PolygonClient, PolygonError
from src.core.models.crypto import RSIData, RSILevels
from src.core.models.signals import (
    TradingSignal,
    SignalType,
    SignalStrength,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class RSIAnalysis:
    """Resultado da análise de RSI"""

    rsi_data: RSIData
    signal: TradingSignal
    interpretation: str
    risk_level: str


class RSIService:
    """Serviço para análise de RSI usando Polygon.io"""

    def __init__(self, polygon_api_key: str):
        self.polygon_api_key = polygon_api_key
        self.rsi_levels = RSILevels()

    async def get_rsi_from_polygon(
        self, symbol: str, timespan: str = "day", window: int = 14
    ) -> Optional[RSIData]:
        """
        Busca RSI da Polygon.io

        Args:
            symbol: Símbolo da crypto (BTC, ETH, etc.)
            timespan: Timeframe (minute, hour, day)
            window: Janela de cálculo RSI
        """
        try:
            async with PolygonClient(self.polygon_api_key) as client:
                rsi_data = await client.get_latest_rsi(symbol, timespan, window)

            if rsi_data:
                logger.info(f"RSI obtido para {symbol}: {rsi_data.value}")
                return rsi_data
            else:
                logger.warning(f"Nenhum dado RSI encontrado para {symbol}")
                return None

        except PolygonError as e:
            logger.error(f"Erro da Polygon.io para {symbol}: {e}")
            return None
        except Exception as e:
            logger.error(f"Erro inesperado ao buscar RSI para {symbol}: {e}")
            return None

    async def get_multiple_rsi(
        self, symbols: List[str], timespan: str = "day", window: int = 14
    ) -> Dict[str, Optional[RSIData]]:
        """Busca RSI para múltiplas cryptos em paralelo"""
        try:
            async with PolygonClient(self.polygon_api_key) as client:
                results = await client.get_multiple_rsi(symbols, timespan, window)

            # Log resultados
            successful = sum(1 for v in results.values() if v is not None)
            logger.info(f"RSI obtido para {successful}/{len(symbols)} símbolos")

            return results

        except Exception as e:
            logger.error(f"Erro ao buscar RSI múltiplo: {e}")
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

    async def get_trading_signals(
        self, symbols: List[str], timespan: str = "day", window: int = 14
    ) -> List[RSIAnalysis]:
        """
        Gera sinais de trading para múltiplas cryptos

        Returns:
            Lista de análises RSI com sinais
        """
        # Buscar RSI para todas as cryptos
        rsi_results = await self.get_multiple_rsi(symbols, timespan, window)

        # Analisar cada RSI e gerar sinais
        analyses = []
        for symbol, rsi_data in rsi_results.items():
            if rsi_data:
                analysis = self.analyze_rsi(rsi_data)
                analyses.append(analysis)
            else:
                logger.warning(
                    f"Não foi possível analisar {symbol} - dados RSI indisponíveis"
                )

        # Ordenar por força do sinal (mais forte primeiro)
        strength_order = {
            SignalStrength.STRONG: 3,
            SignalStrength.MODERATE: 2,
            SignalStrength.WEAK: 1,
        }

        analyses.sort(
            key=lambda x: strength_order.get(x.signal.strength, 0), reverse=True
        )

        logger.info(f"Gerados {len(analyses)} sinais de trading")
        return analyses

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
