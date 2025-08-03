"""
Tasks principais de monitoramento RSI
"""

import asyncio
import time
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from celery import group

from src.core.services.rsi_service import RSIService
from src.core.services.signal_filter import signal_filter
from src.database.connection import SessionLocal
from src.database.models import MonitoringConfig, SignalHistory
from src.integrations.telegram_bot import telegram_client
from src.tasks.celery_app import celery_app
from src.tasks.telegram_tasks import send_telegram_signal
from src.utils.config import settings
from src.utils.logger import get_logger
from src.utils.trading_coins import trading_coins

logger = get_logger(__name__, level="INFO")


class MonitorTaskConfig:
    """Configuração para tasks de monitoramento"""

    def __init__(self):
        self.rsi_window = settings.rsi_calculation_window
        self.rsi_timeframe = settings.rsi_analysis_timeframe
        self.max_retries = settings.task_max_retry_attempts
        self.retry_countdown = settings.task_retry_delay_seconds
        self.cleanup_days = settings.signal_history_retention_days
        self.default_symbols = settings.default_crypto_symbols


# Instância global de configuração
task_config = MonitorTaskConfig()


@celery_app.task(bind=True)
def update_trading_coins(self):
    """
    Task para atualizar lista de trading coins - executa a cada 7 dias
    """
    try:
        logger.info("Iniciando atualização da lista de trading coins")

        # Executar atualização
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            coins = loop.run_until_complete(trading_coins.update_trading_list())

            if coins:
                logger.info(
                    f"Lista de trading coins atualizada com {len(coins)} moedas"
                )

                return {
                    "status": "success",
                    "total_coins": len(coins),
                    "message": f"Lista atualizada com {len(coins)} moedas",
                }
            else:
                logger.error("Falha ao atualizar lista de trading coins")
                return {"status": "error", "message": "Falha ao atualizar lista"}

        finally:
            loop.close()

    except Exception as e:
        logger.error(f"❌ Erro na atualização de trading coins: {e}")

        if self.request.retries < task_config.max_retries:
            logger.info(
                f"Reagendando atualização de trading coins (tentativa {self.request.retries + 1})"
            )
            raise self.retry(countdown=task_config.retry_countdown, exc=e)

        return {"status": "error", "error": str(e)}


@celery_app.task(bind=True)
def monitor_rsi_signals(self):
    """
    Task principal de monitoramento - executa a cada 5 minutos (config no celery_app.py)
    """
    cycle_start_time = time.time()

    try:
        logger.info("=" * 60)
        logger.info("🚀 INICIANDO CICLO DE MONITORAMENTO RSI 🚀")
        logger.info("=" * 60)

        # Obter configuração ativa
        symbols = get_active_symbols()
        if not symbols:
            logger.warning("Nenhum símbolo configurado para monitoramento")
            return {"status": "no_symbols"}

        # Distribuir símbolos por exchange para rate limiting
        symbol_batches = distribute_symbols_by_exchange(symbols)

        # Criar tasks paralelas para cada batch
        job_group = group(
            process_symbol_batch.s(exchange, batch_symbols)
            for exchange, batch_symbols in symbol_batches.items()
        )

        # Executar em paralelo
        result = job_group.apply_async()

        cycle_duration = time.time() - cycle_start_time
        logger.info(
            f"✅ Ciclo iniciado: {len(symbols)} símbolos em {len(symbol_batches)} exchanges "
            f"(inicialização: {cycle_duration:.2f}s)"
        )
        logger.info("-" * 60)

        # Agendar callback para log de fim de ciclo
        finalize_monitoring_cycle.delay(
            cycle_start_time, len(symbols), len(symbol_batches)
        )

        return {
            "status": "started",
            "total_symbols": len(symbols),
            "batches": len(symbol_batches),
            "job_id": result.id,
            "cycle_start_time": cycle_start_time,
        }

    except Exception as e:
        cycle_duration = time.time() - cycle_start_time
        logger.error(
            f"❌ Erro no monitoramento principal: {e} (ciclo: {cycle_duration:.2f}s)"
        )
        return {"status": "error", "error": str(e)}


