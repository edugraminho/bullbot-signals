"""
Serviço para cálculo de recomendações de trading
Calcula stop loss, take profit, risk/reward ratio e qualidade do sinal
"""

from typing import Dict, Optional
from decimal import Decimal

from src.core.models.signals import SignalType, SignalStrength
from src.utils.logger import get_logger

logger = get_logger(__name__)


class TradingRecommendations:
    """Calculador de recomendações de trading baseado em análise técnica"""

    @staticmethod
    def calculate_recommendations(
        signal_type: SignalType,
        signal_strength: SignalStrength,
        current_price: float,
        confluence_details: Dict,
        timeframe: str = "15m",
        market_context: Optional[Dict] = None,
    ) -> Dict:
        """
        Calcula recomendações completas de trading

        Args:
            signal_type: Tipo do sinal (BUY/SELL)
            signal_strength: Força do sinal (WEAK/MODERATE/STRONG)
            current_price: Preço atual da moeda
            confluence_details: Detalhes dos indicadores de confluência
            timeframe: Timeframe do sinal
            market_context: Contexto adicional do mercado

        Returns:
            Dict com recomendações completas de trading
        """
        try:
            logger.debug(
                f"Calculando recomendações para {signal_type.value} {signal_strength.value}"
            )

            # Obter dados dos indicadores
            ema_data = confluence_details.get("EMA", {})
            rsi_data = confluence_details.get("RSI", {})
            market_context = market_context or {}

            # Calcular stop loss baseado em EMA e volatilidade
            stop_loss = TradingRecommendations._calculate_stop_loss(
                signal_type, current_price, ema_data, market_context
            )

            # Calcular take profit baseado na força do sinal e contexto
            take_profit = TradingRecommendations._calculate_take_profit(
                signal_type, signal_strength, current_price, timeframe, market_context
            )

            # Calcular risk/reward ratio
            risk_reward_ratio = TradingRecommendations._calculate_risk_reward(
                signal_type, current_price, stop_loss, take_profit
            )

            # Calcular tamanho de posição sugerido
            position_size = TradingRecommendations._suggest_position_size(
                signal_strength, risk_reward_ratio, market_context
            )

            # Determinar qualidade geral do sinal
            signal_quality = TradingRecommendations._assess_signal_quality(
                signal_strength, risk_reward_ratio, confluence_details, market_context
            )

            recommendations = {
                "entry_price": round(current_price, 6),
                "stop_loss": round(stop_loss, 6) if stop_loss else None,
                "take_profit": round(take_profit, 6) if take_profit else None,
                "risk_reward_ratio": round(risk_reward_ratio, 2)
                if risk_reward_ratio
                else None,
                "position_size_pct": position_size,
                "signal_quality": signal_quality,
                "timeframe": timeframe,
                "strategy_notes": TradingRecommendations._generate_strategy_notes(
                    signal_type, signal_strength, timeframe, confluence_details
                ),
            }

            logger.debug(f"Recomendações calculadas: {recommendations}")
            return recommendations

        except Exception as e:
            logger.error(f"❌ Erro ao calcular recomendações de trading: {e}")
            return {
                "entry_price": current_price,
                "stop_loss": None,
                "take_profit": None,
                "risk_reward_ratio": None,
                "position_size_pct": 1.0,
                "signal_quality": "POOR",
                "timeframe": timeframe,
                "strategy_notes": "Erro no cálculo de recomendações",
            }

    @staticmethod
    def _calculate_stop_loss(
        signal_type: SignalType,
        current_price: float,
        ema_data: Dict,
        market_context: Dict,
    ) -> Optional[float]:
        """Calcula stop loss baseado em EMAs e volatilidade"""
        try:
            volatility = market_context.get("volatility_pct", 3.0)

            # Stop loss baseado em EMA
            if signal_type == SignalType.BUY:
                # Para compra: stop abaixo da EMA21 ou EMA50
                ema_21 = ema_data.get("values", {}).get("ema_21")
                ema_50 = ema_data.get("values", {}).get("ema_50")

                if ema_21:
                    # Stop 1-3% abaixo da EMA21, ajustado pela volatilidade
                    stop_pct = max(1.0, min(3.0, volatility * 0.6))
                    stop_loss = float(ema_21) * (1 - stop_pct / 100)
                elif ema_50:
                    stop_pct = max(2.0, min(4.0, volatility * 0.8))
                    stop_loss = float(ema_50) * (1 - stop_pct / 100)
                else:
                    # Fallback: 2-5% abaixo do preço atual
                    stop_pct = max(2.0, min(5.0, volatility))
                    stop_loss = current_price * (1 - stop_pct / 100)

            else:  # SELL
                # Para venda: stop acima da EMA21 ou EMA50
                ema_21 = ema_data.get("values", {}).get("ema_21")
                ema_50 = ema_data.get("values", {}).get("ema_50")

                if ema_21:
                    stop_pct = max(1.0, min(3.0, volatility * 0.6))
                    stop_loss = float(ema_21) * (1 + stop_pct / 100)
                elif ema_50:
                    stop_pct = max(2.0, min(4.0, volatility * 0.8))
                    stop_loss = float(ema_50) * (1 + stop_pct / 100)
                else:
                    stop_pct = max(2.0, min(5.0, volatility))
                    stop_loss = current_price * (1 + stop_pct / 100)

            return stop_loss

        except Exception as e:
            logger.error(f"❌ Erro ao calcular stop loss: {e}")
            # Fallback conservador
            if signal_type == SignalType.BUY:
                return current_price * 0.97  # 3% abaixo
            else:
                return current_price * 1.03  # 3% acima

    @staticmethod
    def _calculate_take_profit(
        signal_type: SignalType,
        signal_strength: SignalStrength,
        current_price: float,
        timeframe: str,
        market_context: Dict,
    ) -> Optional[float]:
        """Calcula take profit baseado na força do sinal e timeframe"""
        try:
            # Targets baseados na força do sinal
            strength_multipliers = {
                SignalStrength.WEAK: 1.0,
                SignalStrength.MODERATE: 1.5,
                SignalStrength.STRONG: 2.0,
            }

            # Targets baseados no timeframe
            timeframe_targets = {
                "15m": 2.0,  # 2% para scalping
                "1h": 4.0,  # 4% para swing curto
                "4h": 6.0,  # 6% para swing médio
                "1d": 10.0,  # 10% para posição
            }

            base_target = timeframe_targets.get(timeframe, 3.0)
            strength_mult = strength_multipliers.get(signal_strength, 1.0)

            # Ajustar pela volatilidade
            volatility = market_context.get("volatility_pct", 3.0)
            volatility_mult = max(0.5, min(2.0, volatility / 3.0))

            final_target_pct = base_target * strength_mult * volatility_mult

            if signal_type == SignalType.BUY:
                take_profit = current_price * (1 + final_target_pct / 100)
            else:  # SELL
                take_profit = current_price * (1 - final_target_pct / 100)

            return take_profit

        except Exception as e:
            logger.error(f"❌ Erro ao calcular take profit: {e}")
            # Fallback
            if signal_type == SignalType.BUY:
                return current_price * 1.04  # 4% acima
            else:
                return current_price * 0.96  # 4% abaixo

    @staticmethod
    def _calculate_risk_reward(
        signal_type: SignalType,
        current_price: float,
        stop_loss: Optional[float],
        take_profit: Optional[float],
    ) -> Optional[float]:
        """Calcula ratio risco/retorno"""
        try:
            if not stop_loss or not take_profit:
                return None

            if signal_type == SignalType.BUY:
                risk = current_price - stop_loss
                reward = take_profit - current_price
            else:  # SELL
                risk = stop_loss - current_price
                reward = current_price - take_profit

            if risk <= 0:
                return None

            return reward / risk

        except Exception as e:
            logger.error(f"❌ Erro ao calcular risk/reward: {e}")
            return None

    @staticmethod
    def _suggest_position_size(
        signal_strength: SignalStrength,
        risk_reward_ratio: Optional[float],
        market_context: Dict,
    ) -> float:
        """Sugere tamanho de posição como % do capital"""
        try:
            # Tamanho base por força do sinal
            base_sizes = {
                SignalStrength.WEAK: 1.0,  # 1% do capital
                SignalStrength.MODERATE: 2.0,  # 2% do capital
                SignalStrength.STRONG: 3.0,  # 3% do capital
            }

            base_size = base_sizes.get(signal_strength, 1.0)

            # Ajustar pelo risk/reward
            if risk_reward_ratio:
                if risk_reward_ratio >= 3.0:
                    base_size *= 1.2  # Aumentar para RR excelente
                elif risk_reward_ratio < 1.5:
                    base_size *= 0.7  # Diminuir para RR ruim

            # Ajustar pela volatilidade
            volatility = market_context.get("volatility_pct", 3.0)
            if volatility > 8.0:
                base_size *= 0.5  # Reduzir em alta volatilidade
            elif volatility < 2.0:
                base_size *= 1.2  # Aumentar em baixa volatilidade

            return round(max(0.5, min(5.0, base_size)), 1)

        except Exception as e:
            logger.error(f"❌ Erro ao calcular tamanho de posição: {e}")
            return 1.0

    @staticmethod
    def _assess_signal_quality(
        signal_strength: SignalStrength,
        risk_reward_ratio: Optional[float],
        confluence_details: Dict,
        market_context: Dict,
    ) -> str:
        """Avalia qualidade geral do sinal"""
        try:
            score = 0

            # Pontos por força do sinal
            strength_points = {
                SignalStrength.WEAK: 1,
                SignalStrength.MODERATE: 2,
                SignalStrength.STRONG: 3,
            }
            score += strength_points.get(signal_strength, 1)

            # Pontos por risk/reward
            if risk_reward_ratio:
                if risk_reward_ratio >= 3.0:
                    score += 3
                elif risk_reward_ratio >= 2.0:
                    score += 2
                elif risk_reward_ratio >= 1.5:
                    score += 1

            # Pontos por confluência (quantos indicadores confirmam)
            confirming_indicators = sum(
                1
                for indicator, data in confluence_details.items()
                if data.get("score", 0) > 0
            )
            score += min(2, confirming_indicators - 1)  # Máximo 2 pontos

            # Avaliar qualidade final
            if score >= 7:
                return "EXCELLENT"
            elif score >= 5:
                return "GOOD"
            elif score >= 3:
                return "FAIR"
            else:
                return "POOR"

        except Exception as e:
            logger.error(f"❌ Erro ao avaliar qualidade do sinal: {e}")
            return "FAIR"

    @staticmethod
    def _generate_strategy_notes(
        signal_type: SignalType,
        signal_strength: SignalStrength,
        timeframe: str,
        confluence_details: Dict,
    ) -> str:
        """Gera notas estratégicas sobre o sinal"""
        try:
            action = "COMPRA" if signal_type == SignalType.BUY else "VENDA"

            # Identificar indicadores que confirmam
            confirming = []
            if confluence_details.get("RSI", {}).get("score", 0) > 0:
                confirming.append("RSI")
            if confluence_details.get("EMA", {}).get("score", 0) > 0:
                confirming.append("EMA")
            if confluence_details.get("MACD", {}).get("score", 0) > 0:
                confirming.append("MACD")
            if confluence_details.get("Volume", {}).get("score", 0) > 0:
                confirming.append("Volume")

            notes_parts = [
                f"Sinal de {action} {signal_strength.value.upper()} no timeframe {timeframe}.",
                f"Confirmado por: {', '.join(confirming) if confirming else 'apenas RSI'}.",
            ]

            # Adicionar dicas por timeframe
            if timeframe == "15m":
                notes_parts.append("Adequado para scalping. Monitore de perto.")
            elif timeframe in ["1h", "4h"]:
                notes_parts.append("Adequado para swing trading.")
            elif timeframe == "1d":
                notes_parts.append("Sinal de posição de longo prazo.")

            return " ".join(notes_parts)

        except Exception as e:
            logger.error(f"❌ Erro ao gerar notas estratégicas: {e}")
            return "Sinal detectado. Verificar manualmente antes de operar."
