"""
Validação e correção de memos de Secundário

Funções para validar consistência entre facts e texto gerado,
e corrigir formatação numérica para padrão Spectra.
Seguindo padrão estabelecido em shortmemo/searchfund/validator.py
"""

import re
from typing import Dict, Any


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
        section: Nome da seção ("intro", "financials", "transaction")
    
    Returns:
        {
            "is_valid": bool,
            "warnings": List[str],
            "missing_facts": List[str]
        }
    """
    warnings = []
    missing_facts = []
    
    # Validações específicas por seção
    if section == "intro":
        # Deve mencionar nome da empresa
        company_name = facts.get("identification", {}).get("company_name")
        if company_name and company_name not in memo_text:
            missing_facts.append(f"Nome da empresa '{company_name}' não mencionado")
        
        # Deve mencionar margem EBITDA
        margin = facts.get("financials_history", {}).get("ebitda_margin_pct")
        if margin:
            margin_pattern = rf"{str(margin).replace('.', '[.,]')}%"
            if not re.search(margin_pattern, memo_text, re.IGNORECASE):
                warnings.append(f"Margem EBITDA de {margin}% pode não estar mencionada")
        
        # Deve mencionar FCF yield ou geração de caixa
        if "fcf" not in memo_text.lower() and "geração de caixa" not in memo_text.lower():
            warnings.append("FCF ou geração de caixa não mencionado - importante para secundário")
    
    elif section == "financials":
        # Deve mencionar estabilidade de margens
        if "estab" not in memo_text.lower() and "consist" not in memo_text.lower():
            warnings.append("Falta análise de estabilidade/consistência de margens")
        
        # Deve mencionar conversão de FCF
        if "conversão" not in memo_text.lower() and "fcf" not in memo_text.lower():
            warnings.append("Conversão de FCF não mencionada")
        
        # Deve ter análise histórica (5 anos)
        if "5 anos" not in memo_text.lower() and "últimos anos" not in memo_text.lower():
            warnings.append("Falta análise histórica (5 anos)")
    
    elif section == "transaction":
        # Deve mencionar alavancagem
        if "alavancagem" not in memo_text.lower() and "dívida" not in memo_text.lower():
            warnings.append("Alavancagem/estrutura de dívida não mencionada")
        
        # Deve ter breakdown de retornos
        if "fcf" not in memo_text.lower() or "exit" not in memo_text.lower():
            warnings.append("Falta breakdown de retornos (FCF + recap + exit)")
        
        # Deve mencionar dividend recap
        if "dividend" not in memo_text.lower() and "recap" not in memo_text.lower() and "distribuiç" not in memo_text.lower():
            warnings.append("Dividend recapitalization não mencionado")
    
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
    - FCF de 55.5 → FCF de 55,5
    
    Args:
        text: Texto do memo com formatação potencialmente incorreta
    
    Returns:
        Texto com formatação corrigida
    """
    # R$ XXX milhões → R$ XXXm
    text = re.sub(r'R\$\s*(\d+(?:[.,]\d+)?)\s*milh[õo]es?', r'R$ \1m', text, flags=re.IGNORECASE)
    
    # US$ XXX milhões → US$ XXXm
    text = re.sub(r'US\$\s*(\d+(?:[.,]\d+)?)\s*milh[õo]es?', r'US$ \1m', text, flags=re.IGNORECASE)
    
    # Múltiplos com ponto → vírgula (3.5x → 3,5x)
    text = re.sub(r'(\d+)\.(\d+)x', r'\1,\2x', text)
    
    # Espaço antes de % → sem espaço (38 % → 38%)
    text = re.sub(r'(\d+)\s*%', r'\1%', text)
    
    # MOIC: 2.5 → 2,5
    text = re.sub(r'(\d+)\.(\d+)\s*MOIC', r'\1,\2x MOIC', text, flags=re.IGNORECASE)
    
    # IRR: 38.5% → 38,5%
    text = re.sub(r'(\d+)\.(\d+)%\s*(?:IRR|TIR)', r'\1,\2% IRR', text, flags=re.IGNORECASE)
    
    # FCF com ponto → vírgula
    text = re.sub(r'FCF de (\d+)\.(\d+)', r'FCF de \1,\2', text, flags=re.IGNORECASE)
    
    # Dívida/EBITDA com ponto → vírgula
    text = re.sub(r'(\d+)\.(\d+)x\s*(?:Dívida|Debt)', r'\1,\2x Dívida', text, flags=re.IGNORECASE)
    
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


def validate_secundario_intro(memo_text: str, facts: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validação específica para introdução de Secundário.
    
    Checa se segue o padrão obrigatório:
    "Estamos avaliando a {empresa}, líder no segmento de {setor}..."
    
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
    
    # Padrão obrigatório para Secundário
    if "estamos avaliando" not in memo_text[:200].lower():
        errors.append("Primeira frase deve começar com 'Estamos avaliando a {company_name}'")
    
    if "líder" not in memo_text[:300].lower() and "posição" not in memo_text[:300].lower():
        errors.append("Falta menção à posição de mercado")
    
    if "margem ebitda" not in memo_text[:400].lower() and "ebitda" not in memo_text[:400].lower():
        errors.append("Falta menção à margem EBITDA")
    
    return {
        "is_valid": len(errors) == 0,
        "errors": errors
    }


def validate_fcf_metrics(facts: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valida se métricas de FCF estão completas para análise de secundário.
    
    Args:
        facts: Facts estruturados
    
    Returns:
        {
            "complete": bool,
            "missing": List[str],
            "warnings": List[str]
        }
    """
    missing = []
    warnings = []
    
    fin = facts.get("financials_history", {})
    ret = facts.get("returns", {})
    
    # Métricas obrigatórias
    required_metrics = {
        "fcf_current_mm": "FCF atual",
        "fcf_conversion_pct": "Conversão de FCF",
        "ebitda_margin_pct": "Margem EBITDA",
    }
    
    for key, label in required_metrics.items():
        if not fin.get(key):
            missing.append(label)
    
    # Validar ranges saudáveis para secundário
    fcf_conversion = fin.get("fcf_conversion_pct")
    if fcf_conversion and fcf_conversion < 60:
        warnings.append(f"Conversão de FCF de {fcf_conversion}% está abaixo do ideal de 70%+")
    
    ebitda_margin = fin.get("ebitda_margin_pct")
    if ebitda_margin and ebitda_margin < 15:
        warnings.append(f"Margem EBITDA de {ebitda_margin}% pode ser baixa para secundário")
    
    fcf_yield = ret.get("fcf_yield_pct")
    if fcf_yield and fcf_yield < 10:
        warnings.append(f"FCF yield de {fcf_yield}% pode não justificar tese de dividendos")
    
    return {
        "complete": len(missing) == 0,
        "missing": missing,
        "warnings": warnings
    }
