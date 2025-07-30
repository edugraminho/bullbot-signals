"""
Configurações do projeto usando Pydantic Settings
"""

from typing import List, Optional, Union
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Configurações principais do projeto"""

    # API Keys
    polygon_api_key: str = Field(..., env="POLYGON_API_KEY")

    # Database
    database_url: str = Field(
        "postgresql://user:password@localhost/crypto_hunter", env="DATABASE_URL"
    )

    # Redis
    redis_url: str = Field("redis://localhost:6379/0", env="REDIS_URL")

    # Celery
    celery_broker_url: str = Field("redis://localhost:6379/0", env="CELERY_BROKER_URL")
    celery_result_backend: str = Field(
        "redis://localhost:6379/0", env="CELERY_RESULT_BACKEND"
    )

    # API Settings
    api_host: str = Field("0.0.0.0", env="API_HOST")
    api_port: int = Field(8000, env="API_PORT")
    debug: bool = Field(False, env="DEBUG")

    # Polygon.io Settings
    polygon_rate_limit: int = Field(5, env="POLYGON_RATE_LIMIT")  # requests per minute

    # Default Crypto Symbols to Monitor
    default_symbols: List[str] = Field(
        default=["BTCUSD", "ETHUSD", "SOLUSD", "ADAUSD"], env="DEFAULT_SYMBOLS"
    )

    # RSI Settings
    default_rsi_window: int = Field(14, env="DEFAULT_RSI_WINDOW")
    default_timespan: str = Field("day", env="DEFAULT_TIMESPAN")

    # Notification Settings
    telegram_bot_token: Optional[str] = Field(None, env="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: Optional[str] = Field(None, env="TELEGRAM_CHAT_ID")

    # Monitoring Settings
    monitoring_interval: int = Field(300, env="MONITORING_INTERVAL")  # seconds

    @field_validator('default_symbols', mode='before')
    @classmethod
    def parse_default_symbols(cls, v: Union[str, List[str]]) -> List[str]:
        """Converte string separada por vírgulas em lista"""
        if isinstance(v, str):
            # Remove espaços em branco e divide por vírgula
            symbols = [symbol.strip() for symbol in v.split(',') if symbol.strip()]
            return symbols
        elif isinstance(v, list):
            return v
        else:
            return ["BTCUSD", "ETHUSD", "SOLUSD", "ADAUSD"]  # valor padrão

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Instância global das configurações
settings = Settings()
