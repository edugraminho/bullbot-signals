"""
Sistema de filtros para sinais - Anti-spam e cooldown
"""

import os
import time
from datetime import datetime, timedelta
from typing import Optional
import redis
from src.core.models.signals import SignalStrength, SignalType
from src.core.services.rsi_service import RSIAnalysis
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SignalFilter:
    """Sistema de filtros anti-spam para sinais"""

    def __init__(self):
        self.redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "redis"),
            port=os.getenv("REDIS_PORT", 6388),
            db=2,
        )

        # Configurações de cooldown dinâmicas por timeframe e força do sinal (em segundos)
        self.cooldown_rules = {
            "15m": {
                SignalStrength.STRONG: 15 * 60,  # 15 minutos
                SignalStrength.MODERATE: 30 * 60,  # 30 minutos
                SignalStrength.WEAK: 60 * 60,  # 1 hora
            },
            "1h": {
                SignalStrength.STRONG: 60 * 60,  # 1 hora
                SignalStrength.MODERATE: 2 * 3600,  # 2 horas
                SignalStrength.WEAK: 4 * 3600,  # 4 horas
            },
            "4h": {
                SignalStrength.STRONG: 2 * 3600,  # 2 horas
                SignalStrength.MODERATE: 4 * 3600,  # 4 horas
                SignalStrength.WEAK: 6 * 3600,  # 6 horas
            },
            "1d": {
                SignalStrength.STRONG: 6 * 3600,  # 6 horas
                SignalStrength.MODERATE: 12 * 3600,  # 12 horas
                SignalStrength.WEAK: 24 * 3600,  # 24 horas
            },
        }

        # Limites diários por símbolo
        self.daily_limits = {
            "max_signals_per_symbol": 3,
            "max_strong_signals": 2,
        }

    def _get_cooldown_duration(self, timeframe: str, strength: SignalStrength) -> int:
        """
        Obtém a duração do cooldown baseada no timeframe e força do sinal

        Args:
            timeframe: Timeframe do sinal (15m, 1h, 4h, 1d)
            strength: Força do sinal

        Returns:
            Duração do cooldown em segundos
        """
        # Se o timeframe não está configurado, usar proporção baseada no 4h
        if timeframe not in self.cooldown_rules:
            # Calcular proporção baseada no 4h como referência
            base_cooldowns = self.cooldown_rules["4h"]
            timeframe_minutes = self._timeframe_to_minutes(timeframe)
            base_minutes = 4 * 60  # 4h em minutos

            # Proporção = timeframe_atual / timeframe_base
            ratio = timeframe_minutes / base_minutes

            return int(base_cooldowns[strength] * ratio)

        return self.cooldown_rules[timeframe][strength]

    def _timeframe_to_minutes(self, timeframe: str) -> int:
        """
        Converte timeframe para minutos

        Args:
            timeframe: Timeframe (15m, 1h, 4h, 1d, etc)

        Returns:
            Minutos equivalentes
        """
        timeframe = timeframe.lower()
        if timeframe.endswith("m"):
            return int(timeframe[:-1])
        elif timeframe.endswith("h"):
            return int(timeframe[:-1]) * 60
        elif timeframe.endswith("d"):
            return int(timeframe[:-1]) * 24 * 60
        else:
            # Fallback para 4h se não reconhecer
            return 4 * 60

    async def should_send_signal(self, symbol: str, analysis: RSIAnalysis) -> bool:
        """
        Determina se o sinal deve ser enviado baseado nos filtros

        Args:
            symbol: Símbolo da crypto
            analysis: Análise RSI com sinal

        Returns:
            True se deve enviar, False caso contrário
        """
        try:
            # 1. Verificar cooldown básico
            if await self._is_in_cooldown(
                symbol, analysis.signal.timeframe, analysis.signal.strength
            ):
                logger.info(f"Sinal {symbol} em cooldown")
                return False

            # 2. Verificar se sinal é mais forte que o anterior
            if not await self._is_stronger_signal(symbol, analysis):
                logger.info(f"Sinal {symbol} não é mais forte que o anterior")
                return False

            # 3. Verificar limites diários
            if await self._exceeded_daily_limits(symbol, analysis.signal.strength):
                logger.info(f"Limites diários excedidos para {symbol}")
                return False

            logger.info(
                f"Sinal aprovado para {symbol}: {analysis.signal.signal_type.value}"
            )
            return True

        except Exception as e:
            logger.error(f"Erro no filtro de sinais para {symbol}: {e}")
            # Em caso de erro, bloquear sinal por segurança
            return False

    async def _is_in_cooldown(
        self, symbol: str, timeframe: str, strength: SignalStrength
    ) -> bool:
        """Verifica se está em período de cooldown"""
        key = f"cooldown:{symbol}:{timeframe}"

        try:
            last_signal_time = self.redis_client.get(key)
            if not last_signal_time:
                return False

            last_time = float(last_signal_time)
            cooldown_duration = self._get_cooldown_duration(timeframe, strength)

            return (time.time() - last_time) < cooldown_duration

        except Exception as e:
            logger.error(f"Erro ao verificar cooldown: {e}")
            return True  # Em caso de erro, assumir que está em cooldown

    async def _is_stronger_signal(self, symbol: str, analysis: RSIAnalysis) -> bool:
        """Verifica se o sinal atual é mais forte que o último enviado"""
        key = f"last_rsi:{symbol}:{analysis.signal.timeframe}"

        try:
            last_rsi = self.redis_client.get(key)
            if not last_rsi:
                return True  # Primeiro sinal sempre é válido

            last_rsi_value = float(last_rsi)
            current_rsi = analysis.rsi_data.value

            # Para sinais de compra: RSI deve estar mais baixo (mais oversold)
            if analysis.signal.signal_type in [SignalType.BUY, SignalType.STRONG_BUY]:
                return (
                    current_rsi < last_rsi_value - 2.0
                )  # Pelo menos 2 pontos de diferença

            # Para sinais de venda: RSI deve estar mais alto (mais overbought)
            elif analysis.signal.signal_type in [
                SignalType.SELL,
                SignalType.STRONG_SELL,
            ]:
                return (
                    current_rsi > last_rsi_value + 2.0
                )  # Pelo menos 2 pontos de diferença

            return False  # HOLD não precisa ser enviado

        except Exception as e:
            logger.error(f"Erro ao verificar força do sinal: {e}")
            return False

    async def _exceeded_daily_limits(
        self, symbol: str, strength: SignalStrength
    ) -> bool:
        """Verifica se excedeu limites diários"""
        today = datetime.now().strftime("%Y-%m-%d")

        try:
            # Verificar total de sinais do símbolo hoje
            total_key = f"daily_count:{symbol}:{today}"
            total_signals = self.redis_client.get(total_key)
            total_signals = int(total_signals) if total_signals else 0

            if total_signals >= self.daily_limits["max_signals_per_symbol"]:
                return True

            # Verificar sinais STRONG hoje
            if strength == SignalStrength.STRONG:
                strong_key = f"daily_strong:{symbol}:{today}"
                strong_signals = self.redis_client.get(strong_key)
                strong_signals = int(strong_signals) if strong_signals else 0

                if strong_signals >= self.daily_limits["max_strong_signals"]:
                    return True

            return False

        except Exception as e:
            logger.error(f"Erro ao verificar limites diários: {e}")
            return True  # Em caso de erro, assumir que excedeu

    async def mark_signal_sent(self, symbol: str, analysis: RSIAnalysis):
        """Marca que o sinal foi enviado - atualiza contadores"""

        timeframe = analysis.signal.timeframe
        strength = analysis.signal.strength
        rsi_value = analysis.rsi_data.value
        today = datetime.now().strftime("%Y-%m-%d")

        try:
            # Atualizar cooldown
            cooldown_key = f"cooldown:{symbol}:{timeframe}"
            cooldown_duration = self._get_cooldown_duration(timeframe, strength)
            self.redis_client.setex(cooldown_key, cooldown_duration, time.time())

            # Atualizar último RSI
            rsi_key = f"last_rsi:{symbol}:{timeframe}"
            self.redis_client.setex(rsi_key, 86400, rsi_value)  # 24 horas

            # Atualizar contadores diários
            total_key = f"daily_count:{symbol}:{today}"
            self.redis_client.incr(total_key)
            self.redis_client.expire(total_key, 86400)  # Expira em 24h

            if strength == SignalStrength.STRONG:
                strong_key = f"daily_strong:{symbol}:{today}"
                self.redis_client.incr(strong_key)
                self.redis_client.expire(strong_key, 86400)

            logger.info(f"Contadores atualizados para {symbol}")

        except Exception as e:
            logger.error(f"Erro ao marcar sinal enviado: {e}")

    async def get_signal_stats(self, symbol: str) -> dict:
        """Obter estatísticas de sinais para um símbolo"""

        today = datetime.now().strftime("%Y-%m-%d")

        try:
            total_key = f"daily_count:{symbol}:{today}"
            strong_key = f"daily_strong:{symbol}:{today}"

            total_today = self.redis_client.get(total_key)
            strong_today = self.redis_client.get(strong_key)

            return {
                "symbol": symbol,
                "total_today": int(total_today) if total_today else 0,
                "strong_today": int(strong_today) if strong_today else 0,
                "remaining_total": max(
                    0,
                    self.daily_limits["max_signals_per_symbol"]
                    - (int(total_today) if total_today else 0),
                ),
                "remaining_strong": max(
                    0,
                    self.daily_limits["max_strong_signals"]
                    - (int(strong_today) if strong_today else 0),
                ),
            }

        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return {"symbol": symbol, "error": str(e)}


# Instância global
signal_filter = SignalFilter()
