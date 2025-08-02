#!/usr/bin/env python3
"""
Script para atualizar a lista curada de moedas para trading
"""

import asyncio
import sys
import os

# Configurar path antes dos imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_path = os.path.join(project_root, "src")

# Verificar se estamos no container Docker (/app) ou local
if os.path.exists("/app"):
    src_path = "/app/src"
else:
    src_path = os.path.join(project_root, "src")

# Adicionar ao path se não estiver
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Adicionar também o diretório atual (para container Docker)
current_working_dir = os.getcwd()
if current_working_dir not in sys.path:
    sys.path.insert(0, current_working_dir)

# Agora fazer os imports
from src.utils.coin_curator import coin_curator
from src.utils.logger import get_logger
from src.utils.config import settings

logger = get_logger(__name__)


async def main():
    """Função principal"""
    try:
        logger.info("Iniciando atualização da lista curada de moedas...")

        # Atualizar lista
        coins = await coin_curator.update_curated_list()

        if coins:
            logger.info(f"Sucesso! Lista atualizada com {len(coins)} moedas")

            # Mostrar top 10
            logger.info("Top 10 moedas:")
            for i, coin in enumerate(coins[:10], 1):
                logger.info(
                    f"  {i:2d}. {coin.symbol:6s} - {coin.name:20s} - MC: ${coin.market_cap / 1e9:.1f}B"
                )

            # Estatísticas
            total_market_cap = sum(coin.market_cap for coin in coins)
            total_volume = sum(coin.volume_24h for coin in coins)

            # Volume baseado no período configurado
            volume_period = settings.coin_curator_volume_period
            volume_field = (
                f"volume_{volume_period.replace('d', 'd')}"
                if volume_period != "24h"
                else "volume_24h"
            )
            if hasattr(coins[0], volume_field):
                total_volume_period = sum(getattr(coin, volume_field) for coin in coins)
                volume_label = f"Volume {volume_period}"
            else:
                total_volume_period = total_volume
                volume_label = "Volume 24h"

            logger.info(f"Estatísticas:")
            logger.info(f"  Total Market Cap: ${total_market_cap / 1e12:.2f}T")
            logger.info(f"  {volume_label}: ${total_volume_period / 1e9:.2f}B")
            logger.info(
                f"  Média Market Cap: ${total_market_cap / len(coins) / 1e9:.2f}B"
            )

        else:
            logger.error("Falha ao atualizar lista")
            sys.exit(1)

    except Exception as e:
        logger.error(f"❌ Erro inesperado: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
