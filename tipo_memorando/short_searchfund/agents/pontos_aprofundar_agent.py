"""
Agente de Pontos a Aprofundar - Short Memo Search Fund

Responsável por gerar a seção "Pontos a Aprofundar" com questões críticas para DD.
"""

from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import os
from ..shared import (
    build_facts_section,
    get_currency_safe,
    get_name_safe,
    get_text_safe,
    enrich_prompt,
    fix_number_formatting,
)


class PontosAprofundarAgent:
    """Agente especializado em geração de Pontos a Aprofundar para Short Memo Search Fund."""
    
    def __init__(self, model: str = "gpt-4o", temperature: float = 0.25):
        self.model = model
        self.temperature = temperature
        self.section_name = "Pontos a Aprofundar"
        self.llm = None  # Será injetado pelo LangGraph orchestrator
    
    def set_llm(self, llm):
        """Injeta LLM compartilhado (usado pelo LangGraph orchestrator)"""
        self.llm = llm
    
    def generate(
        self,
        facts: Dict[str, Any],
        rag_context: Optional[str] = None
    ) -> str:
        """
        Gera seção de Pontos a Aprofundar.
        
        Args:
            facts: Dict com facts estruturados
            rag_context: Contexto opcional
        
        Returns:
            Texto da seção (lista organizada)
        """
        # Usar LLM injetado se disponível, senão criar novo (compatibilidade)
        if not self.llm:
            apikey = os.getenv("OPENAI_API_KEY")
            if not apikey:
                raise ValueError("OPENAI_API_KEY não encontrada no ambiente")
            self.llm = ChatOpenAI(model=self.model, api_key=apikey, temperature=self.temperature)
        
        llm = self.llm

        # ===== QUERY DOS FACTS (COBERTURA COMPLETA) =====
        identification_section = build_facts_section(
            facts, "identification",
            {
                "company_name": "Nome da empresa",
                "business_description": "Descrição do negócio",
                "investor_name": "Nome do investor/searcher",
            }
        )
        
        # Obtém moeda da transação
        # Obtém moeda da transação (sempre usa fallback "BRL" se desabilitado)
        currency = get_currency_safe(facts, section="transaction_structure", field="currency")
        currency_label = "R$m" if currency == "BRL" else "US$m"
        
        transaction_section = build_facts_section(
            facts, "transaction_structure",
            {
                "stake_pct": "Participação (%)",
                "ev_mm": f"EV ({currency_label})",
                "multiple_ev_ebitda": "Múltiplo EV/EBITDA",
                "seller_note_mm": f"Seller note ({currency_label})",
                "seller_note_terms": "Termos seller note",
                "earnout_mm": f"Earnout ({currency_label})",
                "earnout_conditions": "Condições earnout",
                "closing_adjustments": "Ajustes de fechamento",
            }
        )
        
        financials_section = build_facts_section(
            facts, "financials_history",
            {
                "revenue_cagr_pct": "CAGR receita histórico (%)",
                "ebitda_margin_current_pct": "Margem EBITDA (%)",
                "leverage_net_debt_ebitda": "Alavancagem (ND/EBITDA)",
                "cash_conversion_pct": "Conversão de caixa (%)",
            }
        )
        
        qualitative_section = build_facts_section(
            facts, "qualitative",
            {
                "competitive_advantages": "Vantagens competitivas",
                "main_competitors": "Competidores principais",
                "customer_concentration": "Concentração de clientes",
                "supplier_concentration": "Concentração de fornecedores",
                "key_risks": "Riscos identificados",
                "regulatory_risks": "Riscos regulatórios",
            }
        )
        
        projections_section = build_facts_section(
            facts, "projections",
            {
                "revenue_cagr_projected_pct": "CAGR receita projetado (%)",
                "ebitda_margin_exit_pct": "Margem EBITDA na saída (%)",
                "growth_drivers": "Drivers de crescimento",
            }
        )
        
        # ===== EXTRAI INFORMAÇÕES CHAVE =====
        # Nomes usam placeholder se desabilitados
        company_name = get_name_safe(facts, "identification", "company_name", "[nome da empresa]")
        investor_name = get_name_safe(facts, "identification", "investor_name", "[nome do searcher]")
        
        # Textos retornam None se desabilitados (devem ser omitidos)
        business_description = get_text_safe(facts, "identification", "business_description")
        key_risks = get_text_safe(facts, "qualitative", "key_risks")
        
        # Placeholders apenas para validação do prompt
        if business_description is None:
            business_description = "[descrição do negócio]"
        if key_risks is None:
            key_risks = "[riscos a identificar]"

        # ===== SYSTEM PROMPT (DETALHADO E GUIADO) =====
        system_prompt = f"""Você é um analista sênior de Private Equity com 15 anos de experiência escrevendo a seção "Pontos a Aprofundar" de um Short Memo de Search Fund para o comitê de investimento da Spectra Capital.

═══════════════════════════════════════════════════════════════════════
ESTRUTURA OBRIGATÓRIA - LISTA COM BULLET POINTS
═══════════════════════════════════════════════════════════════════════

**FORMATO:** Lista com bullet points (hífen "-", NÃO numere)
**QUANTIDADE:** 5-8 pontos no total
**COMPRIMENTO:** 1-2 linhas por ponto (máximo)

**VERBOS PERMITIDOS (use APENAS estes no início):**
- Aprofundar
- Entender
- Validar
- Definir
- Montar

**ESTRUTURA DE CADA PONTO:**
[Verbo] + [área/tema específico] + [contexto breve ou detalhamento]

**EXEMPLOS BEM ESCRITOS:**
✓ "Aprofundar na estrutura da transação para entender se a empresa realmente não ficará exposta aos passivos tributários pós-aquisição"
✓ "Validar as premissas de crescimento de 25% a.a. e expansão de margem de 8 p.p. até 2030, que parecem agressivas vs. histórico"
✓ "Entender se a tecnologia da empresa, a base de clientes e os dados de consumo são diferenciais competitivos relevantes"
✓ "Definir como ficará a dinâmica com [parceiro] e possível impacto disso na margem e ROIC"

**EXEMPLOS MAL ESCRITOS:**
✗ "É necessário aprofundar..." (não use conjugações)
✗ "1. Aprofundar..." (não numere)
✗ "Entender o mercado" (genérico demais, seja específico)

═══════════════════════════════════════════════════════════════════════
CATEGORIAS TÍPICAS (PRIORIZE NESTA ORDEM)
═══════════════════════════════════════════════════════════════════════

1. **Estrutura da Transação:**
   - Passivos contingentes, tributários, trabalhistas
   - Seller note (termos não definidos, garantias)
   - Earnout (condições, gatilhos, disputas potenciais)
   - Estruturas especiais (aquisição de ativos, SPVs)
   - Ajustes de preço, escrows, holdbacks

2. **Validação de Premissas Financeiras:**
   - Crescimento agressivo vs. histórico
   - Expansão de margens (realismo, drivers)
   - Capex, working capital, conversão de caixa
   - Qualidade do EBITDA (ajustes recorrentes?)
   - Dividendos projetados vs. geração de caixa

3. **Mercado e Competição:**
   - Market share (espaço para crescimento?)
   - Penetração em novos segmentos/geografias
   - Competidores (ameaça de novos entrantes?)
   - Dinâmica competitiva (poder de precificação)
   - Barreiras de entrada (sustentáveis?)

4. **Riscos Operacionais:**
   - Key man risk (dependência de fundadores)
   - Concentração de clientes/fornecedores
   - Complexidade operacional
   - Transição de management
   - Dependências críticas (concessionárias, parcerias)

5. **Diferenciais Competitivos:**
   - Validar se são reais e defensáveis
   - Tecnologia, base de clientes, dados
   - Switching costs, network effects
   - Qualidade vs. discurso comercial

6. **Governança e Alocação (se relevante):**
   - Estrutura de governança pós-aquisição
   - Alocação do searcher e co-investidores
   - Plano de incentivos para management

═══════════════════════════════════════════════════════════════════════
REGRAS DE ESTILO (NÃO NEGOCIÁVEIS)
═══════════════════════════════════════════════════════════════════════

✅ **Especificidade:**
   - Inclua números quando relevante ("CAGR de 25%", "margem de 58% para 52%")
   - Mencione empresas, parceiros, segmentos específicos
   - Cite valores, percentuais, prazos específicos

✅ **Brevidade:**
   - Máximo 2 linhas por ponto
   - Uma ideia por bullet
   - Direto ao ponto, sem rodeios

✅ **Criticidade:**
   - Priorize pontos que afetam decisão de investimento
   - Foque em incertezas materiais
   - Evite pontos "nice to know" - apenas "need to know"

✅ **Formato:**
   - Use hífen "-" no início de cada ponto
   - NÃO numere ("1.", "2.", etc.)
   - NÃO use subcategorias com subtítulos em negrito
   - NÃO quebre pontos em múltiplas linhas
   - Cada ponto em UMA linha corrida

✅ **Baseie-se em FATOS:**
   - Use APENAS informações dos facts ou RAG context
   - NÃO invente riscos genéricos
   - Se dados ausentes, foque em validações de premissas gerais

═══════════════════════════════════════════════════════════════════════
TRATAMENTO DE DADOS AUSENTES
═══════════════════════════════════════════════════════════════════════

- **Sem riscos específicos identificados:** Foque em validações padrão de DD (qualidade EBITDA, concentração clientes, premissas crescimento)
- **Sem seller note/earnout:** Omita pontos sobre estrutura de pagamento
- **Sem projeções:** Foque em validação de histórico e mercado
- **Informações limitadas:** Priorize pontos de validação geral (mercado, competição, operacional)

**OUTPUT:** Apenas a lista de pontos (5-8 bullets), sem título de seção, sem categorias."""

        # ===== USER PROMPT (COM TODOS OS FACTS + RAG) =====
        rag_section = ""
        if rag_context:
            rag_section = f"""
═══════════════════════════════════════════════════════════════════════
CONTEXTO ADICIONAL DO DOCUMENTO (RAG)
═══════════════════════════════════════════════════════════════════════

Use este contexto para IDENTIFICAR riscos, incertezas e pontos críticos.
Priorize riscos explicitamente mencionados no documento original.

Contexto pode incluir:
- Riscos da estrutura da transação (passivos, seller note, earnout)
- Riscos de mercado e competição (market share, competidores, barreiras)
- Riscos financeiros e premissas (crescimento agressivo, margens, capex)
- Riscos operacionais (key man, dependências, complexidade)

{rag_context}
"""

        user_prompt = f"""
═══════════════════════════════════════════════════════════════════════
DADOS ESTRUTURADOS (FACTS) - USE PARA IDENTIFICAR RISCOS
═══════════════════════════════════════════════════════════════════════

[IDENTIFICAÇÃO]
{identification_section}

[ESTRUTURA DA TRANSAÇÃO]
{transaction_section}

[FINANCIALS HISTÓRICO]
{financials_section}

[QUALITATIVO E RISCOS]
{qualitative_section}

[PROJEÇÕES]
{projections_section}
{rag_section}
═══════════════════════════════════════════════════════════════════════
INSTRUÇÕES FINAIS
═══════════════════════════════════════════════════════════════════════

1. Gere 5-8 pontos em formato de lista com hífen "-"
2. Cada ponto começa com verbo (Aprofundar/Validar/Entender/Definir/Montar)
3. Seja ESPECÍFICO - inclua números, nomes, valores quando relevante
4. Máximo 2 linhas por ponto
5. Priorize riscos mencionados explicitamente nos facts ou RAG
6. Se dados limitados, foque em validações padrão de DD
7. NÃO numere, NÃO use categorias, NÃO quebre linhas
8. Base-se EXCLUSIVAMENTE em informações disponíveis

Comece AGORA com o primeiro ponto:"""

        # Enriquecer prompts com exemplos dos templates
        system_prompt = enrich_prompt("pontos_aprofundar", system_prompt)

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        response = llm.invoke(messages)
        return fix_number_formatting(response.content.strip())
