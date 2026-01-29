"""
Agente de Introdução - Short Memo Search Fund

Responsável por gerar a seção "Introdução" com contexto do searcher e do deal.
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
    get_currency_symbol,
    get_currency_label,
    fix_number_formatting,
    enrich_prompt,
)


class IntroAgent:
    """Agente especializado em geração de Introdução para Short Memo Search Fund."""
    
    def __init__(self, model: str = "gpt-4o", temperature: float = 0.25):
        self.model = model
        self.temperature = temperature
        self.section_name = "Introdução"
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
        Gera seção de Introdução.
        
        PADRÃO OBRIGATÓRIO - Primeira frase:
        "A {investor} (search liderado por {searcher}, que iniciou seu período de busca em {data})
         está avaliando a aquisição da {company}..."
        
        Args:
            facts: Dict com facts estruturados (todas as seções)
            rag_context: Contexto extraído do documento (opcional)
        
        Returns:
            Texto da introdução (4 parágrafos)
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
                "investor_name": "Nome do investidor",
                "investor_nationality": "Nacionalidade",
                "searcher_name": "Responsável(is)",
                "search_start_date": "Início da busca",
                "company_name": "Empresa alvo",
                "company_location": "Localização",
                "business_description": "Descrição do negócio",
                "deal_context": "Contexto do Deal",
            }
        )
        
        # Obtém moeda da transação (sempre usa fallback "BRL" se desabilitado)
        currency = get_currency_safe(facts, section="transaction_structure", field="currency")
        currency_symbol = get_currency_symbol(currency)
        currency_label = get_currency_label(currency)
        
        transaction_section = build_facts_section(
            facts, "transaction_structure",
            {
                "stake_pct": "Participação (%)",
                "ev_mm": f"EV ({currency_label})",
                "multiple_ev_ebitda": "Múltiplo EV/EBITDA",
                "multiple_reference_period": "Período do múltiplo",
                "cash_payment_mm": f"Pagamento à vista ({currency_label})",
                "seller_note_mm": f"Seller note ({currency_label})",
                "seller_note_terms": "Termos seller note",
                "earnout_mm": f"Earnout ({currency_label})",
                "earnout_conditions": "Condições earnout",
                "multiple_with_earnout": "Múltiplo c/ earnout",
            }
        )
        
        financials_section = build_facts_section(
            facts, "financials_history",
            {
                "revenue_current_mm": f"Receita atual ({currency_label})",
                "revenue_cagr_pct": "CAGR receita (%)",
                "revenue_cagr_period": "Período CAGR receita",
                "ebitda_current_mm": f"EBITDA atual ({currency_label})",
                "ebitda_margin_current_pct": "Margem EBITDA (%)",
                "net_debt_mm": f"Dívida líquida ({currency_label})",
                "cash_conversion_pct": "Conversão caixa (%)",
            }
        )
        
        returns_section = build_facts_section(
            facts, "returns",
            {
                "irr_pct": "IRR alvo (%)",
                "moic": "MOIC alvo (x)",
                "holding_period_years": "Holding period (anos)",
            }
        )
        
        projections_section = build_facts_section(
            facts, "projections",
            {
                "exit_year": "Ano de saída",
                "exit_multiple_ev_ebitda": "Múltiplo de saída (EV/EBITDA)",
            }
        )
        
        # ===== EXTRAI INFORMAÇÕES CHAVE PARA VALIDAÇÃO =====
        # Nomes usam placeholder se desabilitados
        search_fund_name = get_name_safe(facts, "identification", "investor_name", "[nome do search fund]")
        searcher_names = get_name_safe(facts, "identification", "searcher_name", "[nome do searcher]")
        company_name = get_name_safe(facts, "identification", "company_name", "[nome da empresa]")
        
        # Datas retornam None se desabilitadas (devem ser omitidas)
        search_start_date = get_text_safe(facts, "identification", "search_start_date")
        if search_start_date is None:
            search_start_date = "[data de início]"  # Placeholder apenas para validação do prompt
        
        # Textos retornam None se desabilitados (devem ser omitidos)
        business_description = get_text_safe(facts, "identification", "business_description")
        if business_description is None:
            business_description = "[descrição do negócio]"  # Placeholder apenas para validação do prompt

        # ===== SYSTEM PROMPT (DETALHADO E GUIADO) =====
        system_prompt = f"""Você é um analista sênior de Private Equity com 15 anos de experiência escrevendo a seção "Introdução" de um Short Memo de Search Fund para o comitê de investimento da Spectra Capital.

