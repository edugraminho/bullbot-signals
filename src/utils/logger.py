"""
Configuração de logging para o projeto
"""

import logging
import sys


def get_logger(name: str, level: str = "INFO") -> logging.Logger:
    """
    Cria um logger configurado para o projeto

    Args:
        name: Nome do logger (geralmente __name__)
        level: Nível de log (DEBUG, INFO, WARNING, ERROR)
    """
    logger = logging.getLogger(name)

    # Evitar duplicação de handlers
    if logger.handlers:
        return logger

    # Configurar nível
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)

    # Criar handler para console
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)

    # Formato das mensagens
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger
