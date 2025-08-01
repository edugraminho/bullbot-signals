"""
Models do banco de dados
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ARRAY
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class SignalHistory(Base):
    """Histórico de sinais enviados"""

    __tablename__ = "signal_history"

    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    rsi_value = Column(Float, nullable=False)
    signal_type = Column(String(20), nullable=False)  # BUY, SELL, HOLD, etc
    strength = Column(String(20), nullable=False)  # WEAK, MODERATE, STRONG
    price = Column(Float, nullable=False)
    timeframe = Column(String(10), nullable=False)  # 15m, 1h, 4h, etc
    source = Column(String(20), nullable=False)  # binance, gate, mexc
    telegram_sent = Column(Boolean, default=False)
    message = Column(Text)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )


class MonitoringConfig(Base):
    """Configurações de monitoramento"""

    __tablename__ = "monitoring_config"

    id = Column(Integer, primary_key=True)
    name = Column(
        String(50), nullable=False, unique=True
    )  # "default", "aggressive", etc
    symbols = Column(ARRAY(String), nullable=False)  # Lista de símbolos
    rsi_oversold = Column(Integer, default=30)
    rsi_overbought = Column(Integer, default=70)
    timeframes = Column(ARRAY(String), default=["15m", "1h", "4h"])
    active = Column(Boolean, default=True)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class TelegramSubscription(Base):
    """Assinaturas do Telegram"""

    __tablename__ = "telegram_subscriptions"

    id = Column(Integer, primary_key=True)
    chat_id = Column(String, nullable=False, unique=True)
    chat_type = Column(String(20), default="private")
    symbols_filter = Column(ARRAY(String))
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
