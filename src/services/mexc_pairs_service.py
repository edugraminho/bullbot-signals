"""
Serviço para gerenciar pares de trading da MEXC
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional

import httpx
from sqlalchemy.dialects.postgresql import insert

from src.database.connection import SessionLocal
from src.database.models import MEXCTradingPair
from src.utils.logger import get_logger

logger = get_logger(__name__)


class MEXCPairsService:
    """Serviço para sincronizar e gerenciar pares de trading da MEXC"""

    def __init__(self):
        from src.utils.config import settings

        self.base_url = settings.mexc_base_url

    async def sync_all_pairs(self) -> Dict[str, int]:
        """
        Sincroniza todos os pares de trading da MEXC

        Returns:
            Dict com contadores de inserções/atualizações
        """
        try:
            logger.info("Iniciando sincronização de pares MEXC...")

            # Buscar dados da MEXC
            ticker_data = await self._fetch_ticker_24hr()
            exchange_info = await self._fetch_exchange_info()

            if not ticker_data or not exchange_info:
                logger.error("❌ Falha ao buscar dados da MEXC")
                return {"inserted": 0, "updated": 0, "errors": 1}

            # Combinar dados
            combined_data = self._combine_mexc_data(ticker_data, exchange_info)

            # Salvar no banco
            result = self._upsert_pairs(combined_data)

            logger.info(
                f"Sincronização concluída: {result['inserted']} inseridos, "
                f"{result['updated']} atualizados, {result['total']} total"
            )
            return result

        except Exception as e:
            logger.error(f"❌ Erro na sincronização MEXC: {e}")
            return {"inserted": 0, "updated": 0, "errors": 1}

    async def _fetch_ticker_24hr(self) -> Optional[List[Dict]]:
        """Busca dados de ticker 24hr de todos os pares"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.base_url}/api/v3/ticker/24hr")
                response.raise_for_status()
                data = response.json()
                logger.info(f"Buscados {len(data)} tickers da MEXC")
                return data
        except Exception as e:
            logger.error(f"❌ Erro ao buscar ticker 24hr: {e}")
            return None

    async def _fetch_exchange_info(self) -> Optional[Dict]:
        """Busca informações dos pares de trading"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.base_url}/api/v3/exchangeInfo")
                response.raise_for_status()
                data = response.json()
                logger.info(
                    f"Buscados dados de {len(data.get('symbols', []))} símbolos da MEXC"
                )
                return data
        except Exception as e:
            logger.error(f"❌ Erro ao buscar exchange info: {e}")
            return None

    def _combine_mexc_data(
        self, ticker_data: List[Dict], exchange_info: Dict
    ) -> List[Dict]:
        """Combina dados do ticker com exchange info"""
        # Criar índice por símbolo para exchange info
        exchange_symbols = {
            symbol["symbol"]: symbol for symbol in exchange_info.get("symbols", [])
        }

        combined = []
        for ticker in ticker_data:
            symbol = ticker["symbol"]
            exchange_data = exchange_symbols.get(symbol, {})

            # Combinar dados
            pair_data = {
                "symbol": symbol,
                "base_asset": exchange_data.get(
                    "baseAsset", symbol.replace("USDT", "")
                ),
                "quote_asset": exchange_data.get("quoteAsset", "USDT"),
                "full_name": exchange_data.get("fullName", ""),
                "current_price": float(ticker["lastPrice"])
                if ticker["lastPrice"]
                else 0,
                "volume_24h": float(ticker["volume"]) if ticker["volume"] else 0,
                "quote_volume_24h": float(ticker["quoteVolume"])
                if ticker["quoteVolume"]
                else 0,
                "open_price_24h": float(ticker["openPrice"])
                if ticker["openPrice"]
                else 0,
                "high_price_24h": float(ticker["highPrice"])
                if ticker["highPrice"]
                else 0,
                "low_price_24h": float(ticker["lowPrice"]) if ticker["lowPrice"] else 0,
                "maker_commission": float(exchange_data.get("makerCommission", 0)),
                "taker_commission": float(exchange_data.get("takerCommission", 0)),
                "base_asset_precision": exchange_data.get("baseAssetPrecision", 8),
                "quote_asset_precision": exchange_data.get("quoteAssetPrecision", 8),
                "is_active": exchange_data.get("status", "1") == "1",
                "is_spot_trading_allowed": exchange_data.get(
                    "isSpotTradingAllowed", True
                ),
                "raw_payload": {
                    "ticker": ticker,
                    "exchange_info": exchange_data,
                    "synced_at": datetime.now(timezone.utc).isoformat(),
                },
                "updated_at": datetime.now(timezone.utc),
            }
            combined.append(pair_data)

        logger.info(f"Combinados dados de {len(combined)} pares")
        return combined

    def _upsert_pairs(self, pairs_data: List[Dict]) -> Dict[str, int]:
        """Insere ou atualiza pares no banco"""
        inserted = 0
        updated = 0

        try:
            with SessionLocal() as session:
                for pair_data in pairs_data:
                    # Usar PostgreSQL UPSERT (INSERT ... ON CONFLICT)
                    stmt = insert(MEXCTradingPair).values(pair_data)
                    stmt = stmt.on_conflict_do_update(
                        index_elements=["symbol"],
                        set_=dict(
                            current_price=stmt.excluded.current_price,
                            volume_24h=stmt.excluded.volume_24h,
                            quote_volume_24h=stmt.excluded.quote_volume_24h,
                            open_price_24h=stmt.excluded.open_price_24h,
                            high_price_24h=stmt.excluded.high_price_24h,
                            low_price_24h=stmt.excluded.low_price_24h,
                            maker_commission=stmt.excluded.maker_commission,
                            taker_commission=stmt.excluded.taker_commission,
                            base_asset_precision=stmt.excluded.base_asset_precision,
                            quote_asset_precision=stmt.excluded.quote_asset_precision,
                            is_active=stmt.excluded.is_active,
                            is_spot_trading_allowed=stmt.excluded.is_spot_trading_allowed,
                            raw_payload=stmt.excluded.raw_payload,
                            updated_at=stmt.excluded.updated_at,
                        ),
                    )

                    result = session.execute(stmt)

                    # Verificar se foi inserção ou atualização
                    if result.rowcount > 0:
                        # Verificar se já existia
                        existing = (
                            session.query(MEXCTradingPair)
                            .filter_by(symbol=pair_data["symbol"])
                            .first()
                        )
                        if existing.created_at == existing.updated_at:
                            inserted += 1
                        else:
                            updated += 1

                session.commit()

            return {
                "inserted": inserted,
                "updated": updated,
                "total": len(pairs_data),
                "errors": 0,
            }

        except Exception as e:
            logger.error(f"❌ Erro ao salvar pares no banco: {e}")
            return {"inserted": 0, "updated": 0, "total": 0, "errors": 1}

    def get_active_symbols(self, quote_asset: str = "USDT") -> List[str]:
        """
        Retorna lista de símbolos ativos - substitui CSV

        Args:
            quote_asset: Filtrar por moeda de cotação (padrão: USDT)

        Returns:
            Lista de símbolos (ex: ["BTC", "ETH", "SOL"])
        """
        try:
            with SessionLocal() as session:
                query = session.query(MEXCTradingPair.base_asset).filter(
                    MEXCTradingPair.is_active == True,  # noqa: E712
                    MEXCTradingPair.is_spot_trading_allowed == True,  # noqa: E712
                    MEXCTradingPair.quote_asset == quote_asset,
                )

                symbols = [row[0] for row in query.all()]
                logger.info(f"Retornados {len(symbols)} símbolos ativos")
                return symbols

        except Exception as e:
            logger.error(f"❌ Erro ao buscar símbolos ativos: {e}")
            return []

    def get_symbol_data(self, symbol: str) -> Optional[Dict]:
        """
        Retorna dados OHLC para indicadores - substitui CSV

        Args:
            symbol: Símbolo da moeda (ex: "BTC")

        Returns:
            Dict com dados OHLC e metadata ou None
        """
        try:
            with SessionLocal() as session:
                # Buscar por base_asset ou symbol completo
                pair = (
                    session.query(MEXCTradingPair)
                    .filter(
                        (MEXCTradingPair.base_asset == symbol.upper())
                        | (MEXCTradingPair.symbol == f"{symbol.upper()}USDT")
                    )
                    .first()
                )

                if not pair:
                    return None

                return {
                    "symbol": pair.base_asset,
                    "full_symbol": pair.symbol,
                    "current_price": float(pair.current_price)
                    if pair.current_price
                    else 0,
                    "open": float(pair.open_price_24h) if pair.open_price_24h else 0,
                    "high": float(pair.high_price_24h) if pair.high_price_24h else 0,
                    "low": float(pair.low_price_24h) if pair.low_price_24h else 0,
                    "close": float(pair.current_price) if pair.current_price else 0,
                    "volume": float(pair.volume_24h) if pair.volume_24h else 0,
                    "quote_volume": float(pair.quote_volume_24h)
                    if pair.quote_volume_24h
                    else 0,
                    "updated_at": pair.updated_at.isoformat()
                    if pair.updated_at
                    else None,
                }

        except Exception as e:
            logger.error(f"❌ Erro ao buscar dados do símbolo {symbol}: {e}")
            return None

    def get_all_usdt_pairs(self) -> List[Dict]:
        """Retorna todos os pares USDT ativos"""
        try:
            with SessionLocal() as session:
                pairs = (
                    session.query(MEXCTradingPair)
                    .filter(
                        MEXCTradingPair.quote_asset == "USDT",
                        MEXCTradingPair.is_active == True,  # noqa: E712
                        MEXCTradingPair.is_spot_trading_allowed == True,  # noqa: E712
                    )
                    .all()
                )

                result = []
                for pair in pairs:
                    result.append(
                        {
                            "symbol": pair.base_asset,
                            "full_symbol": pair.symbol,
                            "current_price": float(pair.current_price)
                            if pair.current_price
                            else 0,
                            "volume_24h": float(pair.volume_24h)
                            if pair.volume_24h
                            else 0,
                            "quote_volume_24h": float(pair.quote_volume_24h)
                            if pair.quote_volume_24h
                            else 0,
                        }
                    )

                logger.info(f"Retornados {len(result)} pares USDT")
                return result

        except Exception as e:
            logger.error(f"❌ Erro ao buscar pares USDT: {e}")
            return []


# Instância global
mexc_pairs_service = MEXCPairsService()
