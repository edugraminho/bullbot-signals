"""
Sistema de filtros para sinais - Anti-spam e cooldown
"""

import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import redis

from src.core.models.signals import SignalStrength, SignalType
from src.utils.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SignalFilter:
    """Sistema de filtros anti-spam para sinais"""

    def __init__(self):
        self.redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "redis"),
            port=os.getenv("REDIS_PORT", 6379),
            db=2,
        )

        # Configurações PADRÃO de cooldown (carregadas do config.py como FALLBACK)
        self.default_cooldown_rules = {
            "15m": {
                SignalStrength.STRONG: settings.signal_filter_cooldown_15m_strong * 60,
                SignalStrength.MODERATE: settings.signal_filter_cooldown_15m_moderate
                * 60,
                SignalStrength.WEAK: settings.signal_filter_cooldown_15m_weak * 60,
            },
            "1h": {
                SignalStrength.STRONG: settings.signal_filter_cooldown_1h_strong * 60,
                SignalStrength.MODERATE: settings.signal_filter_cooldown_1h_moderate
                * 60,
                SignalStrength.WEAK: settings.signal_filter_cooldown_1h_weak * 60,
            },
            "4h": {
                SignalStrength.STRONG: settings.signal_filter_cooldown_4h_strong * 60,
                SignalStrength.MODERATE: settings.signal_filter_cooldown_4h_moderate
                * 60,
                SignalStrength.WEAK: settings.signal_filter_cooldown_4h_weak * 60,
            },
            "1d": {
                SignalStrength.STRONG: settings.signal_filter_cooldown_1d_strong * 60,
                SignalStrength.MODERATE: settings.signal_filter_cooldown_1d_moderate
                * 60,
                SignalStrength.WEAK: settings.signal_filter_cooldown_1d_weak * 60,
            },
        }

        # Limites diários PADRÃO (carregados do config.py como FALLBACK)
        self.default_daily_limits = {
            "max_signals_per_symbol": settings.signal_filter_max_signals_per_symbol,
            "max_strong_signals": settings.signal_filter_max_strong_signals,
            "min_rsi_difference": settings.signal_filter_min_rsi_difference,
        }

        logger.info("🔧 SignalFilter iniciado com configurações do config.py")
        logger.debug(
            f"Cooldown padrão 15m: {settings.signal_filter_cooldown_15m_strong}min (STRONG)"
        )
        logger.debug(
            f"Limites diários: {settings.signal_filter_max_signals_per_symbol} sinais/símbolo/dia"
        )

    def _get_user_filter_configs(
        self, user_configs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Agregar configurações de filtro de múltiplos usuários

        Args:
            user_configs: Lista de filter_config de usuários

        Returns:
            Configuração agregada mais restritiva
        """
        if not user_configs:
            return {}

        aggregated = {
            "cooldown_minutes": {},
            "max_signals_per_day": 999,  # Usar o menor limite
            "min_rsi_difference": 0.0,  # Usar o menor limite
        }

        for config in user_configs:
            if not config or not isinstance(config, dict):
                continue

            # Agregar cooldown_minutes (usar o menor valor = mais restritivo)
            cooldown_config = config.get("cooldown_minutes", {})
            if isinstance(cooldown_config, dict):
                for timeframe, values in cooldown_config.items():
                    if timeframe not in aggregated["cooldown_minutes"]:
                        aggregated["cooldown_minutes"][timeframe] = {}

                    if isinstance(values, dict):
                        for strength, minutes in values.items():
                            current = aggregated["cooldown_minutes"][timeframe].get(
                                strength, 999999
                            )
                            aggregated["cooldown_minutes"][timeframe][strength] = min(
                                current, minutes
                            )
            elif isinstance(cooldown_config, (int, float)):
                # Cooldown simples aplicado a todos os timeframes
                simple_cooldown = int(cooldown_config)
                for tf in ["15m", "1h", "4h", "1d"]:
                    if tf not in aggregated["cooldown_minutes"]:
                        aggregated["cooldown_minutes"][tf] = {}
                    for strength in ["strong", "moderate", "weak"]:
                        current = aggregated["cooldown_minutes"][tf].get(
                            strength, 999999
                        )
                        aggregated["cooldown_minutes"][tf][strength] = min(
                            current, simple_cooldown
                        )

            # Agregar max_signals_per_day (usar o menor)
            max_signals = config.get("max_signals_per_day", 999)
            if isinstance(max_signals, (int, float)):
                aggregated["max_signals_per_day"] = min(
                    aggregated["max_signals_per_day"], int(max_signals)
                )

            # Agregar min_rsi_difference (usar o menor)
            min_diff = config.get("min_rsi_difference", 0.0)
            if isinstance(min_diff, (int, float)):
                aggregated["min_rsi_difference"] = min(
                    aggregated["min_rsi_difference"], float(min_diff)
                )

        return aggregated

    def _get_cooldown_duration(
        self,
        timeframe: str,
        strength: SignalStrength,
        user_filter_config: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Obtém a duração do cooldown baseada no timeframe e força do sinal

        Args:
            timeframe: Timeframe do sinal (15m, 1h, 4h, 1d)
            strength: Força do sinal
            user_filter_config: Configuração de filtro agregada dos usuários

        Returns:
            Duração do cooldown em segundos
        """
        # Tentar usar configuração de usuários primeiro
        if user_filter_config and "cooldown_minutes" in user_filter_config:
            cooldown_config = user_filter_config["cooldown_minutes"]

            if timeframe in cooldown_config:
                strength_str = strength.value.lower()
                if strength_str in cooldown_config[timeframe]:
                    minutes = cooldown_config[timeframe][strength_str]
                    logger.debug(
                        f"Usando cooldown personalizado: {timeframe}/{strength_str} = {minutes}min"
                    )
                    return int(minutes * 60)  # Converter para segundos

        # Fallback para configurações padrão
        if timeframe not in self.default_cooldown_rules:
            # Calcular proporção baseada no 4h como referência
            base_cooldowns = self.default_cooldown_rules["4h"]
            timeframe_minutes = self._timeframe_to_minutes(timeframe)
            base_minutes = 4 * 60  # 4h em minutos

            ratio = timeframe_minutes / base_minutes
            duration = int(base_cooldowns[strength] * ratio)
            logger.debug(
                f"Usando cooldown proporcional: {timeframe}/{strength.value} = {duration}s"
            )
            return duration

        duration = self.default_cooldown_rules[timeframe][strength]
        logger.debug(
            f"Usando cooldown padrão: {timeframe}/{strength.value} = {duration}s"
        )
        return duration

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

    async def should_send_signal(
        self,
        symbol: str,
        analysis_or_confluence,  # Aceita RSIAnalysis ou ConfluenceResult
        user_filter_configs: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        """
        Determina se o sinal deve ser enviado baseado nos filtros

        Args:
            symbol: Símbolo da crypto
            analysis_or_confluence: RSIAnalysis ou ConfluenceResult com sinal
            user_filter_configs: Lista de filter_config dos usuários ativos

        Returns:
            True se deve enviar, False caso contrário
        """
        try:
            # Detectar tipo e extrair informações necessárias
            if hasattr(analysis_or_confluence, "signal") and hasattr(
                analysis_or_confluence, "confluence_score"
            ):
                # É ConfluenceResult
                signal = analysis_or_confluence.signal
                rsi_value = signal.rsi_value if signal else 0
                timeframe = signal.timeframe if signal else "15m"
                strength = signal.strength if signal else SignalStrength.WEAK
                signal_type = signal.signal_type if signal else SignalType.BUY
            elif hasattr(analysis_or_confluence, "signal") and hasattr(
                analysis_or_confluence, "rsi_data"
            ):
                # É RSIAnalysis (legacy)
                signal = analysis_or_confluence.signal
                rsi_value = analysis_or_confluence.rsi_data.value
                timeframe = signal.timeframe
                strength = signal.strength
                signal_type = signal.signal_type
            else:
                logger.error(f"Tipo de análise não reconhecido para {symbol}")
                return False

            if not signal:
                logger.debug(f"Nenhum sinal gerado para {symbol}")
                return False

            # Agregar configurações de filtro dos usuários
            aggregated_filter_config = self._get_user_filter_configs(
                user_filter_configs or []
            )

            if aggregated_filter_config:
                logger.debug(f"Usando filtros personalizados para {symbol}")
            else:
                logger.debug(f"Usando filtros padrão para {symbol}")

            # 1. Verificar cooldown básico
            if await self._is_in_cooldown(
                symbol,
                timeframe,
                strength,
                aggregated_filter_config,
            ):
                logger.debug(f"Sinal {symbol} em cooldown")
                return False

            # 2. Verificar se sinal é mais forte que o anterior
            if not await self._is_stronger_signal_generic(
                symbol, rsi_value, signal_type, timeframe, aggregated_filter_config
            ):
                logger.debug(f"Sinal {symbol} não é mais forte que o anterior")
                return False

            # 3. Verificar limites diários
            if await self._exceeded_daily_limits(
                symbol, strength, aggregated_filter_config
            ):
                logger.debug(f"🚫 Limites diários excedidos para {symbol}")
                return False

            logger.info(
                f"Sinal aprovado para {symbol}: {signal_type.value} (RSI: {rsi_value:.2f})"
            )
            return True

        except Exception as e:
            logger.error(f"❌ Erro no filtro de sinais para {symbol}: {e}")
            # Em caso de erro, bloquear sinal por segurança
            return False

    async def _is_in_cooldown(
        self,
        symbol: str,
        timeframe: str,
        strength: SignalStrength,
        user_filter_config: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Verifica se está em período de cooldown"""
        key = f"cooldown:{symbol}:{timeframe}"

        try:
            last_signal_time = self.redis_client.get(key)
            if not last_signal_time:
                return False

            last_time = float(last_signal_time)
            cooldown_duration = self._get_cooldown_duration(
                timeframe, strength, user_filter_config
            )

            is_in_cooldown = (time.time() - last_time) < cooldown_duration
            if is_in_cooldown:
                remaining = cooldown_duration - (time.time() - last_time)
                logger.debug(
                    f"{symbol} em cooldown por mais {remaining / 60:.1f} minutos"
                )

            return is_in_cooldown

        except Exception as e:
            logger.error(f"❌ Erro ao verificar cooldown: {e}")
            return True  # Em caso de erro, assumir que está em cooldown

    async def _is_stronger_signal_generic(
        self,
        symbol: str,
        current_rsi: float,
        signal_type: SignalType,
        timeframe: str,
        user_filter_config: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Verifica se o sinal atual é mais forte que o último enviado (versão genérica)"""
        key = f"last_rsi:{symbol}:{timeframe}"

        try:
            last_rsi = self.redis_client.get(key)
            if not last_rsi:
                return True  # Primeiro sinal sempre é válido

            last_rsi_value = float(last_rsi)

            # Usar min_rsi_difference personalizado ou padrão
            min_difference = 2.0  # padrão
            if user_filter_config and "min_rsi_difference" in user_filter_config:
                min_difference = user_filter_config["min_rsi_difference"]
                logger.debug(f"Usando diferença RSI personalizada: {min_difference}")
            else:
                min_difference = self.default_daily_limits["min_rsi_difference"]
                logger.debug(f"Usando diferença RSI padrão: {min_difference}")

            # Para sinais de compra: RSI deve estar mais baixo (mais oversold)
            if signal_type in [SignalType.BUY, SignalType.STRONG_BUY]:
                is_stronger = current_rsi < last_rsi_value - min_difference
                logger.debug(
                    f"BUY check: {current_rsi:.2f} < {last_rsi_value:.2f} - {min_difference} = {is_stronger}"
                )
                return is_stronger

            # Para sinais de venda: RSI deve estar mais alto (mais overbought)
            elif signal_type in [SignalType.SELL, SignalType.STRONG_SELL]:
                is_stronger = current_rsi > last_rsi_value + min_difference
                logger.debug(
                    f"SELL check: {current_rsi:.2f} > {last_rsi_value:.2f} + {min_difference} = {is_stronger}"
                )
                return is_stronger

            return False  # HOLD não precisa ser enviado

        except Exception as e:
            logger.error(f"❌ Erro ao verificar força do sinal: {e}")
            return False

    async def _is_stronger_signal(
        self,
        symbol: str,
        analysis,  # Mantido para compatibilidade
        user_filter_config: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Método legacy - mantido para compatibilidade"""
        return await self._is_stronger_signal_generic(
            symbol,
            analysis.rsi_data.value,
            analysis.signal.signal_type,
            analysis.signal.timeframe,
            user_filter_config,
        )

    async def _exceeded_daily_limits(
        self,
        symbol: str,
        strength: SignalStrength,
        user_filter_config: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Verifica se excedeu limites diários"""
        today = datetime.now().strftime("%Y-%m-%d")

        try:
            # Usar limites personalizados ou padrão
            if user_filter_config and "max_signals_per_day" in user_filter_config:
                max_signals = user_filter_config["max_signals_per_day"]
                max_strong = max(1, max_signals // 2)  # Strong = metade do total
                logger.debug(
                    f"Usando limites personalizados: total={max_signals}, strong={max_strong}"
                )
            else:
                max_signals = self.default_daily_limits["max_signals_per_symbol"]
                max_strong = self.default_daily_limits["max_strong_signals"]
                logger.debug(
                    f"Usando limites padrão: total={max_signals}, strong={max_strong}"
                )

            # Verificar total de sinais do símbolo hoje
            total_key = f"daily_count:{symbol}:{today}"
            total_signals = self.redis_client.get(total_key)
            total_signals = int(total_signals) if total_signals else 0

            if total_signals >= max_signals:
                logger.debug(
                    f"🚫 Limite diário total atingido: {total_signals}/{max_signals}"
                )
                return True

            # Verificar sinais STRONG hoje
            if strength == SignalStrength.STRONG:
                strong_key = f"daily_strong:{symbol}:{today}"
                strong_signals = self.redis_client.get(strong_key)
                strong_signals = int(strong_signals) if strong_signals else 0

                if strong_signals >= max_strong:
                    logger.debug(
                        f"🚫 Limite diário STRONG atingido: {strong_signals}/{max_strong}"
                    )
                    return True

            logger.debug(
                f"Limites OK: total={total_signals}/{max_signals}, strong={strength.value}"
            )
            return False

        except Exception as e:
            logger.error(f"❌ Erro ao verificar limites diários: {e}")
            return True  # Em caso de erro, assumir que excedeu

    async def mark_signal_sent(
        self,
        symbol: str,
        analysis_or_confluence,  # Aceita RSIAnalysis ou ConfluenceResult
        user_filter_config: Optional[Dict[str, Any]] = None,
    ):
        """Marca que o sinal foi enviado - atualiza contadores"""

        try:
            # Detectar tipo e extrair informações necessárias
            if hasattr(analysis_or_confluence, "signal") and hasattr(
                analysis_or_confluence, "confluence_score"
            ):
                # É ConfluenceResult
                signal = analysis_or_confluence.signal
                timeframe = signal.timeframe if signal else "15m"
                strength = signal.strength if signal else SignalStrength.WEAK
                rsi_value = signal.rsi_value if signal else 0
            elif hasattr(analysis_or_confluence, "signal") and hasattr(
                analysis_or_confluence, "rsi_data"
            ):
                # É RSIAnalysis (legacy)
                timeframe = analysis_or_confluence.signal.timeframe
                strength = analysis_or_confluence.signal.strength
                rsi_value = analysis_or_confluence.rsi_data.value
            else:
                logger.error(
                    f"Tipo de análise não reconhecido para marcar sinal enviado: {symbol}"
                )
                return

            today = datetime.now().strftime("%Y-%m-%d")

            # Atualizar cooldown com configuração personalizada
            cooldown_key = f"cooldown:{symbol}:{timeframe}"
            cooldown_duration = self._get_cooldown_duration(
                timeframe, strength, user_filter_config
            )
            self.redis_client.setex(cooldown_key, cooldown_duration, time.time())

            # Atualizar último RSI
            rsi_key = f"last_rsi:{symbol}:{timeframe}"
            self.redis_client.setex(rsi_key, 86400, float(rsi_value))  # 24 horas

            # Atualizar contadores diários
            total_key = f"daily_count:{symbol}:{today}"
            self.redis_client.incr(total_key)
            self.redis_client.expire(total_key, 86400)  # Expira em 24h

            if strength == SignalStrength.STRONG:
                strong_key = f"daily_strong:{symbol}:{today}"
                self.redis_client.incr(strong_key)
                self.redis_client.expire(strong_key, 86400)

            logger.info(
                f"Contadores atualizados para {symbol} (cooldown: {cooldown_duration / 60:.1f}min)"
            )

        except Exception as e:
            logger.error(f"❌ Erro ao marcar sinal enviado: {e}")

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
                    self.default_daily_limits["max_signals_per_symbol"]
                    - (int(total_today) if total_today else 0),
                ),
                "remaining_strong": max(
                    0,
                    self.default_daily_limits["max_strong_signals"]
                    - (int(strong_today) if strong_today else 0),
                ),
            }

        except Exception as e:
            logger.error(f"❌ Erro ao obter estatísticas: {e}")
            return {"symbol": symbol, "error": str(e)}


# Instância global
signal_filter = SignalFilter()
