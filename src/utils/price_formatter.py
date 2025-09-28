"""
Utilitários para formatação e parsing seguro de preços/números
"""

from typing import Union, Optional, Any


def format_price(price: Union[float, int], currency_symbol: str = "$") -> str:
    """
    Formata preços de acordo com o valor, ajustando a precisão automaticamente.

    Examples:
        >>> format_price(0.0000023)
        '$0.0000023'
        >>> format_price(0.01223)
        '$0.01223'
        >>> format_price(1.234)
        '$1.234'
        >>> format_price(15.67)
        '$15.67'
        >>> format_price(1234.56)
        '$1,234.56'
    """
    if not isinstance(price, (int, float)):
        raise ValueError(f"Preço deve ser um número, recebido: {type(price)}")

    if price < 0:
        raise ValueError(f"Preço não pode ser negativo: {price}")

    # Para preços muito baixos (< 0.001), usar até 8 casas decimais
    if price < 0.001:
        formatted = f"{currency_symbol}{price:.8f}".rstrip("0").rstrip(".")

    # Para preços baixos (< 0.01), usar até 6 casas decimais
    elif price < 0.01:
        # Para valores como 0.01223, mostrar 5 casas decimais
        formatted = f"{currency_symbol}{price:.5f}"
        # Remover zeros finais apenas se terminar com 0
        if formatted.endswith("0"):
            formatted = formatted[:-1]  # Remove apenas o último zero

    # Para preços entre 0.01 e 0.1, usar até 5 casas decimais
    elif price < 0.1:
        formatted = f"{currency_symbol}{price:.5f}".rstrip("0").rstrip(".")

    # Para preços entre 0.1 e 1, usar até 4 casas decimais
    elif price < 1:
        formatted = f"{currency_symbol}{price:.4f}".rstrip("0").rstrip(".")

    # Para preços entre 1-10, usar 3 casas decimais
    elif price < 10:
        formatted = f"{currency_symbol}{price:.3f}"

    # Para preços altos (>= 10), usar 2 casas decimais com separador de milhares
    else:
        formatted = f"{currency_symbol}{price:,.2f}"

    return formatted


def format_crypto_price(price: Union[float, int]) -> str:
    """
    Formata preços de criptomoedas usando o símbolo padrão '$'.
    """
    return format_price(price, currency_symbol="$")


def format_usd_price(price: Union[float, int]) -> str:
    """
    Formata preços em USD com separador de milhares.
    """
    return format_price(price, currency_symbol="$")


def safe_float(value: Any, default: float = 0.0) -> float:
    """
    Converte valor para float de forma segura, tratando None, strings vazias e valores inválidos.

    Args:
        value: Valor a ser convertido (pode ser None, string, número, etc.)
        default: Valor padrão a retornar em caso de erro

    Returns:
        Float convertido ou valor padrão

    Examples:
        >>> safe_float("123.45")
        123.45
        >>> safe_float(None)
        0.0
        >>> safe_float("", 99.0)
        99.0
        >>> safe_float("invalid", 50.0)
        50.0
    """
    if value is None or value == "":
        return default

    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    """
    Converte valor para int de forma segura, tratando None, strings vazias e valores inválidos.

    Args:
        value: Valor a ser convertido (pode ser None, string, número, etc.)
        default: Valor padrão a retornar em caso de erro

    Returns:
        Int convertido ou valor padrão

    Examples:
        >>> safe_int("123")
        123
        >>> safe_int(None)
        0
        >>> safe_int("", 99)
        99
        >>> safe_int("invalid", 50)
        50
        >>> safe_int(123.45)
        123
    """
    if value is None or value == "":
        return default

    try:
        # Converter para float primeiro para lidar com strings como "123.0"
        return int(float(value))
    except (ValueError, TypeError):
        return default


def safe_price(value: Any, default: float = 0.0) -> float:
    """
    Converte valor para preço de forma segura, garantindo que não seja negativo.

    Args:
        value: Valor a ser convertido
        default: Valor padrão (deve ser >= 0)

    Returns:
        Preço válido (>= 0) ou valor padrão

    Examples:
        >>> safe_price("123.45")
        123.45
        >>> safe_price("-10.0")
        0.0
        >>> safe_price(None, 100.0)
        100.0
    """
    if default < 0:
        raise ValueError("Valor padrão não pode ser negativo para preços")

    price = safe_float(value, default)
    return max(0.0, price)  # Garantir que preço não seja negativo
