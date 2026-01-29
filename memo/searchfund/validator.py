"""
Validador de Memo Completo Search Fund

Utilitários para validar consistência, formatar números e garantir qualidade do memo.
"""

import re
from typing import Dict, Any, List, Tuple, Optional


def fix_number_formatting(text: str) -> str:
    """
    Corrige formatação de números para padrão brasileiro.
    
    Exemplos:
        1.5x -> 1,5x
        15% -> 15%
        R$10MM -> R$ 10 MM
    """
    # Corrigir pontos decimais para vírgulas em números
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
    
    Para Memo Completo, esperamos 5-8 parágrafos por seção (vs 2-4 no Short Memo).
    
    Args:
        section_text: Texto da seção gerada
        section_name: Nome da seção para mensagens de erro
    
    Returns:
        Tuple (is_valid, message)
    """
    paragraphs = [p.strip() for p in section_text.split('\n\n') if p.strip()]
    num_paragraphs = len(paragraphs)
    
    if num_paragraphs < 4:
        return False, f"Seção '{section_name}' muito curta: {num_paragraphs} parágrafos (mínimo: 4 para Memo Completo)"
    
    if num_paragraphs > 10:
        return False, f"Seção '{section_name}' muito longa: {num_paragraphs} parágrafos (máximo: 10)"
    
    # Verificar tamanho médio dos parágrafos (mínimo ~3 linhas)
    total_chars = sum(len(p) for p in paragraphs)
    avg_paragraph_length = total_chars / num_paragraphs
    
    if avg_paragraph_length < 200:
        return False, f"Parágrafos de '{section_name}' muito curtos (média: {avg_paragraph_length:.0f} chars, mínimo: 200)"
    
    return True, f"Seção '{section_name}' validada: {num_paragraphs} parágrafos, {total_chars} caracteres"


def validate_memo_consistency(facts: Dict[str, Any], generated_text: str) -> List[str]:
    """
    Valida consistência entre facts e texto gerado.
    
    Verifica:
    - Números mencionados batem com facts
    - Nomes de empresas corretos
    - Percentuais coerentes
    
    Args:
        facts: Dict de facts estruturados
        generated_text: Texto gerado pelo LLM
    
    Returns:
        Lista de warnings (vazia se tudo OK)
    """
    warnings = []
    
    # Extrair valores-chave dos facts
    idf = facts.get("identification", {})
    trx = facts.get("transaction_structure", {})
    fin = facts.get("financials_history", {})
    ret = facts.get("returns", {})
    
    # Validar nome da empresa
    company_name = idf.get("company_name")
    if company_name and company_name not in generated_text:
        warnings.append(f"Nome da empresa '{company_name}' não encontrado no texto")
    
    # Validar EV
    ev = trx.get("ev_mm")
    if ev:
        ev_str = str(ev).replace('.', ',')
        if ev_str not in generated_text and str(ev) not in generated_text:
            warnings.append(f"EV de {ev} MM não encontrado no texto")
    
    # Validar stake
    stake = trx.get("stake_pct")
    if stake:
        stake_str = str(stake).replace('.', ',')
        if f"{stake_str}%" not in generated_text and f"{stake}%" not in generated_text:
            warnings.append(f"Participação de {stake}% não encontrada no texto")
    
    # Validar múltiplo
    multiple = trx.get("multiple_ev_ebitda")
    if multiple:
        multiple_str = str(multiple).replace('.', ',')
        if f"{multiple_str}x" not in generated_text.lower() and f"{multiple}x" not in generated_text.lower():
            warnings.append(f"Múltiplo de {multiple}x não encontrado no texto")
    
    # Validar IRR
    irr = ret.get("irr_pct")
    if irr:
        irr_str = str(irr).replace('.', ',')
        if f"{irr_str}%" not in generated_text and f"{irr}%" not in generated_text:
            warnings.append(f"IRR de {irr}% não encontrado no texto")
    
    # Validar MOIC
    moic = ret.get("moic")
    if moic:
        moic_str = str(moic).replace('.', ',')
        if f"{moic_str}x" not in generated_text.lower() and f"{moic}x" not in generated_text.lower():
            warnings.append(f"MOIC de {moic}x não encontrado no texto")
    
    return warnings


def validate_financial_coherence(facts: Dict[str, Any]) -> List[str]:
    """
    Valida coerência matemática dos facts financeiros.
    
    Verifica:
    - Margem EBITDA = EBITDA / Receita
    - Múltiplo = EV / EBITDA
    - Soma de pagamentos = EV
    
    Returns:
        Lista de warnings de inconsistência
    """
    warnings = []
    
    trx = facts.get("transaction_structure", {})
    fin = facts.get("financials_history", {})
    
    # Verificar múltiplo EV/EBITDA
    ev = trx.get("ev_mm")
    ebitda = fin.get("ebitda_current_mm")
    multiple = trx.get("multiple_ev_ebitda")
    
    if ev and ebitda and multiple:
        calculated_multiple = round(float(ev) / float(ebitda), 1)
        if abs(calculated_multiple - float(multiple)) > 0.3:
            warnings.append(
                f"Múltiplo inconsistente: EV/EBITDA calculado = {calculated_multiple}x, "
                f"informado = {multiple}x"
            )
    
    # Verificar margem EBITDA
    revenue = fin.get("revenue_current_mm")
    ebitda_margin = fin.get("ebitda_margin_current_pct")
    
    if revenue and ebitda and ebitda_margin:
        calculated_margin = round(float(ebitda) / float(revenue) * 100, 1)
        if abs(calculated_margin - float(ebitda_margin)) > 2:
            warnings.append(
                f"Margem inconsistente: EBITDA/Receita = {calculated_margin}%, "
                f"informado = {ebitda_margin}%"
            )
    
    # Verificar soma de pagamentos
    cash = trx.get("cash_payment_mm", 0) or 0
    seller_note = trx.get("seller_note_mm", 0) or 0
    earnout = trx.get("earnout_mm", 0) or 0
    
    if ev and (cash or seller_note or earnout):
        total_payments = float(cash) + float(seller_note) + float(earnout)
        if abs(total_payments - float(ev)) > 0.5:
            warnings.append(
                f"Soma de pagamentos ({total_payments} MM) difere do EV ({ev} MM)"
            )
    
    return warnings


def validate_returns_coherence(facts: Dict[str, Any]) -> List[str]:
    """
    Valida coerência das projeções de retorno.
    
    Verifica:
    - MOIC faz sentido com IRR e holding period
    - Cenários upside > base > downside
    
    Returns:
        Lista de warnings
    """
    warnings = []
    
    ret = facts.get("returns", {})
    
    irr = ret.get("irr_pct")
    moic = ret.get("moic")
    holding = ret.get("holding_period_years")
    
    # Verificar relação IRR/MOIC/Holding
    if irr and moic and holding:
        try:
            irr_f = float(irr) / 100
            moic_f = float(moic)
            holding_f = float(holding)
            
            # MOIC = (1 + IRR)^holding aproximadamente
            expected_moic = (1 + irr_f) ** holding_f
            
            if abs(expected_moic - moic_f) > 0.5:
                warnings.append(
                    f"MOIC/IRR parecem inconsistentes: IRR {irr}% em {holding} anos "
                    f"deveria dar ~{expected_moic:.1f}x, informado {moic}x"
                )
        except (ValueError, TypeError):
            pass
    
    # Verificar ordenação de cenários
    irr_base = ret.get("irr_pct") or ret.get("irr_base_case")
    irr_upside = ret.get("irr_upside_pct")
    irr_downside = ret.get("irr_downside_pct")
    
    if irr_base and irr_upside and irr_downside:
        try:
            base_f = float(irr_base)
            up_f = float(irr_upside)
            down_f = float(irr_downside)
            
            if not (up_f > base_f > down_f):
                warnings.append(
                    f"Cenários fora de ordem: upside ({up_f}%) deve ser > "
                    f"base ({base_f}%) > downside ({down_f}%)"
                )
        except (ValueError, TypeError):
            pass
    
    return warnings


def validate_complete_memo(
    facts: Dict[str, Any],
    sections: Dict[str, str]
) -> Dict[str, Any]:
    """
    Validação completa do memo antes de finalização.
    
    Args:
        facts: Dict de facts estruturados
        sections: Dict com seções geradas {"intro": "...", "company": "...", etc}
    
    Returns:
        Dict com resultados de validação
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
    
    # Validar coerência financeira dos facts
    financial_warnings = validate_financial_coherence(facts)
    if financial_warnings:
        results["warnings"].extend(financial_warnings)
    
    # Validar coerência de retornos
    returns_warnings = validate_returns_coherence(facts)
    if returns_warnings:
        results["warnings"].extend(returns_warnings)
    
    # Calcular estatísticas totais
    total_chars = sum(stats["char_count"] for stats in results["section_stats"].values())
    total_paragraphs = sum(stats["paragraph_count"] for stats in results["section_stats"].values())
    
    results["total_stats"] = {
        "total_characters": total_chars,
        "total_paragraphs": total_paragraphs,
        "estimated_pages": total_chars / 3000,  # ~3000 chars por página
        "sections_count": len(sections)
    }
    
    return results


