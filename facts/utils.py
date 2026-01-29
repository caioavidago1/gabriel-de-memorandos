"""
Utilitários centralizados para manipulação de facts

Fornece funções helper para acessar e manipular facts com tratamento adequado:
- Acesso seguro com tratamento de campos desabilitados
- Formatação de valores (moeda, nomes, numéricos, etc.)
- Detecção automática de tipos
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
    """
    Obtém fact com tratamento de disabled baseado no tipo.
    
    Args:
        facts: Dict completo de facts (já filtrado por filter_disabled_facts)
        section: Nome da seção
        field: Nome do campo
        fact_type: Tipo do fact para determinar comportamento:
            - "currency": Sempre usa fallback "BRL" se não encontrado
            - "name": Usa placeholder se não encontrado
            - "numeric": Retorna None se não encontrado (deve ser omitido)
            - "date": Retorna None se não encontrado (deve ser omitido)
            - "text": Retorna None se não encontrado (deve ser omitido)
            - "comment": Retorna None se não encontrado (deve ser omitido)
            - "auto": Detecta automaticamente baseado no nome do campo
        default: Valor padrão (usado apenas para currency e name)
        context: Contexto do módulo ("searchfund", "gestora", "primario") para personalizar placeholders
    
    Returns:
        Valor do fact ou None/default conforme tipo
    """
    value = facts.get(section, {}).get(field)
    
    # Se valor existe, retornar
    if value is not None and value != "":
        return value
    
    # Se não existe, tratar conforme tipo
    if fact_type == "auto":
        fact_type = _detect_fact_type(field)
    
    if fact_type == "currency":
        # Moeda sempre usa fallback
        return default or "BRL"
    
    elif fact_type == "name":
        # Nomes usam placeholder
        if default:
            return default
        # Gerar placeholder genérico baseado no campo e contexto
        placeholder = _generate_name_placeholder(field, context)
        return placeholder
    
    elif fact_type in ["numeric", "date", "text", "comment"]:
        # Estes tipos devem ser omitidos se não existirem
        return None
    
    else:
        # Tipo desconhecido: retornar None (omissão segura)
        return None


def _detect_fact_type(field: str) -> str:
    """
    Detecta tipo do fact baseado no nome do campo.
    
    Args:
        field: Nome do campo
    
    Returns:
        Tipo detectado: "currency", "name", "numeric", "date", "text", "comment"
    """
    field_lower = field.lower()
    
    # Moeda
    if "moeda" in field_lower or "currency" in field_lower:
        return "currency"
    
    # Datas
    if any(x in field_lower for x in ["date", "ano", "year", "periodo", "period"]):
        return "date"
    
    # Nomes/Identificadores
    if any(x in field_lower for x in ["nome", "name", "identificador", "vintage"]):
        return "name"
    
    # Valores Numéricos
    if any(x in field_lower for x in ["mm", "pct", "percent", "multiple", "ratio", "irr", "moic", "target", "cap", "ticket", "revenue", "ebitda", "debt", "equity", "cash", "earnout", "seller_note"]):
        return "numeric"
    
    # Comentários
    if "commentary" in field_lower or "comentario" in field_lower:
        return "comment"
    
    # Textos/Descrições (padrão)
    return "text"


def _generate_name_placeholder(field: str, context: Optional[str] = None) -> str:
    """
    Gera placeholder genérico baseado no nome do campo e contexto.
    
    Args:
        field: Nome do campo
        context: Contexto do módulo ("searchfund", "gestora", "primario") para personalizar placeholders
    
    Returns:
        Placeholder formatado
    """
    field_lower = field.lower()
    
    # Mapeamentos específicos por contexto
    if context == "searchfund":
        placeholders = {
            "company_name": "[nome da empresa]",
            "investor_name": "[nome do search fund]",
            "searcher_name": "[nome do searcher]",
            "search_fund_name": "[nome do search fund]",
        }
        # Verificar mapeamento direto
        if field in placeholders:
            return placeholders[field]
        # Gerar genérico baseado em palavras-chave
        if "company" in field_lower or "empresa" in field_lower:
            return "[nome da empresa]"
        elif "investor" in field_lower or "searcher" in field_lower or "search" in field_lower:
            return "[nome do search fund]"
    
    elif context == "gestora":
        placeholders = {
            "gestora_nome": "[nome da gestora]",
            "fundo_nome": "[nome do fundo]",
        }
        # Verificar mapeamento direto
        if field in placeholders:
            return placeholders[field]
        # Gerar genérico baseado em palavras-chave
        if "gestora" in field_lower:
            return "[nome da gestora]"
        elif "fundo" in field_lower:
            return "[nome do fundo]"
    
    elif context == "primario":
        placeholders = {
            "gestora_nome": "[nome da gestora]",
            "fundo_nome": "[nome do fundo]",
        }
        # Verificar mapeamento direto
        if field in placeholders:
            return placeholders[field]
        # Gerar genérico baseado em palavras-chave
        if "gestora" in field_lower:
            return "[nome da gestora]"
        elif "fundo" in field_lower:
            return "[nome do fundo]"
    
    # Fallback genérico (sem contexto ou contexto desconhecido)
    if "gestora" in field_lower:
        return "[nome da gestora]"
    elif "fundo" in field_lower:
        return "[nome do fundo]"
    elif "company" in field_lower or "empresa" in field_lower:
        return "[nome da empresa]"
    elif "investor" in field_lower or "searcher" in field_lower:
        return "[nome do investidor]"
    else:
        return f"[{field}]"


def get_currency_safe(
    facts: Dict[str, Any], 
    section: str, 
    field: str, 
    default: str = "BRL"
) -> str:
    """
    Helper específico para obter moeda com fallback garantido.
    
    Args:
        facts: Dict de facts
        section: Seção
        field: Campo
        default: Valor padrão (padrão: "BRL")
    
    Returns:
        Código da moeda (sempre retorna, nunca None)
    """
    return get_fact_safe(facts, section, field, fact_type="currency", default=default)


def get_name_safe(
    facts: Dict[str, Any], 
    section: str, 
    field: str, 
    default: Optional[str] = None,
    context: Optional[str] = None
) -> Optional[str]:
    """
    Helper específico para obter nome/identificador com placeholder.
    
    Suporta compatibilidade retroativa: se field="searcher_name" e não encontrar,
    tenta "investor_person_names" automaticamente.
    
    Args:
        facts: Dict de facts
        section: Seção
        field: Campo
        default: Placeholder customizado (opcional)
        context: Contexto do módulo para personalizar placeholders
    
    Returns:
        Nome ou placeholder
    """
    # Compatibilidade retroativa: se procurando por searcher_name e não encontrar,
    # tenta investor_person_names
    if field == "searcher_name":
        value = get_fact_safe(facts, section, field, fact_type="name", default=None, context=context)
        if value is None or (isinstance(value, str) and value.startswith("[") and value.endswith("]")):
            # Tenta o nome antigo
            old_value = get_fact_safe(facts, section, "investor_person_names", fact_type="name", default=None, context=context)
            if old_value and not (isinstance(old_value, str) and old_value.startswith("[") and old_value.endswith("]")):
                return old_value
    
    return get_fact_safe(facts, section, field, fact_type="name", default=default, context=context)


def get_numeric_safe(facts: Dict[str, Any], section: str, field: str) -> Optional[Any]:
    """
    Helper específico para obter valor numérico (retorna None se não existir).
    
    Args:
        facts: Dict de facts
        section: Seção
        field: Campo
    
    Returns:
        Valor numérico ou None (deve ser omitido se None)
    """
    return get_fact_safe(facts, section, field, fact_type="numeric")


def get_text_safe(facts: Dict[str, Any], section: str, field: str) -> Optional[str]:
    """
    Helper específico para obter texto/descrição (retorna None se não existir).
    
    Args:
        facts: Dict de facts
        section: Seção
        field: Campo
    
    Returns:
        Texto ou None (deve ser omitido se None)
    """
    return get_fact_safe(facts, section, field, fact_type="text")


def get_fact_value(
    facts: Dict[str, Any],
    section: str,
    field: str,
    default: Any = None
) -> Any:
    """
    Obtém valor de um fact específico com fallback seguro.
    
    Args:
        facts: Dict completo de facts
        section: Nome da seção
        field: Nome do campo
        default: Valor padrão se não encontrado
    
    Returns:
        Valor do fact ou default
    
    Examples:
        >>> facts = {"identification": {"company_name": "TSE"}}
        >>> get_fact_value(facts, "identification", "company_name")
        'TSE'
        >>> get_fact_value(facts, "identification", "missing", "N/A")
        'N/A'
    """
    return facts.get(section, {}).get(field, default)
