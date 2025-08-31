"""
Tasks principais de monitoramento RSI
"""

import asyncio
import time
from datetime import datetime, timedelta, timezone
from typing import List

from src.core.services.rsi_service import RSIService
from src.core.services.signal_filter import signal_filter
from src.database.connection import SessionLocal
from src.database.models import UserMonitoringConfig, SignalHistory
from src.tasks.celery_app import celery_app
from src.utils.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__, level="INFO")


class MonitorTaskConfig:
    """Configuração para tasks de monitoramento"""

    def __init__(self):
        self.rsi_window = settings.rsi_calculation_window
        self.max_retries = settings.task_max_retry_attempts
        self.retry_countdown = settings.task_retry_delay_seconds
        self.cleanup_days = settings.signal_history_retention_days


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
            from src.utils.trading_coins import trading_coins

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
    Task principal de monitoramento - executa sequencialmente
    Agenda próxima execução 1 minuto após término
    """
    cycle_start_time = time.time()

    try:
        logger.info("=" * 60)
        logger.info("🚀 🚀 INICIANDO CICLO DE MONITORAMENTO RSI 🚀 🚀")
        logger.info("=" * 60)

        # Obter configuração ativa
        symbols = get_active_symbols()
        if not symbols:
            logger.warning("Nenhum símbolo configurado para monitoramento")
            # Agendar próxima execução mesmo sem símbolos
            self.apply_async(countdown=60)
            return {"status": "no_symbols"}

        # Usar exchanges padrão para todos os símbolos
        exchanges_with_symbols = {"binance": symbols, "mexc": symbols, "gate": symbols}

        # Criar chain sequencial de tasks
        from celery import chord

        if not symbols:
            logger.warning("Nenhuma exchange com símbolos para processar")
            # Agendar próxima execução mesmo sem exchanges
            self.apply_async(countdown=60)
            return {"status": "no_exchanges"}

        # Criar lista de tasks para executar
        tasks_list = []
        for exchange, batch_symbols in exchanges_with_symbols.items():
            logger.info(f"Preparando {exchange} ({len(batch_symbols)} símbolos)...")
            tasks_list.append(process_symbol_batch.s(exchange, batch_symbols))

        # Usar chord para executar sequencialmente e aguardar resultados

        callback = finalize_monitoring_cycle.s(
            cycle_start_time=cycle_start_time,
            total_symbols=len(symbols),
            total_exchanges=len(exchanges_with_symbols),
        ).set(link=schedule_next_monitoring.s())

        chord(tasks_list, callback).apply_async()

        cycle_duration = time.time() - cycle_start_time
        logger.info(
            f"Chord iniciado: {len(symbols)} símbolos em {len(exchanges_with_symbols)} exchanges "
            f"(inicialização: {cycle_duration:.2f}s)"
        )
        logger.info("-" * 60)

        return {
            "status": "chord_started",
            "total_symbols": len(symbols),
            "exchanges": len(exchanges_with_symbols),
            "cycle_start_time": cycle_start_time,
            "processing_mode": "sequential_chord",
        }

    except Exception as e:
        cycle_duration = time.time() - cycle_start_time
        logger.error(
            f"❌ Erro no monitoramento sequencial: {e} (ciclo: {cycle_duration:.2f}s)"
        )
        # Agendar próxima execução mesmo em caso de erro
        self.apply_async(countdown=60)
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
        logger.info(f"Processando {len(symbols)} símbolos na {exchange}")

        # Carregar TODAS as configurações de monitoramento ativas
        monitoring_configs = get_active_monitoring_configs()

        # Criar RSIService com configurações agregadas mais sensíveis
        if monitoring_configs:
            from src.core.models.crypto import RSILevels

            # Encontrar os thresholds mais sensíveis de todas as configurações
            # (menor oversold e maior overbought para capturar todos os sinais)
            min_oversold = 100
            max_overbought = 0

            for config in monitoring_configs:
                if config.indicators_config and "RSI" in config.indicators_config:
                    rsi_config = config.indicators_config["RSI"]
                    if rsi_config.get("enabled", False):
                        oversold = rsi_config.get("oversold", 20)
                        overbought = rsi_config.get("overbought", 80)

                        min_oversold = min(min_oversold, oversold)
                        max_overbought = max(max_overbought, overbought)

            # Se nenhuma configuração RSI válida foi encontrada, usar padrão
            if min_oversold == 100 or max_overbought == 0:
                logger.warning(
                    "⚠️ Nenhuma configuração RSI válida encontrada, usando padrão"
                )
                rsi_service = RSIService()
            else:
                custom_rsi_levels = RSILevels(
                    oversold=min_oversold,
                    overbought=max_overbought,
                )
                rsi_service = RSIService(custom_rsi_levels=custom_rsi_levels)
        else:
            # Usar configuração padrão se não há configurações
            logger.warning(
                "⚠️ Nenhuma configuração de monitoramento ativa, usando RSI padrão"
            )
            rsi_service = RSIService()

        # Obter timeframes ativos das configurações
        active_timeframes = get_active_timeframes()

        # Processar cada combinação símbolo+timeframe
        results = []
        successful = 0
        filtered = 0
        errors = 0
        no_data = 0
        total_combinations = len(symbols) * len(active_timeframes)
        processed_count = 0

        for symbol in symbols:
            for timeframe in active_timeframes:
                processed_count += 1
                symbol_start_time = time.time()

                result = process_single_symbol(
                    symbol=symbol,
                    exchange=exchange,
                    rsi_service=rsi_service,
                    rsi_window=task_config.rsi_window,
                    rsi_timeframe=timeframe,
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

                # Log de progresso a cada 20 combinações ou no final
                if processed_count % 20 == 0 or processed_count == total_combinations:
                    symbol_duration = time.time() - symbol_start_time
                    logger.info(
                        f"{exchange}: {processed_count}/{total_combinations} combinações processadas "
                        f"({symbol_duration:.2f}s/combinação)"
                    )

        batch_duration = time.time() - batch_start_time
        avg_time_per_combination = (
            batch_duration / total_combinations if total_combinations else 0
        )

        logger.info(
            f"Batch {exchange} concluído: {successful}/{total_combinations} sinais detectados "
            f"({batch_duration:.2f}s total, {avg_time_per_combination:.2f}s/combinação)"
        )

        return {
            "status": "completed",
            "exchange": exchange,
            "total_symbols": len(symbols),
            "total_timeframes": len(active_timeframes),
            "total_combinations": total_combinations,
            "successful": successful,
            "filtered": filtered,
            "errors": errors,
            "no_data": no_data,
            "duration": batch_duration,
            "avg_time_per_combination": avg_time_per_combination,
        }

    except Exception as e:
        batch_duration = time.time() - batch_start_time
        logger.error(
            f"❌ Erro no batch {exchange}: {e} (duração: {batch_duration:.2f}s)"
        )

        if self.request.retries < task_config.max_retries:
            logger.info(
                f"Reagendando batch {exchange} (tentativa {self.request.retries + 1})"
            )
            raise self.retry(countdown=task_config.retry_countdown, exc=e)

        return {"status": "error", "error": str(e)}


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
    symbol_start_time = time.time()  # Adicionar timing para processamento

    try:
        # Buscar RSI (usando async em context)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Usar análise de confluência em vez de RSI puro
        confluence_result = loop.run_until_complete(
            rsi_service.analyze_signal(symbol, rsi_timeframe, rsi_window, exchange)
        )

        if not confluence_result:
            return {"status": "no_data", "symbol": symbol, "exchange": exchange}

        # O analyze_signal já retorna ConfluenceResult com sinal (se houver)
        analysis = confluence_result

        # Log breve da moeda e confluência (apenas para sinais relevantes)

        if not analysis or not analysis.signal:
            rsi_value = analysis.signal.rsi_value if analysis and analysis.signal else 0
            return {
                "status": "neutral_zone",
                "symbol": symbol,
                "rsi_value": rsi_value,
                "confluence_score": analysis.confluence_score.total_score
                if analysis
                else 0,
            }

        # Obter configurações de filtro dos usuários ativos
        active_configs = get_active_monitoring_configs()
        user_filter_configs = []
        for config in active_configs:
            if config.filter_config:
                user_filter_configs.append(config.filter_config)

        # Aplicar filtros anti-spam com configurações personalizadas
        should_send = loop.run_until_complete(
            signal_filter.should_send_signal(symbol, analysis, user_filter_configs)
        )

        if should_send:
            # Agregar configurações de filtro
            from src.core.services.signal_filter import SignalFilter

            temp_filter = SignalFilter()
            aggregated_filter_config = temp_filter._get_user_filter_configs(
                user_filter_configs
            )

            # Marcar sinal como enviado com configurações personalizadas
            loop.run_until_complete(
                signal_filter.mark_signal_sent(
                    symbol, analysis, aggregated_filter_config
                )
            )

            # Salvar sinal no banco de dados
            try:
                db = SessionLocal()

                # Criar registro do sinal com dados de confluência
                signal_record = SignalHistory(
                    symbol=symbol,
                    signal_type=analysis.signal.signal_type.value,
                    strength=analysis.signal.strength.value,
                    price=float(
                        analysis.signal.rsi_value
                    ),  # Usar RSI como preço de referência
                    timeframe=rsi_timeframe,
                    source=exchange,
                    message=analysis.signal.message,  # Usar mensagem da confluência
                    indicator_type=["RSI", "EMA", "MACD", "Volume", "Confluence"],
                    indicator_data={
                        "confluence_score": {
                            "total_score": analysis.confluence_score.total_score,
                            "max_possible_score": analysis.confluence_score.max_possible_score,
                            "details": analysis.confluence_score.details,
                        },
                        "rsi_value": float(analysis.signal.rsi_value),
                        "recommendation": analysis.recommendation,
                        "risk_level": analysis.risk_level,
                    },
                    indicator_config={
                        "rsi_window": rsi_window,
                        "timeframe": rsi_timeframe,
                        "exchange": exchange,
                        "confluence_enabled": True,
                    },
                    volume_24h=None,  # Volume será calculado pelos indicadores de volume
                    price_change_24h=None,  # Não disponível no ConfluenceResult
                    confidence_score=None,  # Usar combined_score como alternativa
                    combined_score=float(analysis.confluence_score.total_score),
                    processed=False,  # Aguardando processamento pelo bot do Telegram
                    processing_time_ms=int((time.time() - symbol_start_time) * 1000),
                )

                db.add(signal_record)
                db.commit()
                db.refresh(signal_record)  # Atualizar objeto com ID
                signal_id = signal_record.id
                db.close()

                logger.info(
                    f"💾 SINAL SALVO NO BANCO: {symbol} | {analysis.signal.signal_type.value} | "
                    f"RSI: {float(analysis.signal.rsi_value):.2f} | Score: {analysis.confluence_score.total_score}/8 | ID: {signal_id}"
                )

            except Exception as db_error:
                logger.error(f"❌ Erro ao salvar sinal no banco: {db_error}")
                signal_id = None
                if "db" in locals():
                    db.rollback()
                    db.close()

            logger.info(
                f"📡 🚀 SINAL DETECTADO: {symbol} | {analysis.signal.signal_type.value} | "
                f"RSI: {float(analysis.signal.rsi_value):.2f} | Score: {analysis.confluence_score.total_score}/8"
            )

            return {
                "status": "signal_sent",
                "symbol": symbol,
                "signal_type": analysis.signal.signal_type.value,
                "rsi_value": float(analysis.signal.rsi_value),
                "confluence_score": analysis.confluence_score.total_score,
                "signal_id": signal_id,
            }

        else:
            return {
                "status": "filtered",
                "symbol": symbol,
                "rsi_value": float(analysis.signal.rsi_value),
                "confluence_score": analysis.confluence_score.total_score,
            }

    except Exception as e:
        logger.error(f"❌ Erro ao processar {symbol} na {exchange}: {e}")
        return {"status": "error", "symbol": symbol, "error": str(e)}

    finally:
        if "loop" in locals():
            loop.close()


def get_active_symbols() -> List[str]:
    """Agregar símbolos de TODAS as configurações ativas de usuários"""
    try:
        db = SessionLocal()
        # Buscar TODAS as configurações ativas
        active_configs = (
            db.query(UserMonitoringConfig)
            .filter(UserMonitoringConfig.active == True)  # noqa: E712
            .all()
        )

        if not active_configs:
            logger.warning("⚠️ Nenhuma configuração de usuário ativa encontrada")
            db.close()
            return []

        # Agregar símbolos únicos de todas as configurações ativas
        all_symbols = set()
        config_count = 0

        for config in active_configs:
            if config.symbols and len(config.symbols) > 0:
                all_symbols.update(config.symbols)
                config_count += 1

        symbols = list(all_symbols)

        logger.info(
            f"Encontrados {len(symbols)} símbolos únicos de {config_count} configurações ativas"
        )

        db.close()
        return symbols

    except Exception as e:
        logger.error(f"❌ Erro ao agregar símbolos das configurações: {e}")
        return []


def get_active_timeframes() -> List[str]:
    """Agregar timeframes únicos de TODAS as configurações ativas de usuários"""
    try:
        db = SessionLocal()
        # Buscar TODAS as configurações ativas
        active_configs = (
            db.query(UserMonitoringConfig)
            .filter(
                UserMonitoringConfig.active == True  # noqa: E712
            )
            .all()
        )

        if not active_configs:
            logger.warning("⚠️ Nenhuma configuração de usuário ativa para timeframes")
            db.close()
            return []

        # Agregar timeframes únicos de todas as configurações ativas
        all_timeframes = set()
        config_count = 0

        for config in active_configs:
            if config.timeframes and len(config.timeframes) > 0:
                all_timeframes.update(config.timeframes)
                config_count += 1
                logger.debug(
                    f"Config '{config.config_name}' (user {config.user_id}): {config.timeframes}"
                )

        timeframes = list(all_timeframes)

        if len(timeframes) == 0:
            logger.warning("⚠️ Nenhum timeframe encontrado nas configurações ativas")

        db.close()
        return timeframes

    except Exception as e:
        logger.error(f"❌ Erro ao agregar timeframes das configurações: {e}")
        return []


def get_active_monitoring_configs() -> List[UserMonitoringConfig]:
    """Obter TODAS as configurações de monitoramento ativas do banco"""
    try:
        db = SessionLocal()
        configs = (
            db.query(UserMonitoringConfig)
            .filter(
                UserMonitoringConfig.active == True  # noqa: E712
            )
            .all()
        )
        db.close()
        return configs
    except Exception as e:
        logger.error(f"❌ Erro ao obter configurações de monitoramento: {e}")
        return []


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
    *batch_results, cycle_start_time: float, total_symbols: int, total_exchanges: int
):
    """Task para finalizar logs do ciclo de monitoramento sequencial"""
    try:
        cycle_duration = time.time() - cycle_start_time

        # Calcular estatísticas totais dos batches
        total_successful = 0
        total_filtered = 0
        total_errors = 0
        total_no_data = 0

        for result in batch_results:
            if isinstance(result, dict):
                total_successful += result.get("successful", 0)
                total_filtered += result.get("filtered", 0)
                total_errors += result.get("errors", 0)
                total_no_data += result.get("no_data", 0)

        logger.info("-" * 60)
        logger.info("🏁 🏁 CICLO SEQUENCIAL CONCLUÍDO 🏁 🏁")
        logger.info(f"Total: {total_symbols} símbolos em {total_exchanges} exchanges")
        logger.info(f"Sinais: {total_successful} | Filtrados: {total_filtered}")
        logger.info(f"Erros: {total_errors} | Sem dados: {total_no_data}")
        logger.info(f"Duração total: {cycle_duration:.2f}s")
        logger.info("=" * 60)

        return {
            "status": "cycle_finalized",
            "total_duration": cycle_duration,
            "total_symbols": total_symbols,
            "total_exchanges": total_exchanges,
            "total_successful": total_successful,
            "total_filtered": total_filtered,
            "total_errors": total_errors,
            "total_no_data": total_no_data,
        }

    except Exception as e:
        logger.error(f"❌ Erro ao finalizar ciclo: {e}")
        return {"status": "error", "error": str(e)}


@celery_app.task
def schedule_next_monitoring(*args):
    """Task para agendar próxima execução do monitoramento"""
    try:
        # Agendar próxima execução em 1 minuto
        monitor_rsi_signals.apply_async(countdown=60)
        logger.info("Próxima execução agendada em 1 minuto")
        return {"status": "next_scheduled", "delay_seconds": 60}
    except Exception as e:
        logger.error(f"❌ Erro ao agendar próxima execução: {e}")
        return {"status": "error", "error": str(e)}
