"""
Geração profissional de memorandos de Private Equity

Baseado em análise de memos reais de fundos de PE/Search Funds brasileiros.
Estilo: analítico, crítico, baseado em dados, com foco em validação.

Arquitetura de Agentes Especializados:
- Search Fund → orchestrator com 5 agentes especializados
- Gestora → orchestrator com 5 agentes especializados
- Outros tipos usam prompts genéricos
"""

import asyncio
from typing import Dict, List, Optional, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import json


# Mapeamento de sections de facts para seções de memo
SECTION_MAPPING = {
    "identification": {
        "keywords": ["introdução", "introduction", "overview", "sumário"],
        "title": "1. Introdução"
    },
    "transaction_structure": {
        "keywords": ["transação", "transaction", "estrutura", "valuation", "deal"],
        "title": "2. Estrutura da Transação"
    },
    "financials_history": {
        "keywords": ["financials", "histórico", "receita", "ebitda", "margem"],
        "title": "3. Histórico Financeiro"
    },
    "saida": {
        "keywords": ["projeções", "saída", "exit", "crescimento", "forecast"],
        "title": "4. Projeções e Saída"
    },
    "returns": {
        "keywords": ["retornos", "returns", "irr", "moic", "retorno"],
        "title": "5. Retornos"
    },
    "qualitative": {
        "keywords": ["mercado", "market", "empresa", "company", "modelo", "riscos", "qualitativo"],
        "title": "6. Aspectos Qualitativos"
    }
}


def build_pe_system_prompt(section_title: str) -> str:
    """
    Cria system prompt específico para analista de Private Equity.
    
    Baseado em análise de memos reais de PE/Search Funds.
    """
    return f"""Você é um analista sênior de Private Equity/Search Funds escrevendo a seção "{section_title}" de um Investment Memo profissional.

**ESTILO E TOM:**
- Tom analítico, crítico mas justo, primeira pessoa do plural ("estamos", "precisaremos")
- Postura de ceticismo balanceado: destaque positivos MAS sempre sinalize riscos e incertezas
- Cada afirmação deve ser sustentada por números específicos, percentuais ou métricas
- Use voz ativa e sentenças concisas (3-5 linhas por parágrafo)

**REGRAS OBRIGATÓRIAS:**
✅ Sempre quantifique: "cresceu 14% CAGR" não "cresceu bastante"
✅ Sinalize incertezas: "Será crucial validarmos...", "Ainda temos que aprofundar..."
✅ Compare sempre: "vs. CAGR histórico de X%", "acima dos peers em Y%"
✅ Use **negrito** para: empresa, valuations, múltiplos, retornos (IRR/MOIC)
✅ Apresente ambos lados: "Por um lado... por outro...", "Apesar de... vale ressaltar que..."

**ESTRUTURA:**
- Parágrafos fluidos (não bullets, exceto para listas de produtos/riscos)
- Lidere com contexto, depois dados: "A companhia cresceu consistentemente, entregando CAGR de X%..."
- Cause-and-effect: "Esse nível é explicado principalmente por..."

**TERMINOLOGIA PE (use naturalmente):**
- Valuation: EV/EBITDA, múltiplos, equity value, enterprise value
- Financiamento: seller note, seller finance, acquisition debt, estruturado em X% à vista
- Retornos: IRR, TIR, MOIC, dividendos
- Crescimento: CAGR, YoY, growth, expansão orgânica
- Eficiência: EBITDA margin, ROIC, NRR (Net Revenue Retention), churn
- Estratégia: cross-sell, upsell, market share, penetração, moat, switching costs

**O QUE EVITAR:**
❌ Linguagem de marketing/vendas ("excelente oportunidade", "incrível potencial")
❌ Afirmações sem dados ("muito bom", "grande crescimento")
❌ Copiar exemplos literalmente - use apenas como referência de ESTILO
❌ Inventar números - use APENAS os facts fornecidos
❌ Markdown headers (##, ###) - use parágrafos fluidos

**OUTPUT:**
- 2-4 parágrafos bem conectados
- Cada parágrafo: 3-5 frases
- Separar parágrafos com linha em branco
- NÃO numerar parágrafos"""


