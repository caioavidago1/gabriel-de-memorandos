"""
Validação e correção de memos de Search Fund

Funções para validar consistência entre facts e texto gerado,
e corrigir formatação numérica para padrão Spectra
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
    """
    warnings = []
    missing_facts = []
    
    # Validações específicas por seção
    if section == "intro":
        investor_name = facts.get("identification", {}).get("investor_name")
        if investor_name and investor_name not in memo_text:
            missing_facts.append(f"Nome do investidor '{investor_name}' não mencionado")
        
        ev = facts.get("transaction_structure", {}).get("ev_mm")
        currency = facts.get("transaction_structure", {}).get("currency") or "BRL"
        currency_symbol = get_currency_symbol(currency)
        if ev:
            ev_pattern = rf"({re.escape(currency_symbol)}\s*)?{int(ev)}\s*m"
            if not re.search(ev_pattern, memo_text, re.IGNORECASE):
                warnings.append(f"EV de {currency_symbol} {ev}m pode não estar mencionado corretamente")
        
        mult = facts.get("transaction_structure", {}).get("multiple_ev_ebitda")
        if mult:
            mult_pattern = rf"{str(mult).replace('.', '[.,]')}x"
            if not re.search(mult_pattern, memo_text, re.IGNORECASE):
                warnings.append(f"Múltiplo de {mult}x pode não estar mencionado")
    
    elif section == "market":
        competitors = facts.get("qualitative", {}).get("main_competitors")
        if competitors and "competidor" not in memo_text.lower():
            warnings.append("Competidores não mencionados na seção Mercado")
        
        if "de acordo com o searcher" not in memo_text.lower() and "segundo o searcher" not in memo_text.lower():
            warnings.append("Falta atribuição ao searcher nos diferenciais competitivos")
    
    elif section == "company":
        company_name = facts.get("identification", {}).get("company_name")
        if company_name and company_name not in memo_text:
            warnings.append(f"Nome da empresa '{company_name}' não mencionado")
        
        business_desc = facts.get("identification", {}).get("business_description")
        if business_desc and len(business_desc) > 10:
            keywords = [w for w in business_desc.split() if len(w) > 4][:3]
            if keywords and not any(kw.lower() in memo_text.lower() for kw in keywords):
                warnings.append("Descrição do negócio pode não estar clara")
    
    elif section == "financials":
        cagr = facts.get("financials_history", {}).get("revenue_cagr_pct")
        period = facts.get("financials_history", {}).get("revenue_cagr_period")
        if cagr and not period:
            warnings.append("CAGR mencionado mas sem período específico (ex: 2019-2024)")
        
        revenue = facts.get("financials_history", {}).get("revenue_current_mm")
        currency = facts.get("transaction_structure", {}).get("currency") or "BRL"
        currency_symbol = get_currency_symbol(currency)
        if revenue:
            rev_pattern = rf"{int(revenue)}\s*m"
            if not re.search(rev_pattern, memo_text, re.IGNORECASE):
                warnings.append(f"Receita de {currency_symbol} {revenue}m pode não estar mencionada")
    
    elif section == "transaction":
        if "atrativ" not in memo_text.lower() and "favorável" not in memo_text.lower():
            warnings.append("Falta análise sobre atratividade da estrutura da transação")
    
    return {
        "is_valid": len(missing_facts) == 0,
        "warnings": warnings,
        "missing_facts": missing_facts
    }


def fix_number_formatting(text: str) -> str:
    """Corrige formatação numérica para padrão Spectra."""
    text = re.sub(r'R\$\s*(\d+(?:[.,]\d+)?)\s*milh[õo]es?', r'R$ \1m', text, flags=re.IGNORECASE)
    text = re.sub(r'US\$\s*(\d+(?:[.,]\d+)?)\s*milh[õo]es?', r'US$ \1m', text, flags=re.IGNORECASE)
    text = re.sub(r'MX\$\s*(\d+(?:[.,]\d+)?)\s*milh[õo]es?', r'MX$ \1m', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d+)\.(\d+)x', r'\1,\2x', text)
    text = re.sub(r'(\d+)\s*%', r'\1%', text)
    text = re.sub(r'(\d+)\.(\d+)\s*MOIC', r'\1,\2 MOIC', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d+)\.(\d+)%\s*(?:IRR|TIR)', r'\1,\2% IRR', text, flags=re.IGNORECASE)
    return text


def check_section_length(
    memo_text: str,
    section: str,
    min_paragraphs: int = 2,
    max_paragraphs: int = 5
) -> Dict[str, Any]:
    """Valida se a seção tem número adequado de parágrafos."""
    paragraphs = [p.strip() for p in memo_text.split("\n\n") if p.strip()]
    count = len(paragraphs)
    is_valid = min_paragraphs <= count <= max_paragraphs
    warning = ""
    if count < min_paragraphs:
        warning = f"Seção '{section}' muito curta ({count} parágrafo(s), esperado mínimo {min_paragraphs})"
    elif count > max_paragraphs:
        warning = f"Seção '{section}' muito longa ({count} parágrafos, esperado máximo {max_paragraphs})"
    return {"is_valid": is_valid, "paragraph_count": count, "warning": warning}


def validate_search_fund_intro(memo_text: str, facts: Dict[str, Any]) -> Dict[str, Any]:
    """Validação específica para introdução de Search Fund."""
    errors = []
    id_facts = facts.get("identification", {})
    casca = id_facts.get("fip_casca") or id_facts.get("investor_name")
    searcher_names = id_facts.get("searcher_name") or id_facts.get("investor_person_names")

    # Primeira frase deve mencionar a casca/FIP ou o investidor (sujeito)
    if casca and casca not in memo_text[:250]:
        errors.append(f"Primeira frase deve mencionar a casca/FIP ou investidor '{casca}'")

    if searcher_names and searcher_names not in memo_text[:250]:
        errors.append(f"Primeira frase deve mencionar o searcher '{searcher_names}'")

    # Aceita "(search fund X liderado por" ou "(search liderado por"
    text_lower = memo_text[:350].lower()
    if "liderado por" not in text_lower:
        errors.append("Falta frase padrão: '(search fund ... liderado por {searcher}, que iniciou...'")
    if "search fund" not in text_lower and "search liderado" not in text_lower:
        errors.append("Falta menção a 'search fund' ou 'search liderado por'")

    if "iniciou seu período de busca" not in text_lower and "iniciou o período de busca" not in text_lower:
        errors.append("Falta menção ao início do período de busca")

    return {"is_valid": len(errors) == 0, "errors": errors}
