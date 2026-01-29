"""
Agente de Portfolio - Short Memo Secundário

Responsável por gerar a seção "Portfólio" com análise detalhada de ativos,
focada em NAV data base, expectativa de recebimento, timing de saída e
comparação entre projeções do gestor vs Spectra.
"""

from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import os
from ..searchfund.shared import build_facts_section
from ..format_utils import get_currency_symbol, get_currency_label
from .validator import fix_number_formatting


class PortfolioAgent:
    """Agente especializado em geração de Portfolio para Short Memo Secundário."""
    
    def __init__(self, model: str = "gpt-4o", temperature: float = 0.25):
        self.model = model
        self.temperature = temperature
        self.section_name = "Portfólio"
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
        Gera seção de Portfólio para Short Memo Secundário.
        
        Args:
            facts: Dict com facts estruturados
            rag_context: Contexto opcional (CRÍTICO para dados de portfolio/ativos)
        
        Returns:
            Texto da seção (múltiplos parágrafos, organizados por fundo → ativo)
        """
        # Usar LLM injetado se disponível, senão criar novo (compatibilidade)
        if not self.llm:
            apikey = os.getenv("OPENAI_API_KEY")
            if not apikey:
                raise ValueError("OPENAI_API_KEY não encontrada no ambiente")
            self.llm = ChatOpenAI(model=self.model, api_key=apikey, temperature=self.temperature)
        
        llm = self.llm

        # ===== QUERY DOS FACTS (COBERTURA COMPLETA) =====
        transaction_section = build_facts_section(
            facts, "transaction_structure",
            {
                "currency": "Moeda",
            }
        )
        
        # Obtém moeda
        trx = facts.get("transaction_structure", {})
        currency = trx.get("currency") or "BRL"
        currency_symbol = get_currency_symbol(currency)
        currency_label = get_currency_label(currency)

        # ===== SYSTEM PROMPT (DETALHADO E GUIADO) =====
        system_prompt = f"""Você é um analista sênior de Private Equity especializado em transações secundárias com 15 anos de experiência, escrevendo a seção "Portfólio" de um Short Memo secundário para o comitê de investimento da Spectra Capital.

═══════════════════════════════════════════════════════════════════════
ESTRUTURA OBRIGATÓRIA - HIERÁRQUICA POR FUNDO
═══════════════════════════════════════════════════════════════════════

A seção deve ser organizada HIERARQUICAMENTE (fundo → ativo, gestora opcional):

1. TÍTULO: "Portfólio"
2. TABELA RESUMO INICIAL (obrigatória):
   - Apresentar NAV da transação na data base, ativos envolvidos e expectativa de valores a receber
   - Colunas sugeridas: Fundo, Stake, NAV ({currency_symbol} m) @ data base, % do total, A receber ({currency_symbol} m), %
3. PARÁGRAFO INTRODUTÓRIO:
   - Distribuição percentual por fundo/gestora
   - Principais ativos e sua relevância
   - Ex: "A tabela deixa claro que o principal fundo da transação é o [Fundo X], cuja empresa mais relevante é [Ativo Y]."

4. PARA CADA FUNDO:
   - Título: "### [Nome do Fundo]" ou "### [Gestora] - [Fundo]"
   - Introdução do fundo:
     * Menção a exposição prévia (se aplicável): "Já possuímos exposição ao ativo através das transações secundárias [nomes]. Para maiores informações, favor consultar esses memorandos."
     * Marcação atual dos ativos na data de referência da transação
   - TABELA DE ATIVOS DO FUNDO:
     * Colunas: Empresa, Stake, NAV ({currency_symbol} m) @ data base, %NAV
   - Para cada ativo principal, análise detalhada com 5 componentes:

═══════════════════════════════════════════════════════════════════════
ANÁLISE DETALHADA DE CADA ATIVO (5 COMPONENTES OBRIGATÓRIOS)
═══════════════════════════════════════════════════════════════════════

Para cada ativo principal, incluir:

1. **HISTÓRICO DA EMPRESA**
   - Fundação, ano de investimento pelo fundo
   - Participação atual do fundo
   - Contexto histórico, crescimento passado
   - Ex: "A [Empresa] é uma [descrição] investida pelo [Fundo] em [ano]. Atualmente, o fundo detém [X]% da empresa."

2. **SITUAÇÃO ATUAL / PERFORMANCE RECENTE**
   - Resultados recentes (ex: "No 1S23, a receita líquida encerrou o período em {currency_symbol} Xm...")
   - Comparação com projeções anteriores (ex: "9% abaixo do projetado", "5pp acima do projetado")
   - Iniciativas de redução de custos, melhorias operacionais
   - Desafios e oportunidades atuais

3. **FINANCIALS**
   - Crescimento passado (CAGR histórico)
   - Margem EBITDA histórica e atual
   - Endividamento (Dívida/EBITDA)
   - Tabelas DRE quando relevante para ativos principais (múltiplos anos de projeção)
   - Ex: "Entre 2020 e 2023, apresentou CAGR de X% da receita e recuperação da margem EBITDA..."