def format_validation_report(validation_results: Dict[str, Any]) -> str:
    """
    Formata relatório de validação para exibição.
    
    Args:
        validation_results: Output de validate_complete_memo
    
    Returns:
        Relatório formatado em texto
    """
    lines = ["=" * 60]
    lines.append("RELATÓRIO DE VALIDAÇÃO - MEMO COMPLETO")
    lines.append("=" * 60)
    
    # Status geral
    status = "✅ APROVADO" if validation_results["is_valid"] else "❌ REPROVADO"
    lines.append(f"\nStatus: {status}")
    
    # Estatísticas totais
    stats = validation_results.get("total_stats", {})
    lines.append(f"\nEstatísticas Totais:")
    lines.append(f"  - Seções: {stats.get('sections_count', 0)}")
    lines.append(f"  - Parágrafos: {stats.get('total_paragraphs', 0)}")
    lines.append(f"  - Caracteres: {stats.get('total_characters', 0):,}")
    lines.append(f"  - Páginas estimadas: {stats.get('estimated_pages', 0):.1f}")
    
    # Detalhes por seção
    lines.append(f"\nDetalhes por Seção:")
    for section, section_stats in validation_results.get("section_stats", {}).items():
        status_icon = "✅" if section_stats["valid"] else "❌"
        lines.append(f"  {status_icon} {section}: {section_stats['paragraph_count']} parágrafos, "
                    f"{section_stats['char_count']:,} chars")
    
    # Erros
    if validation_results.get("errors"):
        lines.append(f"\n❌ Erros ({len(validation_results['errors'])}):")
        for error in validation_results["errors"]:
            lines.append(f"  - {error}")
    
    # Warnings
    if validation_results.get("warnings"):
        lines.append(f"\n⚠️ Avisos ({len(validation_results['warnings'])}):")
        for warning in validation_results["warnings"]:
            lines.append(f"  - {warning}")
    
    lines.append("\n" + "=" * 60)
    
    return "\n".join(lines)


