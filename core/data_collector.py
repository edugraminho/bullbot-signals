"""
Serviço de coleta de dados e cálculo de indicadores.

Integra exchanges e indicadores para fornecer dados
processados e sinais em tempo real.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

from .exchanges import ExchangeManager, ExchangeFactory
from .indicators import RSICalculator, IndicatorResult
from .cache import CacheManager, CacheConfig
from .indicators.base import SignalType

logger = logging.getLogger(__name__)


@dataclass
class DataCollectionConfig:
    """Configuração para coleta de dados."""

    symbols: List[str]
    timeframes: List[str]
    rsi_periods: List[int]
    collection_interval: int = 60  # segundos
    max_data_points: int = 1000


class DataCollector:
    """Serviço principal de coleta de dados."""

    def __init__(self, exchange_manager: ExchangeManager):
        self.exchange_manager = exchange_manager
        self.config = None
        self.is_running = False
        self.collected_data = {}
        self.rsi_calculators = {}

        # Inicializa cache
        cache_config = CacheConfig()
        self.cache = CacheManager(cache_config)

    def configure(self, config: DataCollectionConfig):
        """Configura o coletor de dados."""
        self.config = config

        # Cria calculadores de RSI para diferentes períodos
        for period in config.rsi_periods:
            rsi_params = {
                "period": period,
                "overbought_level": 70,
                "oversold_level": 30,
            }
            self.rsi_calculators[period] = RSICalculator(rsi_params)

        logger.info(
            f"DataCollector configurado: {len(config.symbols)} símbolos, {len(config.timeframes)} timeframes"
        )

    async def start_collection(self):
        """Inicia a coleta contínua de dados."""
        if not self.config:
            raise ValueError("DataCollector deve ser configurado antes de iniciar")

        self.is_running = True
        logger.info("Iniciando coleta de dados...")

        while self.is_running:
            try:
                await self._collect_all_data()
                await asyncio.sleep(self.config.collection_interval)

            except Exception as e:
                logger.error(f"Erro na coleta de dados: {e}")
                await asyncio.sleep(10)  # Espera antes de tentar novamente

    async def stop_collection(self):
        """Para a coleta de dados."""
        self.is_running = False
        logger.info("Coleta de dados parada")

    async def _collect_all_data(self):
        """Coleta dados de todas as exchanges configuradas."""
        for (
            exchange_name,
            exchange,
        ) in self.exchange_manager.get_all_exchanges().items():
            await self._collect_exchange_data(exchange_name, exchange)

    async def _collect_exchange_data(self, exchange_name: str, exchange):
        """Coleta dados de uma exchange específica."""
        try:
            # Busca símbolos se não estiverem mapeados
            if exchange_name not in self.collected_data:
                symbols = await exchange.get_symbols()
                self.collected_data[exchange_name] = {
                    "symbols": symbols,
                    "ohlcv": {},
                    "rsi": {},
                    "last_update": {},
                }

                # Armazena símbolos no cache
                self.cache.set_symbols(exchange_name, symbols)

            # Coleta dados para cada símbolo e timeframe
            for symbol in self.config.symbols:
                for timeframe in self.config.timeframes:
                    await self._collect_symbol_data(
                        exchange_name, exchange, symbol, timeframe
                    )

        except Exception as e:
            logger.error(f"Erro ao coletar dados da exchange {exchange_name}: {e}")

    async def _collect_symbol_data(
        self, exchange_name: str, exchange, symbol: str, timeframe: str
    ):
        """Coleta dados OHLCV para um símbolo específico."""
        try:
            # Verifica cache primeiro
            cached_ohlcv = self.cache.get_ohlcv(exchange_name, symbol, timeframe)
            if cached_ohlcv:
                self.collected_data[exchange_name]["ohlcv"][f"{symbol}_{timeframe}"] = (
                    cached_ohlcv
                )
                # Calcula RSI mesmo com dados do cache
                await self._calculate_rsi_for_symbol(exchange_name, symbol, timeframe)
                return

            # Busca dados da exchange
            ohlcv_data = await exchange.get_ohlcv(
                symbol, timeframe, limit=self.config.max_data_points
            )

            if ohlcv_data:
                # Armazena no cache
                self.cache.set_ohlcv(exchange_name, symbol, timeframe, ohlcv_data)

                # Armazena localmente
                self.collected_data[exchange_name]["ohlcv"][f"{symbol}_{timeframe}"] = (
                    ohlcv_data
                )

                # Calcula RSI
                await self._calculate_rsi_for_symbol(exchange_name, symbol, timeframe)

        except Exception as e:
            logger.error(
                f"Erro ao coletar dados para {exchange_name}:{symbol}:{timeframe}: {e}"
            )

    async def _calculate_rsi_for_symbol(
        self, exchange_name: str, symbol: str, timeframe: str
    ):
        """Calcula RSI para um símbolo específico."""
        try:
            ohlcv_key = f"{symbol}_{timeframe}"
            ohlcv_data = self.collected_data[exchange_name]["ohlcv"].get(ohlcv_key)

            if not ohlcv_data:
                logger.warning(f"Nenhum dado OHLCV encontrado para {ohlcv_key}")
                return

            # Verifica cache RSI
            cached_rsi = self.cache.get_rsi(exchange_name, symbol)
            if cached_rsi:
                self.collected_data[exchange_name]["rsi"][ohlcv_key] = cached_rsi
                return

            # Converte objetos OHLCV para dicionários
            ohlcv_dicts = []
            for ohlcv in ohlcv_data:
                # Verifica se é objeto OHLCV ou já é dicionário
                if hasattr(ohlcv, "timestamp") and hasattr(ohlcv, "open"):
                    # Objeto OHLCV
                    ohlcv_dict = {
                        "timestamp": ohlcv.timestamp,
                        "open": ohlcv.open,
                        "high": ohlcv.high,
                        "low": ohlcv.low,
                        "close": ohlcv.close,
                        "volume": ohlcv.volume,
                        "symbol": ohlcv.symbol,
                        "timeframe": ohlcv.timeframe,
                    }
                elif isinstance(ohlcv, dict):
                    # Já é um dicionário
                    ohlcv_dict = ohlcv
                elif isinstance(ohlcv, str) and "OHLCV(" in ohlcv:
                    # String que representa um objeto OHLCV (do cache)
                    try:
                        # Extrai os valores da string OHLCV
                        import re

                        pattern = r"OHLCV\(timestamp=datetime\.datetime\(([^)]+)\), open=([^,]+), high=([^,]+), low=([^,]+), close=([^,]+), volume=([^,]+), symbol='([^']+)', timeframe='([^']+)'\)"
                        match = re.search(pattern, ohlcv)
                        if match:
                            # Constrói dicionário a partir dos valores extraídos
                            ohlcv_dict = {
                                "timestamp": datetime.now(),  # Usa timestamp atual como fallback
                                "open": float(match.group(2)),
                                "high": float(match.group(3)),
                                "low": float(match.group(4)),
                                "close": float(match.group(5)),
                                "volume": float(match.group(6)),
                                "symbol": match.group(7),
                                "timeframe": match.group(8),
                            }
                        else:
                            logger.error(
                                f"Não foi possível extrair dados da string OHLCV: {ohlcv}"
                            )
                            continue
                    except Exception as e:
                        logger.error(f"Erro ao processar string OHLCV: {e}")
                        continue
                else:
                    # Formato desconhecido
                    logger.error(
                        f"Formato desconhecido para item: {type(ohlcv)} - {ohlcv}"
                    )
                    continue

                ohlcv_dicts.append(ohlcv_dict)

            # Calcula RSI para cada período
            rsi_results = {}
            for period, calculator in self.rsi_calculators.items():
                result = calculator.calculate(ohlcv_dicts)
                if result:
                    rsi_results[f"rsi_{period}"] = {
                        "value": result[-1].value if result else 0,
                        "signal": result[-1].signal.value if result else "NEUTRAL",
                        "strength": result[-1].strength if result else 0,
                        "timestamp": result[-1].timestamp.isoformat()
                        if result and result[-1].timestamp
                        else None,
                    }
                else:
                    logger.warning(
                        f"Nenhum resultado RSI para {symbol} período {period}"
                    )

            # Armazena no cache
            self.cache.set_rsi(exchange_name, symbol, rsi_results)

            # Armazena localmente
            self.collected_data[exchange_name]["rsi"][ohlcv_key] = rsi_results

        except Exception as e:
            logger.error(
                f"Erro ao calcular RSI para {exchange_name}:{symbol}:{timeframe}: {e}"
            )

    def get_latest_rsi(
        self, exchange_name: str, symbol: str, timeframe: str, period: int
    ) -> Optional[IndicatorResult]:
        """Obtém o RSI mais recente para um símbolo."""
        try:
            ohlcv_key = f"{symbol}_{timeframe}"
            rsi_data = self.collected_data[exchange_name]["rsi"].get(ohlcv_key, {})

            rsi_key = f"rsi_{period}"
            if rsi_key in rsi_data:
                rsi_dict = rsi_data[rsi_key]

                # Converte dicionário para IndicatorResult

                # Converte string de timestamp para datetime se necessário
                timestamp = rsi_dict.get("timestamp")
                if isinstance(timestamp, str):
                    try:
                        timestamp = datetime.fromisoformat(
                            timestamp.replace("Z", "+00:00")
                        )
                    except:
                        timestamp = datetime.now()
                elif timestamp is None:
                    timestamp = datetime.now()

                # Converte string de signal para SignalType
                signal_str = rsi_dict.get("signal", "NEUTRAL")
                signal_type = SignalType.NEUTRAL
                try:
                    signal_type = SignalType(signal_str.lower())
                except:
                    pass

                return IndicatorResult(
                    timestamp=timestamp,
                    value=float(rsi_dict.get("value", 0)),
                    signal=signal_type,
                    strength=float(rsi_dict.get("strength", 0)),
                    parameters={"period": period},
                    symbol=symbol,
                    timeframe=timeframe,
                    indicator_type="RSI",
                )

            return None

        except Exception as e:
            logger.error(
                f"Erro ao obter RSI para {exchange_name}:{symbol}:{timeframe}: {e}"
            )
            return None

    def get_all_rsi_signals(self, exchange_name: str) -> Dict[str, IndicatorResult]:
        """Obtém todos os sinais RSI de uma exchange."""
        try:
            all_signals = {}

            for symbol in self.config.symbols:
                for timeframe in self.config.timeframes:
                    for period in self.config.rsi_periods:
                        signal = self.get_latest_rsi(
                            exchange_name, symbol, timeframe, period
                        )
                        if signal:
                            key = f"{exchange_name}:{symbol}:{timeframe}:rsi_{period}"
                            all_signals[key] = signal

            return all_signals

        except Exception as e:
            logger.error(f"Erro ao obter sinais RSI para {exchange_name}: {e}")
            return {}

    def get_overbought_oversold_symbols(
        self, exchange_name: str, min_strength: float = 0.7
    ) -> Dict[str, List[Dict]]:
        """Obtém símbolos com sinais de overbought/oversold."""
        try:
            overbought = []
            oversold = []

            for symbol in self.config.symbols:
                for timeframe in self.config.timeframes:
                    for period in self.config.rsi_periods:
                        signal = self.get_latest_rsi(
                            exchange_name, symbol, timeframe, period
                        )

                        if signal and signal.get("strength", 0) >= min_strength:
                            signal_info = {
                                "symbol": symbol,
                                "timeframe": timeframe,
                                "period": period,
                                "value": signal.get("value", 0),
                                "strength": signal.get("strength", 0),
                                "timestamp": signal.get("timestamp"),
                            }

                            if signal.get("signal") == "overbought":
                                overbought.append(signal_info)
                            elif signal.get("signal") == "oversold":
                                oversold.append(signal_info)

            return {
                "overbought": overbought,
                "oversold": oversold,
            }

        except Exception as e:
            logger.error(f"Erro ao obter símbolos overbought/oversold: {e}")
            return {"overbought": [], "oversold": []}

    def get_data_summary(self) -> Dict[str, Any]:
        """Retorna resumo dos dados coletados."""
        try:
            summary = {
                "total_exchanges": len(self.collected_data),
                "total_symbols": sum(
                    len(data.get("symbols", []))
                    for data in self.collected_data.values()
                ),
                "total_ohlcv_datasets": sum(
                    len(data.get("ohlcv", {})) for data in self.collected_data.values()
                ),
                "total_rsi_datasets": sum(
                    len(data.get("rsi", {})) for data in self.collected_data.values()
                ),
                "cache_stats": self.cache.cache.get_stats(),
            }

            return summary

        except Exception as e:
            logger.error(f"Erro ao gerar resumo de dados: {e}")
            return {}

    async def test_exchange_connections(self) -> Dict[str, bool]:
        """Testa conexões com todas as exchanges."""
        results = {}
        for (
            exchange_name,
            exchange,
        ) in self.exchange_manager.get_all_exchanges().items():
            try:
                await exchange.test_connection()
                results[exchange_name] = True
            except Exception as e:
                logger.error(f"Erro na conexão com {exchange_name}: {e}")
                results[exchange_name] = False
        return results

    def get_available_symbols(self, exchange_name: str) -> List[str]:
        """Obtém símbolos disponíveis de uma exchange."""
        try:
            # Tenta cache primeiro
            cached_symbols = self.cache.get_symbols(exchange_name)
            if cached_symbols:
                return cached_symbols

            # Fallback para dados locais
            return self.collected_data.get(exchange_name, {}).get("symbols", [])

        except Exception as e:
            logger.error(f"Erro ao obter símbolos de {exchange_name}: {e}")
            return []
