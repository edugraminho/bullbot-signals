"""
Handlers para comandos do bot Telegram
"""

import asyncio
from typing import Optional
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.constants import ParseMode
from src.database.models import TelegramSubscription, MonitoringConfig
from src.database.connection import SessionLocal
from src.utils.config import settings
from src.utils.logger import get_logger
import os

logger = get_logger(__name__)


class TelegramBot:
    """Bot do Telegram com handlers para comandos"""

    def __init__(self, token: str):
        self.token = token
        self.application = None
        self.bot = Bot(token=token)

    async def start_handler(self, update: Update, context):
        """Handler para comando /start"""
        try:
            chat_id = str(update.effective_chat.id)
            chat_type = update.effective_chat.type

            logger.info(
                f"Comando /start recebido do chat {chat_id} (tipo: {chat_type})"
            )

            # Verificar se já está cadastrado
            db = SessionLocal()
            existing = (
                db.query(TelegramSubscription)
                .filter(TelegramSubscription.chat_id == chat_id)
                .first()
            )

            if existing:
                if existing.active:
                    message = "✅ Você já está cadastrado e ativo!\n\n"
                else:
                    # Reativar se estava inativo
                    existing.active = True
                    db.commit()
                    message = "✅ Sua assinatura foi reativada!\n\n"
            else:
                # Criar nova assinatura
                subscription = TelegramSubscription(
                    chat_id=chat_id, chat_type=chat_type, active=True
                )
                db.add(subscription)
                db.commit()
                message = "🎉 Bem-vindo ao Crypto Hunter!\n\n✅ Você foi cadastrado com sucesso!\n\n"

            db.close()

            # Mensagem de boas-vindas
            welcome_text = f"""
                {message}
                🤖 <b>Crypto Hunter Bot</b>
            
                📊 <b>O que eu faço:</b>
                • Monitoro indicadores RSI de criptomoedas
                • Envio sinais de compra/venda automaticamente
                • Analiso múltiplas exchanges (Binance, Gate.io, MEXC)

                ⚡ <b>Comandos disponíveis:</b>
                /status - Ver sua configuração atual
                /help - Lista completa de comandos
                /stop - Parar de receber sinais

                🔔 <b>Como funciona:</b>
                Você receberá alertas automáticos quando detectarmos:
                • 🟢 Oportunidades de COMPRA (RSI baixo)
                • 🔴 Oportunidades de VENDA (RSI alto)
                • 📊 Análise detalhada com preços e força do sinal

                <i>⚠️ Lembre-se: Sinais são apenas informativos. Sempre faça sua própria análise!</i>"""

            await update.message.reply_text(welcome_text, parse_mode=ParseMode.HTML)

        except Exception as e:
            logger.error(f"Erro no comando /start: {e}")
            await update.message.reply_text(
                "❌ Erro interno. Tente novamente mais tarde."
            )

    async def status_handler(self, update: Update, context):
        """Handler para comando /status"""
        try:
            chat_id = str(update.effective_chat.id)

            db = SessionLocal()

            # Buscar assinatura
            subscription = (
                db.query(TelegramSubscription)
                .filter(TelegramSubscription.chat_id == chat_id)
                .first()
            )

            if not subscription:
                await update.message.reply_text(
                    "❌ Você não está cadastrado. Use /start para se cadastrar."
                )
                db.close()
                return

            # Buscar configuração ativa
            active_config = (
                db.query(MonitoringConfig)
                .filter(MonitoringConfig.active == True)  # noqa: E712
                .first()
            )

            status_active = "🟢 ATIVO" if subscription.active else "🔴 INATIVO"

            status_text = f"""
                📊 <b>Seu Status no Crypto Hunter</b>

                👤 <b>Assinatura:</b> {status_active}
                🆔 <b>Chat ID:</b> <code>{chat_id}</code>
                📅 <b>Cadastrado em:</b> {subscription.created_at.strftime("%d/%m/%Y às %H:%M")}
                💬 <b>Tipo de chat:</b> {subscription.chat_type}
                """

            # Filtros de símbolos
            if subscription.symbols_filter:
                symbols = ", ".join(subscription.symbols_filter)
                status_text += f"\n🎯 <b>Símbolos filtrados:</b> {symbols}"
            else:
                status_text += f"\n🎯 <b>Símbolos:</b> Todos os monitorados"

            # Configuração ativa do sistema
            if active_config:
                status_text += f"""

                ⚙️ <b>Configuração Ativa do Sistema:</b>
                📈 <b>Nome:</b> {active_config.name}
                📊 <b>Símbolos monitorados:</b> {len(active_config.symbols)} 
                ⏰ <b>Timeframes:</b> {", ".join(active_config.timeframes)}
                📉 <b>RSI Sobrevenda:</b> ≤{active_config.rsi_oversold}
                📈 <b>RSI Sobrecompra:</b> ≥{active_config.rsi_overbought}
                ⏱️ <b>Cooldown:</b> {active_config.cooldown_hours}h entre sinais
                """
            else:
                status_text += "\n\n⚠️ <b>Nenhuma configuração ativa no sistema</b>"

            db.close()

            await update.message.reply_text(status_text, parse_mode=ParseMode.HTML)

        except Exception as e:
            logger.error(f"Erro no comando /status: {e}")
            await update.message.reply_text(
                "❌ Erro ao consultar status. Tente novamente."
            )

    async def help_handler(self, update: Update, context):
        """Handler para comando /help"""
        help_text = """🤖 <b>Crypto Hunter - Lista de Comandos</b>

            <b>📋 Comandos Básicos:</b>
            /start - Cadastrar/reativar assinatura
            /status - Ver seu status e configurações
            /help - Esta lista de comandos
            /stop - Parar de receber sinais

            <b>📊 Sobre os Sinais:</b>
            • <b>RSI (Relative Strength Index):</b> Indica se uma crypto está sobrecomprada ou sobrevendida
            • <b>Sobrevenda (≤30):</b> Possível oportunidade de compra 🟢
            • <b>Sobrecompra (≥70):</b> Possível oportunidade de venda 🔴

            <b>🎯 Tipos de Sinal:</b>
            🚀 <b>STRONG_BUY:</b> Sinal forte de compra
            📈 <b>BUY:</b> Sinal moderado de compra
            📉 <b>SELL:</b> Sinal moderado de venda
            💥 <b>STRONG_SELL:</b> Sinal forte de venda
            ⏸️ <b>HOLD:</b> Manter posição

            <b>💪 Força do Sinal:</b>
            • <b>STRONG:</b> Alta confiança 💪
            • <b>MODERATE:</b> Confiança média 👍
            • <b>WEAK:</b> Baixa confiança 👌

            <b>⚙️ Configurações:</b>
            • Monitoramento a cada 5 minutos
            • Múltiplas exchanges (Binance, Gate.io, MEXC)
            • Cooldown para evitar spam
            • Filtros inteligentes de qualidade

            <i>⚠️ <b>Aviso:</b> Os sinais são apenas informativos e não constituem aconselhamento financeiro. Sempre faça sua própria pesquisa antes de investir!</i>

            💬 <b>Suporte:</b> Em caso de problemas, entre em contato com o administrador.
        """

        await update.message.reply_text(help_text, parse_mode=ParseMode.HTML)

    async def stop_handler(self, update: Update, context):
        """Handler para comando /stop"""
        try:
            chat_id = str(update.effective_chat.id)

            db = SessionLocal()
            subscription = (
                db.query(TelegramSubscription)
                .filter(TelegramSubscription.chat_id == chat_id)
                .first()
            )

            if not subscription:
                await update.message.reply_text("❌ Você não está cadastrado.")
                db.close()
                return

            # Desativar assinatura
            subscription.active = False
            db.commit()
            db.close()

            stop_text = """
                😔 <b>Assinatura Desativada</b>

                Você não receberá mais sinais do Crypto Hunter.

                Para reativar, use o comando /start a qualquer momento.

                🙏 Obrigado por usar nosso serviço!

            """

            await update.message.reply_text(stop_text, parse_mode=ParseMode.HTML)

        except Exception as e:
            logger.error(f"Erro no comando /stop: {e}")
            await update.message.reply_text(
                "❌ Erro ao desativar assinatura. Tente novamente."
            )

    async def unknown_handler(self, update: Update, context):
        """Handler para comandos desconhecidos"""
        unknown_text = """
            ❓ <b>Comando não reconhecido</b>

            Use /help para ver a lista de comandos disponíveis.

            <b>Comandos básicos:</b>
            /start - Cadastrar
            /status - Ver status  
            /help - Lista de comandos
            /stop - Parar sinais
            """

        await update.message.reply_text(unknown_text, parse_mode=ParseMode.HTML)

    def setup_handlers(self):
        """Configurar handlers do bot"""
        if not self.application:
            self.application = Application.builder().token(self.token).build()

        # Handlers de comandos
        self.application.add_handler(CommandHandler("start", self.start_handler))
        self.application.add_handler(CommandHandler("status", self.status_handler))
        self.application.add_handler(CommandHandler("help", self.help_handler))
        self.application.add_handler(CommandHandler("stop", self.stop_handler))

        # Handler para comandos desconhecidos
        self.application.add_handler(
            MessageHandler(filters.COMMAND, self.unknown_handler)
        )

    async def start_polling(self):
        """Iniciar polling do bot"""
        if not self.application:
            self.setup_handlers()

        logger.info("Iniciando polling do bot Telegram...")
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()

    async def stop_polling(self):
        """Parar polling do bot"""
        if self.application:
            logger.info("Parando polling do bot Telegram...")
            await self.application.updater.stop()
            await self.application.stop()


# Instância global do bot
def get_telegram_bot() -> Optional[TelegramBot]:
    """Obter instância do bot Telegram"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.warning("TELEGRAM_BOT_TOKEN não configurado")
        return None

    return TelegramBot(token)


# Para usar em contexto assíncrono
async def run_telegram_bot():
    """Executar bot em modo polling"""
    bot = get_telegram_bot()
    if bot:
        try:
            await bot.start_polling()
            # Manter o bot rodando
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            logger.info("Bot interrompido pelo usuário")
            await bot.stop_polling()
        except Exception as e:
            logger.error(f"Erro no bot: {e}")
            if bot.application:
                await bot.stop_polling()
