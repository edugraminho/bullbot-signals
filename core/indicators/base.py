"""
Interface base para indicadores técnicos.

Define a estrutura comum para todos os indicadores técnicos,
permitindo padronização e extensibilidade.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class SignalType(Enum):
    """Tipos de sinais gerados pelos indicadores."""

    BUY = "buy"
    SELL = "sell"
    NEUTRAL = "neutral"
    OVERBOUGHT = "overbought"
    OVERSOLD = "oversold"


@dataclass
class IndicatorResult:
    """Resultado de cálculo de indicador."""

    timestamp: datetime
    value: float
    signal: SignalType
    strength: float  # 0.0 a 1.0
    parameters: Dict[str, Any]
    symbol: str
    timeframe: str
    indicator_type: str


class IndicatorBase(ABC):
    """Classe base para todos os indicadores técnicos."""

    def __init__(self, parameters: Dict[str, Any]):
        self.parameters = parameters
        self.name = self.__class__.__name__

    @abstractmethod
    def calculate(self, data: List[Dict[str, Any]]) -> List[IndicatorResult]:
        """Calcula o indicador para os dados fornecidos."""
        pass

    @abstractmethod
    def get_latest_signal(
        self, data: List[Dict[str, Any]]
    ) -> Optional[IndicatorResult]:
        """Retorna o sinal mais recente do indicador."""
        pass

    def validate_parameters(self) -> bool:
        """Valida os parâmetros do indicador."""
        return True

    def get_required_data_points(self) -> int:
        """Retorna o número mínimo de pontos de dados necessários."""
        return 100  # Valor padrão

    def _validate_data(self, data: List[Dict[str, Any]]) -> bool:
        """Valida se os dados são suficientes para o cálculo."""
        if len(data) < self.get_required_data_points():
            return False
        return True

    def _extract_close_prices(self, data: List[Dict[str, Any]]) -> List[float]:
        """Extrai preços de fechamento dos dados."""
        return [float(item.get("close", 0)) for item in data]

    def _extract_high_prices(self, data: List[Dict[str, Any]]) -> List[float]:
        """Extrai preços máximos dos dados."""
        return [float(item.get("high", 0)) for item in data]

    def _extract_low_prices(self, data: List[Dict[str, Any]]) -> List[float]:
        """Extrai preços mínimos dos dados."""
        return [float(item.get("low", 0)) for item in data]

    def _extract_volumes(self, data: List[Dict[str, Any]]) -> List[float]:
        """Extrai volumes dos dados."""
        return [float(item.get("volume", 0)) for item in data]

    def _extract_timestamps(self, data: List[Dict[str, Any]]) -> List[datetime]:
        """Extrai timestamps dos dados."""
        timestamps = []
        for item in data:
            if isinstance(item.get("timestamp"), datetime):
                timestamps.append(item["timestamp"])
            elif isinstance(item.get("timestamp"), str):
                # Tenta converter string para datetime
                try:
                    timestamps.append(datetime.fromisoformat(item["timestamp"]))
                except:
                    # Se falhar, usa timestamp atual
                    timestamps.append(datetime.now())
            else:
                # Se não houver timestamp, usa atual
                timestamps.append(datetime.now())

        return timestamps
