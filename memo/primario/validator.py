"""
Validador de Memo Completo Primário

Utilitários para validar consistência e qualidade do memo.
"""

import re
from typing import Dict, Any, List, Tuple


def fix_number_formatting(text: str) -> str:
    """Corrige formatação de números para padrão brasileiro."""
    text = re.sub(r'(\d)\.(\d)', r'\1,\2', text)
    text = re.sub(r'(R\$\s?)(\d+)(MM)', r'R$ \2 MM', text)
    text = re.sub(r'R\$(\d)', r'R$ \1', text)
    text = re.sub(r'(\d+,?\d*)X\b', r'\1x', text, flags=re.IGNORECASE)
    return text


def validate_section_length(section_text: str, section_name: str) -> Tuple[bool, str]:
    """Valida se a seção tem tamanho adequado."""
    paragraphs = [p.strip() for p in section_text.split('\n\n') if p.strip()]
    num_paragraphs = len(paragraphs)
    
    if num_paragraphs < 4:
        return False, f"Seção '{section_name}' muito curta: {num_paragraphs} parágrafos"
    if num_paragraphs > 10:
        return False, f"Seção '{section_name}' muito longa: {num_paragraphs} parágrafos"
    
    return True, f"Seção '{section_name}' validada: {num_paragraphs} parágrafos"


def validate_memo_consistency(facts: Dict[str, Any], generated_text: str) -> List[str]:
    """Valida consistência entre facts e texto gerado."""
    warnings = []
    
    idf = facts.get("identification", {})
    trx = facts.get("transaction_structure", {})
    fin = facts.get("financials_history", {})
    
    # Validar nome da empresa
    company_name = idf.get("company_name")
    if company_name and company_name not in generated_text:
        warnings.append(f"Nome da empresa '{company_name}' não encontrado")
    
    # Validar tamanho da rodada
    round_size = trx.get("round_size_mm")
    if round_size:
        if str(round_size) not in generated_text:
            warnings.append(f"Tamanho da rodada ({round_size} MM) não encontrado")
    
    # Validar valuation
    pre_money = trx.get("pre_money_mm")
    if pre_money:
        if str(pre_money) not in generated_text:
            warnings.append(f"Pre-money valuation ({pre_money} MM) não encontrado")
    
    return warnings


def validate_saas_metrics(facts: Dict[str, Any]) -> List[str]:
    """Valida coerência das métricas SaaS."""
    warnings = []
    
    fin = facts.get("financials_history", {})
    
    # Validar LTV/CAC
    ltv_cac = fin.get("ltv_cac_ratio")
    if ltv_cac:
        try:
            ratio = float(ltv_cac)
            if ratio < 3:
                warnings.append(f"LTV/CAC baixo ({ltv_cac}x) - benchmark mínimo é 3x")
            elif ratio > 10:
                warnings.append(f"LTV/CAC muito alto ({ltv_cac}x) - verificar premissas")
        except (ValueError, TypeError):
            pass
    
    # Validar NRR
    nrr = fin.get("net_revenue_retention_pct")
    if nrr:
        try:
            nrr_f = float(nrr)
            if nrr_f < 100:
                warnings.append(f"NRR abaixo de 100% ({nrr}%) - indica contração")
            elif nrr_f > 150:
                warnings.append(f"NRR muito alto ({nrr}%) - verificar cálculo")
        except (ValueError, TypeError):
            pass
    
    # Validar payback
    payback = fin.get("payback_months")
    if payback:
        try:
            payback_f = float(payback)
            if payback_f > 24:
                warnings.append(f"Payback longo ({payback} meses) - benchmark < 18 meses")
        except (ValueError, TypeError):
            pass
    
    return warnings


def validate_valuation_coherence(facts: Dict[str, Any]) -> List[str]:
    """Valida coerência do valuation."""
    warnings = []
    
    trx = facts.get("transaction_structure", {})
    fin = facts.get("financials_history", {})
    
    pre_money = trx.get("pre_money_mm")
    arr = fin.get("arr_mm")
    
    if pre_money and arr:
        try:
            pre_f = float(pre_money)
            arr_f = float(arr)
            multiple = pre_f / arr_f
            
            if multiple > 20:
                warnings.append(f"Múltiplo ARR alto ({multiple:.1f}x) - verificar justificativa")
            elif multiple < 3:
                warnings.append(f"Múltiplo ARR baixo ({multiple:.1f}x) - oportunidade?")
        except (ValueError, TypeError, ZeroDivisionError):
            pass
    
    return warnings


def validate_complete_memo(
    facts: Dict[str, Any],
    sections: Dict[str, str]
) -> Dict[str, Any]:
    """Validação completa do memo primário."""
    results = {
        "is_valid": True,
        "errors": [],
        "warnings": [],
        "section_stats": {}
    }
    
    for section_name, section_text in sections.items():
        is_valid, message = validate_section_length(section_text, section_name)
        
        results["section_stats"][section_name] = {
            "valid": is_valid,
            "message": message,
            "char_count": len(section_text),
            "paragraph_count": len([p for p in section_text.split('\n\n') if p.strip()])
        }
        
        if not is_valid:
            results["errors"].append(message)
            results["is_valid"] = False
        
        consistency_warnings = validate_memo_consistency(facts, section_text)
        if consistency_warnings:
            results["warnings"].extend(consistency_warnings)
    
    # Validações específicas de SaaS
    saas_warnings = validate_saas_metrics(facts)
    if saas_warnings:
        results["warnings"].extend(saas_warnings)
    
    # Validações de valuation
    valuation_warnings = validate_valuation_coherence(facts)
    if valuation_warnings:
        results["warnings"].extend(valuation_warnings)
    
    total_chars = sum(stats["char_count"] for stats in results["section_stats"].values())
    total_paragraphs = sum(stats["paragraph_count"] for stats in results["section_stats"].values())
    
    results["total_stats"] = {
        "total_characters": total_chars,
        "total_paragraphs": total_paragraphs,
        "estimated_pages": total_chars / 3000,
        "sections_count": len(sections)
    }
    
    return results


def format_validation_report(validation_results: Dict[str, Any]) -> str:
    """Formata relatório de validação."""
    lines = ["=" * 60]
    lines.append("RELATÓRIO DE VALIDAÇÃO - MEMO PRIMÁRIO")
    lines.append("=" * 60)
    
    status = "✅ APROVADO" if validation_results["is_valid"] else "❌ REPROVADO"
    lines.append(f"\nStatus: {status}")
    
    stats = validation_results.get("total_stats", {})
    lines.append(f"\nEstatísticas:")
    lines.append(f"  - Seções: {stats.get('sections_count', 0)}")
    lines.append(f"  - Parágrafos: {stats.get('total_paragraphs', 0)}")
    lines.append(f"  - Páginas estimadas: {stats.get('estimated_pages', 0):.1f}")
    
    if validation_results.get("errors"):
        lines.append(f"\n❌ Erros:")
        for error in validation_results["errors"]:
            lines.append(f"  - {error}")
    
    if validation_results.get("warnings"):
        lines.append(f"\n⚠️ Avisos:")
        for warning in validation_results["warnings"]:
            lines.append(f"  - {warning}")
    
    lines.append("\n" + "=" * 60)
    return "\n".join(lines)
