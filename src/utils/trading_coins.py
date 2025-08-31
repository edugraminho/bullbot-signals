"""
Trading Coins - Sistema para curar lista das melhores moedas para trading usando banco de dados
"""

import asyncio
import aiohttp
from typing import List, Dict, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from src.utils.logger import get_logger
from src.utils.config import settings
from src.database.connection import get_db
from src.database.models import TradingCoin

logger = get_logger(__name__)


class TradingCoins:
    """Sistema para curar lista das melhores moedas para trading usando banco de dados"""

    def __init__(self):
        self.coingecko_api = "https://api.coingecko.com/api/v3"
        self.rate_limit_delay = 6  # 6 segundos entre chamadas API pública

    async def fetch_coin_exchanges(self, coin_id: str) -> List[str]:
        """Busca as exchanges onde uma moeda específica está disponível"""
        try:
            url = f"{self.coingecko_api}/coins/{coin_id}/tickers"
            params = {"page": 1, "per_page": 100}

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()

                        # Extrair exchanges únicas dos tickers
                        exchanges = set()
                        for ticker in data.get("tickers", []):
                            market = ticker.get("market", {})
                            exchange_id = market.get("identifier")
                            if exchange_id:
                                exchanges.add(exchange_id)

                        exchanges_list = list(exchanges)
                        logger.debug(f"Exchanges para {coin_id}: {exchanges_list}")
                        return exchanges_list

                    elif response.status == 429:
                        logger.warning(f"Rate limit para {coin_id}, aguardando...")
                        await asyncio.sleep(self.rate_limit_delay * 2)
                        return []
                    else:
                        logger.warning(
                            f"Erro {response.status} ao buscar exchanges de {coin_id}"
                        )
                        return []

        except Exception as e:
            logger.warning(f"Erro ao buscar exchanges de {coin_id}: {e}")
            return []

    async def fetch_coins_data(self, limit: int = 500) -> List[Dict]:
        """Busca dados das moedas layer-1 da CoinGecko usando filtro por categoria"""
        try:
            url = f"{self.coingecko_api}/coins/markets"
            all_coins = []
            page = 1
            per_page = 250

            while len(all_coins) < limit:
                params = {
                    "vs_currency": "usd",
                    "category": "layer-1",  # Filtro por layer-1 (moedas principais)
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
                            if not data:
                                break
                            all_coins.extend(data)
                            logger.info(f"Página {page}: {len(data)} moedas layer-1")
                            page += 1

                            # Rate limiting
                            if len(all_coins) < limit:
                                await asyncio.sleep(self.rate_limit_delay)
                        elif response.status == 429:
                            logger.warning("Rate limit atingido, aguardando...")
                            await asyncio.sleep(self.rate_limit_delay * 2)
                        else:
                            logger.error(f"❌ Erro na API CoinGecko: {response.status}")
                            break

            logger.info(f"Total buscado: {len(all_coins)} moedas layer-1 da CoinGecko")
            return all_coins[:limit]  # Retorna apenas o limite solicitado

        except Exception as e:
            logger.error(f"❌ Erro ao buscar dados: {e}")
            return []

    async def filter_coins_with_exchanges(self, coins_data: List[Dict]) -> List[Dict]:
        """Filtra moedas e busca exchanges reais para cada uma"""
        filtered_coins = []
        total_coins = len(coins_data)
        blacklist_removed = 0
        market_cap_removed = 0
        volume_removed = 0
        processed = 0

        logger.info(f"Iniciando filtragem de {total_coins} moedas layer-1...")
        logger.info(
            f"Critérios: Market Cap > ${settings.trading_coins_min_market_cap:,}, Volume > ${settings.trading_coins_min_volume:,}"
        )

        for i, coin in enumerate(coins_data):
            # Pular moedas da blacklist
            if coin["symbol"].upper() in settings.trading_coins_blacklist:
                blacklist_removed += 1
                continue

            # Critérios de filtro
            market_cap = coin.get("market_cap", 0)
            volume_24h = coin.get("total_volume", 0)

            # Market cap mínimo
            if market_cap < settings.trading_coins_min_market_cap:
                market_cap_removed += 1
                continue

            # Volume mínimo
            if volume_24h < settings.trading_coins_min_volume:
                volume_removed += 1
                continue

            # Buscar exchanges reais para esta moeda
            logger.info(
                f"Processando {coin['symbol']} ({processed + 1}/{total_coins - blacklist_removed - market_cap_removed - volume_removed})"
            )
            exchanges = await self.fetch_coin_exchanges(coin["id"])

            # Rate limiting entre chamadas
            await asyncio.sleep(self.rate_limit_delay)

            # Adicionar dados necessários
            coin_data = {
                "ranking": len(filtered_coins) + 1,
                "coingecko_id": coin["id"],
                "symbol": coin["symbol"].upper(),
                "name": coin["name"],
                "market_cap": market_cap,
                "market_cap_rank": coin.get("market_cap_rank"),
                "volume_24h": volume_24h,
                "current_price": coin.get("current_price", 0),
                "price_change_24h": coin.get("price_change_24h"),
                "price_change_percentage_24h": coin.get("price_change_percentage_24h"),
                "category": "layer-1",
                "image_url": coin.get("image"),
                "exchanges": exchanges,  # Exchanges reais da API
            }

            filtered_coins.append(coin_data)
            processed += 1

        logger.info(f"Filtragem concluída:")
        logger.info(f"  - Total inicial: {total_coins}")
        logger.info(f"  - Moedas da blacklist removidas: {blacklist_removed}")
        logger.info(f"  - Market cap baixo: {market_cap_removed}")
        logger.info(f"  - Volume baixo: {volume_removed}")
        logger.info(f"  - Moedas processadas: {processed}")
        logger.info(f"  - Moedas válidas: {len(filtered_coins)}")

        return filtered_coins

    def save_to_database(self, coins_data: List[Dict]) -> int:
        """Salva lista de moedas no banco de dados"""
        try:
            db: Session = next(get_db())

            # Desativar todas as moedas existentes
            db.query(TradingCoin).update({"active": False})

            saved_count = 0

            for coin_data in coins_data:
                # Verificar se moeda já existe
                existing_coin = (
                    db.query(TradingCoin)
                    .filter(TradingCoin.coingecko_id == coin_data["coingecko_id"])
                    .first()
                )

                if existing_coin:
                    # Atualizar dados existentes
                    for key, value in coin_data.items():
                        if key != "ranking":
                            setattr(existing_coin, key, value)
                    existing_coin.active = True
                    existing_coin.updated_at = datetime.now(timezone.utc)
                    existing_coin.last_market_update = datetime.now(timezone.utc)
                    existing_coin.exchanges_last_updated = datetime.now(timezone.utc)
                    existing_coin.ranking = coin_data["ranking"]
                else:
                    # Criar nova moeda
                    new_coin = TradingCoin(**coin_data)
                    new_coin.active = True
                    new_coin.last_market_update = datetime.now(timezone.utc)
                    new_coin.exchanges_last_updated = datetime.now(timezone.utc)
                    db.add(new_coin)

                saved_count += 1

            db.commit()
            logger.info(f"Salvadas {saved_count} moedas no banco de dados")
            return saved_count

        except Exception as e:
            logger.error(f"❌ Erro ao salvar no banco: {e}")
            db.rollback()
            return 0
        finally:
            db.close()

    def load_from_database(self, active_only: bool = True) -> List[TradingCoin]:
        """Carrega lista de moedas do banco de dados"""
        try:
            db: Session = next(get_db())

            query = db.query(TradingCoin)

            if active_only:
                query = query.filter(TradingCoin.active == True)

            coins = query.order_by(TradingCoin.ranking.asc()).all()

            logger.info(f"Carregadas {len(coins)} moedas do banco")
            return coins

        except Exception as e:
            logger.error(f"❌ Erro ao carregar do banco: {e}")
            return []
        finally:
            db.close()

    async def update_trading_list(self) -> int:
        """Atualiza a lista de trading coins no banco de dados"""
        logger.info("Iniciando atualização da lista de trading coins...")

        # Buscar dados da CoinGecko (moedas layer-1)
        coins_data = await self.fetch_coins_data(limit=settings.trading_coins_max_limit)
        if not coins_data:
            logger.error("❌ Não foi possível buscar dados da CoinGecko")
            return 0

        # Filtrar moedas E buscar exchanges reais (processo lento)
        logger.info("⏳ Iniciando busca de exchanges reais (processo lento)...")
        filtered_coins = await self.filter_coins_with_exchanges(coins_data)

        if not filtered_coins:
            logger.error("❌ Nenhuma moeda passou nos filtros")
            return 0

        # Salvar no banco de dados
        saved_count = self.save_to_database(filtered_coins)

        logger.info(
            f"Lista de trading coins atualizada com {saved_count} moedas (exchanges reais)"
        )
        return saved_count

    def get_trading_symbols(self, limit: int = None) -> List[str]:
        """Retorna lista de símbolos para trading"""
        coins = self.load_from_database()
        symbols = [coin.symbol for coin in coins]
        return symbols[:limit] if limit else symbols

    def get_coins_by_exchange(self, exchange: str) -> List[str]:
        """Retorna moedas disponíveis em uma exchange específica"""
        coins = self.load_from_database()
        return [
            coin.symbol
            for coin in coins
            if coin.exchanges and exchange in coin.exchanges
        ]

    def get_coin_by_symbol(self, symbol: str) -> Optional[TradingCoin]:
        """Busca uma moeda específica por símbolo"""
        try:
            db: Session = next(get_db())
            coin = (
                db.query(TradingCoin)
                .filter(
                    and_(
                        TradingCoin.symbol == symbol.upper(), TradingCoin.active == True # noqa
                    )
                )
                .first()
            )
            return coin
        except Exception as e:
            logger.error(f"❌ Erro ao buscar moeda {symbol}: {e}")
            return None
        finally:
            db.close()

    def remove_exchange_from_coin(self, symbol: str, exchange: str) -> bool:
        """Remove uma exchange da lista de exchanges de uma moeda"""
        try:
            db: Session = next(get_db())
            coin = (
                db.query(TradingCoin)
                .filter(
                    and_(
                        TradingCoin.symbol == symbol.upper(), TradingCoin.active == True # noqa
                    )
                )
                .first()
            )

            if coin and coin.exchanges and exchange in coin.exchanges:
                coin.exchanges.remove(exchange)
                coin.updated_at = datetime.now(timezone.utc)
                db.commit()
                logger.info(f"Exchange {exchange} removida de {symbol}")
                return True

            return False

        except Exception as e:
            logger.error(f"❌ Erro ao remover {exchange} de {symbol}: {e}")
            return False
        finally:
            db.close()


# Instância global
trading_coins = TradingCoins()