@celery_app.task(bind=True, max_retries=2)
def process_symbol_batch(self, exchange: str, symbols: List[str]):
    """
    Processar batch de símbolos para uma exchange específica

    Args:
        exchange: Nome da exchange (binance, gate, mexc)
        symbols: Lista de símbolos para processar
    """
    batch_start_time = time.time()

    try:
        logger.info(f"🔄 Processando {len(symbols)} símbolos na {exchange}")

        # Carregar configurações de monitoramento do banco
        monitoring_config = get_active_monitoring_config()

        # Criar RSIService com configurações personalizadas se disponível
        if monitoring_config:
            from src.core.models.crypto import RSILevels

            custom_rsi_levels = RSILevels(
                oversold=monitoring_config.rsi_oversold,
                overbought=monitoring_config.rsi_overbought,
            )
            rsi_service = RSIService(custom_rsi_levels=custom_rsi_levels)
        else:
            # config.py
            rsi_service = RSIService()

        # Processar cada símbolo
        results = []
        successful = 0
        filtered = 0
        errors = 0
        no_data = 0

        for i, symbol in enumerate(symbols, 1):
            symbol_start_time = time.time()

            result = process_single_symbol(
                symbol=symbol,
                exchange=exchange,
                rsi_service=rsi_service,
                rsi_window=task_config.rsi_window,
                rsi_timeframe=task_config.rsi_timeframe,
            )

            # Contar estatísticas
            if result.get("status") == "signal_sent":
                successful += 1
            elif result.get("status") == "filtered":
                filtered += 1
            elif result.get("status") == "no_data":
                no_data += 1
            else:
                errors += 1

            results.append(result)

            # Log de progresso a cada 10 símbolos
            if i % 10 == 0 or i == len(symbols):
                symbol_duration = time.time() - symbol_start_time
                logger.info(
                    f"📊 {exchange}: {i}/{len(symbols)} símbolos processados "
                    f"({symbol_duration:.2f}s/símbolo)"
                )

        batch_duration = time.time() - batch_start_time
        avg_time_per_symbol = batch_duration / len(symbols) if symbols else 0

        logger.info(
            f"✅ Batch {exchange} concluído: {successful}/{len(symbols)} sucessos "
            f"({batch_duration:.2f}s total, {avg_time_per_symbol:.2f}s/moeda)"
        )
        logger.info("-" * 40)

        return {
            "status": "completed",
            "exchange": exchange,
            "total": len(symbols),
            "successful": successful,
            "filtered": filtered,
            "errors": errors,
            "no_data": no_data,
            "duration": batch_duration,
            "avg_time_per_symbol": avg_time_per_symbol,
        }

    except Exception as e:
        batch_duration = time.time() - batch_start_time
        logger.error(
            f"❌ Erro no batch {exchange}: {e} (duração: {batch_duration:.2f}s)"
        )

        if self.request.retries < task_config.max_retries:
            logger.info(
                f"🔄 Reagendando batch {exchange} (tentativa {self.request.retries + 1})"
            )
            raise self.retry(countdown=task_config.retry_countdown, exc=e)

        return {"status": "failed", "exchange": exchange, "error": str(e)}


def process_single_symbol(
    symbol: str,
    exchange: str,
    rsi_service: RSIService,
    rsi_window: int,
    rsi_timeframe: str,
) -> dict:
    """
    Processar um único símbolo

    Args:
        symbol: Símbolo da crypto
        exchange: Exchange para buscar dados
        rsi_service: Instância do serviço RSI

    Returns:
        Resultado do processamento
    """
    try:
        # Buscar RSI (usando async em context)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        rsi_data = loop.run_until_complete(
            rsi_service.get_rsi(symbol, rsi_timeframe, rsi_window, exchange)
        )

        if not rsi_data:
            # Moeda não encontrada - remover exchange da lista
            from src.utils.trading_coins import trading_coins

            trading_coins.remove_exchange_from_coin(symbol, exchange)
            logger.debug(f"❌ {symbol}: Sem dados na {exchange}")
            return {"status": "no_data", "symbol": symbol, "exchange": exchange}

        # Analisar RSI
        analysis = rsi_service.analyze_rsi(rsi_data)

        # Log breve da moeda e RSI
        logger.debug(
            f"📊 {symbol}: RSI {rsi_data.value:.2f} | Preço ${rsi_data.current_price}"
        )

        if not analysis:
            logger.debug(f"⚪ {symbol}: Zona neutra (RSI: {rsi_data.value:.2f})")
            return {
                "status": "neutral_zone",
                "symbol": symbol,
                "rsi_value": rsi_data.value,
            }

        # Aplicar filtros anti-spam
        should_send = loop.run_until_complete(
            signal_filter.should_send_signal(symbol, analysis)
        )

        if should_send:
            # Verificar se há assinantes ativos antes de enviar

            chat_ids = loop.run_until_complete(
                telegram_client.get_active_subscribers(symbol)
            )

            if not chat_ids:
                logger.debug(f"Nenhum assinante ativo para {symbol} - sinal ignorado")
                return {
                    "status": "no_subscribers",
                    "symbol": symbol,
                    "rsi_value": rsi_data.value,
                }

            # Enviar sinal via Telegram (task assíncrona)
            # Criar dicionário serializável com os dados do sinal
            signal_data = {
                "symbol": symbol,
                "signal_type": analysis.signal.signal_type.value,
                "rsi_value": float(rsi_data.value),
                "current_price": float(rsi_data.current_price),
                "strength": analysis.signal.strength.value,
                "timeframe": analysis.signal.timeframe,
                "message": analysis.signal.message,
                "source": rsi_data.source,
                "timestamp": rsi_data.timestamp.isoformat(),
            }

            send_telegram_signal.delay(signal_data)

            # Marcar sinal como enviado
            loop.run_until_complete(signal_filter.mark_signal_sent(symbol, analysis))

            logger.info(
                f"📡 🚀 SINAL ENVIADO: {symbol} | {analysis.signal.signal_type.value} | "
                f"RSI: {rsi_data.value:.2f} | {len(chat_ids)} assinantes"
            )

            return {
                "status": "signal_sent",
                "symbol": symbol,
                "signal_type": analysis.signal.signal_type.value,
                "rsi_value": rsi_data.value,
            }

        else:
            logger.debug(f"🔕 {symbol}: Sinal filtrado (RSI: {rsi_data.value:.2f})")
            return {"status": "filtered", "symbol": symbol, "rsi_value": rsi_data.value}

    except Exception as e:
        logger.error(f"❌ Erro ao processar {symbol} na {exchange}: {e}")
        return {"status": "error", "symbol": symbol, "error": str(e)}

    finally:
        if "loop" in locals():
            loop.close()


