"""
Schemas para rotas administrativas
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SystemStatusResponse(BaseModel):
    """Schema de resposta para status do sistema"""

    monitoring_configs: int
    active_configs: int
    unique_active_users: int
    last_signal_count_24h: int
    celery_workers_active: bool


class UserConfigResponse(BaseModel):
    """Schema de resposta para configurações de usuário"""

    id: int
    user_id: int
    user_username: Optional[str]
    config_name: str
    config_type: str
    symbols: List[str]
    timeframes: List[str]
    indicators_config: Optional[Dict[str, Any]]
    filter_config: Optional[Dict[str, Any]]
    priority: int
    active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class UserConfigCreate(BaseModel):
    """Schema para criação de configuração de usuário"""

    user_username: Optional[str] = None
    config_name: str = Field(..., min_length=1, max_length=100)
    config_type: str = Field(default="custom", max_length=50)
    symbols: List[str] = Field(..., min_items=1)
    timeframes: List[str] = Field(..., min_items=1)
    indicators_config: Optional[Dict[str, Any]] = None
    filter_config: Optional[Dict[str, Any]] = None
    priority: int = Field(default=1, ge=1, le=10)
    active: bool = Field(default=True)


class UserConfigUpdate(BaseModel):
    """Schema para atualização de configuração de usuário"""

    user_username: Optional[str] = None
    config_name: Optional[str] = Field(None, min_length=1, max_length=100)
    config_type: Optional[str] = Field(None, max_length=50)
    symbols: Optional[List[str]] = Field(None, min_items=1)
    timeframes: Optional[List[str]] = Field(None, min_items=1)
    indicators_config: Optional[Dict[str, Any]] = None
    filter_config: Optional[Dict[str, Any]] = None
    priority: Optional[int] = Field(None, ge=1, le=10)
    active: Optional[bool] = None


class CeleryStatusResponse(BaseModel):
    """Schema de resposta para status do Celery"""

    active_workers: int
    scheduled_tasks: int
    failed_tasks: int
    monitoring_task_last_run: Optional[datetime]
    monitoring_task_next_run: Optional[datetime]
