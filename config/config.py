"""
Configuração do Crypto Hunter.

Configurações centralizadas usando Pydantic Settings.
"""

import os
from typing import List, Optional, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class ExchangeConfig(BaseSettings):
    """Configuração de exchange."""

    name: str
    api_key: Optional[str] = Field(default=None, env="GATEIO_API_KEY")
    api_secret: Optional[str] = Field(default=None, env="GATEIO_API_SECRET")
    rate_limit: int = Field(default=100, env="EXCHANGE_RATE_LIMIT")
    timeframes: List[str] = Field(default=["1m", "5m", "15m", "1h", "4h", "1d"])
    symbols: List[str] = Field(default=["BTC_USDT", "ETH_USDT", "SOL_USDT", "ADA_USDT"])


class GlobalConfig(BaseSettings):
    """Configurações globais."""

    collection_interval: int = Field(default=60, env="COLLECTION_INTERVAL")
    max_data_points: int = Field(default=1000, env="MAX_DATA_POINTS")
    rsi_periods: List[int] = Field(default=[14, 21, 50])
    overbought_level: float = Field(default=70.0, env="OVERBOUGHT_LEVEL")
    oversold_level: float = Field(default=30.0, env="OVERSOLD_LEVEL")
    min_volume_24h: float = Field(default=1000000, env="MIN_VOLUME_24H")
    max_symbols_per_exchange: int = Field(default=100, env="MAX_SYMBOLS_PER_EXCHANGE")
    timeframes: List[str] = Field(default=["1h", "4h", "1d"])


class NotificationConfig(BaseSettings):
    """Configurações de notificação."""

    enabled: bool = Field(default=True, env="NOTIFICATIONS_ENABLED")
    platforms: List[str] = Field(default=["discord", "telegram"])
    min_signal_strength: float = Field(default=0.7, env="MIN_SIGNAL_STRENGTH")
    check_interval: int = Field(default=300, env="NOTIFICATION_CHECK_INTERVAL")


class AppConfig(BaseSettings):
    """Configuração principal da aplicação."""

    # Database
    database_url: str = Field(
        default="postgresql://crypto_user:crypto_password_2024@db:5432/crypto_hunter",
        env="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://redis:6380/0", env="REDIS_URL")

    # Exchanges
    exchanges: dict = {
        "gateio": ExchangeConfig(
            name="gateio",
            symbols=["BTC_USDT", "ETH_USDT"],
        )
    }

    # Global settings
    global_config: GlobalConfig = GlobalConfig()

    # Notifications
    notifications: NotificationConfig = NotificationConfig()

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


# Instância global
config = AppConfig()
