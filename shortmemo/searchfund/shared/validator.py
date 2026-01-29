"""
Validação e correção de memos de Search Fund

Funções para validar consistência entre facts e texto gerado,
e corrigir formatação numérica para padrão Spectra
Migrado de shortmemo/agents/memo_writer.py
"""

import re
from typing import Dict, Any
from .utils import get_currency_symbol


def validate_memo_consistency(
    memo_text: str,
    facts: Dict[str, Any],
    section: str
) -> Dict[str, Any]:
    """
    Valida se o memo gerado está consistente com os facts estruturados.
    
    Args:
        memo_text: Texto da seção do memo
        facts: Dict com facts estruturados
        section: Nome da seção ("intro", "market", "financials", "company", "transaction")
    
    Returns:
        {
            "is_valid": bool,
            "warnings": List[str],
            "missing_facts": List[str]
        }
    
    Examples:
        >>> facts = {"identification": {"investor_name": "Minerva Capital"}}
        >>> memo = "A TSE é uma empresa de automação"
        >>> result = validate_memo_consistency(memo, facts, "intro")
        >>> result["missing_facts"]
        ["Nome do investidor 'Minerva Capital' não mencionado"]
    """
    warnings = []
    missing_facts = []
    
    # Validações específicas por seção
    if section == "intro":
        # Deve mencionar investor_name
        investor_name = facts.get("identification", {}).get("investor_name")
        if investor_name and investor_name not in memo_text:
            missing_facts.append(f"Nome do investidor '{investor_name}' não mencionado")
        
        # Deve mencionar EV
        ev = facts.get("transaction_structure", {}).get("ev_mm")
        currency = facts.get("transaction_structure", {}).get("currency") or "BRL"
        currency_symbol = get_currency_symbol(currency)
        if ev:
            # Aceita "R$ 138m" ou "US$ 10m" ou "138m"
            ev_pattern = rf"({re.escape(currency_symbol)}\s*)?{int(ev)}\s*m"
            if not re.search(ev_pattern, memo_text, re.IGNORECASE):
                warnings.append(f"EV de {currency_symbol} {ev}m pode não estar mencionado corretamente")
        
        # Deve mencionar múltiplo
        mult = facts.get("transaction_structure", {}).get("multiple_ev_ebitda")
        if mult:
            # Aceita "3.5x" ou "3,5x"
            mult_pattern = rf"{str(mult).replace('.', '[.,]')}x"
            if not re.search(mult_pattern, memo_text, re.IGNORECASE):
                warnings.append(f"Múltiplo de {mult}x pode não estar mencionado")
    
    elif section == "market":
        # Deve mencionar competidores se disponível
        competitors = facts.get("qualitative", {}).get("main_competitors")
        if competitors and "competidor" not in memo_text.lower():
            warnings.append("Competidores não mencionados na seção Mercado")
        
        # Deve ter frase "De acordo com o searcher" para diferenciais
        if "de acordo com o searcher" not in memo_text.lower() and "segundo o searcher" not in memo_text.lower():
            warnings.append("Falta atribuição ao searcher nos diferenciais competitivos")
    
    elif section == "company":
        # Deve mencionar company_name
        company_name = facts.get("identification", {}).get("company_name")
        if company_name and company_name not in memo_text:
            warnings.append(f"Nome da empresa '{company_name}' não mencionado")
        
        # Deve mencionar business_description
        business_desc = facts.get("identification", {}).get("business_description")
        if business_desc and len(business_desc) > 10:
            # Checa se alguma palavra-chave da descrição aparece
            keywords = [w for w in business_desc.split() if len(w) > 4][:3]
            if keywords and not any(kw.lower() in memo_text.lower() for kw in keywords):
                warnings.append("Descrição do negócio pode não estar clara")
    
    elif section == "financials":
        # Deve mencionar CAGR com período
        cagr = facts.get("financials_history", {}).get("revenue_cagr_pct")
        period = facts.get("financials_history", {}).get("revenue_cagr_period")
        if cagr and not period:
            warnings.append("CAGR mencionado mas sem período específico (ex: 2019-2024)")
        
        # Deve mencionar receita atual
        revenue = facts.get("financials_history", {}).get("revenue_current_mm")
        currency = facts.get("transaction_structure", {}).get("currency") or "BRL"
        currency_symbol = get_currency_symbol(currency)
        if revenue:
            rev_pattern = rf"{int(revenue)}\s*m"
            if not re.search(rev_pattern, memo_text, re.IGNORECASE):
                warnings.append(f"Receita de {currency_symbol} {revenue}m pode não estar mencionada")
    
    elif section == "transaction":
        # Deve analisar atratividade da estrutura
        if "atrativ" not in memo_text.lower() and "favorável" not in memo_text.lower():
            warnings.append("Falta análise sobre atratividade da estrutura da transação")
    
    return {
        "is_valid": len(missing_facts) == 0,
        "warnings": warnings,
        "missing_facts": missing_facts
    }


