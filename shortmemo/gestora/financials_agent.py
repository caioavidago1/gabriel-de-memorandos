"""
Agente de Financials - Short Memo Gestora

Responsável por gerar a seção "Financials" com histórico e projeções.
"""

from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import os
from .facts_builder import build_facts_section
from .validator import fix_number_formatting
from .facts_utils import get_name_safe, get_numeric_safe, get_text_safe, get_currency_safe
from ...format_utils import get_currency_symbol, get_currency_label


class FinancialsAgent:
    """Agente especializado em geração de Financials para Short Memo Gestora."""
    
    def __init__(self, model: str = "gpt-4o", temperature: float = 0.25):
        self.model = model
        self.temperature = temperature
        self.section_name = "Financials"
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
        Gera seção de Financials.
        
        Args:
            facts: Dict com facts estruturados
            rag_context: Contexto opcional do RAG
        
        Returns:
            Texto da seção (2-3 parágrafos)
        """
        # Usar LLM injetado se disponível, senão criar novo (compatibilidade)
        if not self.llm:
            apikey = os.getenv("OPENAI_API_KEY")
            if not apikey:
                raise ValueError("OPENAI_API_KEY não encontrada no ambiente")
            self.llm = ChatOpenAI(model=self.model, api_key=apikey, temperature=self.temperature)
        
        llm = self.llm

        # ===== QUERY DOS FACTS =====
        identification_section = build_facts_section(
            facts, "identificacao",
            {
                "company_name": "Nome da empresa",
            }
        )
        
        # Obtém moeda
        currency = get_currency_safe(facts, section="transaction_structure", field="currency")
        currency_label = get_currency_label(currency)
        currency_symbol = get_currency_symbol(currency)
        
        financials_section = build_facts_section(
            facts, "financials_history",
            {
                "revenue_current_mm": f"Receita atual ({currency_label})",
                "revenue_cagr_pct": "CAGR receita histórico (%)",
                "revenue_cagr_period": "Período CAGR",
                "ebitda_current_mm": f"EBITDA atual ({currency_label})",
                "ebitda_margin_current_pct": "Margem EBITDA (%)",
                "ebitda_cagr_pct": "CAGR EBITDA (%)",
                "gross_margin_pct": "Margem bruta (%)",
                "net_debt_mm": f"Dívida líquida ({currency_label})",
                "leverage_net_debt_ebitda": "Alavancagem (ND/EBITDA)",
                "cash_conversion_pct": "Conversão de caixa (% EBITDA)",
                "employees_count": "Funcionários",
                "financials_commentary": "Contexto do histórico",
            }
        )
        
        projections_section = build_facts_section(
            facts, "projections",
            {
                "revenue_exit_mm": f"Receita na saída ({currency_label})",
                "exit_year": "Ano de saída",
                "revenue_cagr_projected_pct": "CAGR receita projetado (%)",
                "projection_period": "Período de projeção",
                "ebitda_exit_mm": f"EBITDA na saída ({currency_label})",
                "ebitda_margin_exit_pct": "Margem EBITDA na saída (%)",
                "exit_multiple_ev_ebitda": "Múltiplo de saída (EV/EBITDA)",
                "growth_drivers": "Drivers de crescimento",
                "margin_expansion_plan": "Plano de expansão de margem",
                "projections_commentary": "Contexto das projeções",
            }
        )
        
        # ===== EXTRAI INFORMAÇÕES CHAVE =====
        company_name = get_name_safe(facts, "identificacao", "company_name", "[nome da empresa]")
        
        # Valores numéricos retornam None se desabilitados
        revenue_current = get_numeric_safe(facts, "financials_history", "revenue_current_mm")
        revenue_cagr = get_numeric_safe(facts, "financials_history", "revenue_cagr_pct")
        ebitda_current = get_numeric_safe(facts, "financials_history", "ebitda_current_mm")
        ebitda_margin = get_numeric_safe(facts, "financials_history", "ebitda_margin_current_pct")
        gross_margin = get_numeric_safe(facts, "financials_history", "gross_margin_pct")
        net_debt = get_numeric_safe(facts, "financials_history", "net_debt_mm")
        leverage = get_numeric_safe(facts, "financials_history", "leverage_net_debt_ebitda")
        cash_conversion = get_numeric_safe(facts, "financials_history", "cash_conversion_pct")
        
        # Projeções
        revenue_exit = get_numeric_safe(facts, "projections", "revenue_exit_mm")
        revenue_cagr_proj = get_numeric_safe(facts, "projections", "revenue_cagr_projected_pct")
        ebitda_exit = get_numeric_safe(facts, "projections", "ebitda_exit_mm")
        ebitda_margin_exit = get_numeric_safe(facts, "projections", "ebitda_margin_exit_pct")
        exit_multiple = get_numeric_safe(facts, "projections", "exit_multiple_ev_ebitda")
        
        # Datas e textos
        revenue_cagr_period = get_text_safe(facts, "financials_history", "revenue_cagr_period")
        exit_year = get_numeric_safe(facts, "projections", "exit_year")
        growth_drivers = get_text_safe(facts, "projections", "growth_drivers")
        financials_commentary = get_text_safe(facts, "financials_history", "financials_commentary")
        projections_commentary = get_text_safe(facts, "projections", "projections_commentary")
        
        # Placeholders apenas para validação do prompt
        if revenue_cagr_period is None:
            revenue_cagr_period = "[período]"
        if exit_year is None:
            exit_year = "[ano de saída]"
        if growth_drivers is None:
            growth_drivers = "[drivers de crescimento]"
        
        # Comentários: usar string vazia se None
        if financials_commentary is None:
            financials_commentary = ""
        if projections_commentary is None:
            projections_commentary = ""

        # ===== SYSTEM PROMPT =====
        system_prompt = f"""Você é um analista sênior de Private Equity com 15 anos de experiência escrevendo a seção "Financials" de um Short Memo de Co-investimento para o comitê de investimento da Spectra Capital.

