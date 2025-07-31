"""
Schemas/DTOs para endpoints de RSI
(Modelos de serialização da API, não de domínio)
"""

from typing import List, Optional, Dict
from pydantic import BaseModel


class RSIResponse(BaseModel):
    """DTO para resposta de consulta de RSI"""

    symbol: str
    rsi_value: float
    current_price: float
    timestamp: str
    timespan: str
    window: int
    source: str
    data_source: str


class MultipleRSIResponse(BaseModel):
    """DTO para resposta de múltiplos RSI"""

    results: Dict[str, Optional[RSIResponse]]
    successful_count: int
    total_count: int


class HealthResponse(BaseModel):
    """DTO para health check"""

    status: str
    api: Dict[str, str]
    message: str
