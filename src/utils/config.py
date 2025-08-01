"""
Configurações do projeto usando Pydantic Settings
"""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Configurações principais do projeto"""

    # ===============================================
    # Monitoring Settings
    # ===============================================

    monitoring_interval: int = 300  # seconds
    rsi_window: int = 14
    rsi_timeframe: str = "15m"
    rsi_oversold_threshold: int = 30
    rsi_overbought_threshold: int = 70

    # Default symbols for monitoring
    default_symbols: List[str] = [
        "BTC",
        "ETH",
        "SOL",
        "AAVE",
        "AERO",
        "AGI",
        "ANKR",
        "BLOCK",
        "ADA",
        "ATOM",
        "CELR",
        "DAO",
        "AVAX",
        "DOT",
        "ASTR",
        "ENJ",
        "GHX",
        "FET",
        "HNT",
        "ATH",
        "HOT",
        "MUBI",
        "HBAR",
        "LDO",
        "AXL",
        "KSM",
        "XRD",
        "IMX",
        "BLUR",
        "MANTA",
        "INJ",
        "PENDLE",
        "CHZ",
        "PRCL",
        "LINK",
        "SEI",
        "DRIFT",
        "RLB",
        "MKR",
        "SUPER",
        "DYDX",
        "SAND",
        "NEAR",
        "TIA",
        "ENA",
        "SFUND",
        "ONDO",
        "VET",
        "ETHFI",
        "SNX",
        "RNDR",
        "VIRTUAL",
        "GALA",
        "SPEC",
        "JUP",
        "TAI",
        "STX",
        "LPT",
        "SUI",
        "PAAL",
        "TON",
        "PRIME",
        "UNI",
        "RAY",
        "RON",
        "SCRT",
        "UMA",
        "USUAL",
    ]

    # Cleanup settings
    cleanup_days: int = 30

    # Task settings
    max_retries: int = 2
    retry_countdown: int = 60

    # ===============================================
    # API Settings
    # ===============================================

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# Global instance of settings
settings = Settings()
