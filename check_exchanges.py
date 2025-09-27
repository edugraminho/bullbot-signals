#!/usr/bin/env python3
"""
Script para verificar se as exchanges estão sendo populadas corretamente
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.trading_coins import trading_coins
from src.utils.logger import get_logger

logger = get_logger(__name__)

def check_exchanges_status():
    """Verifica status das exchanges nas moedas do banco"""
    try:
        coins = trading_coins.load_from_database()

        if not coins:
            logger.info("❌ Nenhuma moeda encontrada no banco")
            return

        total_coins = len(coins)
        with_exchanges = 0
        without_exchanges = 0

        logger.info(f"Verificando exchanges em {total_coins} moedas...")
        logger.info("-" * 50)

        for coin in coins[:10]:  # Mostrar apenas 10 primeiras
            if coin.exchanges and len(coin.exchanges) > 0:
                with_exchanges += 1
                exchanges_str = ", ".join(coin.exchanges)
                logger.info(f"✅ {coin.symbol:6} - {len(coin.exchanges)} exchanges: {exchanges_str}")
            else:
                without_exchanges += 1
                logger.info(f"❌ {coin.symbol:6} - SEM EXCHANGES")

        if total_coins > 10:
            # Contar o restante
            for coin in coins[10:]:
                if coin.exchanges and len(coin.exchanges) > 0:
                    with_exchanges += 1
                else:
                    without_exchanges += 1
            logger.info(f"... (verificadas mais {total_coins - 10} moedas)")

        logger.info("-" * 50)
        logger.info(f"RESUMO:")
        logger.info(f"  Total de moedas: {total_coins}")
        logger.info(f"  Com exchanges: {with_exchanges}")
        logger.info(f"  Sem exchanges: {without_exchanges}")
        logger.info(f"  Percentual com exchanges: {(with_exchanges/total_coins)*100:.1f}%")

        if without_exchanges > 0:
            logger.info(f"\n⚠️ AÇÃO NECESSÁRIA: Execute a task de atualização de exchanges:")
            logger.info("   docker-compose exec app python -c \"from src.tasks.monitor_tasks import update_trading_coins_exchanges; update_trading_coins_exchanges()\"")

    except Exception as e:
        logger.error(f"❌ Erro ao verificar exchanges: {e}")

if __name__ == "__main__":
    check_exchanges_status()