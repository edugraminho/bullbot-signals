"""
Configuração principal do Celery
"""

import os
import logging
from celery import Celery
from src.utils.config import settings

# Configurar Celery
celery_app = Celery(
    "bullbot_signals",
    broker=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0"),
    include=[
        "src.tasks.monitor_tasks",
    ],
)

# Configurações do Celery
celery_app.conf.update(
    # Timezone
    timezone=settings.celery_timezone,
    enable_utc=settings.celery_enable_utc,
    # Broker connection settings
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    # Task routing - usar fila específica para signals
    task_routes={
        "src.tasks.monitor_tasks.*": {"queue": "signals"},
    },
    task_default_queue="signals",
    # Concorrência e Performance
    worker_concurrency=settings.celery_worker_count,
    worker_prefetch_multiplier=settings.celery_tasks_per_worker,
    task_acks_late=settings.celery_task_acknowledge_late,
    task_soft_time_limit=settings.celery_task_warning_timeout,
    task_time_limit=settings.celery_task_force_kill_timeout,
    # Configurações de Memória para ambientes com poucos recursos
    worker_max_memory_per_child=settings.celery_max_memory_per_child,
    # Beat schedule para monitoramento
    beat_schedule={
        "monitor-rsi-signals": {
            "task": "src.tasks.monitor_tasks.monitor_rsi_signals",
            "schedule": 300.0,  # A cada 5 minutos
        },
        # "cleanup-old-signals": {
        #     "task": "src.tasks.monitor_tasks.cleanup_old_signals",
        #     "schedule": float(settings.database_cleanup_interval_seconds),
        # },
        "update-trading-coins": {
            "task": "src.tasks.monitor_tasks.update_trading_coins",
            "schedule": float(
                settings.trading_coins_update_interval_days * 24 * 60 * 60
            ),
        },
    },
)

# Configuração de logging
celery_app.conf.worker_log_format = (
    "[%(asctime)s: %(levelname)s/%(processName)s] %(message)s"
)
celery_app.conf.worker_task_log_format = "[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s"

# Configurações para reduzir logs verbosos
celery_app.conf.worker_redirect_stdouts = False
celery_app.conf.worker_redirect_stdouts_level = "WARNING"

# Configurar logging para evitar logs duplicados - DESABILITAR CELERY LOGS
celery_app.conf.worker_hijack_root_logger = False
celery_app.conf.worker_log_color = False
celery_app.conf.task_always_eager = False

# Silenciar todos os loggers do Celery
logging.getLogger("celery").setLevel(logging.ERROR)
logging.getLogger("celery.worker").setLevel(logging.ERROR)
logging.getLogger("celery.task").setLevel(logging.ERROR)
logging.getLogger("celery.worker.control").setLevel(logging.ERROR)
logging.getLogger("celery.worker.consumer").setLevel(logging.ERROR)
logging.getLogger("celery.worker.consumer.connection").setLevel(logging.ERROR)

# Silenciar logs HTTP
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("httpcore").setLevel(logging.ERROR)
