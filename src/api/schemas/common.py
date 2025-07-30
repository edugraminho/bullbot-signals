"""
Schemas comuns para a API
"""

from typing import Optional, Any, Dict
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """DTO para respostas de erro"""

    detail: str
    error_code: Optional[str] = None
    timestamp: Optional[str] = None


class SuccessResponse(BaseModel):
    """DTO para respostas de sucesso genéricas"""

    message: str
    data: Optional[Dict[str, Any]] = None


class StatusResponse(BaseModel):
    """DTO para status geral da aplicação"""

    status: str
    service: str
    version: str
