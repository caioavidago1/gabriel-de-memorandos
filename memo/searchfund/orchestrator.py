"""
Orchestrator para Memo Completo Search Fund - Estrutura Fixa de 9 Seções

ARQUITETURA:
- Estrutura FIXA de 9 seções (não customizável)
- Cada seção usa função de geração especializada
- Integração com RAG para contexto por seção
- Validação de não-redundância entre seções

SEÇÕES FIXAS:
1. Overview → generate_intro_section
2. Gestor → generate_gestor_section
3. Mercado → generate_market_section
4. Empresa → generate_company_section
5. Transação → generate_transaction_section
6. Projeções Financeiras → generate_projections_section
7. Retornos Esperados → generate_retornos_esperados_section
8. Board e Cap Table → generate_board_cap_table_section
9. Conclusão → generate_conclusao_section
"""

from typing import Dict, Any, Optional, TYPE_CHECKING
from .agents import (
    generate_intro_section,
    generate_gestor_section,
    generate_market_section,
    generate_company_section,
    generate_transaction_section,
    generate_projections_section,
    generate_retornos_esperados_section,
    generate_board_cap_table_section,
    generate_conclusao_section,
)
from . import FIXED_STRUCTURE

if TYPE_CHECKING:
    from core.document_processor import DocumentProcessor


# Mapeamento de seções para funções de geração
SECTION_GENERATORS = {
    "overview": generate_intro_section,
    "gestor": generate_gestor_section,
    "mercado": generate_market_section,
    "empresa": generate_company_section,
    "transacao": generate_transaction_section,
    "projecoes_financeiras": generate_projections_section,
    "retornos_esperados": generate_retornos_esperados_section,
    "board_cap_table": generate_board_cap_table_section,
    "conclusao": generate_conclusao_section,
}

# Queries semânticas para busca RAG por seção no ChromaDB
SECTION_QUERIES = {
    "1. Overview": (
        "overview resumo executivo sumário oportunidade investimento "
        "contexto deal apresentação visão estratégica"
    ),
    "2. Gestor": (
        "gestor searcher empreendedor busca formação histórico "
        "experiência assessment complementaridade referências track record"
    ),
    "3. Mercado": (
        "mercado setor tamanho crescimento tendências competição "
        "dinâmica posicionamento oportunidades ameaças ambiente "
        "contexto macroeconômico demanda fragmentação"
    ),
    "4. Empresa": (
        "empresa histórico fundação posicionamento diferenciação modelo negócio "
        "competências expertise capacidades força equipe management "
        "estrutura operacional produtos clientes fornecedores"
    ),
    "5. Transação": (
        "transação estrutura valuation preço múltiplo ticket investimento "
        "seller note earnout pagamento à vista financiamento"
    ),
    "6. Projeções Financeiras": (
        "projeções financeiras cenário base upside downside receita EBITDA "
        "margem crescimento drivers premissas tabelas ano a ano"
    ),
    "7. Retornos Esperados": (
        "retornos esperados IRR MOIC cenário base upside downside "
        "sensibilidade múltiplo saída timing waterfall benchmark"
    ),
    "8. Board e Cap Table": (
        "board cap table investidores membros composição governança "
        "direitos veto tag-along drag-along participações"
    ),
    "9. Conclusão": (
        "conclusão recomendação pontos positivos riscos principais "
        "alocação sugerida próximos passos balanceamento"
    )
}


