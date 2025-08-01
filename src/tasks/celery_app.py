"""
Configuração principal do Celery
"""

import os
from celery import Celery

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
    timezone="UTC",
    enable_utc=True,
    # Task routing
    task_routes={
        "src.tasks.monitor_tasks.*": {"queue": "monitor"},
        "src.tasks.telegram_tasks.*": {"queue": "telegram"},
        "src.tasks.telegram_bot_task.*": {"queue": "telegram"},
    },
    # Concorrência
    worker_concurrency=4,  # Retry configurations
    task_acks_late=True,
    worker_prefetch_multiplier=1,  # Task time limits
    task_soft_time_limit=300,  # 5 minutos
    task_time_limit=600,  # 10 minutos
    # Beat schedule para monitoramento
    beat_schedule={
        "monitor-rsi-signals": {
            "task": "src.tasks.monitor_tasks.monitor_rsi_signals",
            "schedule": 300.0,  # A cada 5 minutos
        },
        "cleanup-old-signals": {
            "task": "src.tasks.monitor_tasks.cleanup_old_signals",
            "schedule": 86400.0,  # Diário
        },
    },
)

# Configuração de logging
celery_app.conf.worker_log_format = (
    "[%(asctime)s: %(levelname)s/%(processName)s] %(message)s"
)
celery_app.conf.worker_task_log_format = "[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s"
