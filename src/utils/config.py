"""
Configurações do projeto usando Pydantic Settings
"""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Configurações principais do projeto"""

    # ===============================================
    # Polygon.io Settings
    # ===============================================

    # Rate limit - requests per minute
    polygon_rate_limit: int = Field(5, env="POLYGON_RATE_LIMIT")

    # Default Crypto Symbols to Monitor
    default_symbols: List[str] = ["BTCUSD", "ETHUSD", "SOLUSD", "ADAUSD"]

    # RSI Settings
    rsi_adjusted: bool = Field(
        True, env="RSI_ADJUSTED"
    )  # Ajustar para splits suavização
    default_rsi_window: int = 14
    default_timespan: str = "day"

    # ===============================================
    # API Settings
    # ===============================================

    # API Keys
    polygon_api_key: str = Field(..., env="POLYGON_API_KEY")

    # Database
    database_url: str = Field(
        "postgresql://crypto_user:crypto_password_2025@localhost:5438/crypto_hunter",
        env="DATABASE_URL",
    )

    # Redis
    redis_url: str = Field("redis://localhost:6388/0", env="REDIS_URL")

    # Celery
    celery_broker_url: str = Field("redis://localhost:6388/0", env="CELERY_BROKER_URL")
    celery_result_backend: str = Field(
        "redis://localhost:6388/0", env="CELERY_RESULT_BACKEND"
    )

    # API Settings
    api_host: str = Field("0.0.0.0", env="API_HOST")
    api_port: int = Field(8000, env="API_PORT")
    debug: bool = Field(False, env="DEBUG")

    # Notification Settings
    telegram_bot_token: Optional[str] = Field(None, env="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: Optional[str] = Field(None, env="TELEGRAM_CHAT_ID")

    # Monitoring Settings - seconds
    monitoring_interval: int = 300

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# Global instance of settings
settings = Settings()
