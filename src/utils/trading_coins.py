"""
Trading Coins - Sistema para curar lista das melhores moedas para trading
"""

import asyncio
import aiohttp
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json
import os
from dataclasses import dataclass
from src.utils.logger import get_logger
from src.utils.config import settings

logger = get_logger(__name__)


@dataclass
class CoinData:
    """Estrutura de dados para informações da moeda"""

    ranking: int
    symbol: str
    name: str
    market_cap: float
    volume_24h: float
    price: float
    launch_date: str
    exchanges: List[str]
    volume_7d: float = 0.0
    volume_30d: float = 0.0
    min_market_cap: float = 100_000_000  # $100M
    min_volume: float = 10_000_000  # $10M
    volume_period: str = "24h"  # 24h, 7d, 30d
    status: str = "active"

    def to_dict(self) -> Dict:
        return {
            "ranking": self.ranking,
            "symbol": self.symbol,
            "name": self.name,
            "market_cap": self.market_cap,
            "volume_24h": self.volume_24h,
            "volume_7d": self.volume_7d,
            "volume_30d": self.volume_30d,
            "price": self.price,
            "launch_date": self.launch_date,
            "exchanges": ",".join(self.exchanges),
            "min_market_cap": self.min_market_cap,
            "min_volume": self.min_volume,
            "volume_period": self.volume_period,
            "status": self.status,
        }


