#!/usr/bin/env python3
"""
Teste de integração para a API do Gate.io.

Este teste verifica se as credenciais estão configuradas corretamente
e testa a conectividade com a API.
"""

import asyncio
import os
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.exchanges.gateio import GateIOAdapter
from config.config import config
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_gateio_connection():
    """Testa a conexão com a API do Gate.io."""

    print("🔍 Testando conexão com a API do Gate.io...")
    print("=" * 50)

    # Verificar se as credenciais estão configuradas
    api_key = os.getenv("GATEIO_API_KEY")
    api_secret = os.getenv("GATEIO_API_SECRET")

    if not api_key or not api_secret:
        print("❌ ERRO: Credenciais da API não encontradas!")
        print("Configure as variáveis de ambiente:")
        print("  GATEIO_API_KEY=sua_api_key")
        print("  GATEIO_API_SECRET=sua_api_secret")
        print("\nOu crie um arquivo .env na raiz do projeto.")
        return False

    print(f"✅ API Key configurada: {api_key[:8]}...")
    print(f"✅ API Secret configurada: {api_secret[:8]}...")

    try:
        # Criar adapter
        exchange_config = config.exchanges["gateio"]
        adapter = GateIOAdapter(exchange_config.__dict__)

        # Testar conexão básica
        print("\n🔄 Testando conectividade...")
        connection_ok = await adapter.test_connection()

        if not connection_ok:
            print("❌ Falha na conexão com a API")
            return False

        print("✅ Conexão estabelecida com sucesso!")

        # Testar busca de símbolos
        print("\n🔄 Testando busca de símbolos...")
        symbols = await adapter.get_symbols()

        if symbols:
            print(f"✅ Encontrados {len(symbols)} símbolos")
            print("Primeiros 5 símbolos:")
            for i, symbol in enumerate(symbols[:5]):
                print(
                    f"  {i + 1}. {symbol.symbol} ({symbol.base_asset}/{symbol.quote_asset})"
                )
        else:
            print("⚠️  Nenhum símbolo encontrado")

        # Testar busca de dados OHLCV
        print("\n🔄 Testando busca de dados OHLCV...")
        test_symbol = "BTC_USDT"
        ohlcv_data = await adapter.get_ohlcv(test_symbol, "1h", limit=10)

        if ohlcv_data:
            print(f"✅ Obtidos {len(ohlcv_data)} candles para {test_symbol}")
            latest = ohlcv_data[0]
            print(f"Último candle: {latest.timestamp} - Close: {latest.close}")
        else:
            print(f"⚠️  Nenhum dado OHLCV encontrado para {test_symbol}")

        # Testar busca de ticker
        print("\n🔄 Testando busca de ticker...")
        ticker = await adapter.get_ticker(test_symbol)

        if ticker:
            print(f"✅ Ticker obtido para {test_symbol}")
            print(f"Preço atual: {ticker.get('last_price', 'N/A')}")
            print(f"Volume 24h: {ticker.get('volume_24h', 'N/A')}")
        else:
            print(f"⚠️  Ticker não encontrado para {test_symbol}")

        print("\n" + "=" * 50)
        print("🎉 Todos os testes passaram! A API está funcionando corretamente.")
        return True

    except Exception as e:
        print(f"❌ ERRO durante os testes: {e}")
        logger.error(f"Erro detalhado: {e}", exc_info=True)
        return False


async def test_public_endpoints():
    """Testa endpoints públicos da API (sem credenciais)."""

    print("\n🔍 Testando endpoints públicos...")
    print("=" * 30)

    try:
        import gate_api

        # Configuração para endpoints públicos
        configuration = gate_api.Configuration(host="https://api.gateio.ws/api/v4")
        spot_api = gate_api.SpotApi(gate_api.ApiClient(configuration))

        # Testar lista de pares de moedas
        print("🔄 Testando lista de pares de moedas...")
        pairs = spot_api.list_currency_pairs()
        print(f"✅ Encontrados {len(pairs)} pares de moedas")

        # Testar tickers
        print("🔄 Testando tickers...")
        tickers = spot_api.list_tickers()
        print(f"✅ Encontrados {len(tickers)} tickers")

        # Testar candlesticks
        print("🔄 Testando candlesticks...")
        candles = spot_api.list_candlesticks(currency_pair="BTC_USDT", interval="1h")
        print(f"✅ Encontrados {len(candles)} candles para BTC_USDT")

        print("✅ Endpoints públicos funcionando corretamente!")
        return True

    except Exception as e:
        print(f"❌ ERRO nos endpoints públicos: {e}")
        return False


def main():
    """Função principal."""

    print("🚀 Crypto Hunter - Teste de Conexão Gate.io")
    print("=" * 50)

    # Testar endpoints públicos primeiro
    public_ok = asyncio.run(test_public_endpoints())

    if not public_ok:
        print(
            "❌ Problemas com endpoints públicos. Verifique sua conexão com a internet."
        )
        return

    # Testar conexão com credenciais
    connection_ok = asyncio.run(test_gateio_connection())

    if connection_ok:
        print("\n🎯 Resumo:")
        print("✅ Endpoints públicos: OK")
        print("✅ Conexão autenticada: OK")
        print("✅ API Gate.io configurada corretamente!")
    else:
        print("\n❌ Resumo:")
        print("✅ Endpoints públicos: OK")
        print("❌ Conexão autenticada: FALHOU")
        print("❌ Verifique suas credenciais da API")


if __name__ == "__main__":
    main()
