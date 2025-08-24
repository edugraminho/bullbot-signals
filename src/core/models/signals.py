"""
Modelos para sinais de trading
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SignalType(str, Enum):
    """Tipos de sinais"""

    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    STRONG_BUY = "strong_buy"
    STRONG_SELL = "strong_sell"


class SignalStrength(str, Enum):
    """Força do sinal"""

    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"


class TradingSignal(BaseModel):
    """Sinal de trading baseado em confluência de indicadores"""

    symbol: str = Field(..., description="Crypto symbol")
    signal_type: SignalType = Field(..., description="Tipo do sinal")
    strength: SignalStrength = Field(..., description="Força do sinal")
    rsi_value: Decimal = Field(..., description="Valor RSI atual")
    timestamp: datetime = Field(..., description="Momento do sinal")
    timeframe: str = Field(..., description="Timeframe analisado")
    price: Optional[Decimal] = Field(None, description="Preço no momento do sinal")
    message: str = Field(..., description="Mensagem explicativa")

    def to_notification_text(self) -> str:
        """Converte sinal para texto de notificação"""
        emoji = {
            SignalType.STRONG_BUY: "🚀",
            SignalType.BUY: "📈",
            SignalType.HOLD: "⏸️",
            SignalType.SELL: "📉",
            SignalType.STRONG_SELL: "🔴",
        }

        return (
            f"{emoji.get(self.signal_type, '📊')} *{self.symbol}*\n"
            f"Sinal: {self.signal_type.value.upper()}\n"
            f"RSI: {self.rsi_value}\n"
            f"Força: {self.strength.value}\n"
            f"Timeframe: {self.timeframe}\n"
            f"Horário: {self.timestamp.strftime('%H:%M:%S')}\n"
            f"💬 {self.message}"
        )
