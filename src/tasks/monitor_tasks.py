"""
Tasks principais de monitoramento RSI
"""

import asyncio
from typing import List
from celery import group
from src.tasks.celery_app import celery_app
from src.core.services.rsi_service import RSIService
from src.core.services.signal_filter import signal_filter
from src.tasks.telegram_tasks import send_telegram_signal
from src.database.models import MonitoringConfig, SignalHistory
from src.database.connection import SessionLocal
from src.utils.logger import get_logger
from src.utils.config import settings
from datetime import datetime, timedelta, timezone

logger = get_logger(__name__)


class MonitorTaskConfig:
    """Configuração para tasks de monitoramento"""

    def __init__(self):
        self.rsi_window = settings.rsi_window
        self.rsi_timeframe = settings.rsi_timeframe
        self.max_retries = settings.max_retries
        self.retry_countdown = settings.retry_countdown
        self.cleanup_days = settings.cleanup_days
        self.default_symbols = settings.default_symbols


# Instância global de configuração
task_config = MonitorTaskConfig()


@celery_app.task(bind=True)
def monitor_rsi_signals(self):
    """
    Task principal de monitoramento - executa a cada 5 minutos (config no celery_app.py)
    """
    try:
        logger.info("Iniciando monitoramento de sinais RSI")

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

        logger.info(
            f"Monitoramento iniciado para {len(symbols)} símbolos em {len(symbol_batches)} exchanges"
        )

        return {
            "status": "started",
            "total_symbols": len(symbols),
            "batches": len(symbol_batches),
            "job_id": result.id,
        }

    except Exception as e:
        logger.error(f"Erro no monitoramento principal: {e}")
        return {"status": "error", "error": str(e)}


@celery_app.task(bind=True, max_retries=2)
def process_symbol_batch(self, exchange: str, symbols: List[str]):
    """
    Processar batch de símbolos para uma exchange específica

    Args:
        exchange: Nome da exchange (binance, gate, mexc)
        symbols: Lista de símbolos para processar
    """
    try:
        logger.info(f"Processando {len(symbols)} símbolos na {exchange}")

        # Processar cada símbolo
        results = []
        rsi_service = RSIService()

        for symbol in symbols:
            result = process_single_symbol(
                symbol=symbol,
                exchange=exchange,
                rsi_service=rsi_service,
                rsi_window=task_config.rsi_window,
                rsi_timeframe=task_config.rsi_timeframe,
            )
            results.append(result)

        # Estatísticas
        successful = sum(1 for r in results if r.get("status") == "processed")

        logger.info(f"Batch {exchange} concluído: {successful}/{len(symbols)} sucessos")

        return {
            "status": "completed",
            "exchange": exchange,
            "total": len(symbols),
            "successful": successful,
            "results": results,
        }

    except Exception as e:
        logger.error(f"Erro no batch {exchange}: {e}")

        if self.request.retries < task_config.max_retries:
            logger.info(
                f"Reagendando batch {exchange} (tentativa {self.request.retries + 1})"
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
            return {"status": "no_data", "symbol": symbol, "exchange": exchange}

        # Analisar RSI
        analysis = rsi_service.analyze_rsi(rsi_data)

        # Aplicar filtros anti-spam
        should_send = loop.run_until_complete(
            signal_filter.should_send_signal(symbol, analysis)
        )

        if should_send:
            # Enviar sinal via Telegram (task assíncrona)
            # Passar objeto RSIAnalysis completo
            send_telegram_signal.delay(analysis)

            # Marcar sinal como enviado
            loop.run_until_complete(signal_filter.mark_signal_sent(symbol, analysis))

            logger.info(
                f"Sinal enviado para {symbol}: {analysis.signal.signal_type.value}"
            )

            return {
                "status": "signal_sent",
                "symbol": symbol,
                "signal_type": analysis.signal.signal_type.value,
                "rsi_value": rsi_data.value,
            }

        else:
            logger.debug(f"Sinal filtrado para {symbol}")
            return {"status": "filtered", "symbol": symbol, "rsi_value": rsi_data.value}

    except Exception as e:
        logger.error(f"Erro ao processar {symbol} na {exchange}: {e}")
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

        if config and config.symbols:
            symbols = config.symbols
        else:
            # Usar lista padrão se não há configuração
            symbols = task_config.default_symbols

        db.close()
        logger.info(f"Monitorando {len(symbols)} símbolos")
        return symbols

    except Exception as e:
        logger.error(f"Erro ao obter símbolos: {e}")
        return task_config.default_symbols


def distribute_symbols_by_exchange(symbols: List[str]) -> dict:
    """
    Distribuir símbolos entre as exchanges para rate limiting

    Args:
        symbols: Lista de todos os símbolos

    Returns:
        Dict com exchange -> lista de símbolos
    """
    # Distribuição simples: 1/3 para cada exchange
    total = len(symbols)
    third = total // 3

    return {
        "binance": symbols[:third],
        "gate": symbols[third : 2 * third],
        "mexc": symbols[2 * third :],
    }


@celery_app.task
def cleanup_old_signals():
    """Task diária para limpeza de dados antigos"""
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

        logger.info(f"Limpeza concluída: {deleted_count} registros removidos")

        return {
            "status": "completed",
            "deleted_count": deleted_count,
            "cutoff_date": cutoff_date.isoformat(),
        }

    except Exception as e:
        logger.error(f"Erro na limpeza: {e}")
        return {"status": "error", "error": str(e)}
