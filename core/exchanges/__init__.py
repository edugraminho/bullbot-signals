"""
Módulo de exchanges para o Crypto Hunter.

Este módulo contém os adaptadores para diferentes exchanges de criptomoedas,
permitindo uma interface unificada para coleta de dados e execução de trades.
"""

from .base import ExchangeInterface, ExchangeAdapter
from .gateio import GateIOAdapter
from .factory import ExchangeFactory, ExchangeManager

__all__ = [
    "ExchangeInterface",
    "ExchangeAdapter",
    "GateIOAdapter",
    "ExchangeFactory",
    "ExchangeManager",
]
