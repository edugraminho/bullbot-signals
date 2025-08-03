"""
Cliente Telegram para envio de sinais
"""

from typing import List, Optional
from telegram import Bot
from telegram.error import TelegramError
from telegram.request import HTTPXRequest
from src.core.services.rsi_service import RSIAnalysis
from src.database.models import TelegramSubscription
from src.database.connection import SessionLocal
from src.utils.logger import get_logger
from src.utils.price_formatter import format_crypto_price
import os


logger = get_logger(__name__)


class TelegramClient:
    """Cliente para envio de mensagens via Telegram com connection pooling otimizado"""

    def __init__(self, bot_token: str):
        from src.utils.config import settings

        # Configurar request personalizado com pool de conexões otimizado
        self.request = HTTPXRequest(
            connection_pool_size=settings.telegram_connection_pool_size,
            read_timeout=30.0,  # Timeout de leitura
            write_timeout=30.0,  # Timeout de escrita
            connect_timeout=10.0,  # Timeout de conexão
            pool_timeout=settings.telegram_pool_timeout,  # Configurável
        )

        self.bot = Bot(token=bot_token, request=self.request)
        self.bot_token = bot_token
        logger.info(
            f"🔧 Cliente Telegram configurado com pool de {settings.telegram_connection_pool_size} conexões (timeout: {settings.telegram_pool_timeout}s)"
        )

    async def send_signal(self, analysis: RSIAnalysis, chat_ids: List[str]) -> bool:
        """
        Envia sinal para lista de chats

        Args:
            analysis: Análise RSI com sinal
            chat_ids: Lista de IDs dos chats

        Returns:
            True se enviou com sucesso para pelo menos um chat
        """
        if not chat_ids:
            logger.warning("Nenhum chat_id fornecido para envio")
            return False

        message = self._format_signal_message(analysis)
        success_count = 0

        for chat_id in chat_ids:
            try:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode="HTML",
                    disable_web_page_preview=True,
                )
                success_count += 1
                logger.info(f"Sinal enviado para chat {chat_id}")

            except TelegramError as e:
                logger.error(f"❌ Erro ao enviar para chat {chat_id}: {e}")
                # Se chat não existe ou bot foi bloqueado, marcar como inativo
                if (
                    "chat not found" in str(e).lower()
                    or "bot was blocked" in str(e).lower()
                ):
                    await self._deactivate_subscription(chat_id)

        return success_count > 0

    def _format_signal_message(self, analysis: RSIAnalysis) -> str:
        """Formatar mensagem do sinal"""
        signal = analysis.signal
        rsi_data = analysis.rsi_data

        # Emojis por tipo de sinal
        emoji_map = {
            "STRONG_BUY": "🚀🟢",
            "BUY": "📈🟢",
            "SELL": "📉🔴",
            "STRONG_SELL": "💥🔴",
            "HOLD": "⏸️🟡",
        }

        # Emoji de força
        strength_emoji = {
            "STRONG": "💪",
            "MODERATE": "👍",
            "WEAK": "👌",
        }

        emoji = emoji_map.get(signal.signal_type.value, "📊")
        strength_icon = strength_emoji.get(signal.strength.value, "")

        message = f"""
        {emoji} <b>SINAL RSI - {rsi_data.symbol}/USDT</b>

        📊 <b>RSI:</b> {rsi_data.value:.2f}
        💰 <b>Preço:</b> {format_crypto_price(rsi_data.current_price)}
        ⏰ <b>Timeframe:</b> {signal.timeframe}
        📈 <b>Sinal:</b> {signal.signal_type.value} {strength_icon}
        🎯 <b>Força:</b> {signal.strength.value}

        💬 <b>Análise:</b>
        {signal.message}

        🔗 <b>Fonte:</b> {rsi_data.source.title()}
        📅 <b>Horário:</b> {signal.timestamp.strftime("%H:%M:%S UTC")}

        <i>💡 {analysis.interpretation}</i>
        <i>⚠️ Risco: {analysis.risk_level}</i>
        """.strip()

        return message

    async def _deactivate_subscription(self, chat_id: str):
        """Desativar assinatura inválida"""
        try:
            db = SessionLocal()
            subscription = (
                db.query(TelegramSubscription)
                .filter(TelegramSubscription.chat_id == chat_id)
                .first()
            )

            if subscription:
                subscription.active = False
                db.commit()
                logger.info(f"Assinatura {chat_id} desativada")

            db.close()

        except Exception as e:
            logger.error(f"❌ Erro ao desativar assinatura {chat_id}: {e}")

    async def get_active_subscribers(
        self, symbol_filter: Optional[str] = None
    ) -> List[str]:
        """
        Obter lista de chat_ids ativos
        """
        try:
            db = SessionLocal()
            query = db.query(TelegramSubscription).filter(
                TelegramSubscription.active == True  # noqa: E712
            )

            # Filtrar por símbolo se especificado
            if symbol_filter:
                # Assinantes que recebem TODOS os sinais (symbols_filter vazio ou None)
                # OU assinantes que têm esse símbolo específico no filtro
                query = query.filter(
                    (TelegramSubscription.symbols_filter.is_(None))
                    | (TelegramSubscription.symbols_filter == [])
                    | (TelegramSubscription.symbols_filter.any(symbol_filter))
                )

            subscriptions = query.all()
            chat_ids = [sub.chat_id for sub in subscriptions]

            db.close()
            logger.info(f"Encontrados {len(chat_ids)} assinantes ativos")
            return chat_ids

        except Exception as e:
            logger.error(f"❌ Erro ao obter assinantes: {e}")
            return []

    async def test_connection(self) -> bool:
        """Testar conexão com Telegram"""
        try:
            bot_info = await self.bot.get_me()
            logger.info(f"Bot conectado: @{bot_info.username}")
            return True
        except Exception as e:
            logger.error(f"❌ Erro na conexão Telegram: {e}")
            return False


# Configuração do bot
telegram_client = TelegramClient(os.getenv("TELEGRAM_BOT_TOKEN"))
