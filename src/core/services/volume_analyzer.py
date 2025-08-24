"""
Serviço para análise de Volume, OBV e VWAP
Implementação baseada nas fórmulas padrão de análise de volume
"""

from decimal import Decimal
from typing import List

from src.core.models.crypto import VolumeData
from src.utils.logger import get_logger

logger = get_logger(__name__)


class VolumeAnalyzer:
    """Analisador de Volume independente da fonte de dados"""

    @staticmethod
    def calculate_volume_analysis(
        ohlcv_data: List[dict],
        sma_period: int = 20,
        threshold_multiplier: float = 1.2,
        symbol: str = "UNKNOWN",
        timespan: str = "1d",
    ) -> List[VolumeData]:
        """
        Calcula análise de volume a partir de dados OHLCV genéricos

        Args:
            ohlcv_data: Lista de dicionários com dados OHLCV
            sma_period: Período para SMA do volume (padrão: 20)
            threshold_multiplier: Multiplicador para considerar volume alto (padrão: 1.2)
            symbol: Símbolo do ativo
            timespan: Timeframe dos dados

        Returns:
            Lista de VolumeData calculados
        """
        if len(ohlcv_data) < sma_period:
            logger.warning(
                f"Dados insuficientes para análise de volume. Necessário: {sma_period}, disponível: {len(ohlcv_data)}"
            )
            return []

        # Ordenar por timestamp (mais antigo primeiro)
        sorted_data = sorted(ohlcv_data, key=lambda x: x["timestamp"])

        logger.debug(
            f"Calculando análise de volume para {symbol}: {len(sorted_data)} períodos"
        )

        volume_results = []
        obv_running = 0  # OBV acumulativo

        # Começar a partir do período mínimo necessário
        for i in range(sma_period - 1, len(sorted_data)):
            current_data = sorted_data[i]
            current_volume = float(current_data["volume"])
            current_price = float(current_data["close"])

            # Calcular SMA do volume para os últimos 'sma_period' períodos
            volume_period = sorted_data[i - sma_period + 1 : i + 1]
            volumes = [float(item["volume"]) for item in volume_period]
            volume_sma = sum(volumes) / len(volumes)

            # Calcular ratio do volume atual vs SMA
            volume_ratio = current_volume / volume_sma if volume_sma > 0 else 0
            is_high_volume = volume_ratio >= threshold_multiplier

            # Calcular OBV (On-Balance Volume)
            if i > 0:
                prev_close = float(sorted_data[i - 1]["close"])
                if current_price > prev_close:
                    obv_running += current_volume
                elif current_price < prev_close:
                    obv_running -= current_volume
                # Se igual, OBV não muda
            else:
                # Primeiro período, inicializar OBV
                obv_running = current_volume

            # Calcular VWAP (Volume Weighted Average Price)
            # Para VWAP intraday, precisaríamos acumular desde o início do dia
            # Aqui vamos usar uma aproximação com a média ponderada pelo volume
            vwap_period = volume_period
            total_volume = 0
            total_price_volume = 0

            for j, period_data in enumerate(vwap_period):
                period_volume = float(period_data["volume"])
                period_high = float(period_data["high"])
                period_low = float(period_data["low"])
                period_close = float(period_data["close"])
                period_typical = (period_high + period_low + period_close) / 3

                total_volume += period_volume
                total_price_volume += period_typical * period_volume

            vwap = (
                total_price_volume / total_volume if total_volume > 0 else current_price
            )

            # Criar VolumeData
            volume_data = VolumeData(
                symbol=symbol,
                timestamp=current_data["timestamp"],
                volume=Decimal(str(current_volume)),
                volume_sma=Decimal(str(round(volume_sma, 2))),
                volume_ratio=Decimal(str(round(volume_ratio, 3))),
                is_high_volume=is_high_volume,
                obv=Decimal(str(round(obv_running, 2))),
                vwap=Decimal(str(round(vwap, 8))),
                current_price=Decimal(str(current_price)),
                timespan=timespan,
                source="calculated",
            )
            volume_results.append(volume_data)

        if volume_results:
            logger.debug(
                f"Análise de volume calculada: {len(volume_results)} valores para {symbol}"
            )

        return volume_results

    @staticmethod
    def get_latest_volume_analysis(
        ohlcv_data: List[dict],
        sma_period: int = 20,
        threshold_multiplier: float = 1.2,
        symbol: str = "UNKNOWN",
        timespan: str = "1d",
    ) -> VolumeData:
        """
        Calcula e retorna apenas a análise de volume mais recente

        Args:
            ohlcv_data: Lista de dicionários com dados OHLCV
            sma_period: Período para SMA do volume (padrão: 20)
            threshold_multiplier: Multiplicador para considerar volume alto (padrão: 1.2)
            symbol: Símbolo do ativo
            timespan: Timeframe dos dados

        Returns:
            VolumeData do valor mais recente ou None se não conseguir calcular
        """
        volume_values = VolumeAnalyzer.calculate_volume_analysis(
            ohlcv_data, sma_period, threshold_multiplier, symbol, timespan
        )

        if volume_values:
            return volume_values[-1]  # Retorna o mais recente
        return None

    @staticmethod
    def get_latest_volume_with_config(
        ohlcv_data: List[dict],
        symbol: str = "UNKNOWN",
        timespan: str = "1d",
    ) -> VolumeData:
        """
        Calcula análise de volume usando configurações do config.py

        Args:
            ohlcv_data: Lista de dicionários com dados OHLCV
            symbol: Símbolo do ativo
            timespan: Timeframe dos dados

        Returns:
            VolumeData do valor mais recente ou None se não conseguir calcular
        """
        try:
            from src.utils.config import settings

            return VolumeAnalyzer.get_latest_volume_analysis(
                ohlcv_data,
                settings.volume_sma_period,
                settings.volume_threshold_multiplier,
                symbol,
                timespan,
            )
        except Exception as e:
            logger.error(
                f"❌ Erro ao calcular análise de volume com config para {symbol}: {e}"
            )
            return None

    @staticmethod
    def is_high_volume(
        ohlcv_data: List[dict],
        symbol: str = "UNKNOWN",
        timespan: str = "1d",
    ) -> bool:
        """
        Verifica se o volume atual está acima do threshold

        Args:
            ohlcv_data: Lista de dicionários com dados OHLCV
            symbol: Símbolo do ativo
            timespan: Timeframe dos dados

        Returns:
            True se volume está alto, False caso contrário
        """
        try:
            latest_volume = VolumeAnalyzer.get_latest_volume_with_config(
                ohlcv_data, symbol, timespan
            )

            if latest_volume:
                logger.debug(
                    f"Volume {symbol}: {latest_volume.volume_ratio:.2f}x (threshold: {latest_volume.is_high_volume})"
                )
                return latest_volume.is_high_volume

            logger.warning(f"Não foi possível calcular volume para {symbol}")
            return False

        except Exception as e:
            logger.error(f"❌ Erro ao verificar volume para {symbol}: {e}")
            return False

    @staticmethod
    def is_obv_trending_up(
        ohlcv_data: List[dict],
        symbol: str = "UNKNOWN",
        timespan: str = "1d",
        lookback_periods: int = 5,
    ) -> bool:
        """
        Verifica se OBV está em tendência de alta (comparando últimos períodos)

        Args:
            ohlcv_data: Lista de dicionários com dados OHLCV
            symbol: Símbolo do ativo
            timespan: Timeframe dos dados
            lookback_periods: Quantos períodos usar para comparação

        Returns:
            True se OBV está subindo, False caso contrário
        """
        try:
            volume_analysis = VolumeAnalyzer.calculate_volume_analysis(
                ohlcv_data, symbol=symbol, timespan=timespan
            )

            if len(volume_analysis) < lookback_periods:
                logger.warning(
                    f"Dados insuficientes para análise de tendência OBV de {symbol}"
                )
                return False

            # Comparar OBV atual com OBV de alguns períodos atrás
            current_obv = volume_analysis[-1].obv
            past_obv = volume_analysis[-lookback_periods].obv

            is_trending_up = current_obv > past_obv
            logger.debug(
                f"OBV {symbol}: {current_obv:.2f} {'>' if is_trending_up else '<='} {past_obv:.2f} (hace {lookback_periods} períodos)"
            )
            return is_trending_up

        except Exception as e:
            logger.error(f"❌ Erro ao verificar tendência OBV para {symbol}: {e}")
            return False
