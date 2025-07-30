#!/usr/bin/env python3
"""
Script de teste para verificar integração com Polygon.io
"""

import asyncio
import sys
import os
from decimal import Decimal

# Adicionar src ao path
sys.path.insert(0, "src")

from src.adapters.polygon_client import get_crypto_rsi, PolygonError
from src.core.services.rsi_service import RSIService
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def test_basic_connection():
    """Teste básico de conexão"""
    print("🔍 Testando conexão básica com Polygon.io...")

    api_key = os.getenv("POLYGON_API_KEY")
    if not api_key:
        print("❌ POLYGON_API_KEY não encontrada no ambiente")
        print("💡 Configure: export POLYGON_API_KEY='sua_chave_aqui'")
        return False

    try:
        # Teste com Bitcoin
        rsi_data = await get_crypto_rsi(api_key, "BTCUSD")

        if rsi_data:
            print(f"✅ Conexão OK!")
            print(f"📊 BTC RSI: {rsi_data.value}")
            print(f"🕐 Timestamp: {rsi_data.timestamp}")
            print(f"⏱️ Timespan: {rsi_data.timespan}")
            return True
        else:
            print("❌ Nenhum dado retornado")
            return False

    except PolygonError as e:
        print(f"❌ Erro da Polygon.io: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False


async def test_multiple_cryptos():
    """Teste com múltiplas cryptos"""
    print("\n🔍 Testando múltiplas criptomoedas...")

    api_key = os.getenv("POLYGON_API_KEY")
    if not api_key:
        return False

    try:
        service = RSIService(api_key)
        symbols = ["BTCUSD", "ETHUSD", "SOLUSD"]

        results = await service.get_multiple_rsi(symbols)

        print(f"📈 Resultados para {len(symbols)} cryptos:")
        for symbol, rsi_data in results.items():
            if rsi_data:
                print(f"  ✅ {symbol}: RSI {rsi_data.value}")
            else:
                print(f"  ❌ {symbol}: Dados indisponíveis")

        return True

    except Exception as e:
        print(f"❌ Erro no teste múltiplo: {e}")
        return False


async def test_trading_signals():
    """Teste de geração de sinais"""
    print("\n🔍 Testando geração de sinais de trading...")

    api_key = os.getenv("POLYGON_API_KEY")
    if not api_key:
        return False

    try:
        service = RSIService(api_key)
        symbols = ["BTCUSD", "ETHUSD"]

        analyses = await service.get_trading_signals(symbols)

        print(f"🎯 {len(analyses)} sinais gerados:")
        for analysis in analyses:
            signal = analysis.signal
            print(f"  📊 {signal.symbol}:")
            print(f"    🚦 Sinal: {signal.signal_type.value}")
            print(f"    💪 Força: {signal.strength.value}")
            print(f"    📈 RSI: {signal.rsi_value}")
            print(f"    💬 {signal.message}")
            print()

        return True

    except Exception as e:
        print(f"❌ Erro no teste de sinais: {e}")
        return False


async def main():
    """Executa todos os testes"""
    print("🤖 Crypto Hunter - Teste de Integração Polygon.io")
    print("=" * 50)

    tests = [test_basic_connection, test_multiple_cryptos, test_trading_signals]

    passed = 0
    for test in tests:
        if await test():
            passed += 1
        else:
            break

    print("\n" + "=" * 50)
    print(f"🏁 Resultado: {passed}/{len(tests)} testes passaram")

    if passed == len(tests):
        print("🎉 Todos os testes passaram! Integração funcionando.")
        print("\n💡 Próximos passos:")
        print("  1. Configure sua API key: cp env.example .env")
        print("  2. Execute a API: python src/api/main.py")
        print("  3. Acesse: http://localhost:8000/docs")
    else:
        print("😞 Alguns testes falharam. Verifique a configuração.")
        return 1

    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️ Teste cancelado pelo usuário")
        sys.exit(1)
