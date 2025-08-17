"""
Models do banco de dados
"""

from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class SignalHistory(Base):
    """Histórico de sinais detectados"""

    __tablename__ = "signal_history"

    # Campos básicos
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    signal_type = Column(String(20), nullable=False)  # BUY, SELL, HOLD
    strength = Column(String(20), nullable=False)  # WEAK, MODERATE, STRONG
    price = Column(Float, nullable=False)
    timeframe = Column(String(10), nullable=False)  # 15m, 1h, 4h, etc
    source = Column(String(20), nullable=False)  # binance, gate, mexc
    message = Column(Text)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )

    # Campos para múltiplos indicadores
    indicator_type = Column(JSON, nullable=False)  # ["RSI", "MACD", "MA_CROSSOVER"]
    indicator_data = Column(JSON, nullable=False)  # Dados de todos os indicadores
    indicator_config = Column(JSON, nullable=True)  # Configurações dos indicadores

    # Campos de contexto básico
    volume_24h = Column(Float, nullable=True)  # Volume 24h no momento do sinal
    price_change_24h = Column(Float, nullable=True)  # Variação % 24h

    # Campos de qualidade
    confidence_score = Column(Float, nullable=True)  # Score de confiança (0-100)
    combined_score = Column(
        Float, nullable=True
    )  # Score combinado de todos indicadores

    # Controle de processamento (para bot do Telegram)
    processed = Column(Boolean, default=False)  # Se foi processado por algum serviço
    processed_at = Column(DateTime, nullable=True)  # Quando foi processado
    processed_by = Column(String(50), nullable=True)  # Qual serviço processou

    # Auditoria mínima
    processing_time_ms = Column(Integer, nullable=True)  # Tempo de processamento


class UserMonitoringConfig(Base):
    """Configurações de monitoramento de sinais por usuário com dados do Telegram"""

    __tablename__ = "user_monitoring_configs"

    id = Column(Integer, primary_key=True)

    # Identificação do usuário (agora usando chat_id como identificador principal)
    user_id = Column(
        BigInteger, nullable=False, index=True
    )  # ID do usuário (mesmo que chat_id)
    chat_id = Column(
        String(50), nullable=False, unique=True, index=True
    )  # Chat ID do Telegram
    chat_type = Column(
        String(20), nullable=False, default="private"
    )  # "private", "group", "supergroup"

    # Informações do usuário do Telegram
    username = Column(String(100), nullable=True)  # @username do Telegram
    first_name = Column(String(100), nullable=True)  # Primeiro nome
    last_name = Column(String(100), nullable=True)  # Último nome
    user_username = Column(String(100), nullable=True)  # Mantido para compatibilidade

    # Configuração da conta
    config_type = Column(
        String(20), nullable=False, default="personal"
    )  # "personal", "group", "default"
    priority = Column(
        Integer, nullable=False, default=1
    )  # Prioridade da config (caso user tenha múltiplas)

    # Identificação da configuração
    config_name = Column(
        String(50), nullable=False
    )  # "crypto_principais", "altcoins_scalping", etc
    description = Column(Text, nullable=True)  # Descrição da configuração
    active = Column(Boolean, default=True)

    # Configuração de ativos
    symbols = Column(ARRAY(String), nullable=False)  # Lista de símbolos
    timeframes = Column(ARRAY(String), default=["15m", "1h", "4h"])

    # Configuração de indicadores (estrutura flexível JSON)
    indicators_config = Column(JSON, nullable=False)
    # Exemplo: {
    #     "RSI": {
    #         "enabled": true,
    #         "period": 14,
    #         "oversold": 20,
    #         "overbought": 80
    #     },
    #     "MACD": {
    #         "enabled": false,
    #         "fast_period": 12,
    #         "slow_period": 26,
    #         "signal_period": 9
    #     }
    # }

    # Configuração de filtros anti-spam (essencial para evitar ruído)
    filter_config = Column(JSON, nullable=True)
    # Exemplo: {
    #     "cooldown_minutes": {
    #         "15m": {"strong": 15, "moderate": 30, "weak": 60},
    #         "1h": {"strong": 60, "moderate": 120, "weak": 240},
    #         "4h": {"strong": 120, "moderate": 240, "weak": 360}
    #     },
    #     "max_signals_per_day": 3,
    #     "min_rsi_difference": 2.0
    # }

    # Atividade e estatísticas do Telegram
    active = Column(Boolean, default=True, nullable=False)  # Status da assinatura
    last_activity = Column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )  # Última atividade
    signals_received = Column(Integer, default=0)  # Total de sinais recebidos
    last_signal_at = Column(DateTime, nullable=True)  # Último sinal recebido

    # Metadados
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Constraints
    __table_args__ = (
        # Constraint UNIQUE(user_id, config_name)
        UniqueConstraint("user_id", "config_name", name="uq_user_config_name"),
    )
