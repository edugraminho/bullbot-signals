"""
Tasks Celery para Telegram
"""

from celery import current_app
from src.tasks.celery_app import celery_app
from src.integrations.telegram_bot import telegram_client
from src.database.models import SignalHistory
from src.database.connection import SessionLocal
from src.utils.logger import get_logger
import asyncio

logger = get_logger(__name__)


class TelegramTaskConfig:
    """Configuração para tasks do Telegram"""

    def __init__(self):
        self.max_retries = 3
        self.retry_countdown = 60
        self.cleanup_days = 30


# Instância global de configuração
telegram_config = TelegramTaskConfig()


@celery_app.task(bind=True, max_retries=3)
def send_telegram_signal(self, analysis):
    """
    Task para enviar sinal via Telegram

    Args:
        analysis: Objeto RSIAnalysis completo
    """
    try:
        symbol = analysis.rsi_data.symbol
        signal_type = analysis.signal.signal_type.value

        logger.info(f"Enviando sinal Telegram para {symbol}: {signal_type}")

        # Obter assinantes ativos (corrigir para chamada async)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            chat_ids = loop.run_until_complete(
                telegram_client.get_active_subscribers(symbol)
            )
        finally:
            loop.close()

        if not chat_ids:
            logger.warning(f"Nenhum assinante ativo para {symbol}")
            return {"status": "no_subscribers", "symbol": symbol}

        # Enviar sinal via Telegram (corrigir para chamada async)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            success = loop.run_until_complete(
                telegram_client.send_signal(analysis, chat_ids)
            )
        finally:
            loop.close()

        if success:
            # Marcar como enviado no banco
            db = SessionLocal()
            signal_history = SignalHistory(
                symbol=symbol,
                rsi_value=float(analysis.rsi_data.value),
                signal_type=signal_type,
                strength=analysis.signal.strength.value,
                price=float(analysis.rsi_data.current_price),
                timeframe=analysis.signal.timeframe,
                source=analysis.rsi_data.source,
                telegram_sent=True,
                message=analysis.signal.message,
            )
            db.add(signal_history)
            db.commit()
            db.close()

            return {"status": "sent", "symbol": symbol, "recipients": len(chat_ids)}
        else:
            return {
                "status": "failed",
                "symbol": symbol,
                "error": "Telegram send failed",
            }

    except Exception as e:
        logger.error(f"Erro ao enviar sinal Telegram: {e}")

        # Retry em caso de erro
        if self.request.retries < telegram_config.max_retries:
            logger.info(f"Reagendando envio (tentativa {self.request.retries + 1})")
            raise self.retry(countdown=telegram_config.retry_countdown, exc=e)

        return {"status": "failed", "error": str(e)}


@celery_app.task
def test_telegram_connection():
    """Task para testar conexão com Telegram"""
    try:
        # Corrigir para chamada async
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            is_connected = loop.run_until_complete(telegram_client.test_connection())
        finally:
            loop.close()

        return {
            "status": "connected" if is_connected else "disconnected",
            "timestamp": current_app.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Erro no teste de conexão Telegram: {e}")
        return {"status": "error", "error": str(e)}


@celery_app.task
def cleanup_inactive_subscriptions():
    """Task para limpar assinaturas inativas"""
    try:
        db = SessionLocal()

        # Por agora, apenas log - implementar lógica completa depois
        logger.info("Limpeza de assinaturas inativas executada")

        db.close()

        return {"status": "completed", "cleaned": 0}

    except Exception as e:
        logger.error(f"Erro na limpeza de assinaturas: {e}")
        return {"status": "error", "error": str(e)}