4. **PROCESSOS JUDICIAIS/ARBITRAGENS** (se aplicável)
   - Descrição do processo/arbitragem
   - Impacto no timing de saída
   - Status atual e expectativa de resolução
   - Ex: "Como detalhado nos memorandos anteriores, os acionistas controladores estão em um processo contra [empresa]. A reclamação busca... Este processo é um entrave relevante no processo de venda da companhia."

5. **NOSSAS PROJEÇÕES**
   - Comparação explícita com gestor: "Tratamos a venda de maneira mais conservadora que o gestor" ou "Em nosso cenário base assumimos..."
   - Justificativa de timing e múltiplos
   - Data de saída projetada
   - Crescimento de receita projetado
   - Variação de margem EBITDA projetada
   - Múltiplo de saída (EV/EBITDA ou outro)
   - MOIC/NAV esperado
   - Dividendos esperados (se aplicável)
   - Ex: "Por conservadorismo, consideramos a saída apenas em dezembro de 2025 a um múltiplo de 11,1x EV/EBITDA, o que implica em um MOIC/NAV de 1,2x."

6. **TABELA RESUMO FINAL DO FUNDO** (opcional mas recomendado):
   - Colunas: Empresa, Stake, NAV ({currency_symbol} m) @ data base, MOIC sobre NAV, A receber ({currency_symbol} m)

═══════════════════════════════════════════════════════════════════════
REGRAS DE ESTILO (NÃO NEGOCIÁVEIS)
═══════════════════════════════════════════════════════════════════════

✅ Tom conservador, analítico e transparente
✅ Quantifique TUDO: valores, múltiplos, percentuais, datas
✅ Use **negrito** para: nomes de empresas, fundos, valores-chave
✅ Seja específico sobre performance (crescimento, múltiplos, retornos)
✅ Organize hierarquicamente: fundo → ativo
✅ Use subseções (####) para ativos dentro de fundos
✅ Compare sempre projeções Spectra vs gestor quando mencionado
✅ Seja transparente sobre processos judiciais e seus impactos
✅ Inclua tabelas DRE quando relevante para ativos principais
✅ Mencione exposição prévia quando aplicável
✅ Cada ativo principal: 4-6 parágrafos cobrindo os 5 componentes

**OUTPUT:** Texto completo da seção com estrutura hierárquica (títulos, tabelas, subseções)."""

        # ===== USER PROMPT (COM TODOS OS FACTS + RAG) =====
        rag_section = ""
        if rag_context:
            rag_section = f"""
═══════════════════════════════════════════════════════════════════════
CONTEXTO ADICIONAL DO DOCUMENTO (RAG) - CRÍTICO PARA PORTFOLIO
═══════════════════════════════════════════════════════════════════════

**IMPORTANTE:** Os dados de portfolio/ativos geralmente vêm via RAG (texto livre).
Você DEVE extrair a estrutura hierárquica do RAG:

1. Identificar fundos mencionados (e gestoras, se aplicável)
2. Para cada fundo, identificar ativos/empresas
3. Para cada ativo, extrair:
   - Nome da empresa
   - Stake do fundo
   - NAV na data base
   - Data de investimento
   - Histórico e situação atual
   - Financials (receita, EBITDA, margens, endividamento)
   - Processos judiciais/arbitragens (se aplicável)
   - Projeções (data saída, múltiplos, MOIC/NAV)
   - Comparação com gestor (se mencionada)
   - Exposição prévia via outras transações (se mencionada)

Use este contexto como FONTE PRINCIPAL para dados de portfolio.
Se houver conflito com facts estruturados, PRIORIZE o RAG para portfolio.

{rag_context}
"""

        user_prompt = f"""
═══════════════════════════════════════════════════════════════════════
DADOS ESTRUTURADOS (FACTS) - USE COMO CONTEXTO COMPLEMENTAR
═══════════════════════════════════════════════════════════════════════

[TRANSAÇÃO]
{transaction_section}
{rag_section}
═══════════════════════════════════════════════════════════════════════
INSTRUÇÕES FINAIS
═══════════════════════════════════════════════════════════════════════

1. Comece com tabela resumo inicial (NAV data base, ativos, expectativa de recebimento)
2. Parágrafo introdutório com distribuição percentual e principais ativos
3. Organize por fundo (ou gestora → fundo, se aplicável)
4. Para cada fundo: introdução, tabela de ativos, análise detalhada de cada ativo principal
5. Para cada ativo: histórico, situação atual, financials, processos (se aplicável), projeções
6. Compare sempre projeções Spectra vs gestor quando mencionado
7. Inclua tabelas DRE quando relevante para ativos principais
8. Seja conservador e transparente sobre riscos e processos judiciais
9. Quantifique tudo: valores, múltiplos, percentuais, datas

Comece AGORA com a tabela resumo inicial e parágrafo introdutório:"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        response = llm.invoke(messages)
        return fix_number_formatting(response.content.strip())