═══════════════════════════════════════════════════════════════════════
ESTRUTURA OBRIGATÓRIA - 2-3 PARÁGRAFOS
═══════════════════════════════════════════════════════════════════════

§ PARÁGRAFO 1 - Histórico de Receita e EBITDA (2-3 frases):
  - Abertura típica: "Entre [ano inicial] e [ano final], o faturamento da **{company_name}** apresentou CAGR de {revenue_cagr or 'X'}%, passando de {currency_symbol} [valor inicial]m para {currency_symbol} {revenue_current or 'Y'}m."
  - Drivers de crescimento: "sustentado por [fator 1] e [fator 2]"
  - EBITDA: "O EBITDA cresceu de {currency_symbol} [valor inicial]m para {currency_symbol} {ebitda_current or 'Y'}m no mesmo período."
  - Se dados ausentes: "O faturamento da **{company_name}** apresentou crescimento consistente no período analisado."

§ PARÁGRAFO 2 - Margens e Dívida (2-3 frases):
  - Evolução de margem bruta e EBITDA: "A margem bruta tem flutuado entre X% e Y%, fechando [ano] em {gross_margin or 'Z'}%."
  - Patamar atual: "Em [ano atual], a margem EBITDA foi de {ebitda_margin or 'X'}% ({currency_symbol} {ebitda_current or 'Y'}m de EBITDA)."
  - Posição de dívida: "A empresa opera com dívida líquida de {currency_symbol} {net_debt or 'X'}m ({leverage or 'Y,Z'}x EBITDA)" ou "dívida líquida zero/positiva"
  - Conversão de caixa: "com conversão de {cash_conversion or 'X'}% do EBITDA"
  - Se dívida ausente: "A empresa apresenta posição financeira saudável"

§ PARÁGRAFO 3 - Projeções (opcional, 2-3 frases):
  - Cenário base: "No cenário base, projeta-se receita de {currency_symbol} {revenue_exit or 'X'}m em {exit_year} (CAGR de {revenue_cagr_proj or 'Y'}%)"
  - Drivers: "sustentado por {growth_drivers}"
  - Margem e múltiplo: "Com margem EBITDA de {ebitda_margin_exit or 'X'}%, o EBITDA na saída seria de {currency_symbol} {ebitda_exit or 'Y'}m, resultando em saída a {exit_multiple or 'Z,W'}x EBITDA"
  - Se projeções ausentes: Mencione apenas que há projeções de crescimento

═══════════════════════════════════════════════════════════════════════
VOCABULÁRIO ESPECÍFICO DE FINANCIALS (USE NATURALMENTE)
═══════════════════════════════════════════════════════════════════════

✅ "baixa intensidade de capital", "forte geração de caixa"
✅ "conversão de X% do EBITDA em caixa"
✅ "premissas conservadoras/agressivas"
✅ "em linha com", "abaixo/acima do CAGR histórico"
✅ "sustentado por", "passando de {currency_symbol} Xm para {currency_symbol} Ym"
✅ "margem bruta/EBITDA flutuou entre X% e Y%"

