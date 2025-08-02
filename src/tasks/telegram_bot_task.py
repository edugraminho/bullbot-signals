"""
Task Celery para executar o bot Telegram em background
"""

import asyncio
from src.tasks.celery_app import celery_app
from src.integrations.telegram_handlers import run_telegram_bot
from src.utils.logger import get_logger

logger = get_logger(__name__)


@celery_app.task(bind=True)
def start_telegram_bot_polling(self):
    """
    Task para iniciar o bot Telegram em modo polling
    Esta task roda continuamente até ser interrompida
    """
    try:
        logger.info("Iniciando task do bot Telegram...")

        # Executar o bot em loop asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(run_telegram_bot())
        except KeyboardInterrupt:
            logger.info("Bot interrompido manualmente")
        except Exception as e:
            logger.error(f"❌ Erro no bot Telegram: {e}")
            raise
        finally:
            loop.close()

        return {"status": "stopped", "task_id": self.request.id}

    except Exception as e:
        logger.error(f"❌ Erro na task do bot Telegram: {e}")
        return {"status": "error", "error": str(e)}


@celery_app.task
def stop_telegram_bot():
    """Task para parar o bot Telegram (se necessário)"""
    try:
        # Esta é uma implementação simples
        # O bot pode ser parado externamente ou via sinal
        logger.info("Comando para parar bot Telegram recebido")
        return {"status": "stop_requested"}

    except Exception as e:
        logger.error(f"❌ Erro ao parar bot: {e}")
        return {"status": "error", "error": str(e)}