def _get_rag_context_for_section(
    section_title: str,
    memo_id: Optional[str],
    processor: Optional["DocumentProcessor"]
) -> Optional[str]:
    """
    Obtém contexto RAG específico para uma seção usando busca semântica.
    
    Args:
        section_title: Título da seção (ex: "1. Overview")
        memo_id: ID do memo no ChromaDB
        processor: Instância de DocumentProcessor para busca
    
    Returns:
        Contexto RAG relevante para a seção ou None
    """
    if not processor or not memo_id:
        return None
    
    try:
        query = SECTION_QUERIES.get(section_title, "")
        if not query:
            return None
        
        # Buscar contexto relevante no ChromaDB
        results = processor.search_chromadb_chunks(
            memo_id=memo_id,
            query=query,
            top_k=3,
            section=None
        )
        
        if results:
            # Combinar chunks relevantes
            context = "\n\n".join([
                r.get("document", "") or r.get("text", "") or r.get("chunk", "")
                for r in results 
                if r.get("document") or r.get("text") or r.get("chunk")
            ])
            return context if context.strip() else None
        
    except Exception as e:
        # Se houver erro na busca RAG, continuar sem contexto
        print(f"   ⚠️  Erro ao buscar RAG para '{section_title}': {e}")
    
    return None


def generate_full_memo(
    facts: Dict[str, Any],
    rag_context: str = None,  # Deprecated - usar memo_id/processor
    memo_id: Optional[str] = None,
    processor: Optional["DocumentProcessor"] = None,
    model: str = "gpt-4o",
    temperature: float = 0.25
) -> Dict[str, list]:
    """
    Gera memo COMPLETO de Memo Search Fund (estrutura fixa de 9 seções).
    
    Args:
        facts: Facts extraídos (todas as seções)
        rag_context: Contexto do documento (DEPRECATED - usar memo_id/processor)
        memo_id: ID do memo no ChromaDB para busca RAG por seção
        processor: Instância de DocumentProcessor para busca no ChromaDB
        model: Modelo OpenAI
        temperature: Criatividade
    
    Returns:
        Dict com estrutura: {section_title: [paragraph1, paragraph2, ...]}
    """
    memo_sections = {}
    
    print(f"Gerando Memo Completo Search Fund com {len(FIXED_STRUCTURE)} seções...")
    
    for section_title, section_key in FIXED_STRUCTURE.items():
        print(f"   Gerando seção: {section_title}...")
        
        # Obter função de geração
        generator_func = SECTION_GENERATORS.get(section_key)
        if not generator_func:
            print(f"   ⚠️  Função não encontrada para '{section_key}', pulando...")
            continue
        
        # Obter contexto RAG específico para esta seção
        section_rag_context = _get_rag_context_for_section(
            section_title, memo_id, processor
        ) or rag_context  # Fallback para contexto geral se disponível
        
        try:
            # Gerar seção
            section_text = generator_func(
                facts=facts,
                rag_context=section_rag_context,
                model=model,
                temperature=temperature
            )
            
            # Dividir em parágrafos
            paragraphs = [p.strip() for p in section_text.split('\n\n') if p.strip()]
            
            memo_sections[section_title] = paragraphs
            
            print(f"   ✅ '{section_title}': {len(paragraphs)} parágrafo(s)")
            
        except Exception as e:
            print(f"   ❌ Erro ao gerar '{section_title}': {e}")
            memo_sections[section_title] = [f"[Erro ao gerar seção: {str(e)}]"]
    
    print(f"✅ Memo completo gerado com {len(memo_sections)} seções")
    
    # Validação de não-redundância
    try:
        from .validator import validate_no_redundancy
        
        # Converter para formato de texto (juntar parágrafos)
        sections_text = {
            title: "\n\n".join(paragraphs)
            for title, paragraphs in memo_sections.items()
        }
        
        redundancy_check = validate_no_redundancy(sections_text, threshold=0.3)
        
        if redundancy_check["has_redundancy"]:
            print(f"   ⚠️  Redundâncias detectadas: {len(redundancy_check['redundant_pairs'])} pares")
            for suggestion in redundancy_check["suggestions"][:3]:  # Mostrar apenas top 3
                print(f"      - {suggestion}")
        else:
            print(f"   ✅ Nenhuma redundância significativa detectada")
            
    except Exception as e:
        print(f"   ⚠️  Erro na validação de redundância: {e}")
    
    return memo_sections
