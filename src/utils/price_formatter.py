"""
Utilitários para formatação de preços
"""

from typing import Union


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
