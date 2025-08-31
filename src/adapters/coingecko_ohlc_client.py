"""
Cliente CoinGecko para dados OHLC centralizados
"""

import asyncio
import aiohttp
from typing import List, Optional, Dict
from datetime import datetime
from src.utils.logger import get_logger

logger = get_logger(__name__)


class CoinGeckoOHLCClient:
    """Cliente para dados OHLC da CoinGecko"""

    def __init__(self):
        self.base_url = "https://api.coingecko.com/api/v3"
        self.rate_limit_delay = 6  # 6 segundos entre chamadas para API pública

    async def get_ohlc_data(
        self, coin_id: str, vs_currency: str = "usd", days: str = "1"
    ) -> Optional[List[List[float]]]:
        """
        Busca dados OHLC para uma moeda específica

        Args:
            coin_id: ID da moeda na CoinGecko (ex: "bitcoin")
            vs_currency: Moeda de referência (padrão: "usd")
            days: Período em dias ("1", "7", "14", "30", "90", "180", "365")

        Returns:
            Lista de arrays [timestamp, open, high, low, close] ou None se erro
        """
        try:
            url = f"{self.base_url}/coins/{coin_id}/ohlc"
            params = {"vs_currency": vs_currency, "days": days}

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.debug(f"OHLC obtido para {coin_id}: {len(data)} pontos")
                        return data
                    elif response.status == 429:
                        logger.warning(f"Rate limit atingido para {coin_id}")
                        await asyncio.sleep(self.rate_limit_delay * 2)
                        return None
                    else:
                        logger.error(
                            f"❌ Erro na API CoinGecko OHLC para {coin_id}: {response.status}"
                        )
                        return None

        except Exception as e:
            logger.error(f"❌ Erro ao buscar OHLC para {coin_id}: {e}")
            return None

    async def get_multiple_ohlc_data(
        self, coin_ids: List[str], vs_currency: str = "usd", days: str = "1"
    ) -> Dict[str, Optional[List[List[float]]]]:
        """
        Busca dados OHLC para múltiplas moedas com controle de rate limit

        Args:
            coin_ids: Lista de IDs das moedas
            vs_currency: Moeda de referência
            days: Período em dias

        Returns:
            Dict com coin_id como chave e dados OHLC como valor
        """
        results = {}

        for coin_id in coin_ids:
            results[coin_id] = await self.get_ohlc_data(coin_id, vs_currency, days)

            # Rate limiting - aguardar entre chamadas
            if len(coin_ids) > 1:
                await asyncio.sleep(self.rate_limit_delay)

        return results

    def convert_ohlc_to_candles(self, ohlc_data: List[List[float]]) -> List[Dict]:
        """
        Converte dados OHLC para formato de candles mais amigável

        Args:
            ohlc_data: Dados brutos OHLC da API

        Returns:
            Lista de dicionários com campos nomeados
        """
        candles = []

        for candle in ohlc_data:
            if len(candle) >= 5:
                candles.append(
                    {
                        "timestamp": int(candle[0]),
                        "datetime": datetime.fromtimestamp(
                            candle[0] / 1000
                        ).isoformat(),
                        "open": float(candle[1]),
                        "high": float(candle[2]),
                        "low": float(candle[3]),
                        "close": float(candle[4]),
                    }
                )

        return candles

    async def get_latest_price(
        self, coin_id: str, vs_currency: str = "usd"
    ) -> Optional[float]:
        """
        Busca preço atual de uma moeda (último close do OHLC)

        Args:
            coin_id: ID da moeda na CoinGecko
            vs_currency: Moeda de referência

        Returns:
            Preço atual ou None se erro
        """
        try:
            ohlc_data = await self.get_ohlc_data(coin_id, vs_currency, "1")

            if ohlc_data and len(ohlc_data) > 0:
                latest_candle = ohlc_data[-1]
                if len(latest_candle) >= 5:
                    return float(latest_candle[4])  # Close price

            return None

        except Exception as e:
            logger.error(f"❌ Erro ao buscar preço atual de {coin_id}: {e}")
            return None


# Instância global
coingecko_ohlc_client = CoinGeckoOHLCClient()
