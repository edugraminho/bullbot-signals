"""
Sistema de Confluência de Indicadores
Combina RSI, EMA, MACD, Volume para gerar sinais mais precisos
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.models.crypto import RSILevels

from src.core.models.crypto import RSIData
from src.core.models.signals import SignalStrength, SignalType, TradingSignal
from src.core.services.ema_calculator import EMACalculator
from src.core.services.macd_calculator import MACDCalculator
from src.core.services.volume_analyzer import VolumeAnalyzer
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ConfluenceScore:
    """Pontuação de confluência de indicadores"""

    total_score: int
    max_possible_score: int
    signal_strength: SignalStrength
    details: Dict[str, Dict]  # Detalhes de cada indicador
    is_valid_signal: bool


@dataclass
class ConfluenceResult:
    """Resultado da análise de confluência"""

    signal: Optional[TradingSignal]
    confluence_score: ConfluenceScore
    recommendation: str
    risk_level: str
    current_price: float


class ConfluenceAnalyzer:
    """Analisador de confluência de indicadores técnicos"""

    def __init__(self):
        """Inicializa o analisador com configurações padrão"""
        from src.utils.config import settings

        self.config = settings

    def analyze_confluence(
        self,
        ohlcv_data: List[dict],
        rsi_data: RSIData,
        symbol: str = "UNKNOWN",
        timespan: str = "15m",
        custom_rsi_levels: Optional["RSILevels"] = None,
    ) -> ConfluenceResult:
        """
        Analisa confluência de todos os indicadores

        Args:
            ohlcv_data: Dados OHLCV para cálculo dos indicadores
            rsi_data: Dados RSI já calculados
            symbol: Símbolo do ativo
            timespan: Timeframe da análise

        Returns:
            ConfluenceResult com sinal e detalhes
        """
        try:
            logger.debug(f"Iniciando análise de confluência para {symbol} ({timespan})")

            # Calcular todos os indicadores
            ema_data = self._analyze_ema_signals(ohlcv_data, symbol, timespan)
            macd_data = self._analyze_macd_signals(ohlcv_data, symbol, timespan)
            volume_data = self._analyze_volume_signals(ohlcv_data, symbol, timespan)

            # Determinar tipo de sinal baseado no RSI
            signal_type = self._determine_signal_type(rsi_data, custom_rsi_levels)

            if signal_type is None:
                # RSI em zona neutra, não gerar sinal
                return self._create_neutral_result(rsi_data, symbol, timespan)

            # Calcular pontuação de confluência
            confluence_score = self._calculate_confluence_score(
                signal_type, rsi_data, ema_data, macd_data, volume_data, timespan
            )

            # Verificar se o sinal é válido baseado na pontuação mínima
            min_score = self._get_minimum_score(timespan)
            is_valid = confluence_score.total_score >= min_score

            if is_valid:
                # Criar sinal de trading
                signal = self._create_trading_signal(
                    signal_type, confluence_score, rsi_data, symbol, timespan
                )
                recommendation = self._generate_recommendation(
                    confluence_score, signal_type
                )
                risk_level = self._assess_risk_level(confluence_score)
            else:
                signal = None
                recommendation = f"Score insuficiente ({confluence_score.total_score}/{min_score}). Aguardar mais confirmação."
                risk_level = "MEDIO"

            return ConfluenceResult(
                signal=signal,
                confluence_score=confluence_score,
                recommendation=recommendation,
                risk_level=risk_level,
                current_price=float(rsi_data.current_price),
            )

        except Exception as e:
            logger.error(f"❌ Erro na análise de confluência para {symbol}: {e}")
            return self._create_error_result(rsi_data, symbol, timespan)

    def _analyze_ema_signals(
        self, ohlcv_data: List[dict], symbol: str, timespan: str
    ) -> Dict:
        """Analisa sinais das EMAs"""
        try:
            # Calcular múltiplas EMAs
            emas = EMACalculator.calculate_multiple_emas(
                ohlcv_data, symbol=symbol, timespan=timespan
            )

            ema_short = emas.get(self.config.ema_short_period)
            ema_medium = emas.get(self.config.ema_medium_period)
            ema_long = emas.get(self.config.ema_long_period)

            # Verificar tendência
            is_trending_up = EMACalculator.is_trending_up(ohlcv_data, symbol, timespan)

            return {
                "available": ema_short is not None and ema_medium is not None,
                "trending_up": is_trending_up,
                "ema_short": ema_short.value if ema_short else None,
                "ema_medium": ema_medium.value if ema_medium else None,
                "ema_long": ema_long.value if ema_long else None,
                "price_above_long": (
                    ema_long.current_price > ema_long.value if ema_long else False
                ),
            }
        except Exception as e:
            logger.error(f"❌ Erro ao analisar EMAs: {e}")
            return {"available": False, "trending_up": False}

    def _analyze_macd_signals(
        self, ohlcv_data: List[dict], symbol: str, timespan: str
    ) -> Dict:
        """Analisa sinais do MACD"""
        try:
            macd = MACDCalculator.get_latest_macd_with_config(
                ohlcv_data, symbol, timespan
            )
            is_bullish = MACDCalculator.is_bullish_crossover(
                ohlcv_data, symbol, timespan
            )

            return {
                "available": macd is not None,
                "is_bullish": is_bullish,
                "macd_line": macd.macd_line if macd else None,
                "signal_line": macd.signal_line if macd else None,
                "histogram": macd.histogram if macd else None,
            }
        except Exception as e:
            logger.error(f"❌ Erro ao analisar MACD: {e}")
            return {"available": False, "is_bullish": False}

    def _analyze_volume_signals(
        self, ohlcv_data: List[dict], symbol: str, timespan: str
    ) -> Dict:
        """Analisa sinais de volume"""
        try:
            volume = VolumeAnalyzer.get_latest_volume_with_config(
                ohlcv_data, symbol, timespan
            )
            is_high_volume = VolumeAnalyzer.is_high_volume(ohlcv_data, symbol, timespan)
            is_obv_up = VolumeAnalyzer.is_obv_trending_up(ohlcv_data, symbol, timespan)

            return {
                "available": volume is not None,
                "is_high_volume": is_high_volume,
                "is_obv_trending_up": is_obv_up,
                "volume_ratio": volume.volume_ratio if volume else None,
                "obv": volume.obv if volume else None,
                "vwap": volume.vwap if volume else None,
                "price_vs_vwap": (
                    "above"
                    if volume and volume.current_price > volume.vwap
                    else "below"
                    if volume
                    else "unknown"
                ),
            }
        except Exception as e:
            logger.error(f"❌ Erro ao analisar Volume: {e}")
            return {
                "available": False,
                "is_high_volume": False,
                "is_obv_trending_up": False,
            }

    def _determine_signal_type(
        self, rsi_data: RSIData, custom_rsi_levels: Optional["RSILevels"] = None
    ) -> Optional[SignalType]:
        """Determina o tipo de sinal baseado no RSI"""
        rsi_value = rsi_data.value

        # Usar níveis customizados se fornecidos, senão usar config padrão
        if custom_rsi_levels:
            oversold = custom_rsi_levels.oversold
            overbought = custom_rsi_levels.overbought
        else:
            oversold = self.config.rsi_oversold
            overbought = self.config.rsi_overbought

        if rsi_value <= oversold:
            return SignalType.BUY
        elif rsi_value >= overbought:
            return SignalType.SELL
        else:
            return None  # Zona neutra

    def _calculate_confluence_score(
        self,
        signal_type: SignalType,
        rsi_data: RSIData,
        ema_data: Dict,
        macd_data: Dict,
        volume_data: Dict,
        timespan: str,
    ) -> ConfluenceScore:
        """Calcula pontuação de confluência baseada nos indicadores"""
        score = 0
        max_score = 0
        details = {}

        # RSI Score (obrigatório)
        rsi_score = 2  # RSI em zona extrema sempre vale 2 pontos
        score += rsi_score
        max_score += 2
        # Obter níveis RSI do config
        from src.utils.config import settings

        details["RSI"] = {
            "score": rsi_score,
            "value": float(rsi_data.value),
            "reason": f"RSI {rsi_data.value} em zona de {'sobrevenda' if signal_type == SignalType.BUY else 'sobrecompra'}",
            "levels": {
                "oversold": settings.rsi_oversold,
                "overbought": settings.rsi_overbought,
                "current_zone": (
                    "oversold"
                    if rsi_data.value <= settings.rsi_oversold
                    else "overbought"
                    if rsi_data.value >= settings.rsi_overbought
                    else "neutral"
                ),
            },
        }

        # EMA Score
        ema_score = 0
        if ema_data["available"]:
            if signal_type == SignalType.BUY and ema_data["trending_up"]:
                ema_score += 2  # Tendência de alta para compra
            elif signal_type == SignalType.SELL and not ema_data["trending_up"]:
                ema_score += 2  # Tendência de baixa para venda

            if ema_data.get("price_above_long", False):
                ema_score += 1  # Preço acima da EMA longa (filtro adicional)

        score += ema_score
        max_score += 3
        details["EMA"] = {
            "score": ema_score,
            "trending_up": ema_data["trending_up"],
            "reason": f"EMA {'favoravel' if ema_score > 0 else 'desfavoravel'} ao sinal",
            "values": {
                "ema_9": float(ema_data["ema_short"])
                if ema_data["ema_short"]
                else None,
                "ema_21": float(ema_data["ema_medium"])
                if ema_data["ema_medium"]
                else None,
                "ema_50": float(ema_data["ema_long"]) if ema_data["ema_long"] else None,
                "price_above_ema_50": ema_data["price_above_long"],
            },
        }

        # MACD Score
        macd_score = 0
        if macd_data["available"]:
            if signal_type == SignalType.BUY and macd_data["is_bullish"]:
                macd_score = 1  # MACD bullish para compra
            elif signal_type == SignalType.SELL and not macd_data["is_bullish"]:
                macd_score = 1  # MACD bearish para venda

        score += macd_score
        max_score += 1
        details["MACD"] = {
            "score": macd_score,
            "is_bullish": macd_data["is_bullish"],
            "reason": f"MACD {'confirma' if macd_score > 0 else 'nao confirma'} o sinal",
            "values": {
                "macd_line": float(macd_data["macd_line"])
                if macd_data["macd_line"]
                else None,
                "signal_line": float(macd_data["signal_line"])
                if macd_data["signal_line"]
                else None,
                "histogram": float(macd_data["histogram"])
                if macd_data["histogram"]
                else None,
                "crossover": "bullish" if macd_data["is_bullish"] else "bearish",
            },
        }

        # Volume Score
        volume_score = 0
        if volume_data["available"]:
            if volume_data["is_high_volume"]:
                volume_score += 1  # Volume alto sempre é bom

            if signal_type == SignalType.BUY and volume_data["is_obv_trending_up"]:
                volume_score += 1  # OBV subindo para compra
            elif (
                signal_type == SignalType.SELL and not volume_data["is_obv_trending_up"]
            ):
                volume_score += 1  # OBV descendo para venda

        score += volume_score
        max_score += 2
        details["Volume"] = {
            "score": volume_score,
            "is_high_volume": volume_data["is_high_volume"],
            "obv_trending_up": volume_data["is_obv_trending_up"],
            "reason": f"Volume {'suporta' if volume_score > 0 else 'nao suporta'} o sinal",
            "values": {
                "volume_ratio": float(volume_data["volume_ratio"])
                if volume_data["volume_ratio"]
                else None,
                "obv": float(volume_data["obv"]) if volume_data["obv"] else None,
                "vwap": float(volume_data["vwap"]) if volume_data["vwap"] else None,
                "price_vs_vwap": volume_data["price_vs_vwap"],
                "volume_threshold": f"{int((volume_data['volume_ratio'] or 0) * 100)}%"
                if volume_data["volume_ratio"]
                else "N/A",
            },
        }

        # Determinar força do sinal
        score_percentage = (score / max_score) * 100
        if score_percentage >= 80:
            strength = SignalStrength.STRONG
        elif score_percentage >= 60:
            strength = SignalStrength.MODERATE
        else:
            strength = SignalStrength.WEAK

        return ConfluenceScore(
            total_score=score,
            max_possible_score=max_score,
            signal_strength=strength,
            details=details,
            is_valid_signal=score >= self._get_minimum_score(timespan),
        )

    def _get_minimum_score(self, timespan: str) -> int:
        """Obter pontuação mínima necessária para o timeframe"""
        timeframe_scores = {
            "15m": self.config.confluence_min_score_15m,
            "1h": self.config.confluence_min_score_1h,
            "4h": self.config.confluence_min_score_4h,
            "1d": self.config.confluence_min_score_1d,
        }
        return timeframe_scores.get(timespan, 4)  # Default 4

    def _create_trading_signal(
        self,
        signal_type: SignalType,
        confluence_score: ConfluenceScore,
        rsi_data: RSIData,
        symbol: str,
        timespan: str,
    ) -> TradingSignal:
        """Cria sinal de trading com base na confluência"""
        action = "COMPRA" if signal_type == SignalType.BUY else "VENDA"
        message = f"Sinal de {action} {confluence_score.signal_strength.value.upper()} - Score: {confluence_score.total_score}/{confluence_score.max_possible_score}"

        return TradingSignal(
            symbol=symbol,
            signal_type=signal_type,
            strength=confluence_score.signal_strength,
            rsi_value=rsi_data.value,  # Mantido para compatibilidade
            timestamp=rsi_data.timestamp,
            timeframe=timespan,
            price=rsi_data.current_price,  # Preço atual da moeda
            message=message,
        )

    def _generate_recommendation(
        self, confluence_score: ConfluenceScore, signal_type: SignalType
    ) -> str:
        """Gera recomendação textual baseada na confluência"""
        action = "COMPRA" if signal_type == SignalType.BUY else "VENDA"
        strength_text = {
            SignalStrength.STRONG: "FORTE",
            SignalStrength.MODERATE: "MODERADO",
            SignalStrength.WEAK: "FRACO",
        }

        return f"Sinal de {action} {strength_text[confluence_score.signal_strength]} - Score: {confluence_score.total_score}/{confluence_score.max_possible_score}"

    def _assess_risk_level(self, confluence_score: ConfluenceScore) -> str:
        """Avalia nível de risco baseado na confluência"""
        score_percentage = (
            confluence_score.total_score / confluence_score.max_possible_score
        ) * 100

        if score_percentage >= 80:
            return "BAIXO"
        elif score_percentage >= 60:
            return "MEDIO"
        else:
            return "ALTO"

    def _create_neutral_result(
        self, rsi_data: RSIData, symbol: str = "", timespan: str = ""
    ) -> ConfluenceResult:
        """Cria resultado neutro quando RSI está em zona neutra"""
        confluence_score = ConfluenceScore(
            total_score=0,
            max_possible_score=8,
            signal_strength=SignalStrength.WEAK,
            details={"RSI": {"reason": f"RSI {rsi_data.value} em zona neutra"}},
            is_valid_signal=False,
        )

        return ConfluenceResult(
            signal=None,
            confluence_score=confluence_score,
            recommendation="RSI em zona neutra. Aguardar entrada em zona extrema.",
            risk_level="BAIXO",
            current_price=float(rsi_data.current_price),
        )

    def _create_error_result(
        self, rsi_data: RSIData, symbol: str = "", timespan: str = ""
    ) -> ConfluenceResult:
        """Cria resultado de erro"""
        confluence_score = ConfluenceScore(
            total_score=0,
            max_possible_score=8,
            signal_strength=SignalStrength.WEAK,
            details={"ERROR": {"reason": "Erro no calculo de confluencia"}},
            is_valid_signal=False,
        )

        return ConfluenceResult(
            signal=None,
            confluence_score=confluence_score,
            recommendation="Erro na analise. Verificar dados.",
            risk_level="ALTO",
            current_price=float(rsi_data.current_price),
        )
