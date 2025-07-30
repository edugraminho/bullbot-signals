"""
Cliente para integração com Polygon.io API
Documentação: https://polygon.io/docs/rest/indices/technical-indicators/relative-strength-index
"""

import asyncio
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict

import httpx
from pydantic import ValidationError

from src.core.models.crypto import RSIData, PolygonRSIResponse
from src.utils.logger import get_logger

logger = get_logger(__name__)


class PolygonError(Exception):
    """Exceção personalizada para erros da Polygon.io"""

    pass


class PolygonClient:
    """Cliente para API da Polygon.io"""

    def __init__(self, api_key: str, base_url: str = "https://api.polygon.io"):
        self.api_key = api_key
        self.base_url = base_url
        self.session: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Context manager entry"""
        self.session = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "User-Agent": "CryptoHunter/1.0",
            },
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.session:
            await self.session.aclose()

    async def get_rsi(
        self,
        symbol: str,
        timestamp: Optional[str] = None,
        timespan: str = "day",
        multiplier: int = 1,
        window: int = 14,
        series_type: str = "close",
        adjusted: bool = True,
        limit: int = 50,
    ) -> PolygonRSIResponse:
        """
        Busca dados de RSI para um símbolo

        Args:
            symbol: Símbolo da crypto (ex: X:BTCUSD)
            timestamp: Data específica (YYYY-MM-DD) ou timestamp em ms
            timespan: Tamanho da janela (minute, hour, day, week, month)
            multiplier: Multiplicador do timespan (ex: 15 para 15min, 4 para 4hr)
            window: Janela para cálculo RSI (padrão 14)
            series_type: Tipo de preço (close, open, high, low)
            adjusted: Se ajusta para splits/desdobramentos (padrão True)
            limit: Limite de resultados (máx 5000)
        """
        if not self.session:
            raise PolygonError("Cliente não inicializado. Use async with.")

        # Formatar símbolo para Polygon (crypto symbols precisam do prefixo X:)
        if not symbol.startswith("X:"):
            symbol = f"X:{symbol.upper()}"

        url = f"{self.base_url}/v1/indicators/rsi/{symbol}"

        params = {
            "timespan": timespan,
            "window": window,
            "series_type": series_type,
            "adjusted": adjusted,
            "limit": limit,
            "apikey": self.api_key,  # Backup auth method
        }

        # Adicionar multiplier apenas se for diferente de 1
        if multiplier != 1:
            params["timespan.multiplier"] = multiplier

        if timestamp:
            params["timestamp"] = timestamp

        try:
            logger.info(f"Buscando RSI para {symbol} com timespan {timespan}")
            response = await self.session.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            # Verificar status da resposta
            if data.get("status") != "OK":
                error_msg = data.get("error", "Erro desconhecido da Polygon.io")
                raise PolygonError(f"API retornou erro: {error_msg}")

            # Processar resultados
            rsi_values = []
            results = data.get("results", {})
            values = results.get("values", [])

            for item in values:
                try:
                    rsi_data = RSIData(
                        symbol=symbol.replace(
                            "X:", ""
                        ),  # Remove prefixo para padronizar
                        timestamp=datetime.fromtimestamp(item["timestamp"] / 1000),
                        value=Decimal(str(item["value"])),
                        timespan=timespan,
                        window=window,
                        source="polygon",
                    )
                    rsi_values.append(rsi_data)
                except (KeyError, ValueError, ValidationError) as e:
                    logger.warning(f"Erro ao processar item RSI: {e}")
                    continue

            response_obj = PolygonRSIResponse(
                symbol=symbol.replace("X:", ""),
                values=rsi_values,
                next_url=data.get("next_url"),
                request_id=data.get("request_id"),
                status=data.get("status", "OK"),
            )

            logger.info(f"RSI obtido com sucesso: {len(rsi_values)} valores")
            return response_obj

        except httpx.HTTPError as e:
            error_msg = f"Erro HTTP ao buscar RSI: {e}"
            logger.error(error_msg)
            raise PolygonError(error_msg)
        except Exception as e:
            error_msg = f"Erro inesperado ao buscar RSI: {e}"
            logger.error(error_msg)
            raise PolygonError(error_msg)

    async def get_latest_rsi(
        self,
        symbol: str,
        timespan: str = "day",
        multiplier: int = 1,
        window: int = 14,
        adjusted: bool = True,
    ) -> Optional[RSIData]:
        """Busca o RSI mais recente para um símbolo"""
        try:
            response = await self.get_rsi(
                symbol=symbol,
                timespan=timespan,
                multiplier=multiplier,
                window=window,
                adjusted=adjusted,
                limit=1,
            )

            if response.values:
                return response.values[0]
            return None

        except PolygonError:
            raise
        except Exception as e:
            raise PolygonError(f"Erro ao buscar RSI mais recente: {e}")

    async def get_multiple_rsi(
        self,
        symbols: List[str],
        timespan: str = "day",
        multiplier: int = 1,
        window: int = 14,
        adjusted: bool = True,
    ) -> Dict[str, Optional[RSIData]]:
        """
        Busca RSI para múltiplos símbolos em paralelo
        Útil para monitoramento de várias cryptos
        """
        tasks = []
        for symbol in symbols:
            task = self.get_latest_rsi(symbol, timespan, multiplier, window, adjusted)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        response_dict = {}
        for symbol, result in zip(symbols, results):
            if isinstance(result, Exception):
                logger.error(f"Erro ao buscar RSI para {symbol}: {result}")
                response_dict[symbol] = None
            else:
                response_dict[symbol] = result

        return response_dict
