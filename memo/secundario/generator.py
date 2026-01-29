"""
Generator de Memo Completo Secundário

Gera memos extensos (~20 páginas) para transações secundárias.
Cada seção deve ter 5-8 parágrafos com análise aprofundada.
"""

from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from shortmemo.searchfund.shared import build_facts_section


def get_model():
    """Retorna o modelo configurado para geração de memos completos."""
    return ChatOpenAI(model="gpt-4o", temperature=0.25)


# =============================================================================
# PROMPTS POR SEÇÃO - MEMOS COMPLETOS SECUNDÁRIOS
# =============================================================================

INTRO_PROMPT = """
Você é um analista sênior de private equity especializado em transações secundárias.
Escreva a seção de INTRODUÇÃO para um memorando de investimento completo.

OBJETIVO: Apresentar a oportunidade de investimento secundário de forma executiva,
contextualizando a transação no ciclo de vida do fundo vendedor e destacando os
atrativos da entrada neste momento específico.

REQUISITOS DE FORMATO:
- 5-8 parágrafos densos e analíticos
- Aproximadamente 2-3 páginas de conteúdo
- Tom executivo e sofisticado
- Foco em tese de investimento secundário e timing

ESTRUTURA OBRIGATÓRIA:
1. Sumário executivo da oportunidade secundária
2. Contexto do vendedor (GP/LP) e motivação da venda
3. Caracterização do ativo subjacente
4. Tese de investimento e timing de entrada
5. Principais atrativos (desconto, J-curve mitigada, portfólio maduro)
6. Retornos esperados e horizonte
7. Próximos passos do processo

DADOS DA TRANSAÇÃO:
{facts}

Escreva a seção de introdução completa, mantendo rigor analítico e profundidade
adequada para um comitê de investimentos exigente.
"""

SELLER_CONTEXT_PROMPT = """
Você é um analista sênior de private equity especializado em transações secundárias.
Escreva a seção de CONTEXTO DO VENDEDOR para um memorando de investimento completo.

OBJETIVO: Analisar profundamente o vendedor, suas motivações, e as implicações
para a transação secundária.

REQUISITOS DE FORMATO:
- 5-8 parágrafos densos e analíticos
- Aproximadamente 2-3 páginas de conteúdo
- Tom executivo e sofisticado
- Foco em análise do vendedor e implicações

ESTRUTURA OBRIGATÓRIA:
1. Perfil do vendedor (GP-led, LP-led, ou direto)
2. Motivações da venda (liquidez, rebalanceamento, gestão de portfólio)
3. Histórico do vendedor com o ativo
4. Análise do timing da venda
5. Dinâmica de negociação e processo
6. Implicações para o comprador
7. Red flags ou preocupações do vendedor

DADOS DA TRANSAÇÃO:
{facts}

Escreva a seção de contexto do vendedor completa.
"""

PORTFOLIO_PROMPT = """
Você é um analista sênior de private equity especializado em transações secundárias.
Escreva a seção de ANÁLISE DO PORTFÓLIO para um memorando de investimento completo.

OBJETIVO: Analisar em profundidade os ativos subjacentes da transação secundária,
avaliando qualidade, maturidade e potencial de valor.

REQUISITOS DE FORMATO:
- 5-8 parágrafos densos e analíticos
- Aproximadamente 2-3 páginas de conteúdo
- Tom executivo e sofisticado
- Foco em análise bottom-up dos ativos

ESTRUTURA OBRIGATÓRIA:
1. Visão geral do portfólio (número de ativos, concentração)
2. Análise dos principais ativos (top 5-10 posições)
3. Diversificação setorial e geográfica
4. Maturidade do portfólio (vintage, tempo até exit esperado)
5. Qualidade dos GPs subjacentes (se aplicável)
6. Performance histórica dos ativos
7. Comparação com benchmarks de mercado

DADOS DA TRANSAÇÃO:
{facts}

Escreva a seção de análise do portfólio completa.
"""

VALUATION_PROMPT = """
Você é um analista sênior de private equity especializado em transações secundárias.
Escreva a seção de VALUATION E PRICING para um memorando de investimento completo.

OBJETIVO: Analisar a precificação da transação, desconto sobre NAV, metodologias
de avaliação e atratividade relativa.

REQUISITOS DE FORMATO:
- 5-8 parágrafos densos e analíticos
- Aproximadamente 2-3 páginas de conteúdo
- Tom executivo e sofisticado
- Foco em análise quantitativa rigorosa

ESTRUTURA OBRIGATÓRIA:
1. NAV reportado e data de referência
2. Preço proposto e desconto sobre NAV
3. Análise do desconto vs. mercado secundário
4. Metodologia de valuation dos ativos subjacentes
5. Sensibilidade a diferentes cenários de NAV
6. Unfunded commitments e ajustes
7. Comparação com transações recentes

DADOS DA TRANSAÇÃO:
{facts}

Escreva a seção de valuation e pricing completa.
"""

