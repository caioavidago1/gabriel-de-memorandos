"""
Validador de Memo Completo Secundário

Funções de validação para memos completos de transações secundárias.
"""

import re
from typing import Dict, List, Tuple


def fix_number_formatting(text: str) -> str:
    """
    Corrige formatação de números no texto do memo.
    
    Regras:
    - R$ 150 milhões (não R$150MM)
    - US$ 50 million
    - 2,5x (não 2.5x)
    - 15% (não 15 p.p. exceto quando for diferença)
    """
    # Corrigir R$XXX para R$ XXX
    text = re.sub(r'R\$(\d)', r'R$ \1', text)
    
    # Corrigir US$XXX para US$ XXX
    text = re.sub(r'US\$(\d)', r'US$ \1', text)
    
    # Corrigir MM para milhões
    text = re.sub(r'(\d+)\s*MM\b', r'\1 milhões', text)
    
    # Corrigir bi para bilhões
    text = re.sub(r'(\d+)\s*bi\b', r'\1 bilhões', text, flags=re.IGNORECASE)
    
    # Corrigir múltiplos com ponto para vírgula (2.5x -> 2,5x)
    text = re.sub(r'(\d+)\.(\d+)x\b', r'\1,\2x', text)
    
    return text


def validate_section_length(section: str, min_paragraphs: int = 5, max_paragraphs: int = 8) -> Tuple[bool, str]:
    """
    Valida se a seção tem o número adequado de parágrafos.
    
    Args:
        section: Texto da seção
        min_paragraphs: Mínimo de parágrafos esperados
        max_paragraphs: Máximo de parágrafos esperados
    
    Returns:
        Tupla (válido, mensagem)
    """
    paragraphs = [p.strip() for p in section.split('\n\n') if p.strip() and len(p.strip()) > 50]
    count = len(paragraphs)
    
    if count < min_paragraphs:
        return False, f"Seção muito curta: {count} parágrafos (mínimo: {min_paragraphs})"
    elif count > max_paragraphs:
        return False, f"Seção muito longa: {count} parágrafos (máximo: {max_paragraphs})"
    else:
        return True, f"Seção adequada: {count} parágrafos"


def validate_secondary_metrics(text: str) -> Tuple[bool, List[str]]:
    """
    Valida se o memo contém as métricas essenciais de transações secundárias.
    
    Returns:
        Tupla (tem_todas_metricas, lista_metricas_faltando)
    """
    required_metrics = [
        (r'desconto.*(?:NAV|sobre)', "Desconto sobre NAV"),
        (r'NAV\s+(?:reportado|de|combinado)', "NAV reportado"),
        (r'(?:DPI|TVPI|RVPI)', "Métricas de retorno (DPI/TVPI)"),
        (r'unfunded|capital\s+chamado', "Unfunded commitments"),
        (r'vintage\s+(?:year|\d{4})', "Vintage year"),
        (r'(?:TIR|IRR)\s+(?:brut|líquid|projetad)', "TIR projetada"),
        (r'(?:MOIC|múltiplo)', "Múltiplo (MOIC)"),
    ]
    
    missing = []
    for pattern, name in required_metrics:
        if not re.search(pattern, text, re.IGNORECASE):
            missing.append(name)
    
    return len(missing) == 0, missing


def validate_nav_consistency(text: str) -> Tuple[bool, str]:
    """
    Valida consistência das menções a NAV no memo.
    
    Returns:
        Tupla (consistente, mensagem)
    """
    # Extrair menções a NAV com valores
    nav_mentions = re.findall(r'NAV\s+(?:de|reportado|combinado)?\s*(?:de)?\s*R\$\s*([\d,\.]+)\s*(milh[õo]es|bilh[õo]es)?', text, re.IGNORECASE)
    
    if len(nav_mentions) < 2:
        return True, "Poucas menções a NAV para validação"
    
    # Converter para valores numéricos
    values = []
    for match in nav_mentions:
        value = float(match[0].replace(',', '.'))
        if 'bilh' in (match[1] or '').lower():
            value *= 1000
        values.append(value)
    
    # Verificar consistência (permitir variação de 10%)
    if max(values) / min(values) > 1.1:
        return False, f"Valores de NAV inconsistentes: {values}"
    
    return True, "Valores de NAV consistentes"