def build_user_prompt(
    section_title: str,
    facts: Dict[str, Any],
    memo_type: str,
    examples: List[str]
) -> str:
    """
    Monta prompt do usuário com facts e exemplos de referência.
    """
    # Limpar facts vazios/None
    cleaned_facts = {k: v for k, v in facts.items() if v not in (None, "", [], {})}
    
    prompt_parts = [
        f"**TAREFA:** Escrever a seção '{section_title}' para um {memo_type}",
        "",
        "**FACTS EXTRAÍDOS (use APENAS esses dados):**"
    ]
    
    # Formatar facts de forma legível
    for key, value in cleaned_facts.items():
        if isinstance(value, (list, dict)):
            prompt_parts.append(f"- {key}: {json.dumps(value, ensure_ascii=False)}")
        else:
            prompt_parts.append(f"- {key}: {value}")
    
    # Adicionar exemplos de referência se disponíveis
    if examples:
        prompt_parts.append("")
        prompt_parts.append("**EXEMPLOS DE REFERÊNCIA (para inspirar ESTILO e ESTRUTURA, NÃO copie conteúdo):**")
        prompt_parts.append("")
        
        for i, example in enumerate(examples[:3], 1):
            prompt_parts.append(f"--- Exemplo {i} ---")
            prompt_parts.append(example)
            prompt_parts.append("")
    
    prompt_parts.append("**INSTRUÇÕES:**")
    prompt_parts.append("Escreva 2-4 parágrafos profissionais para essa seção usando os facts acima.")
    prompt_parts.append("Siga o estilo analítico dos exemplos, mas adapte o conteúdo aos facts específicos.")
    prompt_parts.append("Retorne APENAS os parágrafos, sem cabeçalhos ou comentários adicionais.")
    
    return "\n".join(prompt_parts)


