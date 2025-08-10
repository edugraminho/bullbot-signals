"""
Rotas essenciais para consumo de sinais
"""

from datetime import datetime, timedelta, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.api.schemas.admin import SignalResponse, SystemStatusResponse
from src.database.connection import get_db
from src.database.models import MonitoringConfig, SignalHistory
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])


# ==========================================
# SYSTEM STATUS ENDPOINT
# ==========================================


@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status(db: Session = Depends(get_db)):
    """Obter status geral do sistema"""
    try:
        # Contar configurações
        total_configs = db.query(MonitoringConfig).count()
        active_configs = (
            db.query(MonitoringConfig).filter(MonitoringConfig.active == True).count()  # noqa: E712
        )

        # Contar sinais das últimas 24h
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        recent_signals = (
            db.query(SignalHistory)
            .filter(SignalHistory.created_at >= yesterday)
            .count()
        )

        # Contar sinais não processados
        unprocessed_signals = (
            db.query(SignalHistory)
            .filter(SignalHistory.processed == False)  # noqa: E712
            .count()
        )

        # TODO: Verificar status do Celery
        celery_workers_active = True  # Placeholder

        return SystemStatusResponse(
            monitoring_configs=total_configs,
            active_configs=active_configs,
            last_signal_count_24h=recent_signals,
            unprocessed_signals=unprocessed_signals,
            celery_workers_active=celery_workers_active,
        )

    except Exception as e:
        logger.error(f"❌ Erro ao obter status do sistema: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# SIGNAL ENDPOINTS (ESSENCIAIS)
# ==========================================


@router.get("/signals/unprocessed", response_model=List[SignalResponse])
async def get_unprocessed_signals(
    limit: int = Query(50, ge=1, le=200, description="Número de sinais"),
    db: Session = Depends(get_db),
):
    """Obter sinais não processados (para bot do Telegram)"""
    try:
        signals = (
            db.query(SignalHistory)
            .filter(SignalHistory.processed == False)  # noqa: E712
            .order_by(SignalHistory.created_at.asc())
            .limit(limit)
            .all()
        )

        return signals

    except Exception as e:
        logger.error(f"❌ Erro ao obter sinais não processados: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/signals/{signal_id}/mark-processed")
async def mark_signal_processed(
    signal_id: int,
    processed_by: str = Query(
        ..., description="Identificação do serviço que processou"
    ),
    db: Session = Depends(get_db),
):
    """Marcar sinal como processado"""
    try:
        signal = db.query(SignalHistory).filter(SignalHistory.id == signal_id).first()

        if not signal:
            raise HTTPException(status_code=404, detail="Sinal não encontrado")

        # Marcar como processado
        signal.processed = True
        signal.processed_at = datetime.now(timezone.utc)
        signal.processed_by = processed_by

        db.commit()

        logger.info(f"✅ Sinal {signal_id} marcado como processado por {processed_by}")
        return {"message": "Sinal marcado como processado", "signal_id": signal_id}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erro ao marcar sinal como processado: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/signals/recent", response_model=List[SignalResponse])
async def get_recent_signals(
    limit: int = Query(10, ge=1, le=50, description="Número de sinais"),
    db: Session = Depends(get_db),
):
    """Obter sinais recentes (para debug/monitoramento)"""
    try:
        signals = (
            db.query(SignalHistory)
            .order_by(SignalHistory.created_at.desc())
            .limit(limit)
            .all()
        )

        return signals

    except Exception as e:
        logger.error(f"❌ Erro ao obter sinais recentes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/signals/last", response_model=List[SignalResponse])
async def get_last_signals(
    limit: int = Query(50, ge=1, le=200, description="Número de sinais"),
    hours: int = Query(24, ge=1, le=168, description="Horas para trás"),
    db: Session = Depends(get_db),
):
    """Obter sinais das últimas X horas (para debug/monitoramento)"""
    try:
        # Calcular timestamp de corte
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        # Buscar sinais recentes
        signals = (
            db.query(SignalHistory)
            .filter(SignalHistory.created_at >= cutoff_time)
            .order_by(SignalHistory.created_at.desc())
            .limit(limit)
            .all()
        )

        return signals

    except Exception as e:
        logger.error(f"❌ Erro ao buscar sinais das últimas {hours}h: {e}")
        raise HTTPException(status_code=500, detail=str(e))
