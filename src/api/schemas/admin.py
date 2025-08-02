"""
Schemas para endpoints de administração
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class MonitoringConfigCreate(BaseModel):
    """Schema para criar configuração de monitoramento"""

    name: str = Field(..., description="Nome da configuração", max_length=50)
    symbols: List[str] = Field(..., description="Lista de símbolos para monitorar")
    rsi_oversold: int = Field(30, ge=1, le=50, description="Limite de sobrevenda")
    rsi_overbought: int = Field(70, ge=50, le=100, description="Limite de sobrecompra")
    timeframes: List[str] = Field(
        ["15m", "1h", "4h"], description="Timeframes para análise"
    )
    active: bool = Field(True, description="Se a configuração está ativa")


class MonitoringConfigUpdate(BaseModel):
    """Schema para atualizar configuração de monitoramento"""

    name: Optional[str] = Field(None, max_length=50)
    symbols: Optional[List[str]] = None
    rsi_oversold: Optional[int] = Field(None, ge=1, le=50)
    rsi_overbought: Optional[int] = Field(None, ge=50, le=100)
    timeframes: Optional[List[str]] = None
    active: Optional[bool] = None


class MonitoringConfigResponse(BaseModel):
    """Schema de resposta para configuração de monitoramento"""

    id: int
    name: str
    symbols: List[str]
    rsi_oversold: int
    rsi_overbought: int
    timeframes: List[str]
    active: bool
    updated_at: datetime

    class Config:
        from_attributes = True


class TelegramSubscriptionCreate(BaseModel):
    """Schema para criar assinatura do Telegram"""

    chat_id: str = Field(..., description="ID do chat do Telegram")
    chat_type: str = Field(
        "private", description="Tipo do chat (private, group, channel)"
    )
    symbols_filter: Optional[List[str]] = Field(
        None, description="Filtro de símbolos específicos"
    )
    active: bool = Field(True, description="Se a assinatura está ativa")


class TelegramSubscriptionUpdate(BaseModel):
    """Schema para atualizar assinatura do Telegram"""

    chat_type: Optional[str] = None
    symbols_filter: Optional[List[str]] = None
    active: Optional[bool] = None


class TelegramSubscriptionResponse(BaseModel):
    """Schema de resposta para assinatura do Telegram"""

    id: int
    chat_id: str
    chat_type: str
    symbols_filter: Optional[List[str]]
    active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class SystemStatusResponse(BaseModel):
    """Schema de resposta para status do sistema"""

    monitoring_configs: int
    active_configs: int
    telegram_subscriptions: int
    active_subscriptions: int
    last_signal_count_24h: int
    celery_workers_active: bool
    telegram_bot_connected: bool


class CeleryStatusResponse(BaseModel):
    """Schema de resposta para status do Celery"""

    active_workers: int
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    monitoring_task_last_run: Optional[datetime]
    monitoring_task_next_run: Optional[datetime]


class TelegramTestResponse(BaseModel):
    """Schema de resposta para teste do Telegram"""

    connected: bool
    bot_username: Optional[str] = None
    bot_id: Optional[int] = None
    error_message: Optional[str] = None


class RecentSignalResponse(BaseModel):
    """Schema de resposta para sinais recentes"""

    id: int
    symbol: str
    rsi_value: float
    signal_type: str
    strength: str
    price: float
    timeframe: str
    source: str
    telegram_sent: bool
    created_at: datetime

    class Config:
        from_attributes = True