def get_active_symbols() -> List[str]:
    """Obter lista de símbolos ativos para monitoramento"""
    try:
        db = SessionLocal()
        config = (
            db.query(MonitoringConfig).filter(MonitoringConfig.active == True).first()  # noqa: E712
        )

        if config and config.symbols and len(config.symbols) > 0:
            # Usar símbolos da configuração do banco
            symbols = config.symbols
            logger.info(f"📋 Usando {len(symbols)} símbolos da configuração do banco")
        else:
            # Usar lista de trading coins se não há configuração ou lista vazia
            symbols = trading_coins.get_trading_symbols(limit=500)
            logger.info(f"📋 Usando {len(symbols)} símbolos da lista de trading coins")

        db.close()
        return symbols

    except Exception as e:
        logger.error(f"❌ Erro ao obter símbolos: {e}")
        # Fallback para lista padrão em caso de erro
        return task_config.default_symbols


def get_active_monitoring_config() -> Optional[MonitoringConfig]:
    """Obter configuração de monitoramento ativa do banco"""
    try:
        db = SessionLocal()
        config = (
            db.query(MonitoringConfig).filter(MonitoringConfig.active == True).first()  # noqa: E712
        )
        db.close()
        return config
    except Exception as e:
        logger.error(f"❌ Erro ao obter configuração de monitoramento: {e}")
        return None


def distribute_symbols_by_exchange(symbols: List[str]) -> dict:
    """
    Distribuir símbolos entre as exchanges baseado na disponibilidade no CSV

    Args:
        symbols: Lista de todos os símbolos

    Returns:
        Dict com exchange -> lista de símbolos
    """
    # Carregar dados do CSV para verificar exchanges disponíveis
    coins = trading_coins.load_from_csv()
    coin_exchanges = {coin.symbol: coin.exchanges for coin in coins}

    # Inicializar listas por exchange
    exchange_symbols = {"binance": [], "gate": [], "mexc": []}

    # Distribuir símbolos baseado nas exchanges disponíveis
    for symbol in symbols:
        available_exchanges = coin_exchanges.get(symbol, [])

        if not available_exchanges:
            # Se não há exchanges, pular
            continue

        # Distribuir para a primeira exchange disponível
        for exchange in ["binance", "gate", "mexc"]:
            if exchange in available_exchanges:
                exchange_symbols[exchange].append(symbol)
                break

    return exchange_symbols


@celery_app.task
def cleanup_old_signals():
    """Task diária para limpeza de dados antigos"""
    cleanup_start_time = time.time()

    try:
        db = SessionLocal()

        # Remover sinais antigos baseado na configuração
        cutoff_date = datetime.now(timezone.utc) - timedelta(
            days=task_config.cleanup_days
        )

        deleted_count = (
            db.query(SignalHistory)
            .filter(SignalHistory.created_at < cutoff_date)
            .delete()
        )

        db.commit()
        db.close()

        cleanup_duration = time.time() - cleanup_start_time
        logger.info(
            f"🧹 Limpeza concluída: {deleted_count} registros removidos ({cleanup_duration:.2f}s)"
        )

        return {
            "status": "completed",
            "deleted_count": deleted_count,
            "cutoff_date": cutoff_date.isoformat(),
            "duration": cleanup_duration,
        }

    except Exception as e:
        cleanup_duration = time.time() - cleanup_start_time
        logger.error(f"❌ Erro na limpeza: {e} (duração: {cleanup_duration:.2f}s)")
        return {"status": "error", "error": str(e)}


@celery_app.task
def finalize_monitoring_cycle(
    cycle_start_time: float, total_symbols: int, total_batches: int
):
    """Task para finalizar logs do ciclo de monitoramento"""
    try:
        # Aguardar um tempo para que os batches terminem
        import time

        time.sleep(10)  # 10 segundos de delay para permitir que os batches terminem

        cycle_duration = time.time() - cycle_start_time
        logger.info("-" * 60)
        logger.info("🏁 FINALIZANDO CICLO DE MONITORAMENTO RSI")
        logger.info(
            f"📊 Total processado: {total_symbols} símbolos em {total_batches} batches"
        )
        logger.info(f"⏱️ Duração total do ciclo: {cycle_duration:.2f}s")
        logger.info("=" * 60)

        return {
            "status": "cycle_finalized",
            "total_duration": cycle_duration,
            "total_symbols": total_symbols,
            "total_batches": total_batches,
        }

    except Exception as e:
        logger.error(f"❌ Erro ao finalizar ciclo: {e}")
        return {"status": "error", "error": str(e)}
