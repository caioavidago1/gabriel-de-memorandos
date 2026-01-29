"""
Validador de Memo Completo Gestora

Utilitários para validar consistência, formatar números e garantir qualidade do memo.
"""

import re
from typing import Dict, Any, List, Tuple, Optional


def fix_number_formatting(text: str) -> str:
    """
    Corrige formatação de números para padrão brasileiro.
    """
    # Corrigir pontos decimais para vírgulas
    text = re.sub(r'(\d)\.(\d)', r'\1,\2', text)
    
    # Garantir espaço antes de MM
    text = re.sub(r'(R\$\s?)(\d+)(MM)', r'R$ \2 MM', text)
    
    # Padronizar R$ com espaço
    text = re.sub(r'R\$(\d)', r'R$ \1', text)
    
    # Garantir formato de múltiplos (x)
    text = re.sub(r'(\d+,?\d*)X\b', r'\1x', text, flags=re.IGNORECASE)
    
    return text


def validate_section_length(section_text: str, section_name: str) -> Tuple[bool, str]:
    """
    Valida se a seção tem tamanho adequado para Memo Completo.
    """
    paragraphs = [p.strip() for p in section_text.split('\n\n') if p.strip()]
    num_paragraphs = len(paragraphs)
    
    if num_paragraphs < 4:
        return False, f"Seção '{section_name}' muito curta: {num_paragraphs} parágrafos (mínimo: 4)"
    
    if num_paragraphs > 10:
        return False, f"Seção '{section_name}' muito longa: {num_paragraphs} parágrafos (máximo: 10)"
    
    total_chars = sum(len(p) for p in paragraphs)
    avg_paragraph_length = total_chars / num_paragraphs
    
    if avg_paragraph_length < 200:
        return False, f"Parágrafos muito curtos (média: {avg_paragraph_length:.0f} chars)"
    
    return True, f"Seção '{section_name}' validada: {num_paragraphs} parágrafos"


def validate_memo_consistency(facts: Dict[str, Any], generated_text: str) -> List[str]:
    """
    Valida consistência entre facts e texto gerado.
    """
    warnings = []
    
    idf = facts.get("identification", {})
    trx = facts.get("transaction_structure", {})
    ret = facts.get("returns", {})
    
    # Validar nome da gestora
    fund_manager = idf.get("fund_manager_name")
    if fund_manager and fund_manager not in generated_text:
        warnings.append(f"Nome da gestora '{fund_manager}' não encontrado")
    
    # Validar tamanho do fundo
    fund_size = trx.get("fund_size_mm")
    if fund_size:
        if str(fund_size) not in generated_text:
            warnings.append(f"Tamanho do fundo ({fund_size} MM) não encontrado")
    
    # Validar management fee
    mgmt_fee = trx.get("management_fee_pct")
    if mgmt_fee:
        if f"{mgmt_fee}%" not in generated_text:
            warnings.append(f"Management fee ({mgmt_fee}%) não encontrado")
    
    # Validar IRR alvo
    irr = ret.get("target_irr_net_pct")
    if irr:
        if f"{irr}%" not in generated_text:
            warnings.append(f"IRR alvo ({irr}%) não encontrado")
    
    return warnings


def validate_track_record_coherence(facts: Dict[str, Any]) -> List[str]:
    """
    Valida coerência dos dados de track record.
    """
    warnings = []
    
    tr = facts.get("track_record", {})
    
    # Verificar IRR vs MOIC
    irr = tr.get("realized_irr_gross_pct")
    moic = tr.get("realized_moic_gross")
    
    if irr and moic:
        try:
            irr_f = float(irr) / 100
            moic_f = float(moic)
            
            # Assumindo holding de 5 anos em média
            expected_moic = (1 + irr_f) ** 5
            
            if abs(expected_moic - moic_f) > 1.0:
                warnings.append(
                    f"IRR ({irr}%) e MOIC ({moic}x) parecem inconsistentes "
                    f"para holding típico de 5 anos"
                )
        except (ValueError, TypeError):
            pass
    
    # Verificar taxa de perda
    loss_ratio = tr.get("loss_ratio_pct")
    if loss_ratio:
        try:
            loss_f = float(loss_ratio)
            if loss_f > 25:
                warnings.append(f"Taxa de perda elevada: {loss_ratio}%")
            elif loss_f < 1:
                warnings.append(f"Taxa de perda muito baixa ({loss_ratio}%), pode estar incompleta")
        except (ValueError, TypeError):
            pass
    
    return warnings


def validate_terms_coherence(facts: Dict[str, Any]) -> List[str]:
    """
    Valida coerência dos termos do fundo.
    """
    warnings = []
    
    trx = facts.get("transaction_structure", {})
    
    # Verificar management fee
    mgmt_fee = trx.get("management_fee_pct")
    if mgmt_fee:
        try:
            fee_f = float(mgmt_fee)
            if fee_f > 2.5:
                warnings.append(f"Management fee acima do padrão: {mgmt_fee}%")
            elif fee_f < 1.0:
                warnings.append(f"Management fee abaixo do padrão: {mgmt_fee}%")
        except (ValueError, TypeError):
            pass
    
    # Verificar carried interest
    carry = trx.get("carried_interest_pct")
    if carry:
        try:
            carry_f = float(carry)
            if carry_f > 25:
                warnings.append(f"Carried interest acima do padrão: {carry}%")
            elif carry_f < 15:
                warnings.append(f"Carried interest abaixo do padrão: {carry}%")
        except (ValueError, TypeError):
            pass
    
    # Verificar GP commitment
    gp_commit = trx.get("gp_commitment_pct")
    if gp_commit:
        try:
            gp_f = float(gp_commit)
            if gp_f < 1:
                warnings.append(f"GP commitment baixo: {gp_commit}%")
        except (ValueError, TypeError):
            pass
    
    return warnings


def validate_complete_memo(
    facts: Dict[str, Any],
    sections: Dict[str, str]
) -> Dict[str, Any]:
    """
    Validação completa do memo de gestora.
    """
    results = {
        "is_valid": True,
        "errors": [],
        "warnings": [],
        "section_stats": {}
    }
    
    # Validar cada seção
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
        
        # Validar consistência com facts
        consistency_warnings = validate_memo_consistency(facts, section_text)
        if consistency_warnings:
            results["warnings"].extend(consistency_warnings)
    
    # Validar track record
    tr_warnings = validate_track_record_coherence(facts)
    if tr_warnings:
        results["warnings"].extend(tr_warnings)
    
    # Validar termos
    terms_warnings = validate_terms_coherence(facts)
    if terms_warnings:
        results["warnings"].extend(terms_warnings)
    
    # Calcular estatísticas totais
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
    """
    Formata relatório de validação.
    """
    lines = ["=" * 60]
    lines.append("RELATÓRIO DE VALIDAÇÃO - MEMO GESTORA")
    lines.append("=" * 60)
    
    status = "✅ APROVADO" if validation_results["is_valid"] else "❌ REPROVADO"
    lines.append(f"\nStatus: {status}")
    
    stats = validation_results.get("total_stats", {})
    lines.append(f"\nEstatísticas Totais:")
    lines.append(f"  - Seções: {stats.get('sections_count', 0)}")
    lines.append(f"  - Parágrafos: {stats.get('total_paragraphs', 0)}")
    lines.append(f"  - Páginas estimadas: {stats.get('estimated_pages', 0):.1f}")
    
    for section, section_stats in validation_results.get("section_stats", {}).items():
        status_icon = "✅" if section_stats["valid"] else "❌"
        lines.append(f"  {status_icon} {section}: {section_stats['paragraph_count']} parágrafos")
    
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
