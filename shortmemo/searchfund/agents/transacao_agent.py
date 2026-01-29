"""
Agente de Transação - Short Memo Search Fund

Responsável por gerar a seção "Transação/Oportunidade" com valuation e estrutura.
"""

from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import os
from ..shared import (
    build_facts_section,
    get_currency_safe,
    get_name_safe,
    get_numeric_safe,
    get_currency_symbol,
    get_currency_label,
    fix_number_formatting,
    enrich_prompt,
)


class TransacaoAgent:
    """Agente especializado em geração de Transação para Short Memo Search Fund."""
    
    def __init__(self, model: str = "gpt-4o", temperature: float = 0.25):
        self.model = model
        self.temperature = temperature
        self.section_name = "Transação/Oportunidade"
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
        Gera seção de Transação/Oportunidade.
        
        Args:
            facts: Dict com facts estruturados
            rag_context: Contexto opcional
        
        Returns:
            Texto da seção (3-4 parágrafos)
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
                "equity_value_mm": f"Equity Value ({currency_label})",
                "multiple_ev_ebitda": "Múltiplo EV/EBITDA",
                "multiple_reference_period": "Período do múltiplo",
                "cash_payment_mm": f"Pagamento à vista ({currency_label})",
                "seller_note_mm": f"Seller note ({currency_label})",
                "seller_note_terms": "Termos seller note",
                "earnout_mm": f"Earnout ({currency_label})",
                "earnout_conditions": "Condições earnout",
                "multiple_with_earnout": "Múltiplo c/ earnout",
                "acquisition_debt_mm": f"Dívida de aquisição ({currency_label})",
                "equity_check_mm": f"Equity check ({currency_label})",
                "debt_equity_ratio": "Debt/Equity",
                "closing_adjustments": "Ajustes de fechamento",
                "escrow_amount": "Escrow",
            }
        )
        
        returns_section = build_facts_section(
            facts, "returns",
            {
                "irr_pct": "IRR alvo (%)",
                "moic": "MOIC alvo (x)",
                "holding_period_years": "Holding period (anos)",
                "entry_multiple": "Múltiplo de entrada",
                "base_case_assumptions": "Premissas do cenário base",
            }
        )
        
        projections_section = build_facts_section(
            facts, "projections",
            {
                "exit_year": "Ano de saída",
                "exit_multiple_ev_ebitda": "Múltiplo de saída (EV/EBITDA)",
                "revenue_cagr_projected": "CAGR receita projetado (%)",
                "ebitda_margin_exit": "Margem EBITDA na saída (%)",
            }
        )
        
        financials_section = build_facts_section(
            facts, "financials_history",
            {
                "ebitda_current_mm": f"EBITDA atual ({currency_label})",
                "net_debt_mm": f"Dívida líquida ({currency_label})",
            }
        )
        
        valuation_section = build_facts_section(
            facts, "valuation",
            {
                "valuation_methodology": "Metodologia de valuation",
                "comparable_multiples": "Múltiplos comparáveis",
                "premium_discount": "Prêmio/desconto",
                "valuation_rationale": "Racional do valuation",
            }
        )
        
        # ===== EXTRAI INFORMAÇÕES CHAVE PARA VALIDAÇÃO =====
        # Nomes usam placeholder se desabilitados
        company_name = get_name_safe(facts, "identification", "company_name", "[nome da empresa]")
        
        # Valores numéricos retornam None se desabilitados (devem ser omitidos)
        ret = facts.get("returns", {})
        irr_pct = get_numeric_safe(facts, "returns", "irr_pct")
        moic = get_numeric_safe(facts, "returns", "moic")
        
        # Datas retornam None se desabilitadas (devem ser omitidas)
        exit_year = get_numeric_safe(facts, "projections", "exit_year")
        exit_multiple = get_numeric_safe(facts, "projections", "exit_multiple_ev_ebitda")
        
        # Placeholders apenas para validação do prompt
        if exit_year is None:
            exit_year = "[ano de saída]"
        if exit_multiple is None:
            exit_multiple = "[múltiplo de saída]"

        # ===== SYSTEM PROMPT (DETALHADO E GUIADO) =====
        system_prompt = f"""Você é um analista sênior de Private Equity com 15 anos de experiência escrevendo a seção "Transação" de um Short Memo de Search Fund para o comitê de investimento da Spectra Capital.

═══════════════════════════════════════════════════════════════════════
ESTRUTURA OBRIGATÓRIA - 3-4 PARÁGRAFOS
═══════════════════════════════════════════════════════════════════════

§ PARÁGRAFO 1 - Estrutura da Transação (2-3 frases):
  - Abertura típica: "A aquisição contempla X% do equity da **{company_name}** a um EV de {currency_symbol} Ym (Zx EBITDA [período])."
  - Composição: "A estrutura da transação inclui três componentes: pagamento à vista de {currency_symbol} Am (Bx EBITDA), seller note de {currency_symbol} Cm com [termos], e earn-out de até {currency_symbol} Dm condicionado a [condições]."
  - Múltiplo com earnout: "Com o pagamento integral do earn-out, o múltiplo de entrada subiria para Xx EBITDA."
  - **IMPORTANTE:** Se componentes estiverem ausentes, ajuste a frase adequadamente

§ PARÁGRAFO 2 - Análise da Estrutura (2-4 frases):
  - Atratividade: "O preço de entrada negociado parece atrativo, especialmente considerando..."
  - Alinhamento: "A estrutura de seller note com [termos] demonstra alinhamento de interesses com o vendedor"
  - Debt/Equity: "A aquisição será realizada sem endividamento" ou "com leverage de X,Yx"
  - Flexibilidade financeira resultante

§ PARÁGRAFO 3 - Retornos Esperados (3-4 frases):
  - Cenário base: "Considerando o cenário base do searcher ([premissas principais]) e saída em {exit_year} a {exit_multiple}x EBITDA, os retornos projetados são de {irr_pct or 'X'}% TIR e {moic or 'Y,Z'}x MOIC."
  - Premissas críticas: "O searcher assume [premissa 1], [premissa 2] e [premissa 3]."
  - Múltiplo de saída: "saída ao mesmo múltiplo de entrada" ou "saída a [X]x EBITDA"
  - Se retornos ausentes: omita números específicos e use "retornos atrativos para a tese"

§ PARÁGRAFO 4 - Upsides/Riscos (opcional, 2-3 frases):
  - Opcionalidades de crescimento que podem gerar retornos superiores
  - Cenários alternativos ou sensibilidades
  - Riscos da tese de retorno ou pontos a aprofundar

═══════════════════════════════════════════════════════════════════════
VOCABULÁRIO ESPECÍFICO DE TRANSAÇÃO (USE NATURALMENTE)
═══════════════════════════════════════════════════════════════════════

✅ "estrutura da transação", "componentes da transação"
✅ "alinhamento de interesses com o vendedor"
✅ "flexibilidade financeira", "posição de caixa pós-fechamento"
✅ "cenário base", "premissas do modelo", "opcionalidades de crescimento"
✅ "múltiplo de entrada/saída", "saída ao mesmo múltiplo"
✅ "aquisição sem endividamento" ou "leverage de X,Yx"

═══════════════════════════════════════════════════════════════════════
REGRAS DE ESTILO (NÃO NEGOCIÁVEIS)
═══════════════════════════════════════════════════════════════════════

✅ Tom profissional e analítico
✅ Quantifique TUDO: valores, múltiplos, prazos, taxas, IRR, MOIC
✅ Use **negrito** para: empresa ({company_name}), valores ({currency_symbol} Xm), múltiplos (Xx)
✅ Seja específico sobre termos (prazos, juros, condições de seller note/earnout)
✅ **SEMPRE** atribua premissas e retornos ao searcher
✅ Cada parágrafo: 3-5 frases, bem conectadas
✅ NÃO invente dados: se campo estiver vazio, ajuste frase ou omita
✅ NÃO use bullets, numerações ou títulos - apenas parágrafos fluidos
✅ Separe parágrafos com linha em branco

═══════════════════════════════════════════════════════════════════════
TRATAMENTO DE DADOS AUSENTES
═══════════════════════════════════════════════════════════════════════

- **Sem seller note/earnout:** Mencione apenas pagamento à vista
- **Sem retornos (IRR/MOIC):** "os retornos projetados são atrativos para a tese de investimento"
- **Sem múltiplo de saída:** "saída ao mesmo múltiplo de entrada" (assumir conservador)
- **Sem premissas detalhadas:** Mencione apenas premissas disponíveis
- **Sem debt/equity:** "A aquisição será realizada sem endividamento" (assumir conservador)

**OUTPUT:** Apenas os 3-4 parágrafos, sem título de seção."""

        # ===== USER PROMPT (COM TODOS OS FACTS + RAG) =====
        rag_section = ""
        if rag_context:
            rag_section = f"""
═══════════════════════════════════════════════════════════════════════
CONTEXTO ADICIONAL DO DOCUMENTO (RAG)
═══════════════════════════════════════════════════════════════════════

Use este contexto para ENRIQUECER a análise da transação (não para sobrescrever facts).
Se houver conflito entre facts estruturados e RAG, PRIORIZE os facts.

Contexto pode incluir:
- Estrutura detalhada da transação (componentes, termos)
- Termos e condições especiais (seller note, earnout, ajustes)
- Retornos esperados e premissas do modelo
- Estratégia de saída e opcionalidades
- Riscos da tese de retorno

{rag_context}
"""

        user_prompt = f"""
═══════════════════════════════════════════════════════════════════════
DADOS ESTRUTURADOS (FACTS) - USE EXATAMENTE COMO FORNECIDO
═══════════════════════════════════════════════════════════════════════

[IDENTIFICAÇÃO]
{identification_section}

[ESTRUTURA DA TRANSAÇÃO]
{transaction_section}

[RETORNOS ALVO]
{returns_section}

[PROJEÇÕES E SAÍDA]
{projections_section}

[FINANCIALS (PARA CONTEXTO)]
{financials_section}

[VALUATION]
{valuation_section}
{rag_section}
═══════════════════════════════════════════════════════════════════════
INSTRUÇÕES FINAIS
═══════════════════════════════════════════════════════════════════════

1. Escreva 3-4 parágrafos seguindo a estrutura obrigatória
2. Primeira frase típica: "A aquisição contempla X% do equity da **{company_name}** a um EV de {currency_symbol} Ym (Zx EBITDA [período])."
3. Use os números EXATOS dos facts - NÃO invente ou arredonde
4. Se retornos (IRR/MOIC) disponíveis: mencione claramente no parágrafo 3
5. Se algum campo estiver ausente, ajuste a frase ou omita (não invente)
6. SEMPRE atribua premissas e retornos ao searcher
7. Mantenha tom profissional e crítico

Comece AGORA com o primeiro parágrafo (estrutura da transação):"""

        # Enriquecer prompts com exemplos dos templates
        system_prompt = enrich_prompt("transacao", system_prompt)

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        response = llm.invoke(messages)
        return fix_number_formatting(response.content.strip())