def validate_discount_coherence(text: str) -> Tuple[bool, str]:
    """
    Valida consistência das menções a desconto sobre NAV.
    
    Returns:
        Tupla (consistente, mensagem)
    """
    # Extrair menções a desconto
    discount_mentions = re.findall(r'desconto\s+(?:de\s+)?(\d+(?:,\d+)?)\s*%', text, re.IGNORECASE)
    
    if len(discount_mentions) < 2:
        return True, "Poucas menções a desconto para validação"
    
    # Converter para valores numéricos
    values = [float(v.replace(',', '.')) for v in discount_mentions]
    
    # Verificar consistência
    if max(values) - min(values) > 2:
        return False, f"Valores de desconto inconsistentes: {values}"
    
    return True, "Valores de desconto consistentes"


def validate_timeline_plausibility(text: str) -> Tuple[bool, str]:
    """
    Valida se o timeline de exits é plausível.
    
    Returns:
        Tupla (plausível, mensagem)
    """
    # Buscar menções a anos de exit
    year_mentions = re.findall(r'(202[4-9]|203[0-5])', text)
    
    if not year_mentions:
        return True, "Sem menções específicas a anos"
    
    years = [int(y) for y in year_mentions]
    min_year = min(years)
    max_year = max(years)
    
    # Timeline típico de secundários: 2-5 anos
    if max_year - min_year > 6:
        return False, f"Timeline muito longo: {min_year}-{max_year}"
    
    # Não deve haver exits no passado
    current_year = 2024
    if min_year < current_year:
        return False, f"Menção a exit no passado: {min_year}"
    
    return True, f"Timeline plausível: {min_year}-{max_year}"


def validate_return_reasonability(text: str) -> Tuple[bool, str]:
    """
    Valida se os retornos projetados são razoáveis para secundários.
    
    Returns:
        Tupla (razoável, mensagem)
    """
    # Buscar TIR mencionada
    irr_matches = re.findall(r'(?:TIR|IRR)\s+(?:brut[ao])?\s+(?:de\s+)?(\d+(?:,\d+)?)\s*%', text, re.IGNORECASE)
    
    if not irr_matches:
        return True, "Sem TIR mencionada para validação"
    
    irr_values = [float(v.replace(',', '.')) for v in irr_matches]
    
    # TIR de secundários tipicamente entre 10-35%
    for irr in irr_values:
        if irr < 8:
            return False, f"TIR muito baixa para PE: {irr}%"
        if irr > 50:
            return False, f"TIR irrealisticamente alta: {irr}%"
    
    # Buscar MOIC
    moic_matches = re.findall(r'(?:MOIC|múltiplo)\s+(?:de\s+)?(\d+(?:,\d+)?)\s*x', text, re.IGNORECASE)
    
    if moic_matches:
        moic_values = [float(v.replace(',', '.')) for v in moic_matches]
        for moic in moic_values:
            if moic < 1.0:
                return False, f"MOIC abaixo de 1x indica perda: {moic}x"
            if moic > 4.0:
                return False, f"MOIC irrealisticamente alto para secundário: {moic}x"
    
    return True, "Retornos projetados dentro de parâmetros razoáveis"


def validate_gp_analysis(text: str) -> Tuple[bool, List[str]]:
    """
    Valida se a análise do GP contém elementos essenciais.
    
    Returns:
        Tupla (tem_todos_elementos, lista_elementos_faltando)
    """
    required_elements = [
        (r'AUM|ativos\s+sob\s+gestão', "AUM do GP"),
        (r'track\s+record|histórico', "Track record"),
        (r'(?:equipe|team|partner)', "Análise da equipe"),
        (r'coinvest|alignment|alinhamento', "Alinhamento de interesses"),
        (r'vintage|fundos?\s+(?:anteriores|histórico)', "Histórico de fundos"),
    ]
    
    missing = []
    for pattern, name in required_elements:
        if not re.search(pattern, text, re.IGNORECASE):
            missing.append(name)
    
    return len(missing) == 0, missing


