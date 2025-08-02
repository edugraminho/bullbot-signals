"""
Rotas de debug e verificação do sistema
"""

from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from src.database.connection import get_db
from src.database.models import SignalHistory
from src.api.schemas.admin import (
    CeleryStatusResponse,
    TelegramTestResponse,
    RecentSignalResponse,
)
from src.integrations.telegram_bot import telegram_client
from src.tasks.celery_app import celery_app
from src.utils.logger import get_logger
from datetime import datetime, timedelta, timezone
import os

logger = get_logger(__name__)

router = APIRouter(prefix="/debug", tags=["Debug"])


@router.get("/celery-status", response_model=CeleryStatusResponse)
async def get_celery_status():
    """Verificar status do Celery"""
    try:
        # Obter informações dos workers ativos
        inspect = celery_app.control.inspect()

        # Workers ativos
        active_workers = 0
        if inspect.active():
            active_workers = len(inspect.active())

        # Tasks agendadas
        scheduled_tasks = 0
        if inspect.scheduled():
            for worker_tasks in inspect.scheduled().values():
                scheduled_tasks += len(worker_tasks)

        # Tasks que falharam (últimas 24h)
        failed_tasks = 0
        # Note: Celery não oferece API simples para isso

        # Informações de beat schedule
        monitoring_task_last_run = None
        monitoring_task_next_run = None

        # TODO: Implementar verificação mais detalhada do beat

        return CeleryStatusResponse(
            active_workers=active_workers,
            scheduled_tasks=scheduled_tasks,
            failed_tasks=failed_tasks,
            monitoring_task_last_run=monitoring_task_last_run,
            monitoring_task_next_run=monitoring_task_next_run,
        )

    except Exception as e:
        logger.error(f"❌ Erro ao verificar status do Celery: {e}")
        raise HTTPException(status_code=500, detail=f"Erro Celery: {str(e)}")


@router.get("/telegram-test", response_model=TelegramTestResponse)
async def test_telegram_connection():
    """Testar conexão com o bot do Telegram"""
    try:
        # Verificar se token está configurado
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            return TelegramTestResponse(
                connected=False,
                error_message="TELEGRAM_BOT_TOKEN não configurado no .env",
            )

        # Testar conexão
        is_connected = await telegram_client.test_connection()

        if is_connected:
            # Obter informações do bot
            bot_info = await telegram_client.bot.get_me()
            return TelegramTestResponse(
                connected=True,
                bot_username=bot_info.username,
                bot_id=bot_info.id,
            )
        else:
            return TelegramTestResponse(
                connected=False, error_message="Falha na conexão com o Telegram"
            )

    except Exception as e:
        logger.error(f"❌ Erro no teste do Telegram: {e}")
        return TelegramTestResponse(connected=False, error_message=str(e))


@router.get("/last-signals", response_model=List[RecentSignalResponse])
async def get_recent_signals(
    limit: int = 50, hours: int = 24, db: Session = Depends(get_db)
):
    """Obter sinais recentes"""
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
        logger.error(f"❌ Erro ao buscar sinais recentes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system-health")
async def check_system_health():
    """Verificação geral de saúde do sistema"""
    try:
        health_status = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "healthy",
            "checks": {},
        }

        # Verificar variáveis de ambiente essenciais
        env_vars = ["TELEGRAM_BOT_TOKEN", "CELERY_BROKER_URL", "CELERY_RESULT_BACKEND"]

        for var in env_vars:
            health_status["checks"][f"env_{var.lower()}"] = {
                "status": "ok" if os.getenv(var) else "missing",
                "value": "***" if os.getenv(var) else None,
            }

        # Verificar Celery
        try:
            inspect = celery_app.control.inspect()
            workers = inspect.active()
            health_status["checks"]["celery_workers"] = {
                "status": "ok" if workers else "no_workers",
                "count": len(workers) if workers else 0,
            }
        except Exception as e:
            health_status["checks"]["celery_workers"] = {
                "status": "error",
                "error": str(e),
            }

        # Verificar Telegram
        try:
            telegram_connected = await telegram_client.test_connection()
            health_status["checks"]["telegram_bot"] = {
                "status": "ok" if telegram_connected else "disconnected"
            }
        except Exception as e:
            health_status["checks"]["telegram_bot"] = {
                "status": "error",
                "error": str(e),
            }

        # Determinar status geral
        failed_checks = [
            check
            for check in health_status["checks"].values()
            if check["status"] not in ["ok"]
        ]

        if failed_checks:
            health_status["status"] = (
                "degraded" if len(failed_checks) < 3 else "unhealthy"
            )

        return health_status

    except Exception as e:
        logger.error(f"❌ Erro na verificação de saúde: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger-monitoring")
async def trigger_monitoring_task():
    """Disparar task de monitoramento manualmente (para testes)"""
    try:
        from src.tasks.monitor_tasks import monitor_rsi_signals

        # Executar task assincronamente
        task_result = monitor_rsi_signals.delay()

        return {
            "message": "Task de monitoramento disparada",
            "task_id": task_result.id,
            "status": "submitted",
        }

    except Exception as e:
        logger.error(f"❌ Erro ao disparar task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/task-result/{task_id}")
async def get_task_result(task_id: str):
    """Obter resultado de uma task específica"""
    try:
        task_result = celery_app.AsyncResult(task_id)

        return {
            "task_id": task_id,
            "status": task_result.status,
            "result": task_result.result,
            "traceback": task_result.traceback,
        }

    except Exception as e:
        logger.error(f"❌ Erro ao obter resultado da task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
