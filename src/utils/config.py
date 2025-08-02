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

    # Intervalos e Frequências
    signal_monitoring_interval_seconds: int = (
        300  # Intervalo entre verificações de sinais
    )
    database_cleanup_interval_seconds: int = (
        86400  # Intervalo para limpeza do banco (24h)
    )

    # Configurações RSI
    rsi_calculation_window: int = 14  # Janela de períodos para cálculo RSI
    rsi_analysis_timeframe: str = "15m"  # Timeframe para análise (15m, 1h, 4h)

    # Símbolos padrão para monitoramento
    default_crypto_symbols: List[str] = [
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

    # Configurações de Limpeza e Retry
    signal_history_retention_days: int = 30  # Dias para manter histórico de sinais
    task_max_retry_attempts: int = 2  # Máximo de tentativas em caso de falha
    task_retry_delay_seconds: int = 60  # Tempo entre tentativas

    # ===============================================
    # Celery Settings
    # ===============================================
    """
        AJUSTES DE PERFORMANCE:
        - Para mais velocidade: aumentar celery_worker_count e celery_tasks_per_worker
        - Para menos uso de recursos: diminuir celery_worker_count
        - Para tasks lentas: aumentar celery_task_warning_timeout
        - Para tasks rápidas: diminuir celery_task_force_kill_timeout

    """

    # Configurações de Timezone
    celery_timezone: str = "UTC"
    celery_enable_utc: bool = True

    # Configurações de Concorrência
    celery_worker_count: int = 4  # Número de workers simultâneos
    celery_task_acknowledge_late: bool = True  # Confirmar task só após conclusão
    celery_tasks_per_worker: int = 1  # Tasks por vez por worker

    # Configurações de Timeout (segundos)
    celery_task_warning_timeout: int = 60  # 300 = 5 min - aviso de timeout
    celery_task_force_kill_timeout: int = 600  # 10 min - força encerramento

    # ===============================================
    # API Settings
    # ===============================================

    # Limites da API - /rsi/multiple?symbols
    api_max_symbols_per_request: int = 200

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# Global instance of settings
settings = Settings()
