#!/usr/bin/env python3
"""
Script principal simplificado do Crypto Hunter.
"""

import asyncio
import logging
import sys
import os

# Adiciona o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.exchanges import ExchangeManager
from core.data_collector import DataCollector, DataCollectionConfig

# Configuração básica de logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    """Função principal simplificada."""
    logger.info("Iniciando Crypto Hunter...")

    # Configura Gate.io
    exchange_manager = ExchangeManager()
    exchange_manager.add_exchange(
        "gateio", {"api_key": None, "api_secret": None, "rate_limit": 100}
    )

    # Configura coletor de dados
    config = DataCollectionConfig(
        symbols=["BTC_USDT", "ETH_USDT"],
        timeframes=["1h", "4h"],
        rsi_periods=[14, 21],
        collection_interval=60,
        max_data_points=500,
    )

    data_collector = DataCollector(exchange_manager)
    data_collector.configure(config)

    # Testa conexão
    connections = await exchange_manager.test_all_connections()
    if connections.get("gateio"):
        logger.info("Gate.io conectada")
    else:
        logger.error("Falha na conexão com Gate.io")
        return

    # Coleta dados uma vez
    await data_collector._collect_all_data()

    # Mostra resultados
    summary = data_collector.get_data_summary()
    logger.info(f"Coletados dados para {summary['total_symbols']} símbolos")

    # Mostra sinais RSI
    rsi_signals = data_collector.get_all_rsi_signals("gateio")
    logger.info(f"Encontrados {len(rsi_signals)} sinais RSI")

    logger.info("Crypto Hunter concluído!")


if __name__ == "__main__":
    asyncio.run(main())
