"""
Agente de Portfolio - Short Memo Primário (Gestora)

Responsável por gerar a seção "Portfolio Atual" com fundos anteriores e deals.
"""

from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import os
from .facts_builder import build_facts_section
from .facts_utils import get_currency_safe, get_name_safe
from .utils import get_currency_symbol, get_currency_label
from .validator import fix_number_formatting
from .templates import enrich_prompt


class PortfolioAgent:
    """Agente especializado em geração de Portfolio para Short Memo Primário."""
    
    def __init__(self, model: str = "gpt-4o", temperature: float = 0.25):
        self.model = model
        self.temperature = temperature
        self.section_name = "Portfolio Atual"
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
        Gera seção de Portfolio Atual.
        
        Args:
            facts: Dict com facts estruturados
            rag_context: Contexto opcional (CRÍTICO para dados de portfolio/deals)
        
        Returns:
            Texto da seção (múltiplos parágrafos, organizados por fundo)
        """
        # Usar LLM injetado se disponível, senão criar novo (compatibilidade)
        if not self.llm:
            apikey = os.getenv("OPENAI_API_KEY")
            if not apikey:
                raise ValueError("OPENAI_API_KEY não encontrada no ambiente")
            self.llm = ChatOpenAI(model=self.model, api_key=apikey, temperature=self.temperature)
        
        llm = self.llm

        # ===== QUERY DOS FACTS (COBERTURA COMPLETA) =====
        gestora_section = build_facts_section(
            facts, "gestora",
            {
                "gestora_nome": "Nome da gestora",
                "gestora_track_record": "Track record",
            }
        )
        
        # Obtém moeda (sempre usa fallback "BRL" se desabilitado)
        currency = get_currency_safe(facts, section="fundo", field="fundo_moeda")
        currency_symbol = get_currency_symbol(currency)
        currency_label = get_currency_label(currency)

        # ===== EXTRAI INFORMAÇÕES CHAVE PARA VALIDAÇÃO =====
        # Nomes usam placeholder se desabilitados
        gestora_nome = get_name_safe(facts, "gestora", "gestora_nome", "[nome da gestora]")

        # ===== SYSTEM PROMPT (DETALHADO E GUIADO) =====
        system_prompt = f"""Você é um analista sênior de Private Equity com 15 anos de experiência escrevendo a seção "Portfolio Atual" de um Short Memo de investimento primário em fundo para o comitê de investimento da Spectra Capital.

═══════════════════════════════════════════════════════════════════════
ESTRUTURA OBRIGATÓRIA - HIERÁRQUICA POR FUNDO
═══════════════════════════════════════════════════════════════════════

A seção deve ser organizada HIERARQUICAMENTE:

1. DEAL BY DEAL (se houver investimentos antes do primeiro fundo)
   - Título: "### 3.1 Deal by Deal"
   - Introdução: "Antes de captar o seu primeiro fundo, a {gestora_nome} realizou os seguintes club deals..."
   - Para cada deal: bullet com formato:
     - **Empresa** (data investimento, valor investido, descrição): Receita passou de X para Y. EBITDA saiu de X para Y. Marcam a Zx EBITDA, resultando em Wx MOIC e V% TIR.

2. FUNDO I (ou nome do fundo anterior)
   - Título: "### 3.2 [Nome do Fundo]"
   - Introdução do fundo: tamanho, vintage, status, % investido, MOIC marcado
   - Para cada empresa/deal: subseção com título "#### [Nome da Empresa]"
   - Formato: "Data | Valor investido | NAV atual, múltiplo | TIR/MOIC"
   - Parágrafos descrevendo: tese, receita atual vs entrada, EBITDA atual vs entrada, performance, riscos

3. FUNDO II (se houver)
   - Mesma estrutura do Fundo I

═══════════════════════════════════════════════════════════════════════
FORMATO DE DEALS/EMPRESAS
═══════════════════════════════════════════════════════════════════════

