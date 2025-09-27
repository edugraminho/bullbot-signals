"""
Modelos de dados para criptomoedas e indicadores
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


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

    oversold: Decimal = Field(20, description="Nível de sobrevenda")
    overbought: Decimal = Field(80, description="Nível de sobrecompra")


class EMAData(BaseModel):
    """Modelo para dados de EMA (Exponential Moving Average)"""

    symbol: str = Field(..., description="Crypto symbol")
    timestamp: datetime = Field(..., description="Data timestamp")
    period: int = Field(..., description="EMA period (9, 21, 50)")
    value: Decimal = Field(..., description="EMA value")
    current_price: Decimal = Field(..., description="Current price of the asset")
    timespan: str = Field(..., description="Timeframe: 15m, 1h, 4h, 1d")
    source: str = Field("calculated", description="Data source")


class MACDData(BaseModel):
    """Modelo para dados de MACD (Moving Average Convergence Divergence)"""

    symbol: str = Field(..., description="Crypto symbol")
    timestamp: datetime = Field(..., description="Data timestamp")
    macd_line: Decimal = Field(..., description="MACD line value")
    signal_line: Decimal = Field(..., description="Signal line value")
    histogram: Decimal = Field(..., description="MACD histogram")
    is_bullish: bool = Field(..., description="MACD line above signal line")
    current_price: Decimal = Field(..., description="Current price of the asset")
    timespan: str = Field(..., description="Timeframe: 15m, 1h, 4h, 1d")
    source: str = Field("calculated", description="Data source")


class VolumeData(BaseModel):
    """Modelo para dados de Volume"""

    symbol: str = Field(..., description="Crypto symbol")
    timestamp: datetime = Field(..., description="Data timestamp")
    volume: Decimal = Field(..., description="Current volume")
    volume_sma: Decimal = Field(..., description="Volume Simple Moving Average")
    volume_ratio: Decimal = Field(..., description="Current volume / SMA ratio")
    is_high_volume: bool = Field(..., description="Volume above threshold")
    obv: Decimal = Field(..., description="On-Balance Volume")
    vwap: Decimal = Field(..., description="Volume Weighted Average Price")
    current_price: Decimal = Field(..., description="Current price of the asset")
    timespan: str = Field(..., description="Timeframe: 15m, 1h, 4h, 1d")
    source: str = Field("calculated", description="Data source")


