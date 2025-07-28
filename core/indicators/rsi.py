"""
Calculador de RSI (Relative Strength Index).

Implementa o cálculo do RSI com suporte a múltiplos períodos,
timeframes e parâmetros configuráveis.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from .base import IndicatorBase, IndicatorResult, SignalType


logger = logging.getLogger(__name__)


class RSICalculator(IndicatorBase):
    """Calculador de RSI com múltiplos parâmetros."""

    def __init__(self, parameters: Dict[str, Any]):
        super().__init__(parameters)

        # Parâmetros padrão do RSI
        self.period = parameters.get("period", 14)
        self.overbought_level = parameters.get("overbought_level", 70)
        self.oversold_level = parameters.get("oversold_level", 30)
        self.smooth_period = parameters.get("smooth_period", 1)

        # Validação de parâmetros
        if not self.validate_parameters():
            raise ValueError("Parâmetros inválidos para RSI")

    def validate_parameters(self) -> bool:
        """Valida os parâmetros do RSI."""
        if self.period < 2:
            logger.error("Período do RSI deve ser >= 2")
            return False

        if self.overbought_level <= self.oversold_level:
            logger.error("Nível de sobrecompra deve ser > nível de sobrevenda")
            return False

        if self.overbought_level > 100 or self.oversold_level < 0:
            logger.error("Níveis devem estar entre 0 e 100")
            return False

        return True

    def get_required_data_points(self) -> int:
        """Retorna o número mínimo de pontos necessários para RSI."""
        return self.period + 10  # Período + buffer

    def calculate(self, data: List[Dict[str, Any]]) -> List[IndicatorResult]:
        """Calcula o RSI para os dados fornecidos."""
        if not self._validate_data(data):
            logger.warning(
                f"Dados insuficientes para RSI. Necessário: {self.get_required_data_points()}, Fornecido: {len(data)}"
            )
            return []

        try:
            # Extrai preços de fechamento
            close_prices = self._extract_close_prices(data)
            timestamps = self._extract_timestamps(data)

            # Calcula o RSI
            rsi_values = self._calculate_rsi(close_prices)

            # Converte para resultados
            results = []
            for i, (timestamp, rsi_value) in enumerate(zip(timestamps, rsi_values)):
                if not np.isnan(rsi_value):
                    signal = self._determine_signal(rsi_value)
                    strength = self._calculate_strength(rsi_value)

                    result = IndicatorResult(
                        timestamp=timestamp,
                        value=float(rsi_value),
                        signal=signal,
                        strength=strength,
                        parameters=self.parameters,
                        symbol=data[0].get("symbol", ""),
                        timeframe=data[0].get("timeframe", ""),
                        indicator_type="RSI",
                    )
                    results.append(result)

            return results

        except Exception as e:
            logger.error(f"Erro ao calcular RSI: {e}")
            return []

    def get_latest_signal(
        self, data: List[Dict[str, Any]]
    ) -> Optional[IndicatorResult]:
        """Retorna o sinal mais recente do RSI."""
        results = self.calculate(data)
        return results[-1] if results else None

    def _calculate_rsi(self, prices: List[float]) -> List[float]:
        """Calcula os valores de RSI usando pandas."""
        try:
            # Converte para pandas Series
            price_series = pd.Series(prices)

            # Calcula mudanças de preço
            delta = price_series.diff()

            # Separa ganhos e perdas
            gains = delta.where(delta > 0, 0)
            losses = -delta.where(delta < 0, 0)

            # Calcula médias móveis exponenciais
            avg_gains = gains.ewm(span=self.period, adjust=False).mean()
            avg_losses = losses.ewm(span=self.period, adjust=False).mean()

            # Calcula RS e RSI
            rs = avg_gains / avg_losses
            rsi = 100 - (100 / (1 + rs))

            # Aplica suavização se configurado
            if self.smooth_period > 1:
                rsi = rsi.rolling(window=self.smooth_period).mean()

            return rsi.tolist()

        except Exception as e:
            logger.error(f"Erro no cálculo interno do RSI: {e}")
            return [np.nan] * len(prices)

    def _determine_signal(self, rsi_value: float) -> SignalType:
        """Determina o tipo de sinal baseado no valor do RSI."""
        if rsi_value >= self.overbought_level:
            return SignalType.OVERBOUGHT
        elif rsi_value <= self.oversold_level:
            return SignalType.OVERSOLD
        elif rsi_value > 50:
            return SignalType.SELL
        elif rsi_value < 50:
            return SignalType.BUY
        else:
            return SignalType.NEUTRAL

    def _calculate_strength(self, rsi_value: float) -> float:
        """Calcula a força do sinal (0.0 a 1.0)."""
        if rsi_value >= self.overbought_level:
            # Força máxima quando muito sobrecomprado
            strength = min(
                1.0, (rsi_value - self.overbought_level) / (100 - self.overbought_level)
            )
            return max(0.8, strength)  # Mínimo 0.8 para sobrecompra extrema
        elif rsi_value <= self.oversold_level:
            # Força máxima quando muito sobrevendido
            strength = min(1.0, (self.oversold_level - rsi_value) / self.oversold_level)
            return max(0.8, strength)  # Mínimo 0.8 para sobrevenda extrema
        else:
            # Força baseada na distância do centro (50)
            distance_from_center = abs(rsi_value - 50)
            return min(0.5, distance_from_center / 50)  # Máximo 0.5 para neutro

    def get_divergence_signal(
        self, price_data: List[Dict[str, Any]], rsi_data: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Detecta divergências entre preço e RSI."""
        if len(price_data) < 20 or len(rsi_data) < 20:
            return None

        try:
            # Extrai dados recentes
            recent_prices = self._extract_close_prices(price_data[-20:])
            recent_rsi = [item["value"] for item in rsi_data[-20:]]

            # Calcula tendências
            price_trend = np.polyfit(range(len(recent_prices)), recent_prices, 1)[0]
            rsi_trend = np.polyfit(range(len(recent_rsi)), recent_rsi, 1)[0]

            # Detecta divergência
            if price_trend > 0 and rsi_trend < 0:
                return {
                    "type": "bearish_divergence",
                    "strength": abs(rsi_trend),
                    "description": "Preço subindo, RSI caindo (divergência de baixa)",
                }
            elif price_trend < 0 and rsi_trend > 0:
                return {
                    "type": "bullish_divergence",
                    "strength": abs(rsi_trend),
                    "description": "Preço caindo, RSI subindo (divergência de alta)",
                }

            return None

        except Exception as e:
            logger.error(f"Erro ao detectar divergência: {e}")
            return None

    def get_overbought_oversold_periods(
        self, rsi_data: List[Dict[str, Any]], min_periods: int = 3
    ) -> List[Dict[str, Any]]:
        """Identifica períodos de sobrecompra/sobrevenda."""
        periods = []
        current_period = None

        for i, data_point in enumerate(rsi_data):
            rsi_value = data_point["value"]
            timestamp = data_point["timestamp"]

            if rsi_value >= self.overbought_level:
                if current_period is None or current_period["type"] != "overbought":
                    if current_period and current_period["duration"] >= min_periods:
                        periods.append(current_period)
                    current_period = {
                        "type": "overbought",
                        "start": timestamp,
                        "duration": 1,
                        "max_value": rsi_value,
                    }
                else:
                    current_period["duration"] += 1
                    current_period["max_value"] = max(
                        current_period["max_value"], rsi_value
                    )

            elif rsi_value <= self.oversold_level:
                if current_period is None or current_period["type"] != "oversold":
                    if current_period and current_period["duration"] >= min_periods:
                        periods.append(current_period)
                    current_period = {
                        "type": "oversold",
                        "start": timestamp,
                        "duration": 1,
                        "min_value": rsi_value,
                    }
                else:
                    current_period["duration"] += 1
                    current_period["min_value"] = min(
                        current_period["min_value"], rsi_value
                    )
            else:
                if current_period and current_period["duration"] >= min_periods:
                    current_period["end"] = timestamp
                    periods.append(current_period)
                current_period = None

        # Adiciona o último período se ainda estiver ativo
        if current_period and current_period["duration"] >= min_periods:
            current_period["end"] = rsi_data[-1]["timestamp"]
            periods.append(current_period)

        return periods