class TradingCoins:
    """Sistema para curar lista das melhores moedas para trading"""

    def __init__(self):
        self.coingecko_api = "https://api.coingecko.com/api/v3"
        self.excluded_categories = {
            "stablecoins",
            "meme-token",
            "wrapped-tokens",
            "governance",
        }
        self.csv_path = "data/trading_coins.csv"
        self.json_path = "data/trading_coins.json"

        # Configurações de volume
        self.volume_period = settings.trading_coins_volume_period
        self.min_volume_threshold = settings.trading_coins_min_volume

        # Criar diretório se não existir
        os.makedirs("data", exist_ok=True)

    async def fetch_coins_data(
        self, limit: int = 500, volume_period: str = "24h"
    ) -> List[Dict]:
        """Busca dados das moedas da CoinGecko"""
        try:
            url = f"{self.coingecko_api}/coins/markets"
            all_coins = []
            page = 1
            per_page = 250

            while len(all_coins) < limit:
                params = {
                    "vs_currency": "usd",
                    "order": "market_cap_desc",
                    "per_page": per_page,
                    "page": page,
                    "sparkline": "false",
                    "price_change_percentage": "24h",
                }

                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            if not data:  # Não há mais dados
                                break
                            all_coins.extend(data)
                            logger.info(f"Página {page}: {len(data)} moedas")
                            page += 1
                        else:
                            logger.error(f"❌ Erro na API CoinGecko: {response.status}")
                            break

            logger.info(f"Total buscado: {len(all_coins)} moedas da CoinGecko")
            return all_coins[:limit]  # Retorna apenas o limite solicitado

        except Exception as e:
            logger.error(f"❌ Erro ao buscar dados: {e}")
            return []

    async def get_coin_details(self, coin_id: str) -> Optional[Dict]:
        """Busca detalhes específicos de uma moeda"""
        try:
            url = f"{self.coingecko_api}/coins/{coin_id}"
            params = {
                "localization": "false",
                "tickers": "true",
                "market_data": "true",
                "community_data": "false",
                "developer_data": "false",
                "sparkline": "false",
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    return None

        except Exception as e:
            logger.error(f"❌ Erro ao buscar detalhes de {coin_id}: {e}")
            return None

    def filter_coins(
        self, coins_data: List[Dict], volume_period: str = "24h"
    ) -> List[CoinData]:
        """Filtra moedas baseado nos critérios de trading"""
        filtered_coins = []
        total_coins = len(coins_data)
        blacklist_removed = 0
        categories_removed = 0
        market_cap_removed = 0
        volume_removed = 0

        logger.info(f"Iniciando filtragem de {total_coins} moedas...")
        logger.info(
            f"Critérios: Market Cap > ${settings.trading_coins_min_market_cap:,}, Volume > ${self.get_min_volume_for_period(volume_period):,}"
        )

        for coin in coins_data:
            # Pular moedas da blacklist
            if coin["symbol"].upper() in settings.trading_coins_blacklist:
                blacklist_removed += 1
                continue

            # Pular categorias indesejadas
            if any(
                cat in coin.get("categories", []) for cat in self.excluded_categories
            ):
                categories_removed += 1
                continue

            # Critérios de filtro
            market_cap = coin.get("market_cap", 0)
            volume_24h = coin.get("total_volume", 0)

            # Market cap mínimo
            if market_cap < settings.trading_coins_min_market_cap:
                market_cap_removed += 1
                continue

            # Volume mínimo baseado no período
            min_volume = self.get_min_volume_for_period(volume_period)
            if volume_24h < min_volume:
                volume_removed += 1
                continue

            # Verificar se está listada em exchanges suportadas
            exchanges = self.get_supported_exchanges(coin.get("id", ""))
            if not exchanges:
                continue

            # Criar objeto CoinData
            coin_data = CoinData(
                ranking=len(filtered_coins) + 1,
                symbol=coin["symbol"].upper(),
                name=coin["name"],
                market_cap=market_cap,
                volume_24h=volume_24h,
                volume_7d=coin.get("total_volume_7d", 0),
                volume_30d=coin.get("total_volume_30d", 0),
                price=coin.get("current_price", 0),
                launch_date=coin.get("genesis_date", ""),
                exchanges=exchanges,
                volume_period=volume_period,
            )

            filtered_coins.append(coin_data)

        logger.info(f"Filtragem concluída:")
        logger.info(f"  - Total inicial: {total_coins}")
        logger.info(f"  - Moedas da blacklist removidas: {blacklist_removed}")
        logger.info(f"  - Categorias removidas: {categories_removed}")
        logger.info(f"  - Market cap baixo: {market_cap_removed}")
        logger.info(f"  - Volume baixo: {volume_removed}")
        logger.info(f"  - Moedas válidas: {len(filtered_coins)}")

        return filtered_coins

    def get_min_volume_for_period(self, period: str) -> float:
        """Retorna o volume mínimo baseado no período"""
        base_volume = self.min_volume_threshold

        if period == "24h":
            return base_volume
        elif period == "7d":
            return base_volume * 7
        elif period == "30d":
            return base_volume * 30
        else:
            return base_volume

    def get_volume_field_for_period(self, period: str) -> str:
        """Retorna o nome do campo de volume baseado no período"""
        if period == "24h":
            return "total_volume"
        elif period == "7d":
            return "total_volume_7d"
        elif period == "30d":
            return "total_volume_30d"
        else:
            return "total_volume"

    def get_supported_exchanges(self, coin_id: str) -> List[str]:
        """Determina em quais exchanges a moeda está disponível"""
        # Por enquanto, assumir que todas estão nas 3 exchanges
        # TODO: Implementar verificação real via APIs
        return ["binance", "mexc", "gate"]

    def save_to_csv(self, coins: List[CoinData]) -> None:
        """Salva lista em CSV"""
        try:
            df = pd.DataFrame([coin.to_dict() for coin in coins])
            df.to_csv(self.csv_path, index=False)
            logger.info(f"Lista salva em {self.csv_path}")
        except Exception as e:
            logger.error(f"❌ Erro ao salvar CSV: {e}")

    def save_to_json(self, coins: List[CoinData]) -> None:
        """Salva lista em JSON"""
        try:
            data = {
                "last_updated": datetime.now().isoformat(),
                "total_coins": len(coins),
                "coins": [coin.to_dict() for coin in coins],
            }

            with open(self.json_path, "w") as f:
                json.dump(data, f, indent=2)

            logger.info(f"Lista salva em {self.json_path}")
        except Exception as e:
            logger.error(f"❌ Erro ao salvar JSON: {e}")

    def load_from_csv(self) -> List[CoinData]:
        """Carrega lista do CSV"""
        try:
            if not os.path.exists(self.csv_path):
                return []

            df = pd.read_csv(self.csv_path)
            coins = []

            for _, row in df.iterrows():
                coin = CoinData(
                    ranking=int(row["ranking"]),
                    symbol=row["symbol"],
                    name=row["name"],
                    market_cap=float(row["market_cap"]),
                    volume_24h=float(row["volume_24h"]),
                    price=float(row["price"]),
                    launch_date=row["launch_date"],
                    exchanges=row["exchanges"].split(",")
                    if pd.notna(row["exchanges"])
                    else [],
                    min_market_cap=float(row["min_market_cap"]),
                    min_volume=float(row["min_volume"]),
                    status=row["status"],
                )
                coins.append(coin)

            logger.info(f"Carregadas {len(coins)} moedas do CSV")
            return coins

        except Exception as e:
            logger.error(f"❌ Erro ao carregar CSV: {e}")
            return []

    async def update_trading_list(self) -> List[CoinData]:
        """Atualiza a lista de trading coins"""
        volume_period = settings.trading_coins_volume_period
        logger.info(
            f"Iniciando atualização da lista de trading coins (volume: {volume_period})..."
        )

        # Buscar dados da CoinGecko
        coins_data = await self.fetch_coins_data(
            limit=1000, volume_period=volume_period
        )
        if not coins_data:
            logger.error("❌ Não foi possível buscar dados da CoinGecko")
            return []

        # Filtrar moedas
        filtered_coins = self.filter_coins(coins_data, volume_period)

        # Salvar em ambos os formatos
        self.save_to_csv(filtered_coins)
        self.save_to_json(filtered_coins)

        logger.info(
            f"Lista de trading coins atualizada com {len(filtered_coins)} moedas"
        )
        return filtered_coins

    def get_trading_symbols(self, limit: int = 200) -> List[str]:
        """Retorna lista de símbolos para trading"""
        coins = self.load_from_csv()
        return [coin.symbol for coin in coins[:limit]]

    def get_coins_by_exchange(self, exchange: str) -> List[str]:
        """Retorna moedas disponíveis em uma exchange específica"""
        coins = self.load_from_csv()
        return [coin.symbol for coin in coins if exchange in coin.exchanges]

    def remove_exchange_from_coin(self, symbol: str, exchange: str) -> None:
        """Remove uma exchange da lista de exchanges de uma moeda"""
        try:
            coins = self.load_from_csv()

            for coin in coins:
                if coin.symbol.upper() == symbol.upper() and exchange in coin.exchanges:
                    coin.exchanges.remove(exchange)
                    self.save_to_csv(coins)
                    break

        except Exception as e:
            logger.error(f"Erro ao remover {exchange} de {symbol}: {e}")


# Instância global
trading_coins = TradingCoins()
