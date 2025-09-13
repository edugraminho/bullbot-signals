"""
Trading Coins - Sistema para curar lista das melhores moedas para trading usando banco de dados
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional

import aiohttp
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from src.database.connection import get_db
from src.database.models import TradingCoin
from src.utils.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class TradingCoins:
    """Sistema para curar lista das melhores moedas para trading usando banco de dados"""

    def __init__(self):
        self.coingecko_api = "https://api.coingecko.com/api/v3"
        self.rate_limit_delay = settings.coingecko_rate_limit_seconds

    async def fetch_coin_exchanges(self, coin_id: str) -> List[str]:
        """Busca as exchanges onde uma moeda específica está disponível com retry em caso de rate limit"""
        for attempt in range(settings.coingecko_max_retries):
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
                            # Rate limit - implementar backoff exponencial
                            backoff_time = settings.coingecko_retry_backoff_base * (
                                2**attempt
                            )
                            logger.warning(
                                f"Rate limit para {coin_id} (tentativa {attempt + 1}/{settings.coingecko_max_retries}), "
                                f"aguardando {backoff_time}s..."
                            )
                            await asyncio.sleep(backoff_time)

                            # Se foi a última tentativa, ainda vai retornar None
                            if attempt == settings.coingecko_max_retries - 1:
                                logger.error(
                                    f"❌ Rate limit persistente para {coin_id} após {settings.coingecko_max_retries} tentativas"
                                )
                                return None  # Indica falha definitiva
                            continue

                        else:
                            logger.warning(
                                f"Erro {response.status} ao buscar exchanges de {coin_id}"
                            )
                            return None  # Indica falha definitiva

            except Exception as e:
                logger.warning(
                    f"Erro ao buscar exchanges de {coin_id} (tentativa {attempt + 1}): {e}"
                )
                if attempt == settings.coingecko_max_retries - 1:
                    return None  # Indica falha definitiva

                # Aguardar antes da próxima tentativa
                await asyncio.sleep(settings.coingecko_retry_backoff_base)

        return None  # Fallback - não deveria chegar aqui

    async def fetch_coins_data(self, limit: int) -> List[Dict]:
        """Busca exatamente {limit} moedas layer-1 da CoinGecko ordenadas por market cap"""
        try:
            url = f"{self.coingecko_api}/coins/markets"
            all_coins = []
            page = 1
            per_page = 250  # Máximo por página da API
            
            logger.info(f"🚀 Buscando {limit} moedas (todas as categorias) ordenadas por market cap...")

            while len(all_coins) < limit:
                params = {
                    "vs_currency": "usd",
                    # REMOVIDO: "category" para buscar TODAS as categorias
                    "order": "market_cap_desc",  # Garantir ordem por market cap
                    "per_page": min(per_page, limit - len(all_coins)),  # Não buscar mais que necessário
                    "page": page,
                    "sparkline": "false",
                    "price_change_percentage": "24h",
                }

                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            if not data:  # Acabaram as moedas disponíveis
                                logger.info(f"⚠️ API retornou {len(all_coins)} moedas (menos que o limite de {limit})")
                                break
                            
                            all_coins.extend(data)
                            logger.info(f"Página {page}: +{len(data)} moedas (total: {len(all_coins)}/{limit})")
                            page += 1

                            # Rate limiting apenas se precisar buscar mais
                            if len(all_coins) < limit:
                                await asyncio.sleep(self.rate_limit_delay)
                                
                        elif response.status == 429:
                            logger.warning("Rate limit atingido, aguardando...")
                            await asyncio.sleep(self.rate_limit_delay * 3)  # Aguardar mais tempo
                        else:
                            logger.error(f"❌ Erro na API CoinGecko: {response.status}")
                            break

            # Garantir que retorna exatamente o limite solicitado
            final_coins = all_coins[:limit]
            logger.info(f"✅ Busca concluída: {len(final_coins)} moedas layer-1")
            return final_coins

        except Exception as e:
            logger.error(f"❌ Erro ao buscar dados: {e}")
            return []



    def save_to_database(self, coins_data: List[Dict]) -> int:
        """Salva lista completa de moedas no banco de dados (com exchanges)"""
        try:
            db: Session = next(get_db())
            saved_count = 0

            for coin_data in coins_data:
                # Verificar se moeda já existe
                existing_coin = (
                    db.query(TradingCoin)
                    .filter(TradingCoin.coingecko_id == coin_data["coingecko_id"])
                    .first()
                )

                if existing_coin:
                    # Atualizar todos os dados
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
                query = query.filter(TradingCoin.active.is_(True))  # noqa

            coins = query.order_by(TradingCoin.ranking.asc()).all()

            logger.info(f"Carregadas {len(coins)} moedas do banco")
            return coins

        except Exception as e:
            logger.error(f"❌ Erro ao carregar do banco: {e}")
            return []
        finally:
            db.close()

    async def populate_trading_coins(self) -> int:
        """Busca e popula moedas da CoinGecko aplicando filtros"""
        logger.info("Iniciando busca e população de trading coins...")

        # Buscar dados da CoinGecko
        coins_data = await self.fetch_coins_data(limit=settings.trading_coins_max_limit)
        if not coins_data:
            logger.error("❌ Não foi possível buscar dados da CoinGecko")
            return 0

        # Aplicar filtros
        filtered_coins = await self.filter_and_prepare_coins(coins_data)
        if not filtered_coins:
            logger.error("❌ Nenhuma moeda passou nos filtros")
            return 0

        # Salvar no banco
        saved_count = self.save_to_database(filtered_coins)
        logger.info(f"População concluída: {saved_count} moedas salvas")
        return saved_count

    async def filter_and_prepare_coins(self, coins_data: List[Dict]) -> List[Dict]:
        """Filtra moedas baseado apenas na blacklist e prepara para salvar"""
        filtered_coins = []
        total_coins = len(coins_data)
        blacklist_removed = 0

        logger.info(f"Iniciando processamento de {total_coins} moedas (todas as categorias)...")
        logger.info("Aplicando filtros: blacklist de símbolos + market cap > $0")

        for coin in coins_data:
            # Pular moedas da blacklist de símbolos (mantido)
            if coin["symbol"].upper() in settings.trading_coins_blacklist:
                blacklist_removed += 1
                continue

            # NOVO: Filtrar categorias indesejadas
            # Nota: A API markets não retorna categoria, então vamos aceitar todas por enquanto
            # e filtrar apenas por símbolo blacklist + market cap mínimo

            # Filtro básico: apenas moedas com market cap > $0 (para evitar moedas "mortas")
            market_cap = coin.get("market_cap") or 0
            if market_cap <= 0:
                continue

            # Preparar dados para salvar (tratando valores null)
            volume_24h = coin.get("total_volume") or 0
            current_price = coin.get("current_price") or 0  # Não pode ser null
            
            coin_data = {
                "ranking": len(filtered_coins) + 1,
                "coingecko_id": coin["id"],
                "symbol": coin["symbol"].upper(),
                "name": coin["name"],
                "market_cap": market_cap,
                "market_cap_rank": coin.get("market_cap_rank"),
                "volume_24h": volume_24h,
                "current_price": current_price,
                "price_change_24h": coin.get("price_change_24h"),
                "price_change_percentage_24h": coin.get("price_change_percentage_24h"),
                "category": "mixed",  # Moedas de várias categorias
                "image_url": coin.get("image"),
            }

            filtered_coins.append(coin_data)

        logger.info("Processamento concluído (filtros aplicados):")
        logger.info(f"  - Total inicial: {total_coins}")
        logger.info(f"  - Moedas da blacklist removidas: {blacklist_removed}")
        logger.info(f"  - Moedas sem market cap removidas: {total_coins - len(filtered_coins) - blacklist_removed}")
        logger.info(f"  - Moedas aceitas: {len(filtered_coins)}")
        logger.info("  - Buscando de TODAS as categorias (não só layer-1)")

        return filtered_coins

    async def update_exchanges_data(self, force_update: bool = False) -> int:
        """Atualiza dados de exchanges para moedas que precisam (processo lento)"""
        logger.info("Iniciando atualização de dados de exchanges...")

        # Buscar moedas que precisam de atualização de exchanges
        coins_needing_update = self.get_coins_needing_exchange_update(force_update)

        if not coins_needing_update:
            logger.info("Nenhuma moeda precisa de atualização de exchanges")
            return 0

        logger.info(
            f"⏳ Atualizando exchanges para {len(coins_needing_update)} moedas..."
        )
        updated_count = 0

        for coin in coins_needing_update:
            exchanges = await self.fetch_coin_exchanges(coin.coingecko_id)

            if exchanges is not None:
                # Sucesso na busca (pode ser lista vazia se moeda não tem exchanges)
                self.update_coin_exchanges(coin.coingecko_id, exchanges)
                updated_count += 1
            else:
                # Falha definitiva - não atualizar exchanges_last_updated
                # Moeda será tentada novamente no próximo ciclo
                logger.warning(
                    f"⚠️ Pulando atualização de exchanges para {coin.symbol} devido a falhas na API"
                )

            # Rate limiting
            await asyncio.sleep(self.rate_limit_delay)

        logger.info(f"Exchanges atualizadas para {updated_count} moedas")
        return updated_count


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
                        TradingCoin.symbol == symbol.upper(),
                        TradingCoin.active == True,  # noqa
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

    def get_coins_needing_exchange_update(
        self, force_update: bool = False
    ) -> List[TradingCoin]:
        """Retorna moedas que precisam de atualização de exchanges"""
        try:
            db: Session = next(get_db())

            if force_update:
                # Forçar atualização de todas as moedas ativas
                coins = db.query(TradingCoin).filter(TradingCoin.active == True).all()  # noqa
            else:
                # Buscar moedas que nunca tiveram exchanges atualizadas ou são muito antigas
                from datetime import timedelta

                cutoff_date = datetime.now(timezone.utc) - timedelta(
                    days=settings.trading_coins_exchanges_update_days
                )

                coins = (
                    db.query(TradingCoin)
                    .filter(
                        and_(
                            TradingCoin.active == True,  # noqa
                            or_(
                                TradingCoin.exchanges_last_updated.is_(None),
                                TradingCoin.exchanges_last_updated < cutoff_date,
                            ),
                        )
                    )
                    .all()
                )

            db.close()
            return coins

        except Exception as e:
            logger.error(f"❌ Erro ao buscar moedas para atualização: {e}")
            return []

    def update_coin_exchanges(self, coingecko_id: str, exchanges: List[str]) -> bool:
        """Atualiza exchanges de uma moeda específica"""
        try:
            db: Session = next(get_db())
            coin = (
                db.query(TradingCoin)
                .filter(TradingCoin.coingecko_id == coingecko_id)
                .first()
            )

            if coin:
                coin.exchanges = exchanges
                coin.exchanges_last_updated = datetime.now(timezone.utc)
                coin.updated_at = datetime.now(timezone.utc)
                db.commit()
                logger.debug(f"Exchanges atualizadas para {coin.symbol}: {exchanges}")
                db.close()
                return True

            db.close()
            return False

        except Exception as e:
            logger.error(f"❌ Erro ao atualizar exchanges de {coingecko_id}: {e}")
            return False

    def remove_exchange_from_coin(self, symbol: str, exchange: str) -> bool:
        """Remove uma exchange da lista de exchanges de uma moeda"""
        try:
            db: Session = next(get_db())
            coin = (
                db.query(TradingCoin)
                .filter(
                    and_(
                        TradingCoin.symbol == symbol.upper(),
                        TradingCoin.active == True,  # noqa
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