async def generate_section_async(
    section_title: str,
    facts: Dict[str, Any],
    memo_type: str,
    memo_examples: List[Dict[str, Any]],
    temperature: float = 0.3,
    rag_context: Optional[str] = None
) -> Dict[str, Any]:
    """
    Gera uma seção do memorando usando few-shot learning.
    
    VERSÃO 2.0: Com roteamento condicional para Search Fund.
    - Se memo_type contém "Search Fund" → usa shortmemo.searchfund.generator
    - Outros tipos → usa prompts genéricos
    
    Args:
        section_title: Título da seção (ex: "1. Introdução")
        facts: Dicionário com facts extraídos para essa seção
        memo_type: Tipo de memorando (ex: "Short Memo - Co-investimento (Search Fund)")
        memo_examples: Lista de memos similares da biblioteca
        temperature: Criatividade do modelo (0.0-1.0)
        rag_context: Contexto do RAG/documento (opcional)
        
    Returns:
        Dict com paragraphs gerados e metadata
    """
    from dotenv import load_dotenv
    load_dotenv()
    
    # ========== ROTEAMENTO CONDICIONAL ==========
    # Se for Search Fund → usar orchestrator com agentes especializados
    if "Search Fund" in memo_type or "search fund" in memo_type.lower():
        try:
            from shortmemo.searchfund.orchestrator import FIXED_STRUCTURE
            
            # Mapear section_title para agente
            section_agent_map = {
                "1. Introdução": "1. Introdução",
                "2. Mercado": "2. Mercado",
                "2. A Empresa": "3. Empresa",
                "3. Empresa": "3. Empresa",
                "4. Financials": "4. Financials",
                "5. Transação": "5. Transação/Oportunidade",
                "5. Transação/Oportunidade": "5. Transação/Oportunidade",
                "6. Pontos a Aprofundar": "6. Pontos a Aprofundar",
            }
            
            orchestrator_section = section_agent_map.get(section_title)
            
            if orchestrator_section and orchestrator_section in FIXED_STRUCTURE:
                agent = FIXED_STRUCTURE[orchestrator_section]
                
                print(f"   📝 [Search Fund] Gerando '{section_title}' com {agent.__class__.__name__}...")
                
                generated_text = agent.generate(
                    facts=facts,
                    rag_context=rag_context
                )
                
                # Dividir em parágrafos
                paragraphs = [p.strip() for p in generated_text.split('\n\n') if p.strip()]
                
                print(f"   ✅ '{section_title}': {len(paragraphs)} parágrafo(s) | Agent: {agent.__class__.__name__}")
                
                return {
                    "paragraphs": paragraphs,
                    "metadata": {
                        "section": section_title,
                        "generator": f"shortmemo.searchfund.{agent.__class__.__name__}",
                        "model": "gpt-4o",
                        "temperature": temperature,
                        "has_rag": rag_context is not None
                    }
                }
            else:
                print(f"   ⚠️  Seção '{section_title}' não mapeada para Search Fund orchestrator")
                # Fallback para prompts genéricos
        
        except ImportError as e:
            print(f"   ⚠️  Erro ao importar orchestrator Search Fund: {e}")
            print(f"   ⤷  Usando prompts genéricos como fallback")
            # Fallback para prompts genéricos
        except Exception as e:
            print(f"   ⚠️  Erro no orchestrator Search Fund: {e}")
            print(f"   ⤷  Usando prompts genéricos como fallback")
    
    # Se for Gestora → usar orchestrator com agentes especializados
    elif "Gestora" in memo_type or "gestora" in memo_type.lower():
        try:
            from shortmemo.gestora.orchestrator import FIXED_STRUCTURE
            
            # Mapear section_title para agente
            section_agent_map = {
                "1. Introdução": "1. Introdução",
                "2. Estratégia e Portfólio": "2. Estratégia e Portfólio",
                "3. Track Record": "3. Track Record",
                "4. Oportunidade": "4. Oportunidade",
                "5. Riscos e Considerações": "5. Riscos e Considerações",
            }
            
            orchestrator_section = section_agent_map.get(section_title)
            
            if orchestrator_section and orchestrator_section in FIXED_STRUCTURE:
                agent = FIXED_STRUCTURE[orchestrator_section]
                
                print(f"   📝 [Gestora] Gerando '{section_title}' com {agent.__class__.__name__}...")
                
                generated_text = agent.generate(
                    facts=facts,
                    rag_context=rag_context
                )
                
                # Dividir em parágrafos
                paragraphs = [p.strip() for p in generated_text.split('\n\n') if p.strip()]
                
                print(f"   ✅ '{section_title}': {len(paragraphs)} parágrafo(s) | Agent: {agent.__class__.__name__}")
                
                return {
                    "paragraphs": paragraphs,
                    "metadata": {
                        "section": section_title,
                        "generator": f"shortmemo.gestora.{agent.__class__.__name__}",
                        "model": "gpt-4o",
                        "temperature": temperature,
                        "has_rag": rag_context is not None
                    }
                }
            else:
                print(f"   ⚠️  Seção '{section_title}' não mapeada para Gestora orchestrator")
                # Fallback para prompts genéricos
        
        except ImportError as e:
            print(f"   ⚠️  Erro ao importar orchestrator Gestora: {e}")
            print(f"   ⤷  Usando prompts genéricos como fallback")
            # Fallback para prompts genéricos
        except Exception as e:
            print(f"   ⚠️  Erro no orchestrator Gestora: {e}")
            print(f"   ⤷  Usando prompts genéricos como fallback")
    
    # ========== PROMPTS GENÉRICOS (outros tipos de memo) ==========
    # Mapear section_title para fact_section
    fact_section = None
    for section, config in SECTION_MAPPING.items():
        if config["title"] == section_title:
            fact_section = section
            break
    
    # Gerar sem exemplos (few-shot removido)
    example_paragraphs = []
    
    # Criar LLM
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=temperature
    )
    
    # Montar prompts
    system_prompt = build_pe_system_prompt(section_title)
    user_prompt = build_user_prompt(section_title, facts, memo_type, example_paragraphs)
    
    # Gerar
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]
    
    print(f"   📝 Gerando '{section_title}'...")
    
    response = await llm.ainvoke(messages)
    
    # Parse resposta em parágrafos
    content = response.content.strip()
    
    # Dividir por dupla quebra de linha
    paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
    
    # Se retornou tudo em um bloco, tentar dividir por quebra simples
    if len(paragraphs) == 1 and len(content) > 500:
        single_break = [p.strip() for p in content.split('\n') if p.strip() and len(p.strip()) > 80]
        if len(single_break) > 1:
            paragraphs = single_break
    
    # Limpar numeração indesejada (ex: "1. ", "- ")
    import re
    cleaned_paragraphs = []
    for p in paragraphs:
        p_clean = re.sub(r'^\d+\.\s*', '', p)
        p_clean = re.sub(r'^[-•]\s*', '', p_clean)
        cleaned_paragraphs.append(p_clean)
    
    print(f"   ✅ '{section_title}': {len(cleaned_paragraphs)} parágrafo(s) | {len(example_paragraphs)} exemplo(s) usados")
    
    return {
        "paragraphs": cleaned_paragraphs,
        "metadata": {
            "section": section_title,
            "examples_used": len(example_paragraphs),
            "generator": "generic",
            "model": "gpt-4o",
            "temperature": temperature
        }
    }


