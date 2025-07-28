"""
Aplicação principal FastAPI do Crypto Hunter.

Fornece API REST para coleta de dados, indicadores
e sinais de trading em tempo real.
"""

import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from core.exchanges import ExchangeManager, ExchangeFactory
from core.data_collector import DataCollector, DataCollectionConfig
from core.cache import CacheManager, CacheConfig
from config.config import config

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Variáveis globais
exchange_manager = None
data_collector = None
cache_manager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação."""
    global exchange_manager, data_collector, cache_manager

    # Inicialização
    logger.info("Iniciando aplicação...")

    # Inicializa cache
    cache_config = CacheConfig()
    cache_manager = CacheManager(cache_config)

    # Inicializa exchange manager
    exchange_manager = ExchangeManager()
    exchange_factory = ExchangeFactory()

    # Adiciona exchanges da configuração
    for exchange_name, exchange_config in config.exchanges.items():
        exchange_config_dict = {
            "api_key": exchange_config.api_key,
            "api_secret": exchange_config.api_secret,
            "rate_limit": exchange_config.rate_limit,
        }
        exchange = exchange_factory.create_exchange(exchange_name, exchange_config_dict)
        if exchange:
            exchange_manager.add_exchange_instance(exchange_name, exchange)

    # Inicializa data collector
    data_collector = DataCollector(exchange_manager)

    # Configura data collector
    collection_config = DataCollectionConfig(
        symbols=config.exchanges["gateio"].symbols,
        timeframes=config.global_config.timeframes,
        rsi_periods=config.global_config.rsi_periods,
        collection_interval=config.global_config.collection_interval,
        max_data_points=config.global_config.max_data_points,
    )
    data_collector.configure(collection_config)

    # Coleta dados iniciais
    logger.info("Coletando dados iniciais...")
    try:
        await data_collector._collect_all_data()
        logger.info("Dados iniciais coletados com sucesso")
    except Exception as e:
        logger.error(f"Erro na coleta inicial de dados: {e}")

    logger.info("Aplicação iniciada com sucesso")

    yield

    # Cleanup
    logger.info("Encerrando aplicação...")


# Cria aplicação FastAPI
app = FastAPI(
    title="Crypto Hunter API",
    description="API para coleta de dados e sinais de trading",
    version="1.0.0",
    lifespan=lifespan,
)

# Configura CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Endpoint raiz."""
    return {"message": "Crypto Hunter API", "version": "1.0.0", "status": "running"}


@app.get("/health")
async def health_check():
    """Verifica saúde da aplicação."""
    try:
        # Verifica cache
        cache_healthy = cache_manager.health_check()

        # Verifica exchanges
        exchange_status = await data_collector.test_exchange_connections()

        return {
            "status": "healthy",
            "cache": "connected" if cache_healthy else "disconnected",
            "exchanges": exchange_status,
            "timestamp": "2024-01-01T00:00:00Z",
        }
    except Exception as e:
        logger.error(f"Health check falhou: {e}")
        raise HTTPException(status_code=500, detail="Service unhealthy")


@app.get("/exchanges")
async def list_exchanges():
    """Lista exchanges disponíveis."""
    try:
        exchanges = list(exchange_manager.get_all_exchanges().keys())
        return {"exchanges": exchanges, "total": len(exchanges)}
    except Exception as e:
        logger.error(f"Erro ao listar exchanges: {e}")
        raise HTTPException(status_code=500, detail="Erro interno")


@app.get("/symbols")
async def list_symbols():
    """Lista símbolos disponíveis."""
    try:
        symbols = {}
        for exchange_name in exchange_manager.get_all_exchanges().keys():
            symbols[exchange_name] = data_collector.get_available_symbols(exchange_name)

        return {"symbols": symbols, "total_exchanges": len(symbols)}
    except Exception as e:
        logger.error(f"Erro ao listar símbolos: {e}")
        raise HTTPException(status_code=500, detail="Erro interno")


@app.get("/rsi/{symbol}")
async def get_rsi_signals(symbol: str):
    """Obtém sinais RSI para um símbolo específico."""
    try:
        rsi_signals = data_collector.get_all_rsi_signals("gateio")

        # Filtra pelo símbolo (rsi_signals é um dicionário)
        symbol_signals = []
        for key, signal in rsi_signals.items():
            if symbol in key:
                symbol_signals.append(
                    {
                        "key": key,
                        "value": signal.value,
                        "signal": signal.signal.value,
                        "strength": signal.strength,
                        "timestamp": signal.timestamp.isoformat()
                        if signal.timestamp
                        else None,
                    }
                )

        return {
            "symbol": symbol,
            "signals": symbol_signals,
            "total": len(symbol_signals),
        }
    except Exception as e:
        logger.error(f"Erro ao obter sinais RSI para {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno")


@app.get("/signals")
async def get_all_signals():
    """Obtém todos os sinais RSI."""
    try:
        rsi_signals = data_collector.get_all_rsi_signals("gateio")

        # Converte para formato serializável
        signals_list = []
        overbought_count = 0
        oversold_count = 0

        for key, signal in rsi_signals.items():
            signal_data = {
                "key": key,
                "value": signal.value,
                "signal": signal.signal.value,
                "strength": signal.strength,
                "timestamp": signal.timestamp.isoformat() if signal.timestamp else None,
            }
            signals_list.append(signal_data)

            if signal.signal.value == "overbought":
                overbought_count += 1
            elif signal.signal.value == "oversold":
                oversold_count += 1

        return {
            "signals": signals_list,
            "total": len(signals_list),
            "overbought": overbought_count,
            "oversold": oversold_count,
        }
    except Exception as e:
        logger.error(f"Erro ao obter sinais: {e}")
        raise HTTPException(status_code=500, detail="Erro interno")


@app.get("/cache/stats")
async def get_cache_stats():
    """Obtém estatísticas do cache."""
    try:
        stats = cache_manager.cache.get_stats()
        return {"cache_stats": stats, "health": cache_manager.health_check()}
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas do cache: {e}")
        raise HTTPException(status_code=500, detail="Erro interno")


@app.post("/cache/clear")
async def clear_cache():
    """Limpa todo o cache."""
    try:
        success = cache_manager.cache.clear()
        return {
            "success": success,
            "message": "Cache limpo com sucesso" if success else "Erro ao limpar cache",
        }
    except Exception as e:
        logger.error(f"Erro ao limpar cache: {e}")
        raise HTTPException(status_code=500, detail="Erro interno")


@app.get("/data/summary")
async def get_data_summary():
    """Obtém resumo dos dados coletados."""
    try:
        summary = data_collector.get_data_summary()
        return summary
    except Exception as e:
        logger.error(f"Erro ao obter resumo de dados: {e}")
        raise HTTPException(status_code=500, detail="Erro interno")


@app.get("/config")
async def get_config():
    """Obtém configuração atual (sem dados sensíveis)."""
    try:
        return {
            "exchanges": list(config.exchanges.keys()),
            "symbols": config.exchanges["gateio"].symbols,
            "timeframes": config.global_config.timeframes,
            "rsi_periods": config.global_config.rsi_periods,
            "collection_interval": config.global_config.collection_interval,
            "notifications_enabled": config.notifications.enabled,
        }
    except Exception as e:
        logger.error(f"Erro ao obter configuração: {e}")
        raise HTTPException(status_code=500, detail="Erro interno")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
