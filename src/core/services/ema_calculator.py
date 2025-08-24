"""
Serviço para cálculo de EMA (Exponential Moving Average)
Implementação baseada na fórmula padrão de EMA
"""

from decimal import Decimal
from typing import List

from src.core.models.crypto import EMAData
from src.utils.logger import get_logger

logger = get_logger(__name__)


class EMACalculator:
    """Calculador de EMA (Exponential Moving Average) independente da fonte de dados"""

    @staticmethod
    def calculate_ema(
        ohlcv_data: List[dict],
        period: int = 21,
        symbol: str = "UNKNOWN",
        timespan: str = "1d",
    ) -> List[EMAData]:
        """
        Calcula EMA a partir de dados OHLCV genéricos

        Args:
            ohlcv_data: Lista de dicionários com dados OHLCV
            period: Período da EMA (padrão: 21)
            symbol: Símbolo do ativo
            timespan: Timeframe dos dados

        Returns:
            Lista de EMAData calculados
        """
        if len(ohlcv_data) < period:
            logger.warning(
                f"Dados insuficientes para calcular EMA {period}. Necessário: {period}, disponível: {len(ohlcv_data)}"
            )
            return []

        # Ordenar por timestamp (mais antigo primeiro)
        sorted_data = sorted(ohlcv_data, key=lambda x: x["timestamp"])

        # Extrair preços de fechamento
        closes = [float(item["close"]) for item in sorted_data]

        logger.debug(f"Calculando EMA {period} para {symbol}: {len(closes)} períodos")

        # Calcular multiplicador da EMA
        # Fórmula: multiplicador = 2 / (periodo + 1)
        multiplier = 2.0 / (period + 1)

        ema_values = []

        # Primeira EMA é a média simples dos primeiros 'period' valores
        first_ema = sum(closes[:period]) / period

        # Criar primeiro valor EMAData
        first_ema_data = EMAData(
            symbol=symbol,
            timestamp=sorted_data[period - 1]["timestamp"],
            period=period,
            value=Decimal(str(round(first_ema, 8))),
            current_price=Decimal(str(sorted_data[period - 1]["close"])),
            timespan=timespan,
            source="calculated",
        )
        ema_values.append(first_ema_data)

        # Calcular EMA para os valores restantes
        # Fórmula: EMA_hoje = (Preço_hoje * multiplicador) + (EMA_ontem * (1 - multiplicador))
        current_ema = first_ema

        for i in range(period, len(closes)):
            current_price = closes[i]
            current_ema = (current_price * multiplier) + (
                current_ema * (1 - multiplier)
            )

            ema_data = EMAData(
                symbol=symbol,
                timestamp=sorted_data[i]["timestamp"],
                period=period,
                value=Decimal(str(round(current_ema, 8))),
                current_price=Decimal(str(sorted_data[i]["close"])),
                timespan=timespan,
                source="calculated",
            )
            ema_values.append(ema_data)

        if ema_values:
            logger.debug(
                f"EMA {period} calculada: {len(ema_values)} valores para {symbol}"
            )

        return ema_values

    @staticmethod
    def get_latest_ema(
        ohlcv_data: List[dict],
        period: int = 21,
        symbol: str = "UNKNOWN",
        timespan: str = "1d",
    ) -> EMAData:
        """
        Calcula e retorna apenas a EMA mais recente

        Args:
            ohlcv_data: Lista de dicionários com dados OHLCV
            period: Período da EMA (padrão: 21)
            symbol: Símbolo do ativo
            timespan: Timeframe dos dados

        Returns:
            EMAData do valor mais recente ou None se não conseguir calcular
        """
        ema_values = EMACalculator.calculate_ema(ohlcv_data, period, symbol, timespan)

        if ema_values:
            return ema_values[-1]  # Retorna o mais recente
        return None

    @staticmethod
    def calculate_multiple_emas(
        ohlcv_data: List[dict],
        periods: List[int] = None,
        symbol: str = "UNKNOWN",
        timespan: str = "1d",
    ) -> dict:
        """
        Calcula múltiplas EMAs para os períodos especificados

        Args:
            ohlcv_data: Lista de dicionários com dados OHLCV
            periods: Lista de períodos para calcular (padrão: [9, 21, 50])
            symbol: Símbolo do ativo
            timespan: Timeframe dos dados

        Returns:
            Dicionário com período como chave e EMAData mais recente como valor
        """
        if periods is None:
            from src.utils.config import settings

            periods = [
                settings.ema_short_period,
                settings.ema_medium_period,
                settings.ema_long_period,
            ]

        results = {}

        for period in periods:
            try:
                latest_ema = EMACalculator.get_latest_ema(
                    ohlcv_data, period, symbol, timespan
                )
                if latest_ema:
                    results[period] = latest_ema
                    logger.debug(f"EMA {period}: {latest_ema.value}")
                else:
                    logger.warning(
                        f"Não foi possível calcular EMA {period} para {symbol}"
                    )
                    results[period] = None
            except Exception as e:
                logger.error(f"❌ Erro ao calcular EMA {period}: {e}")
                results[period] = None

        return results

    @staticmethod
    def is_trending_up(
        ohlcv_data: List[dict],
        symbol: str = "UNKNOWN",
        timespan: str = "1d",
    ) -> bool:
        """
        Verifica se o ativo está em tendência de alta baseado nas EMAs

        Lógica: EMA 9 > EMA 21 = Tendência de alta

        Args:
            ohlcv_data: Lista de dicionários com dados OHLCV
            symbol: Símbolo do ativo
            timespan: Timeframe dos dados

        Returns:
            True se em tendência de alta, False caso contrário
        """
        try:
            from src.utils.config import settings

            ema_short = EMACalculator.get_latest_ema(
                ohlcv_data, settings.ema_short_period, symbol, timespan
            )
            ema_medium = EMACalculator.get_latest_ema(
                ohlcv_data, settings.ema_medium_period, symbol, timespan
            )

            if ema_short and ema_medium:
                is_up = ema_short.value > ema_medium.value
                logger.debug(
                    f"Tendência {symbol}: EMA{settings.ema_short_period}={ema_short.value:.4f} {'>' if is_up else '<='} EMA{settings.ema_medium_period}={ema_medium.value:.4f}"
                )
                return is_up

            logger.warning(f"Não foi possível determinar tendência para {symbol}")
            return False

        except Exception as e:
            logger.error(f"❌ Erro ao verificar tendência para {symbol}: {e}")
            return False