def generate_section_sync(
    section_title: str,
    facts: Dict[str, Any],
    memo_type: str,
    temperature: float = 0.3
) -> Dict[str, Any]:
    """
    Wrapper síncrono para usar no Streamlit.
    
    Args:
        section_title: Título da seção
        facts: Facts extraídos
        memo_type: Tipo de memorando
        temperature: Criatividade (0.0-1.0, default 0.3 para manter precisão)
        
    Returns:
        Dict com paragraphs e metadata
    """
    # Gerar sem exemplos (biblioteca removida)
    memo_examples = []
    
    # Executar async
    return asyncio.run(generate_section_async(
        section_title, facts, memo_type, memo_examples, temperature
    ))


async def regenerate_paragraph_async(
    section_title: str,
    paragraph_index: int,
    current_paragraphs: List[str],
    facts: Dict[str, Any],
    memo_type: str,
    instructions: Optional[str] = None,
    temperature: float = 0.5
) -> str:
    """
    Regenera um parágrafo específico mantendo coerência com vizinhos.
    
    Args:
        section_title: Título da seção
        paragraph_index: Índice do parágrafo (0-based)
        current_paragraphs: Lista completa de parágrafos atuais
        facts: Facts da seção
        memo_type: Tipo de memorando
        instructions: Instruções específicas (ex: "Seja mais técnico")
        temperature: Criatividade (0.5 por padrão para regeneração)
        
    Returns:
        Novo parágrafo regenerado
    """
    from dotenv import load_dotenv
    load_dotenv()
    
    llm = ChatOpenAI(model="gpt-4o", temperature=temperature)
    
    # Montar contexto com parágrafos vizinhos
    context_parts = [
        f"**SEÇÃO:** {section_title}",
        f"**TIPO:** {memo_type}",
        "",
        "**FACTS:**"
    ]
    
    cleaned_facts = {k: v for k, v in facts.items() if v not in (None, "", [], {})}
    for key, value in cleaned_facts.items():
        context_parts.append(f"- {key}: {value}")
    
    context_parts.append("")
    
    # Parágrafo anterior (se houver)
    if paragraph_index > 0:
        context_parts.append("**PARÁGRAFO ANTERIOR:**")
        context_parts.append(current_paragraphs[paragraph_index - 1])
        context_parts.append("")
    
    # Parágrafo atual (a ser regenerado)
    context_parts.append("**PARÁGRAFO ATUAL (REGENERAR):**")
    context_parts.append(current_paragraphs[paragraph_index])
    context_parts.append("")
    
    # Parágrafo seguinte (se houver)
    if paragraph_index < len(current_paragraphs) - 1:
        context_parts.append("**PARÁGRAFO SEGUINTE:**")
        context_parts.append(current_paragraphs[paragraph_index + 1])
        context_parts.append("")
    
    # Instruções específicas
    if instructions:
        context_parts.append("**INSTRUÇÕES ESPECÍFICAS:**")
        context_parts.append(instructions)
        context_parts.append("")
    
    context_parts.append("**TAREFA:**")
    context_parts.append("Reescreva APENAS o parágrafo marcado como 'ATUAL', mantendo coerência com os vizinhos.")
    context_parts.append("Retorne SOMENTE o novo parágrafo, sem comentários adicionais.")
    
    messages = [
        SystemMessage(content=build_pe_system_prompt(section_title)),
        HumanMessage(content="\n".join(context_parts))
    ]
    
    response = await llm.ainvoke(messages)
    new_paragraph = response.content.strip()
    
    # Limpar numeração se houver
    import re
    new_paragraph = re.sub(r'^\d+\.\s*', '', new_paragraph)
    new_paragraph = re.sub(r'^[-•]\s*', '', new_paragraph)
    
    print(f"   🔄 Parágrafo {paragraph_index + 1} regenerado")
    
    return new_paragraph


