"""
Utilitário para carregar configurações do projeto.

Centraliza o carregamento de configurações de diferentes
formatos (YAML, JSON, env) e fornece acesso unificado.
"""

import os
import yaml
import json
from typing import Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Carregador de configurações do projeto."""

    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_cache = {}

    def load_yaml(self, filename: str) -> Dict[str, Any]:
        """Carrega arquivo YAML."""
        file_path = self.config_dir / filename

        if not file_path.exists():
            logger.warning(f"Arquivo de configuração não encontrado: {file_path}")
            return {}

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                logger.info(f"✅ Configuração carregada: {filename}")
                return config or {}
        except Exception as e:
            logger.error(f"❌ Erro ao carregar {filename}: {e}")
            return {}

    def load_json(self, filename: str) -> Dict[str, Any]:
        """Carrega arquivo JSON."""
        file_path = self.config_dir / filename

        if not file_path.exists():
            logger.warning(f"Arquivo de configuração não encontrado: {file_path}")
            return {}

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                logger.info(f"✅ Configuração carregada: {filename}")
                return config
        except Exception as e:
            logger.error(f"❌ Erro ao carregar {filename}: {e}")
            return {}

    def load_env(self, prefix: str = "CRYPTO_HUNTER_") -> Dict[str, Any]:
        """Carrega variáveis de ambiente com prefixo específico."""
        config = {}

        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Remove o prefixo e converte para lowercase
                config_key = key[len(prefix) :].lower()
                config[config_key] = value

        if config:
            logger.info(f"✅ {len(config)} variáveis de ambiente carregadas")

        return config

    def get_exchange_config(self, exchange_name: str) -> Dict[str, Any]:
        """Retorna configuração específica de uma exchange."""
        config = self.load_yaml("exchanges.yaml")
        return config.get(exchange_name, {})

    def get_global_config(self) -> Dict[str, Any]:
        """Retorna configurações globais."""
        config = self.load_yaml("exchanges.yaml")
        return config.get("global", {})

    def get_notification_config(self) -> Dict[str, Any]:
        """Retorna configurações de notificação."""
        config = self.load_yaml("exchanges.yaml")
        return config.get("notifications", {})

    def merge_configs(self, *configs: Dict[str, Any]) -> Dict[str, Any]:
        """Mescla múltiplas configurações."""
        merged = {}

        for config in configs:
            if config:
                merged.update(config)

        return merged

    def validate_exchange_config(self, config: Dict[str, Any]) -> bool:
        """Valida configuração de exchange."""
        required_fields = ["name", "rate_limit"]

        for field in required_fields:
            if field not in config:
                logger.error(f"Campo obrigatório ausente na configuração: {field}")
                return False

        return True

    def get_database_config(self) -> Dict[str, Any]:
        """Retorna configuração do banco de dados."""
        # Tenta carregar de arquivo específico
        db_config = self.load_yaml("database.yaml")

        if not db_config:
            # Configuração padrão
            db_config = {
                "host": os.getenv("DB_HOST", "localhost"),
                "port": int(os.getenv("DB_PORT", "5432")),
                "database": os.getenv("DB_NAME", "crypto_hunter"),
                "username": os.getenv("DB_USER", "postgres"),
                "password": os.getenv("DB_PASSWORD", ""),
                "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
                "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "20")),
            }

        return db_config

    def get_redis_config(self) -> Dict[str, Any]:
        """Retorna configuração do Redis."""
        redis_config = {
            "host": os.getenv("REDIS_HOST", "localhost"),
            "port": int(os.getenv("REDIS_PORT", "6379")),
            "db": int(os.getenv("REDIS_DB", "0")),
            "password": os.getenv("REDIS_PASSWORD", None),
            "decode_responses": True,
        }

        return redis_config


# Instância global do carregador de configurações
config_loader = ConfigLoader()


def get_config() -> Dict[str, Any]:
    """Função de conveniência para obter configurações."""
    return config_loader.merge_configs(
        config_loader.load_yaml("exchanges.yaml"), config_loader.load_env()
    )