def fix_number_formatting(text: str) -> str:
    """
    Corrige formatação numérica para padrão Spectra.
    
    Padrões corrigidos:
    - R$ XXX milhões → R$ XXXm
    - 3.5x → 3,5x
    - 38 % → 38%
    - 2.5 MOIC → 2,5 MOIC
    
    Args:
        text: Texto do memo com formatação potencialmente incorreta
    
    Returns:
        Texto com formatação corrigida
    
    Examples:
        >>> fix_number_formatting("R$ 138 milhões")
        'R$ 138m'
        >>> fix_number_formatting("múltiplo de 3.5x")
        'múltiplo de 3,5x'
        >>> fix_number_formatting("margem de 38 %")
        'margem de 38%'
    """
    # R$ XXX milhões → R$ XXXm
    text = re.sub(r'R\$\s*(\d+(?:[.,]\d+)?)\s*milh[õo]es?', r'R$ \1m', text, flags=re.IGNORECASE)
    
    # US$ XXX milhões → US$ XXXm
    text = re.sub(r'US\$\s*(\d+(?:[.,]\d+)?)\s*milh[õo]es?', r'US$ \1m', text, flags=re.IGNORECASE)
    
    # MX$ XXX milhões → MX$ XXXm
    text = re.sub(r'MX\$\s*(\d+(?:[.,]\d+)?)\s*milh[õo]es?', r'MX$ \1m', text, flags=re.IGNORECASE)
    
    # Múltiplos com ponto → vírgula (3.5x → 3,5x)
    text = re.sub(r'(\d+)\.(\d+)x', r'\1,\2x', text)
    
    # Espaço antes de % → sem espaço (38 % → 38%)
    text = re.sub(r'(\d+)\s*%', r'\1%', text)
    
    # MOIC: 2.5 → 2,5
    text = re.sub(r'(\d+)\.(\d+)\s*MOIC', r'\1,\2 MOIC', text, flags=re.IGNORECASE)
    
    # IRR: 38.5% → 38,5%
    text = re.sub(r'(\d+)\.(\d+)%\s*(?:IRR|TIR)', r'\1,\2% IRR', text, flags=re.IGNORECASE)
    
    return text


def check_section_length(
    memo_text: str,
    section: str,
    min_paragraphs: int = 2,
    max_paragraphs: int = 5
) -> Dict[str, Any]:
    """
    Valida se a seção tem número adequado de parágrafos.
    
    Args:
        memo_text: Texto da seção
        section: Nome da seção
        min_paragraphs: Mínimo de parágrafos esperados
        max_paragraphs: Máximo de parágrafos esperados
    
    Returns:
        {
            "is_valid": bool,
            "paragraph_count": int,
            "warning": str (se inválido)
        }
    """
    # Conta parágrafos (separados por linha dupla)
    paragraphs = [p.strip() for p in memo_text.split("\n\n") if p.strip()]
    count = len(paragraphs)
    
    is_valid = min_paragraphs <= count <= max_paragraphs
    warning = ""
    
    if count < min_paragraphs:
        warning = f"Seção '{section}' muito curta ({count} parágrafo(s), esperado mínimo {min_paragraphs})"
    elif count > max_paragraphs:
        warning = f"Seção '{section}' muito longa ({count} parágrafos, esperado máximo {max_paragraphs})"
    
    return {
        "is_valid": is_valid,
        "paragraph_count": count,
        "warning": warning
    }


def validate_search_fund_intro(memo_text: str, facts: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validação específica para introdução de Search Fund.
    
    Checa se segue o padrão obrigatório:
    "A {investor} (search liderado por {searcher}, que iniciou seu período de busca em {data})..."
    
    Args:
        memo_text: Texto da introdução
        facts: Facts estruturados
    
    Returns:
        {
            "is_valid": bool,
            "errors": List[str]
        }
    """
    errors = []
    
    # Padrão obrigatório para Search Fund
    investor_name = facts.get("identification", {}).get("investor_name")
    # Compatibilidade: aceita tanto searcher_name quanto investor_person_names
    searcher_names = facts.get("identification", {}).get("searcher_name") or facts.get("identification", {}).get("investor_person_names")
    
    if investor_name and investor_name not in memo_text[:200]:
        errors.append("Primeira frase deve começar com 'A {investor_name}'")
    
    if searcher_names and searcher_names not in memo_text[:200]:
        errors.append(f"Primeira frase deve mencionar o searcher '{searcher_names}'")
    
    if "search liderado por" not in memo_text[:300].lower():
        errors.append("Falta frase padrão: '(search liderado por {searcher}, que iniciou...'")
    
    if "iniciou seu período de busca" not in memo_text[:300].lower() and \
       "iniciou o período de busca" not in memo_text[:300].lower():
        errors.append("Falta menção ao início do período de busca")
    
    return {
        "is_valid": len(errors) == 0,
        "errors": errors
    }
