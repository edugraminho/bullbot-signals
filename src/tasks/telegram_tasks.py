"""
Tasks Celery para Telegram
"""

from celery import current_app
from src.tasks.celery_app import celery_app
from src.integrations.telegram_bot import telegram_client
from src.database.models import SignalHistory
from src.database.connection import SessionLocal
from src.utils.logger import get_logger
from src.utils.price_formatter import format_crypto_price
import asyncio
import random
from telegram.error import TimedOut, NetworkError, RetryAfter

logger = get_logger(__name__)


async def send_message_with_retry(
    bot, chat_id: str, message_text: str, max_retries: int = 3
) -> bool:
    """
    Envia mensagem com retry inteligente e backoff exponencial

    Args:
        bot: Instância do bot Telegram
        chat_id: ID do chat
        message_text: Texto da mensagem
        max_retries: Máximo de tentativas

    Returns:
        True se enviou com sucesso, False caso contrário

    Por que essa abordagem:
    - Backoff exponencial: reduz carga na API
    - Jitter: evita "thundering herd" (todas as tasks tentando ao mesmo tempo)
    - Tratamento específico para diferentes tipos de erro
    - Sem sleep bloqueante: usa asyncio.sleep que não bloqueia a thread
    """

    for attempt in range(max_retries + 1):
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=message_text,
                parse_mode="HTML",
                disable_web_page_preview=True,
            )
            return True

        except RetryAfter as e:
            # API rate limit - esperar o tempo indicado
            wait_time = e.retry_after + random.uniform(0.1, 0.5)  # Jitter
            logger.warning(
                f"⏳ Rate limit para chat {chat_id}: aguardando {wait_time:.1f}s"
            )
            await asyncio.sleep(wait_time)

        except (TimedOut, NetworkError) as e:
            if attempt < max_retries:
                # Backoff exponencial com jitter
                wait_time = (2**attempt) + random.uniform(0.1, 1.0)
                logger.warning(
                    f"🔄 Tentativa {attempt + 1}/{max_retries + 1} para chat {chat_id} - aguardando {wait_time:.1f}s"
                )
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"❌ Falha definitiva para chat {chat_id}: {e}")
                return False

        except Exception as e:
            logger.error(f"❌ Erro inesperado para chat {chat_id}: {e}")
            return False

    return False


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
        # Verificar se o cliente Telegram está disponível
        if telegram_client is None:
            logger.error(
                "❌ Cliente Telegram não está disponível - verificar TELEGRAM_BOT_TOKEN"
            )
            return {"status": "failed", "error": "Telegram client not available"}

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

        logger.info(
            f"🚀 Iniciando envio de sinal Telegram para {symbol}: {signal_type}"
        )

        # Usar um único loop para toda a operação
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Função assíncrona principal que executa todas as operações
            async def process_telegram_signal():
                # Obter assinantes ativos
                logger.info(f"🔍 Buscando assinantes para {symbol}...")
                chat_ids = await telegram_client.get_active_subscribers(symbol)
                logger.info(f"📋 Encontrados {len(chat_ids)} assinantes para {symbol}")

                if not chat_ids:
                    logger.warning(f"❌ Nenhum assinante ativo para {symbol}")
                    return {"status": "no_subscribers", "symbol": symbol}

                # Enviar mensagens diretamente para cada chat
                success_count = 0

                # Formatar mensagem (sempre recebemos dicionário)
                formatted_price = format_crypto_price(current_price)

                message_text = f"""
🚀 <b>SINAL RSI - {symbol}/USDT</b>

📊 <b>RSI:</b> {rsi_value:.2f}
💰 <b>Preço:</b> {formatted_price}
⏰ <b>Timeframe:</b> {timeframe}
📈 <b>Sinal:</b> {signal_type.upper()}
🎯 <b>Força:</b> {strength.upper()}

💬 <b>Análise:</b>
{message}

🔗 <b>Fonte:</b> {source.title()}
📅 <b>Horário:</b> {timestamp}

<i>🤖 Sinal automático do Crypto Hunter!</i>
                """.strip()

                # Enviar para cada chat usando retry inteligente
                logger.info(f"📤 Enviando mensagem para {len(chat_ids)} chats...")

                # Processar chats em pequenos lotes para evitar sobrecarga
                from src.utils.config import settings

                batch_size = settings.telegram_batch_size  # Configurável
                for i in range(0, len(chat_ids), batch_size):
                    batch_chat_ids = chat_ids[i : i + batch_size]
                    logger.info(
                        f"📤 Processando lote {i // batch_size + 1}: {len(batch_chat_ids)} chats"
                    )

                    # Criar tasks assíncronas para o lote
                    send_tasks = [
                        send_message_with_retry(
                            telegram_client.bot, chat_id, message_text
                        )
                        for chat_id in batch_chat_ids
                    ]

                    # Executar lote e contar sucessos
                    batch_results = await asyncio.gather(
                        *send_tasks, return_exceptions=True
                    )

                    for chat_id, result in zip(batch_chat_ids, batch_results):
                        if isinstance(result, Exception):
                            logger.error(f"❌ Exceção para chat {chat_id}: {result}")
                        elif result:
                            success_count += 1
                            logger.info(
                                f"✅ Mensagem enviada com sucesso para chat {chat_id}"
                            )
                        else:
                            logger.error(f"❌ Falha no envio para chat {chat_id}")

                    # Pequena pausa entre lotes para distribuir a carga
                    if i + batch_size < len(chat_ids):
                        await asyncio.sleep(0.1)  # 100ms entre lotes

                return {
                    "success": success_count > 0,
                    "chat_ids": chat_ids,
                    "symbol": symbol,
                    "sent_count": success_count,
                }

            # Executar a operação completa
            result = loop.run_until_complete(process_telegram_signal())

            logger.info(f"📊 Resultado do processamento para {symbol}: {result}")

            # Verificar se houve sucesso
            if result.get("status") == "no_subscribers":
                logger.warning(f"❌ Nenhum assinante para {symbol}")
                return result

            success = result.get("success", False)
            sent_count = result.get("sent_count", 0)

        except Exception as e:
            logger.error(f"❌ Erro durante processamento assíncrono: {e}")
            success = False
            sent_count = 0
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

            logger.info(
                f"✅ Sinal enviado com sucesso para {symbol} - {sent_count} destinatários"
            )
            return {"status": "sent", "symbol": symbol, "recipients": sent_count}
        else:
            logger.error(f"❌ Falha no envio do sinal para {symbol}")
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