═══════════════════════════════════════════════════════════════════════
REGRAS DE ESTILO (NÃO NEGOCIÁVEIS)
═══════════════════════════════════════════════════════════════════════

✅ Tom profissional e analítico
✅ Quantifique TUDO: valores, margens, CAGRs, períodos
✅ Use **negrito** para: empresa ({company_name}), valores ({currency_symbol} Xm), percentuais (X%)
✅ SEMPRE mencione períodos para CAGRs ("CAGR de X% entre 2020 e 2024")
✅ Cada parágrafo: 3-5 frases, bem conectadas
✅ NÃO invente dados: se campo estiver vazio, ajuste frase ou omita
✅ NÃO use bullets, numerações ou títulos - apenas parágrafos fluidos
✅ Separe parágrafos com linha em branco

═══════════════════════════════════════════════════════════════════════
TRATAMENTO DE DADOS AUSENTES
═══════════════════════════════════════════════════════════════════════

- **Sem CAGR histórico:** "O faturamento da **{company_name}** apresentou crescimento consistente"
- **Sem margens:** Mencione apenas margem EBITDA atual se disponível
- **Sem dívida:** "A empresa apresenta posição financeira saudável"
- **Sem projeções:** "Há projeções de crescimento sustentado pelo mercado e execução operacional"
- **Sem drivers de crescimento:** "sustentado por execução da estratégia e captura de mercado"

**OUTPUT:** Apenas os 2-3 parágrafos, sem título de seção."""

        # ===== USER PROMPT =====
        rag_section = ""
        if rag_context:
            rag_section = f"""
═══════════════════════════════════════════════════════════════════════
CONTEXTO ADICIONAL DO DOCUMENTO (RAG)
═══════════════════════════════════════════════════════════════════════

Use este contexto para ENRIQUECER a análise financeira (não para sobrescrever facts).
Se houver conflito entre facts estruturados e RAG, PRIORIZE os facts.

Contexto pode incluir:
- Histórico de receita ano a ano (valores, CAGR, explicações)
- Evolução de margens e EBITDA (variações, drivers)
- Dívida, capital de giro e geração de caixa
- Projeções detalhadas e drivers de crescimento

{rag_context}
"""

        commentary_section = ""
        if financials_commentary or projections_commentary:
            commentary_section = f"""
═══════════════════════════════════════════════════════════════════════
CONTEXTO QUALITATIVO DO ANALISTA (USE COMO NORTE)
═══════════════════════════════════════════════════════════════════════

[CONTEXTO DO HISTÓRICO]
{financials_commentary if financials_commentary else "Não fornecido - use apenas dados estruturados e RAG"}

[CONTEXTO DAS PROJEÇÕES]
{projections_commentary if projections_commentary else "Não fornecido - use apenas dados estruturados e RAG"}

**IMPORTANTE:** Use estes contextos para EXPLICAR os números, mas os valores numéricos DEVEM vir dos facts estruturados.
"""

        user_prompt = f"""
═══════════════════════════════════════════════════════════════════════
DADOS ESTRUTURADOS (FACTS) - USE EXATAMENTE COMO FORNECIDO
═══════════════════════════════════════════════════════════════════════

[IDENTIFICAÇÃO]
{identification_section}

[HISTÓRICO FINANCEIRO]
{financials_section}

[PROJEÇÕES E SAÍDA]
{projections_section}
{commentary_section}{rag_section}
═══════════════════════════════════════════════════════════════════════
INSTRUÇÕES FINAIS
═══════════════════════════════════════════════════════════════════════

1. Escreva 2-3 parágrafos seguindo a estrutura obrigatória
2. Primeira frase típica: "Entre [ano] e [ano], o faturamento da **{company_name}** apresentou CAGR de X%, passando de {currency_symbol} Ym para {currency_symbol} Zm."
3. Use os números EXATOS dos facts - NÃO invente ou arredonde
4. Se projeções disponíveis: mencione claramente no parágrafo 3
5. Se algum campo estiver ausente, ajuste a frase ou omita (não invente)
6. SEMPRE mencione períodos para CAGRs
7. Use commentary e RAG para EXPLICAR números, não para alterá-los
8. Mantenha tom profissional e crítico

Comece AGORA com o primeiro parágrafo (histórico de receita):"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        response = llm.invoke(messages)
        return fix_number_formatting(response.content.strip())