Para cada empresa/deal, incluir:
- Nome da empresa
- Data de investimento (ex: "Set/23", "Ago/22")
- Valor investido ({currency_symbol} X mi)
- NAV atual e múltiplo de marcação (ex: "R$ 39,9 mi de NAV, 10,3x EBITDA")
- Retornos: TIR e MOIC (ex: "74%/3,0x (TIR/MOIC brutos)")
- Descrição da tese de investimento
- Receita: passou de X para Y
- EBITDA: saiu de X para Y (ou negativo para positivo)
- Múltiplo de marcação (EBITDA ou Receita)
- Status: ativo, desinvestido, em processo de saída
- Comentários sobre performance, riscos, pontos de atenção

═══════════════════════════════════════════════════════════════════════
REGRAS DE ESTILO (NÃO NEGOCIÁVEIS)
═══════════════════════════════════════════════════════════════════════

✅ Tom profissional, objetivo e transparente
✅ Quantifique TUDO: valores, múltiplos, percentuais, datas
✅ Use **negrito** para: nomes de empresas, fundos, valores-chave
✅ Seja específico sobre performance (crescimento, múltiplos, retornos)
✅ Organize hierarquicamente: fundo → empresa
✅ Use bullets para listar empresas dentro de deal by deal
✅ Use subseções (####) para empresas dentro de fundos
✅ Mencione deals problemáticos ou em turnaround de forma honesta
✅ Destaque deals de destaque (exits, alta performance)
✅ Cada empresa: 2-4 parágrafos descrevendo tese, performance e status

**OUTPUT:** Texto completo da seção com estrutura hierárquica (títulos, bullets, subseções)."""

        # ===== USER PROMPT (COM TODOS OS FACTS + RAG) =====
        rag_section = ""
        if rag_context:
            rag_section = f"""
═══════════════════════════════════════════════════════════════════════
CONTEXTO ADICIONAL DO DOCUMENTO (RAG) - CRÍTICO PARA PORTFOLIO
═══════════════════════════════════════════════════════════════════════

**IMPORTANTE:** Os dados de portfolio/deals geralmente vêm via RAG (texto livre).
Você DEVE extrair a estrutura hierárquica do RAG:

1. Identificar fundos mencionados (deal by deal, Fundo I, Fundo II, etc)
2. Para cada fundo, identificar empresas/deals
3. Para cada deal, extrair:
   - Nome da empresa
   - Data de investimento
   - Valor investido
   - Receita atual vs entrada
   - EBITDA atual vs entrada
   - Múltiplo de marcação
   - MOIC e TIR
   - Status (ativo/desinvestido)

Use este contexto como FONTE PRINCIPAL para dados de portfolio.
Se houver conflito com facts estruturados, PRIORIZE o RAG para portfolio.

{rag_context}
"""

        user_prompt = f"""
═══════════════════════════════════════════════════════════════════════
DADOS ESTRUTURADOS (FACTS) - USE COMO CONTEXTO COMPLEMENTAR
═══════════════════════════════════════════════════════════════════════

[GESTORA]
{gestora_section}
{rag_section}
═══════════════════════════════════════════════════════════════════════
INSTRUÇÕES FINAIS
═══════════════════════════════════════════════════════════════════════

1. Organize a seção hierarquicamente: deal by deal → Fundo I → Fundo II (se houver)
2. Para cada fundo: introdução com tamanho, status, MOIC marcado
3. Para cada empresa: nome, data, valor, performance detalhada
4. Use bullets para deal by deal, subseções (####) para empresas em fundos
5. Seja transparente sobre performance (bons e maus resultados)
6. Quantifique tudo: valores, múltiplos, percentuais

Comece AGORA com a estrutura hierárquica (deal by deal ou primeiro fundo):"""

        # Enriquecer prompts com exemplos dos templates
        system_prompt = enrich_prompt("portfolio", system_prompt)

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        response = llm.invoke(messages)
        return fix_number_formatting(response.content.strip())
