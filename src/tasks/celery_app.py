"""
Configuração principal do Celery
"""

import os
from celery import Celery
from src.utils.config import settings

# Configurar Celery
celery_app = Celery(
    "crypto_hunter",
    broker=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0"),
    include=[
        "src.tasks.monitor_tasks",
        "src.tasks.telegram_tasks",
        "src.tasks.telegram_bot_task",
    ],
)

# Configurações do Celery
celery_app.conf.update(
    # Timezone
    timezone=settings.celery_timezone,
    enable_utc=settings.celery_enable_utc,
    # Task routing
    task_routes={
        "src.tasks.monitor_tasks.*": {"queue": "monitor"},
        "src.tasks.telegram_tasks.*": {"queue": "telegram"},
        "src.tasks.telegram_bot_task.*": {"queue": "telegram"},
    },
    # Concorrência e Performance
    worker_concurrency=settings.celery_worker_count,
    task_acks_late=settings.celery_task_acknowledge_late,
    worker_prefetch_multiplier=settings.celery_tasks_per_worker,
    task_soft_time_limit=settings.celery_task_warning_timeout,
    task_time_limit=settings.celery_task_force_kill_timeout,
    # Beat schedule para monitoramento
    beat_schedule={
        "monitor-rsi-signals": {
            "task": "src.tasks.monitor_tasks.monitor_rsi_signals",
            "schedule": float(settings.signal_monitoring_interval_seconds),
        },
        "cleanup-old-signals": {
            "task": "src.tasks.monitor_tasks.cleanup_old_signals",
            "schedule": float(settings.database_cleanup_interval_seconds),
        },
    },
)

# Configuração de logging
celery_app.conf.worker_log_format = (
    "[%(asctime)s: %(levelname)s/%(processName)s] %(message)s"
)
celery_app.conf.worker_task_log_format = "[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s"