def validate_memo_consistency(memo_sections: Dict[str, str]) -> List[str]:
    """
    Valida consistência entre seções do memo completo.
    
    Args:
        memo_sections: Dict com seções do memo
    
    Returns:
        Lista de inconsistências encontradas
    """
    issues = []
    
    full_text = " ".join(memo_sections.values())
    
    # Validar métricas secundárias
    has_metrics, missing_metrics = validate_secondary_metrics(full_text)
    if not has_metrics:
        issues.append(f"Métricas secundárias faltando: {', '.join(missing_metrics)}")
    
    # Validar consistência de NAV
    nav_ok, nav_msg = validate_nav_consistency(full_text)
    if not nav_ok:
        issues.append(nav_msg)
    
    # Validar consistência de desconto
    discount_ok, discount_msg = validate_discount_coherence(full_text)
    if not discount_ok:
        issues.append(discount_msg)
    
    # Validar timeline
    timeline_ok, timeline_msg = validate_timeline_plausibility(full_text)
    if not timeline_ok:
        issues.append(timeline_msg)
    
    # Validar retornos
    returns_ok, returns_msg = validate_return_reasonability(full_text)
    if not returns_ok:
        issues.append(returns_msg)
    
    return issues


def validate_complete_memo(memo_sections: Dict[str, str]) -> Dict[str, any]:
    """
    Validação completa do memo secundário.
    
    Args:
        memo_sections: Dict com todas as seções do memo
    
    Returns:
        Dict com resultados da validação
    """
    results = {
        "valid": True,
        "section_lengths": {},
        "metrics_coverage": {},
        "consistency_issues": [],
        "recommendations": []
    }
    
    # Validar comprimento de cada seção
    for section_name, content in memo_sections.items():
        is_valid, msg = validate_section_length(content)
        results["section_lengths"][section_name] = {
            "valid": is_valid,
            "message": msg
        }
        if not is_valid:
            results["valid"] = False
    
    # Validar métricas
    full_text = " ".join(memo_sections.values())
    has_metrics, missing = validate_secondary_metrics(full_text)
    results["metrics_coverage"] = {
        "complete": has_metrics,
        "missing": missing
    }
    if not has_metrics:
        results["valid"] = False
    
    # Validar consistência
    consistency_issues = validate_memo_consistency(memo_sections)
    results["consistency_issues"] = consistency_issues
    if consistency_issues:
        results["valid"] = False
    
    # Validar análise do GP se presente
    if "gp_analysis" in memo_sections:
        gp_ok, gp_missing = validate_gp_analysis(memo_sections["gp_analysis"])
        if not gp_ok:
            results["recommendations"].append(f"Análise do GP incompleta. Faltam: {', '.join(gp_missing)}")
    
    # Recomendações gerais
    if results["valid"]:
        results["recommendations"].append("Memo aprovado para revisão final")
    else:
        results["recommendations"].append("Memo requer revisão antes de submissão")
    
    return results


def format_validation_report(validation_results: Dict) -> str:
    """
    Formata relatório de validação para exibição.
    
    Args:
        validation_results: Resultado de validate_complete_memo
    
    Returns:
        String formatada com o relatório
    """
    lines = ["=" * 50, "RELATÓRIO DE VALIDAÇÃO - MEMO SECUNDÁRIO", "=" * 50, ""]
    
    # Status geral
    status = "✅ APROVADO" if validation_results["valid"] else "❌ REQUER REVISÃO"
    lines.append(f"Status Geral: {status}")
    lines.append("")
    
    # Comprimento das seções
    lines.append("📏 COMPRIMENTO DAS SEÇÕES:")
    for section, result in validation_results["section_lengths"].items():
        icon = "✅" if result["valid"] else "⚠️"
        lines.append(f"  {icon} {section}: {result['message']}")
    lines.append("")
    
    # Cobertura de métricas
    lines.append("📊 COBERTURA DE MÉTRICAS SECUNDÁRIAS:")
    if validation_results["metrics_coverage"]["complete"]:
        lines.append("  ✅ Todas as métricas essenciais presentes")
    else:
        lines.append("  ⚠️ Métricas faltando:")
        for metric in validation_results["metrics_coverage"]["missing"]:
            lines.append(f"    - {metric}")
    lines.append("")
    
    # Problemas de consistência
    if validation_results["consistency_issues"]:
        lines.append("⚠️ PROBLEMAS DE CONSISTÊNCIA:")
        for issue in validation_results["consistency_issues"]:
            lines.append(f"  - {issue}")
        lines.append("")
    
    # Recomendações
    lines.append("💡 RECOMENDAÇÕES:")
    for rec in validation_results["recommendations"]:
        lines.append(f"  • {rec}")
    
    lines.append("")
    lines.append("=" * 50)
    
    return "\n".join(lines)
