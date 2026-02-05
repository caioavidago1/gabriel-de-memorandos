"""
Utilitários centralizados para manipulação de facts
"""

from typing import Dict, Any, Optional


def get_fact_safe(
    facts: Dict[str, Any],
    section: str,
    field: str,
    fact_type: str = "auto",
    default: Optional[Any] = None,
    context: Optional[str] = None
) -> Optional[Any]:
    """Obtém fact com tratamento baseado no tipo."""
    value = facts.get(section, {}).get(field)

    if value is not None and value != "":
        return value

    if fact_type == "auto":
        fact_type = _detect_fact_type(field)

    if fact_type == "currency":
        return default or "BRL"
    elif fact_type == "name":
        if default:
            return default
        return _generate_name_placeholder(field, context)
    elif fact_type in ["numeric", "date", "text", "comment"]:
        return None
    else:
        return None


def _detect_fact_type(field: str) -> str:
    """Detecta tipo do fact baseado no nome do campo."""
    field_lower = field.lower()
    if "moeda" in field_lower or "currency" in field_lower:
        return "currency"
    if any(x in field_lower for x in ["date", "ano", "year", "periodo", "period"]):
        return "date"
    if any(x in field_lower for x in ["nome", "name", "identificador", "vintage"]):
        return "name"
    if any(x in field_lower for x in ["mm", "pct", "percent", "multiple", "ratio", "irr", "moic", "target", "cap", "ticket", "revenue", "ebitda", "debt", "equity", "cash", "earnout", "seller_note"]):
        return "numeric"
    if "commentary" in field_lower or "comentario" in field_lower:
        return "comment"
    return "text"


def _generate_name_placeholder(field: str, context: Optional[str] = None) -> str:
    """Gera placeholder baseado no nome do campo e contexto."""
    field_lower = field.lower()
    if context == "searchfund":
        placeholders = {
            "company_name": "[nome da empresa]",
            "investor_name": "[nome do search fund]",
            "searcher_name": "[nome do searcher]",
            "search_fund_name": "[nome do search fund]",
        }
        if field in placeholders:
            return placeholders[field]
        if "company" in field_lower or "empresa" in field_lower:
            return "[nome da empresa]"
        elif "investor" in field_lower or "searcher" in field_lower or "search" in field_lower:
            return "[nome do search fund]"
    elif context == "gestora" or context == "primario":
        placeholders = {
            "gestora_nome": "[nome da gestora]",
            "fundo_nome": "[nome do fundo]",
        }
        if field in placeholders:
            return placeholders[field]
        if "gestora" in field_lower:
            return "[nome da gestora]"
        elif "fundo" in field_lower:
            return "[nome do fundo]"
    if "gestora" in field_lower:
        return "[nome da gestora]"
    elif "fundo" in field_lower:
        return "[nome do fundo]"
    elif "company" in field_lower or "empresa" in field_lower:
        return "[nome da empresa]"
    elif "investor" in field_lower or "searcher" in field_lower:
        return "[nome do investidor]"
    return f"[{field}]"


def get_currency_safe(
    facts: Dict[str, Any],
    section: str,
    field: str,
    default: str = "BRL"
) -> str:
    """Helper para obter moeda com fallback."""
    return get_fact_safe(facts, section, field, fact_type="currency", default=default)


def get_name_safe(
    facts: Dict[str, Any],
    section: str,
    field: str,
    default: Optional[str] = None,
    context: Optional[str] = None
) -> Optional[str]:
    """Helper para obter nome/identificador com placeholder."""
    if field == "searcher_name":
        value = get_fact_safe(facts, section, field, fact_type="name", default=None, context=context)
        if value is None or (isinstance(value, str) and value.startswith("[") and value.endswith("]")):
            old_value = get_fact_safe(facts, section, "investor_person_names", fact_type="name", default=None, context=context)
            if old_value and not (isinstance(old_value, str) and old_value.startswith("[") and old_value.endswith("]")):
                return old_value
    return get_fact_safe(facts, section, field, fact_type="name", default=default, context=context)


def get_numeric_safe(facts: Dict[str, Any], section: str, field: str) -> Optional[Any]:
    """Helper para obter valor numérico."""
    return get_fact_safe(facts, section, field, fact_type="numeric")


def get_text_safe(facts: Dict[str, Any], section: str, field: str) -> Optional[str]:
    """Helper para obter texto/descrição."""
    return get_fact_safe(facts, section, field, fact_type="text")


def get_fact_value(
    facts: Dict[str, Any],
    section: str,
    field: str,
    default: Any = None
) -> Any:
    """Obtém valor de um fact específico com fallback seguro."""
    return facts.get(section, {}).get(field, default)