RETURNS_PROMPT = """
Você é um analista sênior de private equity especializado em transações secundárias.
Escreva a seção de RETORNOS ESPERADOS para um memorando de investimento completo.

OBJETIVO: Apresentar análise detalhada dos retornos projetados, cenários,
e comparação com alternativas de investimento.

REQUISITOS DE FORMATO:
- 5-8 parágrafos densos e analíticos
- Aproximadamente 2-3 páginas de conteúdo
- Tom executivo e sofisticado
- Foco em modelagem de retornos

ESTRUTURA OBRIGATÓRIA:
1. TIR bruta e líquida projetada (base case)
2. Múltiplo de capital esperado (MOIC/TVPI)
3. Cenários (bear, base, bull) com premissas
4. Análise de sensibilidade
5. Curva de distribuições esperadas (J-curve)
6. Comparação com fundos primários e diretos
7. Drivers de upside e downside

DADOS DA TRANSAÇÃO:
{facts}

Escreva a seção de retornos esperados completa.
"""

STRUCTURE_PROMPT = """
Você é um analista sênior de private equity especializado em transações secundárias.
Escreva a seção de ESTRUTURA DA TRANSAÇÃO para um memorando de investimento completo.

OBJETIVO: Detalhar a estrutura jurídica, mecânica da transação, e termos
negociados.

REQUISITOS DE FORMATO:
- 5-8 parágrafos densos e analíticos
- Aproximadamente 2-3 páginas de conteúdo
- Tom executivo e sofisticado
- Foco em aspectos estruturais e legais

ESTRUTURA OBRIGATÓRIA:
1. Tipo de transação (LP interest, GP-led, direct)
2. Estrutura jurídica e veículos envolvidos
3. Mecanismo de transferência
4. Consent requirements e processo
5. Cronograma da transação
6. Condições precedentes
7. Aspectos tributários e regulatórios

DADOS DA TRANSAÇÃO:
{facts}

Escreva a seção de estrutura da transação completa.
"""

GP_ANALYSIS_PROMPT = """
Você é um analista sênior de private equity especializado em transações secundárias.
Escreva a seção de ANÁLISE DO GP para um memorando de investimento completo.

OBJETIVO: Avaliar a qualidade do General Partner que gerencia os ativos
subjacentes da transação.

REQUISITOS DE FORMATO:
- 5-8 parágrafos densos e analíticos
- Aproximadamente 2-3 páginas de conteúdo
- Tom executivo e sofisticado
- Foco em track record e qualidade da gestão

ESTRUTURA OBRIGATÓRIA:
1. Perfil do GP (AUM, fundos, histórico)
2. Track record histórico (TIR, múltiplos por vintage)
3. Análise da equipe de investimento
4. Estratégia de investimento e execução
5. Alignment of interests e coinvestimento
6. Relação com LPs e reputação de mercado
7. Avaliação de riscos do GP

DADOS DA TRANSAÇÃO:
{facts}

Escreva a seção de análise do GP completa.
"""

RISKS_PROMPT = """
Você é um analista sênior de private equity especializado em transações secundárias.
Escreva a seção de RISCOS E MITIGANTES para um memorando de investimento completo.

OBJETIVO: Apresentar análise completa dos riscos específicos de transações
secundárias e os mitigantes identificados.

REQUISITOS DE FORMATO:
- 5-8 parágrafos densos e analíticos
- Aproximadamente 2-3 páginas de conteúdo
- Tom executivo e sofisticado
- Foco em riscos secundário-específicos

ESTRUTURA OBRIGATÓRIA:
1. Riscos de valuation (NAV stale, marks agressivos)
2. Riscos de informação (assimetria, due diligence limitada)
3. Riscos de concentração (portfólio, setor, geografia)
4. Riscos de liquidez e exit
5. Riscos de GP (key man, performance futura)
6. Riscos de mercado e macro
7. Mitigantes estruturais e operacionais

DADOS DA TRANSAÇÃO:
{facts}

Escreva a seção de riscos e mitigantes completa.
"""


# =============================================================================
# FUNÇÕES DE GERAÇÃO POR SEÇÃO
# =============================================================================

def generate_intro_section(facts: dict, model=None) -> str:
    """Gera seção de introdução do memo secundário completo."""
    model = model or get_model()
    
    prompt = PromptTemplate(
        template=INTRO_PROMPT,
        input_variables=["facts"]
    )
    
    chain = prompt | model
    
    response = chain.invoke({
        "facts": build_facts_section(facts)
    })
    
    return response.content


