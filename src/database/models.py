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
    timeframes = Column(ARRAY(String), default=["15m"])

    # Configuração de indicadores (estrutura flexível JSON)
    indicators_config = Column(JSON, nullable=False)
    # Exemplo: {
    #     "RSI": {
    #         "enabled": true,
    #         "period": 14,
    #         "oversold": 20,
    #         "overbought": 80
    #     },
    #     "EMA": {
    #         "enabled": true,
    #         "short_period": 9,
    #         "medium_period": 21,
    #         "long_period": 50
    #     },
    #     "MACD": {
    #         "enabled": true,
    #         "fast_period": 12,
    #         "slow_period": 26,
    #         "signal_period": 9
    #     },
    #     "Volume": {
    #         "enabled": true,
    #         "sma_period": 20,
    #         "threshold_multiplier": 1.2
    #     },
    #     "Bollinger": {
    #         "enabled": false,
    #         "period": 20,
    #         "std_dev": 2.0
    #     },
    #     "Confluence": {
    #         "enabled": true,
    #         "min_score_15m": 4,
    #         "min_score_1h": 4,
    #         "min_score_4h": 5,
    #         "min_score_1d": 5
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


class TradingCoin(Base):
    """Tabela para armazenar as moedas selecionadas para trading"""

    __tablename__ = "trading_coins"

    # Campos básicos
    id = Column(Integer, primary_key=True)
    coingecko_id = Column(String(100), nullable=False, unique=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    name = Column(String(100), nullable=False)

    # Dados de mercado
    market_cap = Column(Float, nullable=False)
    market_cap_rank = Column(Integer, nullable=True)
    volume_24h = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    price_change_24h = Column(Float, nullable=True)
    price_change_percentage_24h = Column(Float, nullable=True)

    # Metadados
    category = Column(String(50), nullable=True, index=True)
    image_url = Column(String(500), nullable=True)

    # Exchanges onde está disponível (JSON array)
    exchanges = Column(JSON, nullable=True)  # ["binance", "mexc", "gate"]

    # Controle interno
    ranking = Column(Integer, nullable=False, index=True)
    active = Column(Boolean, default=True, nullable=False, index=True)

    # Auditoria
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    last_market_update = Column(DateTime, nullable=True)
    exchanges_last_updated = Column(DateTime, nullable=True)

    def to_dict(self) -> dict:
        """Converte o modelo para dicionário"""
        return {
            "id": self.id,
            "coingecko_id": self.coingecko_id,
            "symbol": self.symbol,
            "name": self.name,
            "market_cap": self.market_cap,
            "market_cap_rank": self.market_cap_rank,
            "volume_24h": self.volume_24h,
            "current_price": self.current_price,
            "price_change_24h": self.price_change_24h,
            "price_change_percentage_24h": self.price_change_percentage_24h,
            "category": self.category,
            "image_url": self.image_url,
            "exchanges": self.exchanges,
            "ranking": self.ranking,
            "active": self.active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_market_update": self.last_market_update.isoformat()
            if self.last_market_update
            else None,
            "exchanges_last_updated": self.exchanges_last_updated.isoformat()
            if self.exchanges_last_updated
            else None,
        }
