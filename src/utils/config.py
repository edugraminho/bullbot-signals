"""
Configurações do projeto usando Pydantic Settings
"""

from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configurações principais do projeto"""

    # ===============================================
    # Monitoring Settings
    # ===============================================

    # Configurações RSI
    rsi_calculation_window: int = 14  # Janela de períodos para cálculo RSI
    rsi_analysis_timeframe: str = "15m"  # Timeframe para análise (15m, 1h, 4h)

    # Limites RSI para sinais - O sistema prioriza a conf do banco quando ela existe
    rsi_oversold: int = 30  # ≤ Nível de sobrevenda
    rsi_overbought: int = 70 # ≥ Nível de sobrecompra
    rsi_extreme_oversold: int = 20  # ≤ Sobrevenda extrema
    rsi_extreme_overbought: int = 80  # ≥ Sobrecompra extrema

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

    # Intervalos e Frequências
    signal_monitoring_interval_seconds: int = (
        300  # Intervalo entre verificações de sinais - 5 minutos
    )
    database_cleanup_interval_seconds: int = (
        86400  # Intervalo para limpeza do banco (24h)
    )

    # Configurações de Timezone
    celery_timezone: str = "UTC"
    celery_enable_utc: bool = True

    # Configurações de Concorrência - EM PROD COLOCAR 8 WORKERS E 4 TASK PER WORKER
    celery_worker_count: int = (
        4  # Número de workers (processos) simultâneos que vai executar
    )
    celery_tasks_per_worker: int = (
        1  # Define quantas tarefas cada worker pode processar por vez
    )
    celery_task_acknowledge_late: bool = True  # Confirmar task só após conclusão

    # Configurações de Timeout (segundos)
    celery_task_warning_timeout: int = 300  # 300 = 5 min - aviso de timeout
    celery_task_force_kill_timeout: int = 600  # 10 min - força encerramento

    # ===============================================
    # API Settings
    # ===============================================

    # Limites da API - /rsi/multiple?symbols
    api_max_symbols_per_request: int = 200

    # Configurações do Trading Coins - src/utils/trading_coins.py
    trading_coins_volume_period: str = "24h"  # 24h, 7d, 30d
    trading_coins_min_market_cap: int = 50_000_000  # $50M
    trading_coins_min_volume: int = 3_000_000  # $3M
    trading_coins_update_interval_days: int = 7  # Atualizar lista a cada 7 dias

    # Blacklist de moedas (stablecoins + problemáticas)
    trading_coins_blacklist: List[str] = [
        # Stablecoins
        "USDT",
        "USDC",
        "BUSD",
        "DAI",
        "TUSD",
        "FRAX",
        "USDP",
        "USDD",
        "GUSD",
        "LUSD",
        "USDN",
        "USDK",
        "USDJ",
        "USDE",
        "USDS",
        "USD1",
        "BSC-USD",
        "USDF",
        "PYUSD",
        "USDX",
        "GHO",
        "AUSD",
        "SRUSD",
        "DOLA",
        "SUSDE",
        "SUSDS",
        "USDT0",
        "FDUSD",
        "USDG",
        "USDC.E",
        "USDL",
        "BITCOIN",
        "REKT",
        "MELANIA",
        "ALCH",
        "XPR",
        "RPL",
        "WETH",
    ]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# Global instance of settings
settings = Settings()
