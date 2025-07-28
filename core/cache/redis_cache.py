"""
Implementação do cache Redis com cache-aside híbrido.

Fornece cache com TTL configurável para diferentes tipos
de dados com estratégias de fallback e invalidação.
"""

import json
import logging
import hashlib
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
import redis
from dataclasses import dataclass, asdict
import pickle

logger = logging.getLogger(__name__)


@dataclass
class CacheConfig:
    """Configuração do cache."""

    # TTL padrão para diferentes tipos de dados (em segundos)
    ohlcv_ttl: int = 300  # 5 minutos
    rsi_ttl: int = 120  # 2 minutos
    symbols_ttl: int = 3600  # 1 hora
    ticker_ttl: int = 60  # 1 minuto

    # Configurações de Redis
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None

    # Configurações de cache
    max_memory: int = 100 * 1024 * 1024  # 100MB
    compression_threshold: int = 1024  # Comprimir dados > 1KB
    enable_compression: bool = True


class RedisCache:
    """Cache Redis com cache-aside híbrido e TTL."""

    def __init__(self, config: CacheConfig):
        self.config = config
        self.redis_client = redis.Redis(
            host=config.redis_host,
            port=config.redis_port,
            db=config.redis_db,
            password=config.redis_password,
            decode_responses=False,  # Para suportar pickle
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
        )

        # Testa conexão
        try:
            self.redis_client.ping()
            logger.info("Cache Redis conectado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao conectar com Redis: {e}")
            raise

    def _generate_key(self, prefix: str, *args) -> str:
        """Gera chave de cache baseada em prefixo e argumentos."""
        key_parts = [prefix] + [str(arg) for arg in args]
        return ":".join(key_parts)

    def _serialize_data(self, data: Any) -> bytes:
        """Serializa dados para armazenamento no Redis."""
        try:
            # Tenta JSON primeiro (mais eficiente)
            if isinstance(data, (dict, list, str, int, float, bool)):
                return json.dumps(data, default=str).encode("utf-8")

            # Fallback para pickle
            return pickle.dumps(data)
        except Exception as e:
            logger.warning(f"Erro na serialização, usando pickle: {e}")
            return pickle.dumps(data)

    def _deserialize_data(self, data: bytes) -> Any:
        """Deserializa dados do Redis."""
        try:
            # Tenta JSON primeiro
            json_data = data.decode("utf-8")
            return json.loads(json_data)
        except (UnicodeDecodeError, json.JSONDecodeError):
            # Fallback para pickle
            return pickle.loads(data)

    def _compress_data(self, data: bytes) -> bytes:
        """Comprime dados se necessário."""
        if (
            not self.config.enable_compression
            or len(data) < self.config.compression_threshold
        ):
            return data

        try:
            import gzip

            return gzip.compress(data)
        except ImportError:
            logger.warning("gzip não disponível, dados não comprimidos")
            return data

    def _decompress_data(self, data: bytes) -> bytes:
        """Descomprime dados se necessário."""
        if not self.config.enable_compression:
            return data

        try:
            import gzip

            return gzip.decompress(data)
        except (ImportError, OSError):
            return data

    def get(self, key: str, default: Any = None) -> Any:
        """Obtém dados do cache."""
        try:
            data = self.redis_client.get(key)
            if data is None:
                return default

            decompressed = self._decompress_data(data)
            return self._deserialize_data(decompressed)

        except Exception as e:
            logger.error(f"Erro ao obter cache para {key}: {e}")
            return default

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Define dados no cache."""
        try:
            serialized = self._serialize_data(value)
            compressed = self._compress_data(serialized)

            if ttl:
                self.redis_client.setex(key, ttl, compressed)
            else:
                self.redis_client.set(key, compressed)

            return True

        except Exception as e:
            logger.error(f"Erro ao definir cache para {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Remove dados do cache."""
        try:
            result = self.redis_client.delete(key)
            return result > 0

        except Exception as e:
            logger.error(f"Erro ao deletar cache para {key}: {e}")
            return False

    def exists(self, key: str) -> bool:
        """Verifica se chave existe no cache."""
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Erro ao verificar cache {key}: {e}")
            return False

    def get_ttl(self, key: str) -> int:
        """Retorna TTL restante de uma chave."""
        try:
            ttl = self.redis_client.ttl(key)
            return ttl if ttl > 0 else 0
        except Exception as e:
            logger.error(f"Erro ao obter TTL de {key}: {e}")
            return 0

    def set_many(self, data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Define múltiplos dados no cache."""
        try:
            pipeline = self.redis_client.pipeline()

            for key, value in data.items():
                serialized = self._serialize_data(value)
                compressed = self._compress_data(serialized)

                if ttl:
                    pipeline.setex(key, ttl, compressed)
                else:
                    pipeline.set(key, compressed)

            pipeline.execute()
            return True

        except Exception as e:
            logger.error(f"Erro ao definir múltiplos caches: {e}")
            return False

    def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Obtém múltiplos dados do cache."""
        try:
            pipeline = self.redis_client.pipeline()
            for key in keys:
                pipeline.get(key)

            results = pipeline.execute()

            data = {}
            for key, result in zip(keys, results):
                if result is not None:
                    decompressed = self._decompress_data(result)
                    data[key] = self._deserialize_data(decompressed)

            return data

        except Exception as e:
            logger.error(f"Erro ao obter múltiplos caches: {e}")
            return {}

    def invalidate_pattern(self, pattern: str) -> int:
        """Invalida chaves que correspondem ao padrão."""
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info(f"Cache invalidate_pattern: {deleted} chaves removidas")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Erro ao invalidar padrão {pattern}: {e}")
            return 0

    def clear(self) -> bool:
        """Limpa todo o cache."""
        try:
            self.redis_client.flushdb()
            logger.info("Cache limpo completamente")
            return True
        except Exception as e:
            logger.error(f"Erro ao limpar cache: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache."""
        try:
            info = self.redis_client.info()
            return {
                "total_connections_received": info.get("total_connections_received", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(info),
            }
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return {}

    def _calculate_hit_rate(self, info: Dict[str, Any]) -> float:
        """Calcula taxa de hit do cache."""
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses

        if total == 0:
            return 0.0

        return round((hits / total) * 100, 2)

    def health_check(self) -> bool:
        """Verifica saúde do cache."""
        try:
            self.redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Health check falhou: {e}")
            return False
