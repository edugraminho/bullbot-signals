"""
Modelos de dados para criptomoedas e indicadores
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class Cryptocurrency(BaseModel):
    """Modelo para criptomoeda"""

    symbol: str = Field(..., description="Symbol like BTC, ETH")
    name: Optional[str] = Field(None, description="Full name like Bitcoin")
    exchange: Optional[str] = Field(None, description="Exchange name")


class RSIData(BaseModel):
    """Modelo para dados do RSI"""

    symbol: str = Field(..., description="Crypto symbol")
    timestamp: datetime = Field(..., description="Data timestamp")
    value: Decimal = Field(..., description="RSI value (0-100)")
    current_price: Decimal = Field(..., description="Current price of the asset")
    timespan: str = Field(..., description="Timeframe: minute, hour, day")
    window: int = Field(14, description="RSI calculation window")
    source: str = Field(..., description="Data source: polygon, calculated")


class OHLCVData(BaseModel):
    """Dados OHLCV para cálculo manual de RSI"""

    symbol: str
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    timespan: str


class RSILevels(BaseModel):
    """Níveis de RSI para sinais"""

    oversold: Decimal = Field(30, description="Nível de sobrevenda")
    overbought: Decimal = Field(70, description="Nível de sobrecompra")
    extreme_oversold: Decimal = Field(20, description="Sobrevenda extrema")
    extreme_overbought: Decimal = Field(80, description="Sobrecompra extrema")