def generate_seller_context_section(facts: dict, model=None) -> str:
    """Gera seção de contexto do vendedor do memo secundário completo."""
    model = model or get_model()
    
    prompt = PromptTemplate(
        template=SELLER_CONTEXT_PROMPT,
        input_variables=["facts"]
    )
    
    chain = prompt | model
    
    response = chain.invoke({
        "facts": build_facts_section(facts)
    })
    
    return response.content


def generate_portfolio_section(facts: dict, model=None) -> str:
    """Gera seção de análise do portfólio do memo secundário completo."""
    model = model or get_model()
    
    prompt = PromptTemplate(
        template=PORTFOLIO_PROMPT,
        input_variables=["facts"]
    )
    
    chain = prompt | model
    
    response = chain.invoke({
        "facts": build_facts_section(facts)
    })
    
    return response.content


def generate_valuation_section(facts: dict, model=None) -> str:
    """Gera seção de valuation e pricing do memo secundário completo."""
    model = model or get_model()
    
    prompt = PromptTemplate(
        template=VALUATION_PROMPT,
        input_variables=["facts"]
    )
    
    chain = prompt | model
    
    response = chain.invoke({
        "facts": build_facts_section(facts)
    })
    
    return response.content


def generate_returns_section(facts: dict, model=None) -> str:
    """Gera seção de retornos esperados do memo secundário completo."""
    model = model or get_model()
    
    prompt = PromptTemplate(
        template=RETURNS_PROMPT,
        input_variables=["facts"]
    )
    
    chain = prompt | model
    
    response = chain.invoke({
        "facts": build_facts_section(facts)
    })
    
    return response.content


def generate_structure_section(facts: dict, model=None) -> str:
    """Gera seção de estrutura da transação do memo secundário completo."""
    model = model or get_model()
    
    prompt = PromptTemplate(
        template=STRUCTURE_PROMPT,
        input_variables=["facts"]
    )
    
    chain = prompt | model
    
    response = chain.invoke({
        "facts": build_facts_section(facts)
    })
    
    return response.content


def generate_gp_analysis_section(facts: dict, model=None) -> str:
    """Gera seção de análise do GP do memo secundário completo."""
    model = model or get_model()
    
    prompt = PromptTemplate(
        template=GP_ANALYSIS_PROMPT,
        input_variables=["facts"]
    )
    
    chain = prompt | model
    
    response = chain.invoke({
        "facts": build_facts_section(facts)
    })
    
    return response.content


def generate_risks_section(facts: dict, model=None) -> str:
    """Gera seção de riscos e mitigantes do memo secundário completo."""
    model = model or get_model()
    
    prompt = PromptTemplate(
        template=RISKS_PROMPT,
        input_variables=["facts"]
    )
    
    chain = prompt | model
    
    response = chain.invoke({
        "facts": build_facts_section(facts)
    })
    
    return response.content


# =============================================================================
# FUNÇÃO PRINCIPAL - ROTEADOR DE SEÇÕES
# =============================================================================

def generate_section(section_name: str, facts: dict, model=None) -> str:
    """
    Gera uma seção específica do memo secundário completo.
    
    Args:
        section_name: Nome da seção a gerar
        facts: Dicionário com facts estruturados
        model: Modelo LLM (opcional, usa GPT-4o por padrão)
    
    Returns:
        Texto da seção gerada
    
    Seções disponíveis:
        - intro: Introdução e sumário executivo
        - seller_context: Contexto do vendedor
        - portfolio: Análise do portfólio
        - valuation: Valuation e pricing
        - returns: Retornos esperados
        - structure: Estrutura da transação
        - gp_analysis: Análise do GP
        - risks: Riscos e mitigantes
    """
    generators = {
        "intro": generate_intro_section,
        "seller_context": generate_seller_context_section,
        "portfolio": generate_portfolio_section,
        "valuation": generate_valuation_section,
        "returns": generate_returns_section,
        "structure": generate_structure_section,
        "gp_analysis": generate_gp_analysis_section,
        "risks": generate_risks_section,
    }
    
    if section_name not in generators:
        available = ", ".join(generators.keys())
        raise ValueError(f"Seção '{section_name}' não encontrada. Disponíveis: {available}")
    
    return generators[section_name](facts, model)


def generate_full_memo(facts: dict, model=None) -> dict:
    """
    Gera o memo secundário completo com todas as seções.
    
    Args:
        facts: Dicionário com facts estruturados
        model: Modelo LLM (opcional)
    
    Returns:
        Dict com todas as seções geradas
    """
    sections = [
        "intro",
        "seller_context",
        "portfolio",
        "valuation",
        "returns",
        "structure",
        "gp_analysis",
        "risks"
    ]
    
    memo = {}
    for section in sections:
        memo[section] = generate_section(section, facts, model)
    
    return memo
