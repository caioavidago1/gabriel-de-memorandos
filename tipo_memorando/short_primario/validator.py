"""
Validação e correção de memos de Primário (Growth Equity)

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
        section: Nome da seção ("intro", "company", "financials")
    
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
        
        # Deve mencionar ARR
        arr = facts.get("financials_history", {}).get("arr_current_mm")
        if arr:
            arr_pattern = rf"{str(arr).replace('.', '[.,]')}m|{int(float(arr))}m"
            if not re.search(arr_pattern, memo_text, re.IGNORECASE):
                warnings.append(f"ARR de {arr}m pode não estar mencionado corretamente")
        
        # Deve mencionar crescimento
        growth = facts.get("financials_history", {}).get("arr_growth_yoy_pct")
        if growth:
            growth_pattern = rf"{str(growth).replace('.', '[.,]')}%"
            if not re.search(growth_pattern, memo_text, re.IGNORECASE):
                warnings.append(f"Crescimento de {growth}% pode não estar mencionado")
        
        # Deve mencionar LTV/CAC
        ltv_cac = facts.get("unit_economics", {}).get("ltv_cac_ratio")
        if ltv_cac and "ltv" not in memo_text.lower() and "cac" not in memo_text.lower():
            warnings.append("LTV/CAC não mencionado - métrica importante para SaaS")
    
    elif section == "company":
        # Deve mencionar modelo de negócio
        if "modelo" not in memo_text.lower() and "negócio" not in memo_text.lower():
            warnings.append("Modelo de negócio não claramente descrito")
        
        # Deve mencionar clientes
        if "cliente" not in memo_text.lower() and "customer" not in memo_text.lower():
            warnings.append("Base de clientes não mencionada")
    
    elif section == "financials":
        # Deve mencionar NRR
        nrr = facts.get("unit_economics", {}).get("nrr_pct")
        if nrr and "nrr" not in memo_text.lower() and "net revenue retention" not in memo_text.lower():
            warnings.append("NRR (Net Revenue Retention) não mencionado")
        
        # Deve mencionar margem bruta
        if "margem bruta" not in memo_text.lower() and "gross margin" not in memo_text.lower():
            warnings.append("Margem bruta não mencionada - importante para SaaS")
        
        # Deve ter comparação com benchmarks
        if "benchmark" not in memo_text.lower() and "peer" not in memo_text.lower():
            warnings.append("Falta comparação com benchmarks de mercado")
    
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
    - MOIC: 2.5 → 2,5x MOIC
    - IRR: 38.5% → 38,5% IRR
    
    Args:
        text: Texto do memo com formatação potencialmente incorreta
    
    Returns:
        Texto com formatação corrigida
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
    
    # MOIC: 2.5 → 2,5x MOIC
    text = re.sub(r'(\d+)\.(\d+)\s*MOIC', r'\1,\2x MOIC', text, flags=re.IGNORECASE)
    
    # IRR: 38.5% → 38,5% IRR
    text = re.sub(r'(\d+)\.(\d+)%\s*(?:IRR|TIR)', r'\1,\2% IRR', text, flags=re.IGNORECASE)
    
    # TIR: 38.5% → 38,5% TIR
    text = re.sub(r'(\d+)\.(\d+)%\s*TIR', r'\1,\2% TIR', text, flags=re.IGNORECASE)
    
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


def validate_primario_intro(memo_text: str, facts: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validação específica para introdução de Primário.
    
    Checa se segue o padrão obrigatório:
    "Estamos avaliando a {empresa}, uma plataforma {tipo} com ARR de {valor}..."
    
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
    
    # Padrão obrigatório para Primário
    if "estamos avaliando" not in memo_text[:200].lower():
        errors.append("Primeira frase deve começar com 'Estamos avaliando a {company_name}'")
    
    if "arr" not in memo_text[:400].lower() and "receita" not in memo_text[:400].lower():
        errors.append("Falta menção a ARR ou receita")
    
    if "crescimento" not in memo_text[:400].lower() and "yoy" not in memo_text[:400].lower():
        errors.append("Falta menção ao crescimento/YoY")
    
    return {
        "is_valid": len(errors) == 0,
        "errors": errors
    }


def validate_unit_economics(facts: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valida se unit economics estão completos para análise.
    
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
    
    ue = facts.get("unit_economics", {})
    
    # Métricas obrigatórias
    required_metrics = {
        "ltv_cac_ratio": "LTV/CAC ratio",
        "payback_months": "Payback em meses",
        "nrr_pct": "NRR (Net Revenue Retention)",
    }
    
    for key, label in required_metrics.items():
        if not ue.get(key):
            missing.append(label)
    
    # Validar ranges saudáveis
    ltv_cac = ue.get("ltv_cac_ratio")
    if ltv_cac and ltv_cac < 3:
        warnings.append(f"LTV/CAC de {ltv_cac}x está abaixo do benchmark de 3x")
    
    payback = ue.get("payback_months")
    if payback and payback > 18:
        warnings.append(f"Payback de {payback} meses está acima do ideal de 12-18 meses")
    
    nrr = ue.get("nrr_pct")
    if nrr and nrr < 100:
        warnings.append(f"NRR de {nrr}% abaixo de 100% indica contração na base")
    
    return {
        "complete": len(missing) == 0,
        "missing": missing,
        "warnings": warnings
    }
