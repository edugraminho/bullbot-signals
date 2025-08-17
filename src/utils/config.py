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
    rsi_oversold: int = 20  # ≤ Nível de sobrevenda
    rsi_overbought: int = 80  # ≥ Nível de sobrecompra

    # ===============================================
    # Signal Filter Settings (FALLBACK GLOBAL)
    # ===============================================

    # Configurações de Cooldown por Timeframe e Força (em minutos)
    signal_filter_cooldown_15m_strong: int = 15  # 15 minutos
    signal_filter_cooldown_15m_moderate: int = 30  # 30 minutos
    signal_filter_cooldown_15m_weak: int = 60  # 1 hora

    signal_filter_cooldown_1h_strong: int = 60  # 1 hora
    signal_filter_cooldown_1h_moderate: int = 120  # 2 horas
    signal_filter_cooldown_1h_weak: int = 240  # 4 horas

    signal_filter_cooldown_4h_strong: int = 120  # 2 horas
    signal_filter_cooldown_4h_moderate: int = 240  # 4 horas
    signal_filter_cooldown_4h_weak: int = 360  # 6 horas

    signal_filter_cooldown_1d_strong: int = 360  # 6 horas
    signal_filter_cooldown_1d_moderate: int = 720  # 12 horas
    signal_filter_cooldown_1d_weak: int = 1440  # 24 horas

    # Limites Diários de Sinais
    signal_filter_max_signals_per_symbol: int = 3  # Máximo de sinais por símbolo/dia
    signal_filter_max_strong_signals: int = 2  # Máximo de sinais STRONG por símbolo/dia
    signal_filter_min_rsi_difference: float = (
        2.0  # Diferença mínima de RSI para novo sinal
    )

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
        AJUSTES DE PERFORMANCE (PROCESSAMENTO SEQUENCIAL):
        - Sistema configurado para processamento sequencial (economia de recursos)
        - Para mais velocidade: aumentar signal_monitoring_interval_seconds
        - Para menos uso de recursos: manter configuração atual
        - Para tasks lentas: aumentar celery_task_warning_timeout
        - Para tasks rápidas: diminuir celery_task_force_kill_timeout

    """

    # Intervalos e Frequências
    signal_monitoring_interval_seconds: int = (  # REMOVIDO
        300  # Intervalo entre verificações de sinais - 5 minutos
    )
    database_cleanup_interval_seconds: int = (
        86400  # Intervalo para limpeza do banco (24h)
    )

    # Configurações de Timezone
    celery_timezone: str = "UTC"
    celery_enable_utc: bool = True

    # Configurações de Concorrência
    celery_worker_count: int = 1  # Acima de 1 é arriscado para T3-micro
    celery_tasks_per_worker: int = 1  # Acima de 1 é arriscado para T3-micro
    celery_task_acknowledge_late: bool = True  # Confirmar task só após conclusão

    # Configurações de Timeout (segundos)
    celery_task_warning_timeout: int = 600  # 10 min - aviso de timeout
    celery_task_force_kill_timeout: int = 900  # 15 min - força encerramento

    # Configurações de Memória
    celery_max_memory_per_child: int = 200000  # 200MB por processo filho (KB)

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
    trading_coins_max_limit: int = 500  # Máximo de moedas para buscar das exchanges

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
