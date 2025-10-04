"""
Builder para estruturar dados completos de sinais
Constrói o JSON indicator_data com estrutura rica e organizada
"""

from typing import Dict, Optional
from datetime import datetime, timezone

from src.core.services.confluence_analyzer import ConfluenceResult
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SignalDataBuilder:
    """Builder para estruturar dados completos de sinais"""

    @staticmethod
    def build_indicator_data(
        confluence_result: ConfluenceResult,
        market_data_24h: Optional[Dict] = None,
        market_context: Optional[Dict] = None,
        trading_recommendations: Optional[Dict] = None,
    ) -> Dict:
        """
        Constrói estrutura completa de dados do sinal

        Args:
            confluence_result: Resultado da análise de confluência
            market_data_24h: Dados 24h da MEXC
            market_context: Contexto adicional do mercado
            trading_recommendations: Recomendações de trading

        Returns:
            Dict estruturado com todos os dados do sinal
        """
        try:
            logger.debug("Construindo dados estruturados do sinal")

            # Dados básicos do sinal
            signal_data = {
                "signal_info": {
                    "type": confluence_result.signal.signal_type.value
                    if confluence_result.signal
                    else None,
                    "strength": confluence_result.signal.strength.value
                    if confluence_result.signal
                    else None,
                    "message": confluence_result.signal.message
                    if confluence_result.signal
                    else None,
                    "recommendation": confluence_result.recommendation,
                    "risk_level": confluence_result.risk_level,
                    "timestamp": confluence_result.signal.timestamp.isoformat()
                    if confluence_result.signal
                    else datetime.now(timezone.utc).isoformat(),
                }
            }

            # Dados de mercado 24h
            if market_data_24h:
                signal_data["market_data"] = {
                    "current_price": market_data_24h.get("current_price"),
                    "volume_24h": market_data_24h.get("volume_24h"),
                    "quote_volume_24h": market_data_24h.get("quote_volume_24h"),
                    "price_change_24h": market_data_24h.get("price_change_24h"),
                    "price_change_24h_pct": market_data_24h.get("price_change_24h_pct"),
                    "high_24h": market_data_24h.get("high_price_24h"),
                    "low_24h": market_data_24h.get("low_price_24h"),
                    "open_24h": market_data_24h.get("open_price_24h"),
                    "weighted_avg_price": market_data_24h.get("weighted_avg_price"),
                    "bid_price": market_data_24h.get("bid_price"),
                    "ask_price": market_data_24h.get("ask_price"),
                    "spread_pct": SignalDataBuilder._calculate_spread_pct(
                        market_data_24h.get("bid_price"),
                        market_data_24h.get("ask_price"),
                    ),
                    "trades_count_24h": market_data_24h.get("count"),
                    "source": market_data_24h.get("source", "mexc"),
                }
            else:
                signal_data["market_data"] = {
                    "current_price": confluence_result.current_price,
                    "source": "confluence_result",
                }

            # Análise de confluência detalhada
            signal_data["confluence_analysis"] = {
                "total_score": confluence_result.confluence_score.total_score,
                "max_possible_score": confluence_result.confluence_score.max_possible_score,
                "score_percentage": round(
                    (
                        confluence_result.confluence_score.total_score
                        / confluence_result.confluence_score.max_possible_score
                    )
                    * 100,
                    1,
                )
                if confluence_result.confluence_score.max_possible_score > 0
                else 0,
                "signal_strength": confluence_result.confluence_score.signal_strength.value,
                "is_valid_signal": confluence_result.confluence_score.is_valid_signal,
                "breakdown_by_indicator": confluence_result.confluence_score.details,
            }

            # Indicadores técnicos individuais estruturados
            signal_data["technical_indicators"] = (
                SignalDataBuilder._structure_technical_indicators(
                    confluence_result.confluence_score.details
                )
            )

            # Contexto de mercado adicional
            if market_context:
                signal_data["market_context"] = {
                    "volatility_pct": market_context.get("volatility_pct"),
                    "trend_sentiment": market_context.get("trend_sentiment"),
                    "price_momentum_pct": market_context.get("price_momentum_pct"),
                    "range_ratio": market_context.get("range_ratio"),
                    "volume_ratio": market_context.get("volume_ratio"),
                    "is_high_volatility": market_context.get("is_high_volatility"),
                    "is_expanding_range": market_context.get("is_expanding_range"),
                    "avg_volume_10_periods": market_context.get("avg_volume_10"),
                }

            # Recomendações de trading
            if trading_recommendations:
                signal_data["trading_recommendations"] = trading_recommendations

            # Metadados
            signal_data["metadata"] = {
                "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
                "data_structure_version": "2.0",
                "components_included": list(signal_data.keys()),
            }

            logger.debug(
                f"Dados estruturados construídos com {len(signal_data)} seções"
            )
            return signal_data

        except Exception as e:
            logger.error(f"❌ Erro ao construir dados estruturados: {e}")
            # Fallback mínimo
            return {
                "signal_info": {
                    "type": confluence_result.signal.signal_type.value
                    if confluence_result.signal
                    else None,
                    "recommendation": confluence_result.recommendation,
                    "error": f"Erro na construção dos dados: {str(e)}",
                },
                "confluence_analysis": {
                    "total_score": confluence_result.confluence_score.total_score,
                    "max_possible_score": confluence_result.confluence_score.max_possible_score,
                },
            }

    @staticmethod
    def _structure_technical_indicators(confluence_details: Dict) -> Dict:
        """Estrutura dados dos indicadores técnicos de forma organizada"""
        try:
            structured = {}

            # RSI
            if "RSI" in confluence_details:
                rsi_data = confluence_details["RSI"]
                structured["rsi"] = {
                    "value": rsi_data.get("value"),
                    "score": rsi_data.get("score"),
                    "levels": rsi_data.get("levels", {}),
                    "zone": rsi_data.get("levels", {}).get("current_zone", "unknown"),
                    "interpretation": rsi_data.get("reason"),
                    "is_contributing": rsi_data.get("score", 0) > 0,
                }

            # EMA
            if "EMA" in confluence_details:
                ema_data = confluence_details["EMA"]
                ema_values = ema_data.get("values", {})
                structured["ema"] = {
                    "score": ema_data.get("score"),
                    "trending_up": ema_data.get("trending_up"),
                    "interpretation": ema_data.get("reason"),
                    "values": {
                        "ema_9": ema_values.get("ema_9"),
                        "ema_21": ema_values.get("ema_21"),
                        "ema_50": ema_values.get("ema_50"),
                    },
                    "price_position": {
                        "above_ema_50": ema_values.get("price_above_ema_50"),
                        "trend_alignment": "bullish"
                        if ema_data.get("trending_up")
                        else "bearish",
                    },
                    "is_contributing": ema_data.get("score", 0) > 0,
                }

            # MACD
            if "MACD" in confluence_details:
                macd_data = confluence_details["MACD"]
                macd_values = macd_data.get("values", {})
                structured["macd"] = {
                    "score": macd_data.get("score"),
                    "is_bullish": macd_data.get("is_bullish"),
                    "interpretation": macd_data.get("reason"),
                    "values": {
                        "macd_line": macd_values.get("macd_line"),
                        "signal_line": macd_values.get("signal_line"),
                        "histogram": macd_values.get("histogram"),
                    },
                    "crossover_type": macd_values.get("crossover"),
                    "momentum_strength": SignalDataBuilder._assess_macd_strength(
                        macd_values
                    ),
                    "is_contributing": macd_data.get("score", 0) > 0,
                }

            # Volume
            if "Volume" in confluence_details:
                volume_data = confluence_details["Volume"]
                volume_values = volume_data.get("values", {})
                structured["volume"] = {
                    "score": volume_data.get("score"),
                    "is_high_volume": volume_data.get("is_high_volume"),
                    "obv_trending_up": volume_data.get("obv_trending_up"),
                    "interpretation": volume_data.get("reason"),
                    "values": {
                        "volume_ratio": volume_values.get("volume_ratio"),
                        "volume_threshold": volume_values.get("volume_threshold"),
                        "obv": volume_values.get("obv"),
                        "vwap": volume_values.get("vwap"),
                    },
                    "price_vs_vwap": volume_values.get("price_vs_vwap"),
                    "volume_quality": SignalDataBuilder._assess_volume_quality(
                        volume_data
                    ),
                    "is_contributing": volume_data.get("score", 0) > 0,
                }

            return structured

        except Exception as e:
            logger.error(f"❌ Erro ao estruturar indicadores técnicos: {e}")
            return {}

    @staticmethod
    def _calculate_spread_pct(
        bid_price: Optional[float], ask_price: Optional[float]
    ) -> Optional[float]:
        """Calcula spread em % entre bid e ask"""
        try:
            if not bid_price or not ask_price or bid_price <= 0:
                return None

            spread = ask_price - bid_price
            spread_pct = (spread / bid_price) * 100
            return round(spread_pct, 4)
        except:
            return None

    @staticmethod
    def _assess_macd_strength(macd_values: Dict) -> str:
        """Avalia força do MACD baseado no histograma"""
        try:
            histogram = macd_values.get("histogram")
            if not histogram:
                return "unknown"

            abs_histogram = abs(float(histogram))
            if abs_histogram > 1.0:
                return "strong"
            elif abs_histogram > 0.3:
                return "moderate"
            else:
                return "weak"
        except:
            return "unknown"

    @staticmethod
    def _assess_volume_quality(volume_data: Dict) -> str:
        """Avalia qualidade do volume"""
        try:
            is_high = volume_data.get("is_high_volume", False)
            obv_up = volume_data.get("obv_trending_up", False)

            if is_high and obv_up:
                return "excellent"
            elif is_high or obv_up:
                return "good"
            else:
                return "poor"
        except:
            return "unknown"
