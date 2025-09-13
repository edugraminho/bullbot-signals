#!/usr/bin/env python3
"""
Teste simples para validar o fluxo de atualização de exchanges das trading coins.

Execute com:
docker-compose exec app python test_trading_coins.py
"""

import asyncio
import sys
import os

# Adicionar o src ao path para importações
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.trading_coins import trading_coins
from src.utils.logger import get_logger
from src.utils.config import settings

logger = get_logger(__name__)


async def test_fetch_coin_exchanges():
    """Testa a busca de exchanges para uma moeda específica"""
    logger.info("=" * 50)
    logger.info("TESTE: Buscar exchanges para Bitcoin")
    logger.info("=" * 50)
    
    # Usar Bitcoin como exemplo (sempre disponível)
    bitcoin_id = "bitcoin"
    
    try:
        exchanges = await trading_coins.fetch_coin_exchanges(bitcoin_id)
        
        if exchanges is not None:
            logger.info(f"✅ Bitcoin encontrado em {len(exchanges)} exchanges:")
            for exchange in exchanges:
                logger.info(f"   - {exchange}")
            return True
        else:
            logger.error("❌ Falha ao buscar exchanges do Bitcoin")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erro no teste: {e}")
        return False


async def test_populate_sample_coins():
    """Popula o banco com algumas moedas de exemplo para teste"""
    logger.info("=" * 50)
    logger.info("TESTE: Popular banco com moedas de exemplo")
    logger.info("=" * 50)
    
    # Criar algumas moedas de exemplo para teste
    sample_coins = [
        {
            "ranking": 1,
            "coingecko_id": "bitcoin",
            "symbol": "BTC",
            "name": "Bitcoin",
            "market_cap": 2000000000000,
            "market_cap_rank": 1,
            "volume_24h": 30000000000,
            "current_price": 100000,
            "price_change_24h": 1000,
            "price_change_percentage_24h": 1.0,
            "category": settings.trading_coins_category,
            "image_url": "https://assets.coingecko.com/coins/images/1/large/bitcoin.png"
        },
        {
            "ranking": 2,
            "coingecko_id": "ethereum",
            "symbol": "ETH", 
            "name": "Ethereum",
            "market_cap": 500000000000,
            "market_cap_rank": 2,
            "volume_24h": 20000000000,
            "current_price": 4000,
            "price_change_24h": 100,
            "price_change_percentage_24h": 2.5,
            "category": settings.trading_coins_category,
            "image_url": "https://assets.coingecko.com/coins/images/279/large/ethereum.png"
        },
        {
            "ranking": 3,
            "coingecko_id": "solana",
            "symbol": "SOL",
            "name": "Solana", 
            "market_cap": 100000000000,
            "market_cap_rank": 5,
            "volume_24h": 5000000000,
            "current_price": 200,
            "price_change_24h": 10,
            "price_change_percentage_24h": 5.0,
            "category": settings.trading_coins_category,
            "image_url": "https://assets.coingecko.com/coins/images/4128/large/solana.png"
        }
    ]
    
    try:
        saved_count = trading_coins.save_to_database(sample_coins)
        
        if saved_count > 0:
            logger.info(f"✅ {saved_count} moedas de exemplo salvas no banco")
            return True
        else:
            logger.error("❌ Falha ao salvar moedas de exemplo")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erro ao popular banco: {e}")
        return False


