"""
Serviço para cálculo de MACD (Moving Average Convergence Divergence)
Implementação baseada na fórmula padrão MACD
"""

from decimal import Decimal
from typing import List

from src.core.models.crypto import MACDData
from src.core.services.ema_calculator import EMACalculator
from src.utils.logger import get_logger

logger = get_logger(__name__)


class MACDCalculator:
    """Calculador de MACD (Moving Average Convergence Divergence) independente da fonte de dados"""

    @staticmethod
    def calculate_macd(
        ohlcv_data: List[dict],
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
        symbol: str = "UNKNOWN",
        timespan: str = "1d",
    ) -> List[MACDData]:
        """
        Calcula MACD a partir de dados OHLCV genéricos

        Args:
            ohlcv_data: Lista de dicionários com dados OHLCV
            fast_period: Período da EMA rápida (padrão: 12)
            slow_period: Período da EMA lenta (padrão: 26)
            signal_period: Período da linha de sinal (padrão: 9)
            symbol: Símbolo do ativo
            timespan: Timeframe dos dados

        Returns:
            Lista de MACDData calculados
        """
        # Verificar se temos dados suficientes
        min_required = slow_period + signal_period
        if len(ohlcv_data) < min_required:
            logger.warning(
                f"Dados insuficientes para calcular MACD. Necessário: {min_required}, disponível: {len(ohlcv_data)}"
            )
            return []

        logger.debug(f"Calculando MACD para {symbol}: {len(ohlcv_data)} períodos")

        # Calcular EMAs necessárias
        ema_fast_values = EMACalculator.calculate_ema(
            ohlcv_data, fast_period, symbol, timespan
        )
        ema_slow_values = EMACalculator.calculate_ema(
            ohlcv_data, slow_period, symbol, timespan
        )

        if not ema_fast_values or not ema_slow_values:
            logger.error(f"❌ Erro ao calcular EMAs para MACD de {symbol}")
            return []

        # Alinhar as EMAs pelo timestamp (a EMA lenta começa depois)
        # Pegar apenas os valores que temos para ambas as EMAs
        start_index = slow_period - fast_period  # Diferença entre os períodos
        aligned_fast = ema_fast_values[start_index:]
        aligned_slow = ema_slow_values

        # Calcular linha MACD (EMA rápida - EMA lenta)
        macd_line_values = []
        for i in range(len(aligned_slow)):
            if i < len(aligned_fast):
                macd_value = aligned_fast[i].value - aligned_slow[i].value
                macd_line_values.append(
                    {
                        "timestamp": aligned_slow[i].timestamp,
                        "value": float(macd_value),
                        "current_price": aligned_slow[i].current_price,
                    }
                )

        # Calcular linha de sinal (EMA da linha MACD)
        # Criar dados OHLCV artificiais para a linha MACD
        macd_ohlcv = []
        for item in macd_line_values:
            macd_ohlcv.append(
                {
                    "timestamp": item["timestamp"],
                    "close": item["value"],  # Usar valor MACD como "close"
                    "open": item["value"],
                    "high": item["value"],
                    "low": item["value"],
                    "volume": 1,  # Volume fictício
                }
            )

        # Calcular EMA da linha MACD para obter linha de sinal
        signal_ema_values = EMACalculator.calculate_ema(
            macd_ohlcv, signal_period, symbol, timespan
        )

        if not signal_ema_values:
            logger.error(f"❌ Erro ao calcular linha de sinal para MACD de {symbol}")
            return []

        # Montar resultado final
        macd_results = []
        start_signal_index = len(macd_line_values) - len(signal_ema_values)

        for i, signal_ema in enumerate(signal_ema_values):
            macd_index = start_signal_index + i

            if macd_index < len(macd_line_values):
                macd_value = Decimal(str(macd_line_values[macd_index]["value"]))
                signal_value = signal_ema.value
                histogram = macd_value - signal_value
                is_bullish = macd_value > signal_value

                macd_data = MACDData(
                    symbol=symbol,
                    timestamp=signal_ema.timestamp,
                    macd_line=macd_value,
                    signal_line=signal_value,
                    histogram=histogram,
                    is_bullish=is_bullish,
                    current_price=Decimal(
                        str(macd_line_values[macd_index]["current_price"])
                    ),
                    timespan=timespan,
                    source="calculated",
                )
                macd_results.append(macd_data)

        if macd_results:
            logger.debug(f"MACD calculado: {len(macd_results)} valores para {symbol}")

        return macd_results

    @staticmethod
    def get_latest_macd(
        ohlcv_data: List[dict],
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
        symbol: str = "UNKNOWN",
        timespan: str = "1d",
    ) -> MACDData:
        """
        Calcula e retorna apenas o MACD mais recente

        Args:
            ohlcv_data: Lista de dicionários com dados OHLCV
            fast_period: Período da EMA rápida (padrão: 12)
            slow_period: Período da EMA lenta (padrão: 26)
            signal_period: Período da linha de sinal (padrão: 9)
            symbol: Símbolo do ativo
            timespan: Timeframe dos dados

        Returns:
            MACDData do valor mais recente ou None se não conseguir calcular
        """
        macd_values = MACDCalculator.calculate_macd(
            ohlcv_data, fast_period, slow_period, signal_period, symbol, timespan
        )

        if macd_values:
            return macd_values[-1]  # Retorna o mais recente
        return None

    @staticmethod
    def get_latest_macd_with_config(
        ohlcv_data: List[dict],
        symbol: str = "UNKNOWN",
        timespan: str = "1d",
    ) -> MACDData:
        """
        Calcula MACD usando configurações do config.py

        Args:
            ohlcv_data: Lista de dicionários com dados OHLCV
            symbol: Símbolo do ativo
            timespan: Timeframe dos dados

        Returns:
            MACDData do valor mais recente ou None se não conseguir calcular
        """
        try:
            from src.utils.config import settings

            return MACDCalculator.get_latest_macd(
                ohlcv_data,
                settings.macd_fast_period,
                settings.macd_slow_period,
                settings.macd_signal_period,
                symbol,
                timespan,
            )
        except Exception as e:
            logger.error(f"❌ Erro ao calcular MACD com config para {symbol}: {e}")
            return None

    @staticmethod
    def is_bullish_crossover(
        ohlcv_data: List[dict],
        symbol: str = "UNKNOWN",
        timespan: str = "1d",
    ) -> bool:
        """
        Verifica se houve cruzamento bullish recente (MACD > Signal)

        Args:
            ohlcv_data: Lista de dicionários com dados OHLCV
            symbol: Símbolo do ativo
            timespan: Timeframe dos dados

        Returns:
            True se MACD está acima da linha de sinal, False caso contrário
        """
        try:
            latest_macd = MACDCalculator.get_latest_macd_with_config(
                ohlcv_data, symbol, timespan
            )

            if latest_macd:
                logger.debug(
                    f"MACD {symbol}: {latest_macd.macd_line:.6f} {'>' if latest_macd.is_bullish else '<='} {latest_macd.signal_line:.6f}"
                )
                return latest_macd.is_bullish

            logger.warning(f"Não foi possível calcular MACD para {symbol}")
            return False

        except Exception as e:
            logger.error(f"❌ Erro ao verificar cruzamento MACD para {symbol}: {e}")
            return False
