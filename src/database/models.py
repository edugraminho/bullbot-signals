"""
Models do banco de dados
"""

from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class SignalHistory(Base):
    """Histórico de sinais detectados com dados completos de confluência e trading"""

    __tablename__ = "signal_history"

    # Campos básicos
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    signal_type = Column(String(20), nullable=False)  # BUY, SELL, HOLD
    strength = Column(String(20), nullable=False)  # WEAK, MODERATE, STRONG
    price = Column(Float, nullable=False)  # Preço atual da moeda no momento do sinal
    timeframe = Column(String(10), nullable=False)  # 15m, 1h, 4h, etc
    source = Column(String(20), nullable=False)  # mexc
    message = Column(Text)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )

    # Dados técnicos específicos
    rsi_value = Column(Float, nullable=False)  # Valor do RSI no momento do sinal
    entry_price = Column(Float, nullable=True)  # Preço de entrada sugerido
    stop_loss = Column(Float, nullable=True)  # Stop loss calculado
    take_profit = Column(Float, nullable=True)  # Take profit calculado
    risk_reward_ratio = Column(Float, nullable=True)  # Ratio risco/retorno

    # Campos para múltiplos indicadores
    indicator_type = Column(
        JSON, nullable=False
    )  # ["RSI", "EMA", "MACD", "Volume", "Confluence"]
    indicator_data = Column(
        JSON, nullable=False
    )  # Dados estruturados de todos os indicadores
    # Exemplo indicator_data: {
    #     "signal_info": {
    #         "type": "BUY",
    #         "strength": "STRONG",
    #         "message": "Sinal de compra forte detectado",
    #         "recommendation": "COMPRA FORTE",
    #         "risk_level": "MEDIUM",
    #         "timestamp": "2024-01-15T10:30:00Z"
    #     },
    #     "market_data": {
    #         "current_price": 43250.75,
    #         "volume_24h": 1234567.89,
    #         "price_change_24h_pct": 2.45,
    #         "high_24h": 44000.0,
    #         "low_24h": 42500.0,
    #         "spread_pct": 0.02,
    #         "source": "mexc"
    #     },
    #     "confluence_analysis": {
    #         "total_score": 6,
    #         "max_possible_score": 8,
    #         "score_percentage": 75.0,
    #         "signal_strength": "STRONG",
    #         "is_valid_signal": true,
    #         "breakdown_by_indicator": {
    #             "RSI": {"score": 2, "value": 25.5, "reason": "RSI em zona de sobrevenda"},
    #             "EMA": {"score": 2, "trending_up": true, "reason": "Preço acima das EMAs"},
    #             "MACD": {"score": 1, "is_bullish": true, "reason": "Crossover bullish"},
    #             "Volume": {"score": 1, "is_high_volume": true, "reason": "Volume acima da média"}
    #         }
    #     },
    #     "technical_indicators": {
    #         "rsi": {
    #             "value": 25.5,
    #             "score": 2,
    #             "zone": "oversold",
    #             "interpretation": "RSI em zona de sobrevenda forte",
    #             "is_contributing": true
    #         },
    #         "ema": {
    #             "score": 2,
    #             "trending_up": true,
    #             "values": {"ema_9": 43100.0, "ema_21": 42900.0, "ema_50": 42700.0},
    #             "price_position": {"above_ema_50": true, "trend_alignment": "bullish"},
    #             "is_contributing": true
    #         },
    #         "macd": {
    #             "score": 1,
    #             "is_bullish": true,
    #             "values": {"macd_line": 150.5, "signal_line": 120.3, "histogram": 30.2},
    #             "crossover_type": "bullish_crossover",
    #             "momentum_strength": "moderate",
    #             "is_contributing": true
    #         },
    #         "volume": {
    #             "score": 1,
    #             "is_high_volume": true,
    #             "obv_trending_up": true,
    #             "values": {"volume_ratio": 1.45, "obv": 123456.78, "vwap": 43150.0},
    #             "volume_quality": "good",
    #             "is_contributing": true
    #         }
    #     },
    #     "trading_recommendations": {
    #         "entry_price": 43250.75,
    #         "stop_loss": 41800.0,
    #         "take_profit": 45500.0,
    #         "risk_reward_ratio": 2.1,
    #         "position_size_pct": 2.5,
    #         "signal_quality": "GOOD",
    #         "timeframe": "15m",
    #         "strategy_notes": "Sinal de COMPRA STRONG no timeframe 15m. Confirmado por: RSI, EMA, MACD, Volume. Adequado para scalping."
    #     },
    #     "metadata": {
    #         "analysis_timestamp": "2024-01-15T10:30:15Z",
    #         "data_structure_version": "2.0",
    #         "components_included": ["signal_info", "market_data", "confluence_analysis", "technical_indicators", "trading_recommendations", "metadata"]
    #     }
    # }

    indicator_config = Column(
        JSON, nullable=True
    )  # Configurações dos indicadores usadas no sinal
    # Exemplo indicator_config: {
    #     "rsi_window": 14,
    #     "timeframe": "15m",
    #     "exchange": "mexc",
    #     "confluence_enabled": true,
    #     "custom_rsi_levels": {
    #         "oversold": 30,
    #         "overbought": 70
    #     },
    #     "ema_periods": {
    #         "short": 9,
    #         "medium": 21,
    #         "long": 50
    #     },
    #     "macd_config": {
    #         "fast_period": 12,
    #         "slow_period": 26,
    #         "signal_period": 9
    #     },
    #     "volume_config": {
    #         "sma_period": 20,
    #         "threshold_multiplier": 1.2
    #     },
    #     "confluence_thresholds": {
    #         "15m": {"min_score": 4, "min_indicators": 2},
    #         "1h": {"min_score": 4, "min_indicators": 2},
    #         "4h": {"min_score": 5, "min_indicators": 3}
    #     }
    # }

    # Dados de mercado no momento do sinal
    volume_24h = Column(Float, nullable=True)  # Volume 24h real da MEXC
    price_change_24h = Column(Float, nullable=True)  # Variação % 24h real
    high_24h = Column(Float, nullable=True)  # Máxima 24h
    low_24h = Column(Float, nullable=True)  # Mínima 24h
    quote_volume_24h = Column(Float, nullable=True)  # Volume em USDT 24h

    # Contexto de mercado adicional
    market_context = Column(JSON, nullable=True)  # Contexto adicional do mercado
    # Exemplo market_context: {
    #     "volatility_pct": 3.25,
    #     "trend_sentiment": "bullish",
    #     "price_momentum_pct": 1.85,
    #     "range_ratio": 1.15,
    #     "volume_ratio": 1.45,
    #     "is_high_volatility": false,
    #     "is_expanding_range": true,
    #     "avg_volume_10_periods": 987654.32,
    #     "market_phase": "trending",
    #     "support_resistance": {
    #         "nearest_support": 42500.0,
    #         "nearest_resistance": 44000.0,
    #         "support_strength": "strong",
    #         "resistance_strength": "moderate"
    #     },
    #     "momentum_indicators": {
    #         "price_velocity": 0.85,
    #         "acceleration": 0.15,
    #         "momentum_direction": "positive"
    #     },
    #     "volume_analysis": {
    #         "volume_trend": "increasing",
    #         "volume_profile": "bullish",
    #         "institutional_activity": "moderate"
    #     },
    #     "market_structure": {
    #         "trend_strength": "moderate",
    #         "consolidation_risk": "low",
    #         "breakout_potential": "high"
    #     }
    # }

    # Campos de qualidade melhorados
    confidence_score = Column(Float, nullable=True)  # % de confluência (0-100)
    combined_score = Column(Float, nullable=True)  # Score absoluto dos indicadores
    max_possible_score = Column(Integer, nullable=True)  # Score máximo possível

    # Controle de processamento (para bot do Telegram)
    processed = Column(Boolean, default=False)  # Se foi processado por algum serviço
    processed_at = Column(DateTime, nullable=True)  # Quando foi processado
    processed_by = Column(String(50), nullable=True)  # Qual serviço processou

    # Auditoria e performance
    processing_time_ms = Column(
        Integer, nullable=True
    )  # Tempo de processamento do sinal
    signal_quality = Column(String(20), nullable=True)  # EXCELLENT, GOOD, FAIR, POOR

    # Debug e monitoramento - dados originais para auditoria
    raw_payload = Column(JSON, nullable=True)  # Dados brutos originais da API/cálculos
    # Exemplo raw_payload: {
    #     "ohlcv_data": [...],  # Dados OHLCV originais da MEXC
    #     "rsi_calculation": {...},  # Dados intermediários do cálculo RSI
    #     "market_data_24h": {...},  # Dados 24h da MEXC
    #     "confluence_details": {...},  # Detalhes completos da confluência
    #     "api_response_times": {...},  # Tempos de resposta das APIs
    #     "timestamp": "2024-01-15T10:30:15Z",
    #     "debug_info": {...}  # Informações adicionais para debug
    # }


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


class MEXCTradingPair(Base):
    """Pares de trading da MEXC Exchange"""

    __tablename__ = "trading_coins"

    # Identificação
    id = Column(Integer, primary_key=True)
    symbol = Column(String(30), nullable=False, unique=True, index=True)
    base_asset = Column(String(20), nullable=False, index=True)
    quote_asset = Column(String(10), nullable=False, index=True)
    full_name = Column(String(200))

    # Dados OHLC para indicadores - usar Float para volumes grandes
    current_price = Column(Float)
    volume_24h = Column(Float)
    quote_volume_24h = Column(Float)
    open_price_24h = Column(Float)
    high_price_24h = Column(Float)
    low_price_24h = Column(Float)

    # Trading essencial
    maker_commission = Column(Float)
    taker_commission = Column(Float)
    base_asset_precision = Column(Integer)
    quote_asset_precision = Column(Integer)

    # Status
    is_active = Column(Boolean, default=True, index=True)
    is_spot_trading_allowed = Column(Boolean, default=True)

    # Payload completo
    raw_payload = Column(JSON)

    # Controle
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        index=True,
    )
