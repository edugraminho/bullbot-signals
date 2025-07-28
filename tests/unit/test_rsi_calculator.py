"""
Testes básicos para o calculador de RSI.
"""

import pytest
from datetime import datetime, timedelta

from core.indicators.rsi import RSICalculator
from core.indicators.base import SignalType


def test_rsi_initialization():
    """Testa inicialização do RSI."""
    rsi_params = {"period": 14, "overbought_level": 70, "oversold_level": 30}
    calculator = RSICalculator(rsi_params)

    assert calculator.period == 14
    assert calculator.overbought_level == 70
    assert calculator.oversold_level == 30


def test_rsi_calculation_basic():
    """Testa cálculo básico de RSI."""
    rsi_params = {"period": 14, "overbought_level": 70, "oversold_level": 30}
    calculator = RSICalculator(rsi_params)

    # Dados de teste com variação suficiente para RSI
    test_data = []
    base_time = datetime.now()

    # Cria dados com variação de preços
    for i in range(50):  # Mais dados para RSI
        # Variação de preços para gerar RSI válido
        if i < 25:
            close_price = 100.0 + i * 0.5  # Tendência de alta
        else:
            close_price = 112.5 - (i - 25) * 0.3  # Tendência de baixa

        test_data.append(
            {
                "timestamp": base_time + timedelta(hours=i),
                "close": close_price,
                "open": close_price - 0.1,
                "high": close_price + 0.2,
                "low": close_price - 0.2,
                "volume": 1000.0,
                "symbol": "BTC_USDT",
                "timeframe": "1h",
            }
        )

    results = calculator.calculate(test_data)

    assert len(results) > 0, (
        f"RSI deveria retornar resultados, mas retornou {len(results)}"
    )
    assert all(isinstance(r.value, float) for r in results)
    assert all(0 <= r.value <= 100 for r in results)


def test_rsi_signal_detection():
    """Testa detecção de sinais de RSI."""
    rsi_params = {"period": 14, "overbought_level": 70, "oversold_level": 30}
    calculator = RSICalculator(rsi_params)

    # Teste de sobrecompra
    overbought_result = calculator._determine_signal(75.0)
    assert overbought_result == SignalType.OVERBOUGHT

    # Teste de sobrevenda
    oversold_result = calculator._determine_signal(25.0)
    assert oversold_result == SignalType.OVERSOLD

    # Teste neutro
    neutral_result = calculator._determine_signal(50.0)
    assert neutral_result == SignalType.NEUTRAL


def test_rsi_insufficient_data():
    """Testa comportamento com dados insuficientes."""
    rsi_params = {"period": 14, "overbought_level": 70, "oversold_level": 30}
    calculator = RSICalculator(rsi_params)

    # Dados insuficientes
    test_data = []
    for i in range(10):  # Menos que o mínimo necessário
        test_data.append(
            {
                "timestamp": datetime.now(),
                "close": 100.0 + i * 0.1,
                "symbol": "BTC_USDT",
                "timeframe": "1h",
            }
        )

    results = calculator.calculate(test_data)
    assert len(results) == 0, "Deveria retornar lista vazia para dados insuficientes"


def test_rsi_strength_calculation():
    """Testa cálculo de força do sinal."""
    rsi_params = {"period": 14, "overbought_level": 70, "oversold_level": 30}
    calculator = RSICalculator(rsi_params)

    # Teste força máxima (sobrecompra extrema)
    strength_high = calculator._calculate_strength(90.0)
    assert strength_high >= 0.8

    # Teste força mínima (neutro)
    strength_neutral = calculator._calculate_strength(50.0)
    assert strength_neutral <= 0.5
