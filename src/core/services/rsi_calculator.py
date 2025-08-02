"""
Serviço independente para cálculo de RSI
Baseado na documentação oficial do TradingView
"""

from decimal import Decimal
from typing import List

from src.core.models.crypto import RSIData
from src.utils.logger import get_logger

logger = get_logger(__name__)


class RSICalculator:
    """Calculador de RSI independente da fonte de dados"""

    @staticmethod
    def calculate_rsi(
        ohlcv_data: List[dict],
        period: int = 14,
        symbol: str = "UNKNOWN",
        timespan: str = "1d",
    ) -> List[RSIData]:
        """
        Calcula RSI a partir de dados OHLCV genéricos

        Args:
            ohlcv_data: Lista de dicionários com dados OHLCV
            period: Período do RSI (padrão: 14)
            symbol: Símbolo do ativo
            timespan: Timeframe dos dados

        Returns:
            Lista de RSIData calculados
        """
        if len(ohlcv_data) < period + 1:
            logger.warning(
                f"Dados insuficientes para calcular RSI. Necessário: {period + 1}, disponível: {len(ohlcv_data)}"
            )
            return []

        # Ordenar por timestamp (mais antigo primeiro)
        sorted_data = sorted(ohlcv_data, key=lambda x: x["timestamp"])

        # Extrair preços de fechamento
        closes = [float(item["close"]) for item in sorted_data]

        logger.debug(f"Calculando RSI para {symbol}: {len(closes)} períodos")

        # Calcular mudanças (conforme documentação TradingView)
        changes = []
        for i in range(1, len(closes)):
            change = closes[i] - closes[i - 1]
            changes.append(change)

        # Separar ganhos e perdas (conforme Pine Script)
        gains = [max(change, 0) for change in changes]
        losses = [abs(min(change, 0)) for change in changes]

        if len(gains) < period:
            return []

        # Calcular médias iniciais (primeiro período)
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period

        rsi_values = []

        # Calcular RSI para cada período (método RMA/SMMA do TradingView)
        for i in range(period, len(changes)):
            # Atualizar médias usando RMA (Relative Moving Average) - método TradingView
            # Fórmula: RMA = (RMA_anterior * (period - 1) + valor_atual) / period
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period

            # Calcular RSI (fórmula oficial TradingView)
            if avg_loss == 0:
                rsi = 100.0
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))

            # Criar objeto RSIData
            # Índice correto: i corresponde ao período atual no loop (começa em period)
            # sorted_data[i+1] corresponde ao candle atual para o qual calculamos o RSI
            ohlcv_item = sorted_data[i + 1]  # +1 porque mudanças começam do índice 1

            rsi_data = RSIData(
                symbol=symbol,
                timestamp=ohlcv_item["timestamp"],
                value=Decimal(str(round(rsi, 2))),
                current_price=Decimal(str(ohlcv_item["close"])),
                timespan=timespan,
                window=period,
                source="calculated",
            )
            rsi_values.append(rsi_data)

        if rsi_values:
            logger.debug(f"RSI calculado: {len(rsi_values)} valores para {symbol}")

        return rsi_values

    @staticmethod
    def get_latest_rsi(
        ohlcv_data: List[dict],
        period: int = 14,
        symbol: str = "UNKNOWN",
        timespan: str = "1d",
    ) -> RSIData:
        """
        Calcula e retorna apenas o RSI mais recente

        Args:
            ohlcv_data: Lista de dicionários com dados OHLCV
            period: Período do RSI (padrão: 14)
            symbol: Símbolo do ativo
            timespan: Timeframe dos dados

        Returns:
            RSIData do valor mais recente ou None se não conseguir calcular
        """
        rsi_values = RSICalculator.calculate_rsi(ohlcv_data, period, symbol, timespan)

        if rsi_values:
            return rsi_values[-1]  # Retorna o mais recente
        return None
