"""
Factory para criação e gerenciamento de exchanges.

Centraliza a criação de adaptadores de exchanges e fornece
métodos para gerenciar múltiplas exchanges simultaneamente.
"""

import logging
from typing import Dict, List, Optional, Any
from .base import ExchangeInterface
from .gateio import GateIOAdapter


logger = logging.getLogger(__name__)


class ExchangeFactory:
    """Factory para criação de adaptadores de exchanges."""

    _adapters = {
        "gateio": GateIOAdapter,
        # Futuras exchanges serão adicionadas aqui
        # "binance": BinanceAdapter,
        # "bybit": BybitAdapter,
    }

    @classmethod
    def create_exchange(
        cls, exchange_name: str, config: Dict[str, Any]
    ) -> Optional[ExchangeInterface]:
        """Cria uma instância de exchange baseada no nome."""
        try:
            adapter_class = cls._adapters.get(exchange_name.lower())
            if not adapter_class:
                logger.error(f"Exchange '{exchange_name}' não suportada")
                return None

            # Adiciona o nome da exchange à configuração
            config["name"] = exchange_name.lower()

            exchange = adapter_class(config)
            logger.info(f"Exchange '{exchange_name}' criada com sucesso")
            return exchange

        except Exception as e:
            logger.error(f"Erro ao criar exchange '{exchange_name}': {e}")
            return None

    @classmethod
    def get_supported_exchanges(cls) -> List[str]:
        """Retorna lista de exchanges suportadas."""
        return list(cls._adapters.keys())

    @classmethod
    def register_adapter(cls, name: str, adapter_class):
        """Registra um novo adapter de exchange."""
        cls._adapters[name.lower()] = adapter_class
        logger.info(f"Novo adapter registrado: {name}")


class ExchangeManager:
    """Gerencia múltiplas exchanges simultaneamente."""

    def __init__(self):
        self.exchanges: Dict[str, ExchangeInterface] = {}
        self.logger = logging.getLogger(__name__)

    def add_exchange(self, name: str, config: Dict[str, Any]) -> bool:
        """Adiciona uma exchange ao gerenciador."""
        exchange = ExchangeFactory.create_exchange(name, config)
        if exchange:
            self.exchanges[name] = exchange
            self.logger.info(f"Exchange '{name}' adicionada ao gerenciador")
            return True
        return False

    def add_exchange_instance(self, name: str, exchange: ExchangeInterface) -> bool:
        """Adiciona uma instância de exchange ao gerenciador."""
        try:
            self.exchanges[name] = exchange
            self.logger.info(f"Exchange '{name}' adicionada ao gerenciador")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao adicionar exchange '{name}': {e}")
            return False

    def get_exchange(self, name: str) -> Optional[ExchangeInterface]:
        """Retorna uma exchange específica."""
        return self.exchanges.get(name)

    def get_all_exchanges(self) -> Dict[str, ExchangeInterface]:
        """Retorna todas as exchanges configuradas."""
        return self.exchanges.copy()

    async def test_all_connections(self) -> Dict[str, bool]:
        """Testa a conectividade de todas as exchanges."""
        results = {}

        for name, exchange in self.exchanges.items():
            try:
                is_connected = await exchange.test_connection()
                results[name] = is_connected

                status = "Conectado" if is_connected else "Falha na conexão"
                self.logger.info(f"{name}: {status}")

            except Exception as e:
                results[name] = False
                self.logger.error(f"Erro ao testar {name}: {e}")

        return results

    async def get_all_symbols(self) -> Dict[str, List]:
        """Busca símbolos de todas as exchanges."""
        all_symbols = {}

        for name, exchange in self.exchanges.items():
            try:
                symbols = await exchange.get_symbols()
                all_symbols[name] = symbols
                self.logger.info(f"{name}: {len(symbols)} símbolos encontrados")

            except Exception as e:
                self.logger.error(f"Erro ao buscar símbolos de {name}: {e}")
                all_symbols[name] = []

        return all_symbols

    def remove_exchange(self, name: str) -> bool:
        """Remove uma exchange do gerenciador."""
        if name in self.exchanges:
            del self.exchanges[name]
            self.logger.info(f"Exchange '{name}' removida do gerenciador")
            return True
        return False

    def clear_exchanges(self):
        """Remove todas as exchanges."""
        self.exchanges.clear()
        self.logger.info("Todas as exchanges removidas do gerenciador")
