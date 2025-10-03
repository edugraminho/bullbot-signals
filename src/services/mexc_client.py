"""
Cliente para API da MEXC (Spot)
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional

import httpx

from src.core.models.crypto import OHLCVData, RSIData
from src.core.services.rsi_calculator import RSICalculator
from src.utils.logger import get_logger
from src.utils.price_formatter import safe_float, safe_int, safe_price

logger = get_logger(__name__)


class MEXCError(Exception):
    """Exceção personalizada para erros da MEXC"""

    pass


class MEXCClient:
    """Cliente para API da MEXC (Spot)"""

    def __init__(self, base_url: str = "https://api.mexc.com"):
        self.base_url = base_url
        self.session: Optional[httpx.AsyncClient] = None
        self._should_close = False

    async def _ensure_session(self):
        """Garante que a sessão está inicializada"""
        if self.session is None:
            self.session = httpx.AsyncClient(timeout=30.0)
            self._should_close = True

    async def close(self):
        """Fecha a sessão HTTP"""
        if self.session and self._should_close:
            await self.session.aclose()
            self.session = None

    async def __aenter__(self):
        """Context manager entry"""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self.close()

    async def get_ohlcv(
        self,
        symbol: str,
        interval: str = "4h",
        limit: int = 50,
        from_timestamp: Optional[int] = None,
        to_timestamp: Optional[int] = None,
    ) -> List[OHLCVData]:
        """
        Busca dados OHLCV da MEXC (Spot)

        Args:
            symbol: Símbolo do par (ex: BTCUSDT)
            interval: Intervalo de tempo (1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1M)
            limit: Quantidade de candles (máx 1000)
            from_timestamp: Timestamp inicial (opcional)
            to_timestamp: Timestamp final (opcional)

        Returns:
            Lista de dados OHLCV

        Raises:
            MEXCError: Em caso de erro na API
        """
        try:
            # Converter símbolo: BTC -> BTCUSDT (formato spot)
            symbol = symbol.upper()
            if not symbol.endswith("USDT"):
                symbol = f"{symbol}USDT"

            # Construir URL e parâmetros (API spot)
            url = f"{self.base_url}/api/v3/klines"
            params = {
                "symbol": symbol,
                "interval": interval,
                "limit": min(limit, 1000),
            }

            # Adicionar timestamps se fornecidos
            if from_timestamp:
                params["start"] = from_timestamp
            if to_timestamp:
                params["end"] = to_timestamp

            await self._ensure_session()
            logger.debug(f"Buscando OHLCV para {symbol} com intervalo {interval}")
            response = await self.session.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            # Armazenar dados brutos da API para debug
            raw_api_response = {
                "symbol": symbol,
                "interval": interval,
                "response_data": data,
                "timestamp": datetime.now().isoformat(),
            }

            # MEXC retorna array de arrays com 6 elementos:
            # [timestamp, open, high, low, close, volume]
            ohlcv_data = []

            for item in data:
                try:
                    # MEXC retorna timestamp em milissegundos (13 dígitos)
                    timestamp_raw = int(item[0])
                    timestamp = datetime.fromtimestamp(timestamp_raw / 1000)

                    # Converter valores para Decimal
                    open_val = Decimal(str(item[1]))
                    high_val = Decimal(str(item[2]))
                    low_val = Decimal(str(item[3]))
                    close_val = Decimal(str(item[4]))
                    volume_val = Decimal(str(item[5]))

                    ohlcv_data.append(
                        OHLCVData(
                            symbol=symbol,
                            timestamp=timestamp,
                            open=open_val,
                            high=high_val,
                            low=low_val,
                            close=close_val,
                            volume=volume_val,
                            timespan=interval,
                        )
                    )
                except (ValueError, IndexError, OSError) as e:
                    logger.warning(f"Erro ao processar item OHLCV: {e}")
                    continue

            logger.debug(
                f"OHLCV obtido com sucesso: {len(ohlcv_data)} valores para {symbol}"
            )

            # Retornar dados com raw_api_response separado
            return ohlcv_data, raw_api_response

        except httpx.HTTPError as e:
            # Log mais detalhado para erro 400 (Bad Request)
            if hasattr(e, "response") and e.response.status_code == 400:
                error_msg = f"Erro 400 Bad Request ao buscar OHLCV para {symbol} {interval}: Símbolo ou timeframe pode não estar disponível na MEXC"
                logger.warning(error_msg)  # Warning em vez de error para 400
            else:
                error_msg = f"Erro HTTP ao buscar OHLCV: {e}"
                logger.error(error_msg)
            raise MEXCError(error_msg)
        except Exception as e:
            error_msg = f"Erro ao buscar OHLCV para {symbol}: {e}"
            logger.error(error_msg)
            raise MEXCError(error_msg)

    async def get_latest_rsi(
        self,
        symbol: str,
        interval: str = "4h",
        period: int = 14,
    ) -> Optional[RSIData]:
        """Busca OHLCV e calcula o RSI mais recente"""
        try:
            # Buscar dados suficientes para calcular RSI usando configuração
            total_periods = period + 100
            logger.debug(f"Buscando RSI MEXC: {symbol} {interval}")
            ohlcv_data, raw_api_response = await self.get_ohlcv(symbol, interval, total_periods)

            if not ohlcv_data:
                return None

            # Converter OHLCVData para formato genérico para o calculador
            ohlcv_dict = [
                {
                    "timestamp": item.timestamp,
                    "close": float(item.close),
                    "open": float(item.open),
                    "high": float(item.high),
                    "low": float(item.low),
                    "volume": float(item.volume),
                }
                for item in ohlcv_data
            ]

            # Calcular RSI usando o calculador independente
            rsi_data = RSICalculator.get_latest_rsi(
                ohlcv_dict, period, symbol, interval
            )

            if rsi_data:
                # Adicionar preço atual (último preço de fechamento)
                rsi_data.current_price = ohlcv_data[-1].close
                rsi_data.source = "mexc"

                # Adicionar dados brutos da API para debug
                rsi_data.raw_api_response = raw_api_response

                logger.info(f"RSI MEXC calculado para {symbol}: {rsi_data.value}")
                logger.info(f"Preço atual MEXC: {rsi_data.current_price}")
                return rsi_data
            else:
                logger.warning(f"Nenhum dado RSI MEXC calculado para {symbol}")
                return None

        except MEXCError as e:
            logger.error(f"❌ Erro da MEXC para {symbol}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Erro ao calcular RSI MEXC para {symbol}: {e}")
            return None

    async def get_market_data_24h(self, symbol: str) -> Optional[dict]:
        """
        Busca dados de mercado 24h completos da MEXC

        Args:
            symbol: Símbolo do par (ex: BTCUSDT, SOL)

        Returns:
            Dict com dados 24h ou None se erro
        """
        try:
            # Converter símbolo: BTC -> BTCUSDT (formato spot)
            symbol = symbol.upper()
            if not symbol.endswith("USDT"):
                symbol = f"{symbol}USDT"

            # Buscar dados ticker 24hr
            url = f"{self.base_url}/api/v3/ticker/24hr"
            params = {"symbol": symbol}

            await self._ensure_session()
            logger.debug(f"Buscando dados 24h para {symbol}")
            response = await self.session.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            if not data:
                logger.warning(f"Nenhum dado 24h encontrado para {symbol}")
                return None

            # Estruturar dados de mercado com parsing seguro usando funções utilitárias
            market_data = {
                "symbol": symbol,
                "current_price": safe_price(
                    data.get("lastPrice")
                ),  # Preços não podem ser negativos
                "open_price_24h": safe_price(data.get("openPrice")),
                "high_price_24h": safe_price(data.get("highPrice")),
                "low_price_24h": safe_price(data.get("lowPrice")),
                "volume_24h": safe_float(data.get("volume")),  # Volume pode ser 0
                "quote_volume_24h": safe_float(data.get("quoteVolume")),
                "price_change_24h": safe_float(
                    data.get("priceChange")
                ),  # Pode ser negativo
                "price_change_24h_pct": safe_float(data.get("priceChangePercent")),
                "weighted_avg_price": safe_price(data.get("weightedAvgPrice")),
                "prev_close_price": safe_price(data.get("prevClosePrice")),
                "bid_price": safe_price(data.get("bidPrice")),
                "ask_price": safe_price(data.get("askPrice")),
                "open_time": safe_int(data.get("openTime")),
                "close_time": safe_int(data.get("closeTime")),
                "count": safe_int(data.get("count")),  # Número de trades
                "timestamp": datetime.now(timezone.utc),
                "source": "mexc",
            }

            logger.debug(
                f"Dados 24h obtidos para {symbol}: preço {market_data['current_price']}, volume {market_data['volume_24h']}"
            )
            return market_data

        except httpx.HTTPError as e:
            logger.error(f"❌ Erro HTTP ao buscar dados 24h: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Erro ao buscar dados 24h para {symbol}: {e}")
            return None

    async def get_market_context(self, symbol: str, ohlcv_data: List[dict]) -> dict:
        """
        Calcula contexto adicional de mercado para melhor análise

        Args:
            symbol: Símbolo do ativo
            ohlcv_data: Dados OHLCV históricos

        Returns:
            Dict com contexto de mercado
        """
        try:
            if not ohlcv_data or len(ohlcv_data) < 20:
                return {}

            # Ordenar dados por timestamp
            sorted_data = sorted(ohlcv_data, key=lambda x: x["timestamp"])
            latest = sorted_data[-1]

            # Calcular volatilidade (desvio padrão dos closes)
            closes = [float(item["close"]) for item in sorted_data[-20:]]
            avg_price = sum(closes) / len(closes)
            variance = sum((price - avg_price) ** 2 for price in closes) / len(closes)
            volatility = (variance**0.5) / avg_price * 100  # % de volatilidade

            # Calcular range médio (high-low)
            ranges = [
                float(item["high"]) - float(item["low"]) for item in sorted_data[-10:]
            ]
            avg_range = sum(ranges) / len(ranges)
            current_range = float(latest["high"]) - float(latest["low"])
            range_ratio = current_range / avg_range if avg_range > 0 else 1

            # Determinar sentimento baseado nos últimos candles
            recent_closes = closes[-5:]  # Últimos 5 closes
            trend = "bullish" if recent_closes[-1] > recent_closes[0] else "bearish"

            # Calcular força do movimento
            price_momentum = (
                (closes[-1] - closes[-3]) / closes[-3] * 100 if closes[-3] > 0 else 0
            )

            context = {
                "volatility_pct": round(volatility, 2),
                "range_ratio": round(range_ratio, 2),
                "trend_sentiment": trend,
                "price_momentum_pct": round(price_momentum, 2),
                "is_high_volatility": volatility > 5.0,
                "is_expanding_range": range_ratio > 1.2,
                "avg_volume_10": sum(
                    float(item["volume"]) for item in sorted_data[-10:]
                )
                / 10,
                "volume_ratio": float(latest["volume"])
                / (sum(float(item["volume"]) for item in sorted_data[-10:]) / 10)
                if sorted_data
                else 1,
            }

            logger.debug(f"Contexto de mercado calculado para {symbol}: {context}")
            return context

        except Exception as e:
            logger.error(f"❌ Erro ao calcular contexto de mercado para {symbol}: {e}")
            return {}
