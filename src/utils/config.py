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

    # Timeframes padrão para monitoramento (quando usuário não configura)
    default_monitoring_timeframes: List[str] = ["15m"]

    # Limites RSI para sinais - O sistema prioriza a conf do banco quando ela existe
    rsi_oversold: int = 20  # ≤ Nível de sobrevenda
    rsi_overbought: int = 80  # ≥ Nível de sobrecompra

    # ===============================================
    # Technical Indicators Settings
    # ===============================================

    # Configurações EMA (Exponential Moving Average)
    ema_short_period: int = 9  # EMA curta para detecção de tendência
    ema_medium_period: int = 21  # EMA média para confirmação
    ema_long_period: int = 50  # EMA longa para filtro principal

    # Configurações MACD (Moving Average Convergence Divergence)
    macd_fast_period: int = 12  # Período EMA rápida
    macd_slow_period: int = 26  # Período EMA lenta
    macd_signal_period: int = 9  # Período da linha de sinal

    # Configurações Bollinger Bands
    bollinger_period: int = 20  # Período da média móvel central
    bollinger_std_dev: float = 2.0  # Desvio padrão das bandas

    # Configurações Volume
    volume_sma_period: int = 20  # Período para média móvel do volume
    volume_threshold_multiplier: float = 1.2  # Volume deve ser 120% da média

    # Configurações de Confluência
    confluence_min_score_15m: int = 4  # Score mínimo para sinais de 15min
    confluence_min_score_1h: int = 4  # Score mínimo para sinais de 1h
    confluence_min_score_4h: int = 5  # Score mínimo para sinais de 4h
    confluence_min_score_1d: int = 5  # Score mínimo para sinais de 1d

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

    # Configurações de Retry
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
    mexc_sync_interval_seconds: int = 300  # Sincronização MEXC a cada 5 minutos
    signal_monitoring_interval_seconds: int = 300  # Monitoramento de sinais a cada 5 minutos

    # Configurações de Timezone
    celery_timezone: str = "UTC"
    celery_enable_utc: bool = True

    # Configurações de Concorrência
    celery_worker_count: int = 1  # Acima de 1 é arriscado para T3-micro
    celery_tasks_per_worker: int = 1  # Acima de 1 é arriscado para T3-micro
    celery_task_acknowledge_late: bool = True  # Confirmar task só após conclusão

    # Configurações de Timeout (segundos) - Aumentado para suportar 1700+ moedas
    celery_task_warning_timeout: int = 3000  # 50 min - aviso de timeout
    celery_task_force_kill_timeout: int = 3600  # 60 min - força encerramento

    # Configurações de Memória
    celery_max_memory_per_child: int = 400000  # 400MB por processo filho (KB)

    # ===============================================
    # API Settings
    # ===============================================

    # Limites da API - /rsi/multiple?symbols
    api_max_symbols_per_request: int = 200

    # Configurações MEXC
    mexc_base_url: str = "https://api.mexc.com"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# Global instance of settings
settings = Settings()
