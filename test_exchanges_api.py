#!/usr/bin/env python3
"""
Teste direto da API CoinGecko para buscar exchanges
"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.trading_coins import trading_coins
from src.utils.logger import get_logger

logger = get_logger(__name__)

async def test_exchanges_api():
    """Testa busca de exchanges na API CoinGecko"""

    test_coins = ["bitcoin", "ethereum", "solana"]

    logger.info("🧪 Testando busca de exchanges na API CoinGecko...")
    logger.info("-" * 50)

    for coin_id in test_coins:
        try:
            logger.info(f"🔍 Buscando exchanges para {coin_id}...")

            exchanges = await trading_coins.fetch_coin_exchanges(coin_id)

            if exchanges is not None:
                logger.info(f"✅ {coin_id}: {len(exchanges)} exchanges encontradas")

                # Mostrar as primeiras 10 exchanges
                for i, exchange in enumerate(exchanges[:10]):
                    logger.info(f"   {i+1:2d}. {exchange}")

                if len(exchanges) > 10:
                    logger.info(f"   ... e mais {len(exchanges) - 10} exchanges")

                # Verificar se tem as exchanges que o sistema usa
                our_exchanges = ["binance", "mexc", "gate"]
                found_exchanges = [ex for ex in our_exchanges if ex in exchanges]

                if found_exchanges:
                    logger.info(f"🎯 Exchanges do nosso sistema: {', '.join(found_exchanges)}")
                else:
                    logger.warning(f"⚠️ Nenhuma das nossas exchanges encontrada para {coin_id}")

            else:
                logger.error(f"❌ Falha ao buscar exchanges para {coin_id}")

            logger.info("-" * 30)

            # Rate limiting
            await asyncio.sleep(2)

        except Exception as e:
            logger.error(f"❌ Erro ao testar {coin_id}: {e}")

if __name__ == "__main__":
    asyncio.run(test_exchanges_api())