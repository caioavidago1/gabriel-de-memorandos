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
        
        PADRÃO - Parágrafo 1: "{casca} (search fund {nacionalidade} liderado por {searcher}, que iniciou
        seu período de busca no {data}) está avaliando a aquisição de uma companhia especializada em ..."
        Parágrafo 2: estrutura da transação (equity %, valor, múltiplos, % à vista, acquisition debt).
        
        Args:
            facts: Dict com facts estruturados (todas as seções)
            rag_context: Contexto extraído do documento (opcional)
        
        Returns:
            Texto da introdução (2 parágrafos)
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
                "fip_casca": "FIP (casca)",
                "investor_name": "Nome do investidor",
                "investor_nationality": "Nacionalidade do Search",
                "searcher_name": "Nome(s) do(s) Searcher(s)",
                "search_start_date": "Início do Período de Busca",
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
        # Casca (FIP): sujeito da primeira frase; fallback para investor_name
        casca = get_text_safe(facts, "identification", "fip_casca") or get_name_safe(facts, "identification", "investor_name", None)
        if not casca:
            casca = "[nome da casca/FIP]"
        # Nacionalidade: "search fund mexicano" / "search fund brasileiro"
        nationality_raw = get_text_safe(facts, "identification", "investor_nationality")
        if nationality_raw:
            nationality_raw = nationality_raw.strip().lower()
            if not nationality_raw.endswith(("o", "a", "e")):  # ex: "Brasil" -> "brasileiro" não aplicável, usar como está
                search_fund_nacionalidade = f"search fund {nationality_raw}"
            else:
                search_fund_nacionalidade = f"search fund {nationality_raw}"
        else:
            search_fund_nacionalidade = "search fund"
        searcher_names = get_name_safe(facts, "identification", "searcher_name", "[nome do searcher]")
        company_name = get_name_safe(facts, "identification", "company_name", "[nome da empresa]")
        search_start_date = get_text_safe(facts, "identification", "search_start_date")
        if search_start_date is None:
            search_start_date = "[data de início]"
        business_description = get_text_safe(facts, "identification", "business_description")
        if business_description is None:
            business_description = "[descrição do negócio]"
        company_location = get_text_safe(facts, "identification", "company_location")

        # ===== SYSTEM PROMPT (DETALHADO E GUIADO) =====
        system_prompt = f"""Você é um analista sênior de Private Equity com 15 anos de experiência escrevendo a seção "Introdução" de um Short Memo de Search Fund para o comitê de investimento da Spectra Capital.

═══════════════════════════════════════════════════════════════════════
PADRÃO OBRIGATÓRIO - PARÁGRAFO 1
═══════════════════════════════════════════════════════════════════════

**Primeira frase (EXATAMENTE esta estrutura):**

"A {casca} (search fund {search_fund_nacionalidade} liderado por {searcher_names}, que iniciou seu período de busca no {search_start_date}) está avaliando a aquisição de uma companhia especializada em {business_description}."

- Use "no" ou "em" conforme soe natural com a data (ex: "no segundo semestre de 2024", "em 2024").
- Opcional: após a descrição do negócio, acrescentar localização ou contexto se disponível nos facts (ex: "com foco na península da Baja California (região conhecida pelo turismo...)" ou "com foco em [company_location]").
- **Sujeito da frase é sempre a CASCA/FIP** (não "A X"), salvo se o fact fip_casca estiver vazio.

═══════════════════════════════════════════════════════════════════════
PARÁGRAFO 2 - ESTRUTURA DA TRANSAÇÃO (PADRÃO OBRIGATÓRIO)
═══════════════════════════════════════════════════════════════════════

Siga este modelo:

"A aquisição contempla [X]% do equity da [empresa] por [moeda] [valor] ([múltiplo]x EBITDA [ano]) e, incluindo custos de transação, search capital e step-up, o valor total da transação chega a [moeda] [valor total] ([múltiplo2]x EBITDA [ano] ou [múltiplo3]x EBITDA [ano]), estruturados em [Y]% à vista e [Z]% via acquisition debt, cujos termos [ainda estão em negociação / conforme detalhado nos facts]."

- Use stake_pct, company_name, equity_value_mm ou ev_mm, multiple_ev_ebitda, multiple_reference_period.
- Use total_transaction_value_mm e multiple_total quando disponíveis; caso contrário, adapte ("valor total não divulgado" ou "ainda em negociação").
- Use cash_pct_total e acquisition debt % (100 - cash_pct ou valor explícito dos facts). Se acquisition debt não houver %, use "via acquisition debt, cujos termos ainda estão em negociação".

═══════════════════════════════════════════════════════════════════════
ESTRUTURA OBRIGATÓRIA - 2 PARÁGRAFOS
═══════════════════════════════════════════════════════════════════════

§ PARÁGRAFO 1 - Contexto do Search e da empresa alvo:
  - Primeira frase no padrão acima (casca + search fund {search_fund_nacionalidade} + searcher + início da busca + companhia especializada em ...).
  - Incluir localização ou detalhe geográfico quando disponível nos facts (ex: com foco em região X).

§ PARÁGRAFO 2 - Estrutura da Transação:
  - Seguir o modelo: aquisição contempla X% equity da [empresa] por [valor] (múltiplo); valor total com custos/step-up; % à vista e % acquisition debt; termos.
  - Quantifique sempre com valores e múltiplos dos facts.

═══════════════════════════════════════════════════════════════════════
REGRAS DE ESTILO (NÃO NEGOCIÁVEIS)
═══════════════════════════════════════════════════════════════════════

✅ Tom profissional, primeira pessoa plural: "estamos avaliando", "entendemos que"
✅ Quantifique TUDO: valores exatos, múltiplos, percentuais
✅ Seja específico: "R$ 45m" não "valor significativo"
✅ Cada parágrafo: 3-5 frases, bem conectadas e sem repetição de informação
✅ NÃO invente dados: se campo estiver vazio, trate como "ainda em discussão" ou "não disponível"
✅ NÃO use bullets, numerações ou títulos - apenas parágrafos fluidos
✅ Separe parágrafos com linha em branco

**OUTPUT:** Apenas os 2 parágrafos, sem título de seção."""

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

1. Parágrafo 1: comece com a casca/FIP como sujeito, depois "(search fund [nacionalidade] liderado por [searcher], que iniciou seu período de busca no/em [data]) está avaliando a aquisição de uma companhia especializada em [descrição]."
2. Parágrafo 2: use o modelo da estrutura da transação (equity %, valor, múltiplos, valor total, % à vista, acquisition debt).
3. Use os números EXATOS dos facts; se algum campo faltar, use "ainda em discussão", "em negociação" ou "não informado".
4. Escreva EXATAMENTE 2 parágrafos. Tom profissional e analítico.

Comece AGORA com o primeiro parágrafo:"""

        # Enriquecer prompt com exemplos dos templates
        system_prompt = enrich_prompt("intro", system_prompt)

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        response = llm.invoke(messages)
        return fix_number_formatting(response.content.strip())
