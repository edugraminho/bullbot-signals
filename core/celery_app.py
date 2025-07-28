"""
Configuração do Celery para processamento assíncrono.

Define a aplicação Celery e suas configurações para
processamento de tarefas em background.
"""

import os
from celery import Celery
from celery.schedules import crontab
import logging

logger = logging.getLogger(__name__)

# Configuração do Celery
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")

# Criação da aplicação Celery
celery_app = Celery(
    "crypto_hunter",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=[
        "core.tasks.data_collection",
        "core.tasks.rsi_calculation",
        "core.tasks.notifications",
    ],
)

# Configurações do Celery
celery_app.conf.update(
    # Configurações básicas
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Configurações de tarefas
    task_always_eager=False,
    task_eager_propagates=True,
    # Configurações de worker
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    # Configurações de beat (agendamento)
    beat_schedule={
        "collect-market-data": {
            "task": "core.tasks.data_collection.collect_market_data",
            "schedule": crontab(minute="*/5"),  # A cada 5 minutos
        },
        "calculate-rsi-signals": {
            "task": "core.tasks.rsi_calculation.calculate_rsi_signals",
            "schedule": crontab(minute="*/1"),  # A cada minuto
        },
        "send-notifications": {
            "task": "core.tasks.notifications.send_notifications",
            "schedule": crontab(minute="*/2"),  # A cada 2 minutos
        },
    },
    # Configurações de resultado
    result_expires=3600,  # 1 hora
    task_ignore_result=False,
    # Configurações de logging
    worker_log_format="[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
    worker_task_log_format="[%(asctime)s: %(levelname)s/%(processName)s] [%(task_name)s(%(task_id)s)] %(message)s",
)

# Configuração de logging
celery_app.conf.update(
    worker_log_level="INFO",
    worker_log_color=True,
)


# Tarefas de exemplo (serão implementadas nos módulos específicos)
@celery_app.task(bind=True)
def debug_task(self):
    """Tarefa de debug para testar o Celery."""
    logger.info(f"Request: {self.request!r}")
    return "Debug task completed"


@celery_app.task
def health_check():
    """Tarefa de health check do Celery."""
    logger.info("Celery health check completed")
    return {"status": "healthy", "timestamp": "2025-01-XX"}


if __name__ == "__main__":
    celery_app.start()
