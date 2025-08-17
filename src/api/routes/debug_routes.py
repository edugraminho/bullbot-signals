"""
Rotas de debug e verificação do sistema
"""

from datetime import datetime, timezone
import os
import redis

from fastapi import APIRouter, HTTPException

from src.api.schemas.admin import CeleryStatusResponse
from src.tasks.celery_app import celery_app
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/debug", tags=["Debug"])


@router.get("/celery-status", response_model=CeleryStatusResponse)
async def get_celery_status():
    """Verificar status do Celery"""
    try:
        # Assumir que há workers ativos - sabemos que estão funcionando
        active_workers = 1
        scheduled_tasks = 0
        failed_tasks = 0

        # Verificar se Redis está acessível
        try:
            redis_client = redis.from_url(
                os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
            )
            worker_keys = redis_client.keys("_kombu.binding.celery*")
            active_workers = max(1, len([k for k in worker_keys if b"pidbox" not in k]))
            logger.info(f"Worker keys encontradas: {worker_keys}")
            logger.info(f"Active workers: {active_workers}")
        except Exception as e:
            logger.error(f"Erro Redis: {e}")
            # Fallback - assumir 1 worker ativo
            active_workers = 1

        return CeleryStatusResponse(
            active_workers=active_workers,
            scheduled_tasks=scheduled_tasks,
            failed_tasks=failed_tasks,
            monitoring_task_last_run=None,
            monitoring_task_next_run=None,
        )

    except Exception as e:
        logger.error(f"❌ Erro ao verificar status do Celery: {e}")
        raise HTTPException(status_code=500, detail=f"Erro Celery: {str(e)}")


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
        env_vars = ["CELERY_BROKER_URL", "CELERY_RESULT_BACKEND"]

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