async def test_update_exchanges_limited():
    """Testa atualização de exchanges para algumas moedas"""
    logger.info("=" * 50)
    logger.info("TESTE: Atualizar exchanges (limitado)")
    logger.info("=" * 50)
    
    try:
        # Buscar algumas moedas existentes no banco
        coins = trading_coins.load_from_database()
        if not coins:
            logger.warning("⚠️ Nenhuma moeda encontrada no banco")
            return False
        
        # Pegar só as 3 primeiras para teste
        test_coins = coins[:3]
        logger.info(f"Testando atualização para {len(test_coins)} moedas:")
        
        for coin in test_coins:
            logger.info(f"   - {coin.symbol} ({coin.coingecko_id})")
        
        # Forçar atualização dessas moedas
        updated_count = 0
        
        for coin in test_coins:
            exchanges = await trading_coins.fetch_coin_exchanges(coin.coingecko_id)
            
            if exchanges is not None:
                success = trading_coins.update_coin_exchanges(coin.coingecko_id, exchanges)
                if success:
                    updated_count += 1
                    logger.info(f"✅ {coin.symbol}: {len(exchanges)} exchanges atualizadas")
                else:
                    logger.error(f"❌ Falha ao atualizar {coin.symbol} no banco")
            else:
                logger.warning(f"⚠️ Sem dados de exchanges para {coin.symbol}")
            
            # Rate limiting para evitar sobrecarga da API
            await asyncio.sleep(settings.coingecko_rate_limit_seconds)
        
        logger.info(f"Resultado: {updated_count}/{len(test_coins)} moedas atualizadas")
        return updated_count > 0
        
    except Exception as e:
        logger.error(f"❌ Erro no teste de atualização: {e}")
        return False


def test_database_connection():
    """Testa conexão com banco e carregamento de moedas"""
    logger.info("=" * 50)
    logger.info("TESTE: Conexão com banco de dados")
    logger.info("=" * 50)
    
    try:
        coins = trading_coins.load_from_database()
        
        if coins:
            logger.info(f"✅ Banco conectado: {len(coins)} moedas carregadas")
            
            # Mostrar algumas moedas como exemplo
            for i, coin in enumerate(coins[:5]):
                exchanges_info = f"{len(coin.exchanges)} exchanges" if coin.exchanges else "sem exchanges"
                logger.info(f"   {i+1}. {coin.symbol} - {exchanges_info}")
            
            if len(coins) > 5:
                logger.info(f"   ... e mais {len(coins) - 5} moedas")
                
            return True
        else:
            logger.warning("⚠️ Banco conectado mas nenhuma moeda encontrada")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erro ao conectar com banco: {e}")
        return False


async def main():
    """Executa todos os testes"""
    logger.info("🚀 INICIANDO TESTES DE TRADING COINS")
    logger.info(f"Configurações:")
    logger.info(f"  - Categoria: {settings.trading_coins_category}")
    logger.info(f"  - Min Market Cap: ${settings.trading_coins_min_market_cap:,}")
    logger.info(f"  - Min Volume: ${settings.trading_coins_min_volume:,}")
    logger.info(f"  - Rate Limit: {settings.coingecko_rate_limit_seconds}s")
    
    tests_passed = 0
    total_tests = 4
    
    # Teste 1: Conexão com banco (pode estar vazio)
    test_database_connection()  # Não conta para aprovação
    
    # Teste 2: Popular banco com moedas de exemplo
    if await test_populate_sample_coins():
        tests_passed += 1
    
    # Teste 3: Buscar exchanges para Bitcoin
    if await test_fetch_coin_exchanges():
        tests_passed += 1
    
    # Teste 4: Atualizar exchanges limitado
    if await test_update_exchanges_limited():
        tests_passed += 1
        
    # Teste 5: Verificar se banco foi populado corretamente
    if test_database_connection():
        tests_passed += 1
    
    # Resultado final
    logger.info("=" * 50)
    logger.info("RESULTADO DOS TESTES")
    logger.info("=" * 50)
    logger.info(f"Testes executados: {total_tests}")
    logger.info(f"Testes aprovados: {tests_passed}")
    logger.info(f"Taxa de sucesso: {(tests_passed/total_tests)*100:.1f}%")
    
    if tests_passed == total_tests:
        logger.info("🎉 Todos os testes passaram! Sistema funcionando corretamente.")
        return 0
    else:
        logger.error("❌ Alguns testes falharam. Verifique os logs acima.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)