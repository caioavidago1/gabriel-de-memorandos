"""
Validação e correção de memos de Gestora

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
        section: Nome da seção ("intro", "track_record", "strategy")
    
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
        # Deve mencionar nome da gestora
        gestora_name = facts.get("identification", {}).get("gestora_name")
        if gestora_name and gestora_name not in memo_text:
            missing_facts.append(f"Nome da gestora '{gestora_name}' não mencionado")
        
        # Deve mencionar AUM
        aum = facts.get("identification", {}).get("aum_mm")
        if aum:
            # Aceita "R$ 2.1 bilhões" ou "R$ 2100m" ou "2,1 bilhões"
            aum_str = str(aum)
            if not re.search(rf"{aum_str}|{int(float(aum_str)) if '.' not in aum_str else aum_str.replace('.', ',')}|bilh", memo_text, re.IGNORECASE):
                warnings.append(f"AUM de {aum} pode não estar mencionado corretamente")
        
        # Deve mencionar IRR médio
        irr = facts.get("performance", {}).get("irr_avg_pct")
        if irr:
            irr_pattern = rf"{str(irr).replace('.', '[.,]')}%"
            if not re.search(irr_pattern, memo_text, re.IGNORECASE):
                warnings.append(f"IRR médio de {irr}% pode não estar mencionado")
    
    elif section == "track_record":
        # Deve mencionar DPI
        if "dpi" not in memo_text.lower():
            warnings.append("DPI (Distributions to Paid-In) não mencionado")
        
        # Deve mencionar TVPI ou valor total
        if "tvpi" not in memo_text.lower() and "valor total" not in memo_text.lower():
            warnings.append("TVPI ou valor total não mencionado")
        
        # Deve ter análise de concentração
        if "top" not in memo_text.lower() and "concentra" not in memo_text.lower():
            warnings.append("Falta análise de concentração de retornos")
    
    elif section == "strategy":
        # Deve mencionar setores de foco
        sectors = facts.get("strategy", {}).get("focus_sectors")
        if sectors and "setor" not in memo_text.lower() and "foco" not in memo_text.lower():
            warnings.append("Setores de foco não claramente mencionados")
        
        # Deve mencionar ticket size
        ticket = facts.get("strategy", {}).get("ticket_size_mm")
        if ticket and "ticket" not in memo_text.lower():
            warnings.append("Tamanho de ticket não mencionado")
    
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
    - R$ X.X bilhões → R$ X,X bilhões
    - 3.5x → 3,5x
    - 38 % → 38%
    - 2.5 MOIC → 2,5x MOIC
    
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
    
    # DPI/TVPI: 1.5x → 1,5x
    text = re.sub(r'(\d+)\.(\d+)x?\s*(?:DPI|TVPI|RVPI)', lambda m: f"{m.group(1)},{m.group(2)}x {m.group(0).split()[-1] if len(m.group(0).split()) > 1 else 'DPI'}", text, flags=re.IGNORECASE)
    
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


def validate_gestora_intro(memo_text: str, facts: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validação específica para introdução de Gestora.
    
    Checa se segue o padrão obrigatório:
    "Estamos avaliando a {gestora}, fundada em {ano}, com foco em {estratégia}..."
    
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
    
    # Padrão obrigatório para Gestora
    if "estamos avaliando" not in memo_text[:200].lower():
        errors.append("Primeira frase deve começar com 'Estamos avaliando a {gestora_name}'")
    
    if "fundada em" not in memo_text[:300].lower():
        errors.append("Falta menção ao ano de fundação")
    
    if "foco em" not in memo_text[:300].lower() and "com foco" not in memo_text[:300].lower():
        errors.append("Falta menção à estratégia/foco da gestora")
    
    if "aum" not in memo_text[:400].lower() and "bilh" not in memo_text[:400].lower():
        errors.append("Falta menção ao AUM")
    
    return {
        "is_valid": len(errors) == 0,
        "errors": errors
    }
