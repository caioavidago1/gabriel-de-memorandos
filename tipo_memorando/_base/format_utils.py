"""
Utilitários compartilhados para formatação de valores

Funções de formatação, conversão de moedas e helpers compartilhados
entre todos os módulos de tipo_memorando.

Migrado de shortmemo/ para tipo_memorando/_base/
"""


def get_currency_symbol(currency_code: str) -> str:
    """
    Converte código de moeda para símbolo.
    
    Args:
        currency_code: Código da moeda (BRL, USD, EUR, MXN, etc)
    
    Returns:
        Símbolo da moeda (R$, US$, €, etc)
    
    Examples:
        >>> get_currency_symbol("BRL")
        'R$'
        >>> get_currency_symbol("USD")
        'US$'
        >>> get_currency_symbol("MXN")
        'MX$'
    """
    currency_map = {
        "BRL": "R$",
        "USD": "US$",
        "EUR": "€",
        "MXN": "MX$",
        "GBP": "£",
        "CLP": "CLP$",
        "COP": "COP$",
        "ARS": "ARS$"
    }
    return currency_map.get(currency_code, currency_code)


def get_currency_label(currency_code: str) -> str:
    """
    Converte código de moeda para label formatado para uso em facts.
    
    Args:
        currency_code: Código da moeda (BRL, USD, EUR, etc)
    
    Returns:
        Label formatado (R$ MM, US$ MM, € MM, etc)
    
    Examples:
        >>> get_currency_label("BRL")
        'R$ MM'
        >>> get_currency_label("USD")
        'US$ MM'
    """
    return f"{get_currency_symbol(currency_code)} MM"


def format_currency_value(value: float, currency_code: str = "BRL") -> str:
    """
    Formata valor monetário com símbolo de moeda.
    
    Args:
        value: Valor em milhões
        currency_code: Código da moeda
    
    Returns:
        String formatada (ex: "R$ 138m", "US$ 10m")
    
    Examples:
        >>> format_currency_value(138, "BRL")
        'R$ 138m'
        >>> format_currency_value(10.5, "USD")
        'US$ 10,5m'
    """
    symbol = get_currency_symbol(currency_code)
    
    # Formatar com vírgula para decimais (padrão brasileiro)
    if value % 1 == 0:
        value_str = str(int(value))
    else:
        value_str = str(value).replace(".", ",")
    
    return f"{symbol} {value_str}m"


def format_multiple(value: float) -> str:
    """
    Formata múltiplo com vírgula (padrão Spectra).
    
    Args:
        value: Valor do múltiplo
    
    Returns:
        String formatada (ex: "3,5x", "4,0x")
    
    Examples:
        >>> format_multiple(3.5)
        '3,5x'
        >>> format_multiple(4)
        '4,0x'
    """
    return f"{str(value).replace('.', ',')}x"


def format_percentage(value: float) -> str:
    """
    Formata percentual sem espaço antes do símbolo.
    
    Args:
        value: Valor do percentual (sem símbolo %)
    
    Returns:
        String formatada (ex: "38%", "15,5%")
    
    Examples:
        >>> format_percentage(38)
        '38%'
        >>> format_percentage(15.5)
        '15,5%'
    """
    if value % 1 == 0:
        value_str = str(int(value))
    else:
        value_str = str(value).replace(".", ",")
    
    return f"{value_str}%"