═══════════════════════════════════════════════════════════════════════
PADRÃO OBRIGATÓRIO - PRIMEIRA FRASE
═══════════════════════════════════════════════════════════════════════

"A {search_fund_name} (search liderado por {searcher_names}, que iniciou seu período de busca em {search_start_date}) está avaliando a aquisição da {company_name}, uma companhia especializada em {business_description}."

**REGRA CRÍTICA:** Use EXATAMENTE essa estrutura, substituindo apenas os valores entre {{}} pelos facts fornecidos.

═══════════════════════════════════════════════════════════════════════
ESTRUTURA OBRIGATÓRIA - 4 PARÁGRAFOS
═══════════════════════════════════════════════════════════════════════

§ PARÁGRAFO 1 - Contexto do Search e Deal:
  - Primeira frase segue o padrão obrigatório acima
  - Mencione imediatamente: participação adquirida, EV ({currency_symbol}m), múltiplo de entrada
  - Inclua período de referência do múltiplo (ex: "LTM mai/25")

§ PARÁGRAFO 2 - Estrutura da Transação:
  - Detalhe: EV, múltiplo EV/EBITDA, % equity adquirido
  - Pagamento: à vista, seller note (valor + termos principais), earnout (valor + condições)
  - Se earnout presente: mencione múltiplo total incluindo earnout
  - IMPORTANTE: Se algum campo estiver ausente, use "ainda em discussão" ou "não divulgado"

§ PARÁGRAFO 3 - Snapshot Financeiro:
  - Receita atual, EBITDA, margem EBITDA
  - Crescimento histórico (CAGR) se disponível
  - Dívida líquida e alavancagem se disponível
  - Conecte com retornos: IRR alvo, MOIC alvo, holding period

§ PARÁGRAFO 4 - Contexto Estratégico:
  - Tese de investimento resumida
  - Principais drivers de valor
  - Próximos passos ou pontos de atenção

═══════════════════════════════════════════════════════════════════════
REGRAS DE ESTILO (NÃO NEGOCIÁVEIS)
═══════════════════════════════════════════════════════════════════════

✅ Tom profissional, primeira pessoa plural: "estamos avaliando", "entendemos que"
✅ Quantifique TUDO: valores exatos, múltiplos, percentuais
✅ Use **negrito** para: empresa, searcher, valores (R$ Xm), múltiplos (Xx)
✅ Seja específico: "R$ 45m" não "valor significativo"
✅ Cada parágrafo: 3-5 frases, bem conectadas
✅ NÃO invente dados: se campo estiver vazio, trate como "ainda em discussão" ou "não disponível"
✅ NÃO use bullets, numerações ou títulos - apenas parágrafos fluidos
✅ Separe parágrafos com linha em branco

**OUTPUT:** Apenas os 4 parágrafos, sem título de seção."""

        # ===== USER PROMPT (COM TODOS OS FACTS + RAG) =====
        rag_section = ""
        if rag_context:
            rag_section = f"""
═══════════════════════════════════════════════════════════════════════
CONTEXTO ADICIONAL DO DOCUMENTO (RAG)
═══════════════════════════════════════════════════════════════════════

Use este contexto para ENRIQUECER o texto (não para sobrescrever facts).
Se houver conflito entre facts estruturados e RAG, PRIORIZE os facts.

{rag_context}
"""

        user_prompt = f"""
═══════════════════════════════════════════════════════════════════════
DADOS ESTRUTURADOS (FACTS) - USE EXATAMENTE COMO FORNECIDO
═══════════════════════════════════════════════════════════════════════

[IDENTIFICAÇÃO]
{identification_section}

[TRANSAÇÃO]
{transaction_section}

[FINANCIALS HISTÓRICO]
{financials_section}

[RETORNOS ALVO]
{returns_section}

[PROJEÇÕES DE SAÍDA]
{projections_section}
{rag_section}
═══════════════════════════════════════════════════════════════════════
INSTRUÇÕES FINAIS
═══════════════════════════════════════════════════════════════════════

1. Escreva EXATAMENTE 4 parágrafos seguindo a estrutura obrigatória
2. Use os números EXATOS dos facts - NÃO invente ou arredonde
3. Se algum campo estiver ausente, marque como "ainda em discussão" ou omita
4. Siga o padrão da primeira frase sem exceções
5. Mantenha tom profissional e analítico

Comece AGORA com o primeiro parágrafo (primeira frase obrigatória):"""

        # Enriquecer prompt com exemplos dos templates
        system_prompt = enrich_prompt("intro", system_prompt)

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        response = llm.invoke(messages)
        return fix_number_formatting(response.content.strip())
