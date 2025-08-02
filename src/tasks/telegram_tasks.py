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
        analysis: Objeto RSIAnalysis completo ou dicionário com dados do sinal
    """
    try:
        # Verificar se é dicionário ou objeto
        if isinstance(analysis, dict):
            # Dados vindos de monitor_tasks
            symbol = analysis["symbol"]
            signal_type = analysis["signal_type"]
            rsi_value = analysis["rsi_value"]
            current_price = analysis["current_price"]
            strength = analysis["strength"]
            timeframe = analysis["timeframe"]
            message = analysis["message"]
            source = analysis["source"]
            timestamp = analysis["timestamp"]
        else:
            # Objeto RSIAnalysis
            symbol = analysis.rsi_data.symbol
            signal_type = analysis.signal.signal_type.value
            rsi_value = float(analysis.rsi_data.value)
            current_price = float(analysis.rsi_data.current_price)
            strength = analysis.signal.strength.value
            timeframe = analysis.signal.timeframe
            message = analysis.signal.message
            source = analysis.rsi_data.source
            timestamp = analysis.rsi_data.timestamp.isoformat()

        logger.info(f"Enviando sinal Telegram para {symbol}: {signal_type}")

        # Obter assinantes ativos
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

        # Enviar sinal via Telegram
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            if isinstance(analysis, dict):
                # Criar mensagem de teste
                test_message = f"""
🚀 <b>SINAL RSI - {symbol}/USDT</b>

📊 <b>RSI:</b> {rsi_value:.2f}
💰 <b>Preço:</b> ${current_price:,.2f}
⏰ <b>Timeframe:</b> {timeframe}
📈 <b>Sinal:</b> {signal_type.upper()}
🎯 <b>Força:</b> {strength.upper()}

💬 <b>Análise:</b>
{message}

🔗 <b>Fonte:</b> {source.title()}
📅 <b>Horário:</b> {timestamp}

<i>🤖 Sinal automático do Crypto Hunter!</i>
                """.strip()

                # Enviar mensagem diretamente
                async def send_messages():
                    success_count = 0
                    for chat_id in chat_ids:
                        try:
                            await telegram_client.bot.send_message(
                                chat_id=chat_id,
                                text=test_message,
                                parse_mode="HTML",
                                disable_web_page_preview=True,
                            )
                            success_count += 1
                            logger.info(f"Mensagem enviada para chat {chat_id}")
                        except Exception as e:
                            logger.error(f"❌ Erro ao enviar para chat {chat_id}: {e}")
                    return success_count > 0

                success = loop.run_until_complete(send_messages())
            else:
                # Objeto RSIAnalysis - usar método original
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
                rsi_value=rsi_value,
                signal_type=signal_type,
                strength=strength,
                price=current_price,
                timeframe=timeframe,
                source=source,
                telegram_sent=True,
                message=message,
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
        logger.error(f"❌ Erro ao enviar sinal Telegram: {e}")

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
        logger.error(f"❌ Erro no teste de conexão Telegram: {e}")
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
        logger.error(f"❌ Erro na limpeza de assinaturas: {e}")
        return {"status": "error", "error": str(e)}
