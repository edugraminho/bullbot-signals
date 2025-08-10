"""
Schemas essenciais para consumo de sinais
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class SystemStatusResponse(BaseModel):
    """Schema de resposta para status do sistema"""

    monitoring_configs: int
    active_configs: int
    last_signal_count_24h: int
    unprocessed_signals: int
    celery_workers_active: bool


class SignalResponse(BaseModel):
    """Schema de resposta para sinais"""

    id: int
    symbol: str
    signal_type: str
    strength: str
    price: float
    timeframe: str
    source: str
    message: str
    indicator_type: List[str]
    indicator_data: Dict[str, Any]
    confidence_score: Optional[float]
    combined_score: Optional[float]
    processed: bool
    processed_at: Optional[datetime]
    processed_by: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class CeleryStatusResponse(BaseModel):
    """Schema de resposta para status do Celery"""

    active_workers: int
    scheduled_tasks: int
    failed_tasks: int
    monitoring_task_last_run: Optional[datetime]
    monitoring_task_next_run: Optional[datetime]
