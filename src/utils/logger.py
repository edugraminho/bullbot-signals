"""
Configuração de logging para o projeto
"""

import logging
import sys

# Handler global único para evitar duplicação
_global_handler = None


def get_logger(name: str, level: str = "WARNING") -> logging.Logger:
    """
    Cria um logger configurado para o projeto

    Args:
        name: Nome do logger (geralmente __name__)
        level: Nível de log (DEBUG, INFO, WARNING, ERROR)
    """
    global _global_handler

    logger = logging.getLogger(name)

    # Configurar nível
    log_level = getattr(logging, level.upper(), logging.WARNING)
    logger.setLevel(log_level)

    # Criar handler global único se não existir
    if _global_handler is None:
        _global_handler = logging.StreamHandler(sys.stdout)
        _global_handler.setLevel(logging.INFO)

        # Formato das mensagens
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        _global_handler.setFormatter(formatter)

    # Adicionar handler global se não estiver presente
    if _global_handler not in logger.handlers:
        logger.addHandler(_global_handler)

    return logger