def regenerate_paragraph_sync(
    section_title: str,
    paragraph_index: int,
    current_paragraphs: List[str],
    facts: Dict[str, Any],
    memo_type: str,
    instructions: Optional[str] = None,
    temperature: float = 0.5
) -> str:
    """
    Wrapper síncrono para regeneração de parágrafo.
    """
    return asyncio.run(regenerate_paragraph_async(
        section_title,
        paragraph_index,
        current_paragraphs,
        facts,
        memo_type,
        instructions,
        temperature
    ))


async def generate_all_sections_async(
    facts: Dict[str, Dict[str, Any]],
    memo_type: str,
    sections_to_generate: Optional[List[str]] = None,
    temperature: float = 0.3
) -> Dict[str, Dict[str, Any]]:
    """
    Gera todas as seções do memorando em paralelo.
    
    Args:
        facts: Dict com {section_key: {...facts...}}
        memo_type: Tipo do memorando
        sections_to_generate: Lista de section keys ou None para todas
        temperature: Criatividade do modelo
        
    Returns:
        Dict com {section_title: {paragraphs: [...], metadata: {...}}}
    """
    # Gerar sem exemplos (biblioteca removida)
    memo_examples = []
    
    print(f"\n🚀 Gerando memorando profissional")
    print(f"   Tipo: {memo_type}")
    
    # Determinar seções a gerar
    if sections_to_generate is None:
        sections_to_generate = list(facts.keys())
    
    # Criar tasks de geração
    tasks = []
    section_titles = []
    
    for section_key in sections_to_generate:
        if section_key not in SECTION_MAPPING:
            continue
        
        section_title = SECTION_MAPPING[section_key]["title"]
        section_facts = facts.get(section_key, {})
        
        if not section_facts:
            print(f"   ⚠️  Seção '{section_title}' não tem facts - pulando")
            continue
        
        section_titles.append(section_title)
        tasks.append(generate_section_async(
            section_title, section_facts, memo_type, memo_examples, temperature
        ))
    
    # Executar em paralelo
    print(f"   Gerando {len(tasks)} seção(ões) em paralelo...\n")
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Organizar resultados
    generated = {}
    success_count = 0
    
    for section_title, result in zip(section_titles, results):
        if isinstance(result, Exception):
            print(f"   ❌ Erro em '{section_title}': {result}")
            generated[section_title] = {
                "paragraphs": [f"Erro ao gerar: {str(result)}"],
                "metadata": {"error": str(result)}
            }
        else:
            generated[section_title] = result
            success_count += 1
    
    print(f"\n✅ Geração concluída!")
    print(f"   Seções geradas com sucesso: {success_count}/{len(tasks)}")
    
    return generated


def generate_all_sections_sync(
    facts: Dict[str, Dict[str, Any]],
    memo_type: str,
    sections_to_generate: Optional[List[str]] = None,
    temperature: float = 0.3
) -> Dict[str, Dict[str, Any]]:
    """
    Wrapper síncrono para geração completa do memorando.
    """
    return asyncio.run(generate_all_sections_async(
        facts, memo_type, sections_to_generate, temperature
    ))