def validate_no_redundancy(sections: Dict[str, str], threshold: float = 0.3) -> Dict[str, Any]:
    """
    Valida se há redundâncias significativas entre seções do memo.
    
    Compara conteúdo entre seções usando similaridade de texto e identifica
    sobreposições significativas que devem ser removidas.
    
    Args:
        sections: Dict com seções geradas {section_title: text, ...}
        threshold: Threshold de similaridade para considerar redundância (0.0-1.0)
    
    Returns:
        Dict com:
        {
            "has_redundancy": bool,
            "redundant_pairs": List[Tuple[str, str, float]],  # (section1, section2, similarity)
            "suggestions": List[str]  # Sugestões de ajuste
        }
    """
    from difflib import SequenceMatcher
    
    redundant_pairs = []
    suggestions = []
    
    section_names = list(sections.keys())
    
    # Comparar cada par de seções
    for i, section1_name in enumerate(section_names):
        for j, section2_name in enumerate(section_names[i+1:], start=i+1):
            section1_text = sections[section1_name].lower()
            section2_text = sections[section2_name].lower()
            
            # Calcular similaridade usando SequenceMatcher
            similarity = SequenceMatcher(None, section1_text, section2_text).ratio()
            
            if similarity > threshold:
                redundant_pairs.append((section1_name, section2_name, similarity))
                
                # Gerar sugestão
                suggestions.append(
                    f"Redundância detectada entre '{section1_name}' e '{section2_name}' "
                    f"(similaridade: {similarity:.1%}). "
                    f"Considere remover informações duplicadas ou ajustar o escopo de cada seção."
                )
    
    # Verificar seções que mencionam os mesmos números/fatos repetidamente
    # (isso é mais difícil de detectar automaticamente, mas podemos sugerir)
    
    return {
        "has_redundancy": len(redundant_pairs) > 0,
        "redundant_pairs": redundant_pairs,
        "suggestions": suggestions,
        "total_checks": len(section_names) * (len(section_names) - 1) // 2
    }
