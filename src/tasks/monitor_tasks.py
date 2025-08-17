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
from src.database.models import UserMonitoringConfig, SignalHistory
from src.tasks.celery_app import celery_app
from src.utils.config import settings
from src.utils.logger import get_logger
from src.utils.trading_coins import trading_coins

logger = get_logger(__name__, level="DEBUG")


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

        # Distribuir símbolos por exchange para rate limiting
        symbol_batches = distribute_symbols_by_exchange(symbols)

        # Criar chain sequencial de tasks
        from celery import chord

        # Filtrar exchanges com símbolos
        exchanges_with_symbols = {
            exchange: batch_symbols
            for exchange, batch_symbols in symbol_batches.items()
            if batch_symbols
        }

        if not exchanges_with_symbols:
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
                logger.info(
                    f"RSI agregado: oversold≤{min_oversold}, overbought≥{max_overbought}"
                )
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

        logger.info(
            f"Processando {len(symbols)} símbolos × {len(active_timeframes)} timeframes = {total_combinations} combinações"
        )

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
        logger.info(
            f"{len(symbols)} símbolos × {len(active_timeframes)} timeframes = {total_combinations} combinações"
        )
        logger.info("-" * 40)

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
            f"{symbol}: RSI {rsi_data.value:.2f} | Preço ${rsi_data.current_price}"
        )

        if not analysis:
            logger.debug(f"{symbol}: Zona neutra (RSI: {rsi_data.value:.2f})")
            return {
                "status": "neutral_zone",
                "symbol": symbol,
                "rsi_value": rsi_data.value,
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

                # Criar registro do sinal
                signal_record = SignalHistory(
                    symbol=symbol,
                    signal_type=analysis.signal.signal_type.value,
                    strength=analysis.signal.strength.value,
                    price=float(rsi_data.current_price),
                    timeframe=rsi_timeframe,
                    source=exchange,
                    message=f"RSI {float(rsi_data.value):.2f} - {analysis.signal.signal_type.value} signal",
                    indicator_type=["RSI"],
                    indicator_data={
                        "rsi_value": float(rsi_data.value),
                        "rsi_window": rsi_window,
                        "oversold_level": float(rsi_service.rsi_levels.oversold),
                        "overbought_level": float(rsi_service.rsi_levels.overbought),
                    },
                    indicator_config={
                        "rsi_window": rsi_window,
                        "timeframe": rsi_timeframe,
                        "exchange": exchange,
                    },
                    volume_24h=float(rsi_data.volume_24h)
                    if hasattr(rsi_data, "volume_24h")
                    and rsi_data.volume_24h is not None
                    else None,
                    price_change_24h=float(rsi_data.price_change_24h)
                    if hasattr(rsi_data, "price_change_24h")
                    and rsi_data.price_change_24h is not None
                    else None,
                    confidence_score=float(analysis.confidence_score)
                    if hasattr(analysis, "confidence_score")
                    and analysis.confidence_score is not None
                    else None,
                    combined_score=float(analysis.combined_score)
                    if hasattr(analysis, "combined_score")
                    and analysis.combined_score is not None
                    else None,
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
                    f"RSI: {float(rsi_data.value):.2f} | ID: {signal_id}"
                )

            except Exception as db_error:
                logger.error(f"❌ Erro ao salvar sinal no banco: {db_error}")
                signal_id = None
                if "db" in locals():
                    db.rollback()
                    db.close()

            logger.info(
                f"📡 🚀 SINAL DETECTADO: {symbol} | {analysis.signal.signal_type.value} | "
                f"RSI: {float(rsi_data.value):.2f}"
            )

            return {
                "status": "signal_sent",
                "symbol": symbol,
                "signal_type": analysis.signal.signal_type.value,
                "rsi_value": float(rsi_data.value),
                "signal_id": signal_id,
            }

        else:
            logger.debug(f"{symbol}: Sinal filtrado (RSI: {rsi_data.value:.2f})")
            return {"status": "filtered", "symbol": symbol, "rsi_value": rsi_data.value}

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
        # Buscar TODAS as configurações ativas (não apenas a primeira)
        active_configs = (
            db.query(UserMonitoringConfig)
            .filter(
                UserMonitoringConfig.active == True  # noqa: E712
            )
            .all()
        )

        if not active_configs:
            logger.warning("⚠️ Nenhuma configuração de usuário ativa encontrada")
            db.close()
            # Fallback para lista padrão apenas se não há configurações
            fallback_symbols = trading_coins.get_trading_symbols(
                limit=settings.trading_coins_max_limit
            )
            logger.info(
                f"Usando {len(fallback_symbols)} símbolos do fallback (trading coins)"
            )
            return fallback_symbols

        # Agregar símbolos únicos de todas as configurações ativas
        all_symbols = set()
        config_count = 0

        for config in active_configs:
            if config.symbols and len(config.symbols) > 0:
                all_symbols.update(config.symbols)
                config_count += 1
                logger.debug(
                    f"Config '{config.config_name}' (user {config.user_id}): {len(config.symbols)} símbolos"
                )

        symbols = list(all_symbols)
        logger.info(
            f"Agregados {len(symbols)} símbolos únicos de {config_count} configurações ativas"
        )

        if len(symbols) == 0:
            logger.warning("⚠️ Nenhum símbolo encontrado nas configurações ativas")

        db.close()
        return symbols

    except Exception as e:
        logger.error(f"❌ Erro ao agregar símbolos das configurações: {e}")
        # Fallback para lista padrão em caso de erro
        fallback_symbols = task_config.default_symbols
        logger.info(f"Usando {len(fallback_symbols)} símbolos do fallback padrão")
        return fallback_symbols


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
            # Fallback para timeframes padrão
            default_timeframes = ["15m", "1h", "4h"]
            logger.info(f"Usando timeframes padrão: {default_timeframes}")
            return default_timeframes

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
        logger.info(
            f"Agregados {len(timeframes)} timeframes únicos de {config_count} configurações: {timeframes}"
        )

        if len(timeframes) == 0:
            logger.warning("⚠️ Nenhum timeframe encontrado nas configurações ativas")
            timeframes = ["15m", "1h", "4h"]  # fallback

        db.close()
        return timeframes

    except Exception as e:
        logger.error(f"❌ Erro ao agregar timeframes das configurações: {e}")
        # Fallback para timeframes padrão
        return ["15m", "1h", "4h"]


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
