"""
Agente de Empresa - Short Memo Gestora

Responsável por gerar a seção "Empresa" com modelo de negócio e diferenciais.
"""

from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import os
from ..facts_builder import build_facts_section
from ..validator import fix_number_formatting
from ..facts_utils import get_name_safe, get_text_safe, get_numeric_safe, get_currency_safe
from ..._base.format_utils import get_currency_symbol, get_currency_label


class EmpresaAgent:
    """Agente especializado em geração de Empresa para Short Memo Gestora."""
    
    def __init__(self, model: str = "gpt-4o", temperature: float = 0.25):
        self.model = model
        self.temperature = temperature
        self.section_name = "Empresa"
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
        Gera seção sobre a Empresa.
        
        Args:
            facts: Dict com facts estruturados
            rag_context: Contexto opcional
        
        Returns:
            Texto da seção (3-5 parágrafos)
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
            facts, "identification",
            {
                "company_name": "Nome da empresa",
                "company_location": "Localização",
                "company_founding_year": "Ano de fundação",
                "business_description": "Descrição do negócio",
            }
        )
        
        # Obtém moeda
        currency = get_currency_safe(facts, section="transaction_structure", field="currency")
        currency_symbol = get_currency_symbol(currency)
        currency_label = get_currency_label(currency)
        
        financials_section = build_facts_section(
            facts, "financials_history",
            {
                "revenue_current_mm": f"Receita atual ({currency_label})",
                "revenue_cagr_pct": "CAGR receita (%)",
                "revenue_cagr_period": "Período CAGR",
                "ebitda_current_mm": f"EBITDA atual ({currency_label})",
                "ebitda_margin_current_pct": "Margem EBITDA (%)",
                "gross_margin_pct": "Margem bruta (%)",
                "employees_count": "Número de funcionários",
                "cash_conversion_pct": "Conversão caixa (%)",
            }
        )
        
        qualitative_section = build_facts_section(
            facts, "qualitativo",
            {
                "business_model": "Modelo de negócio",
                "main_products_services": "Principais produtos/serviços",
                "revenue_streams": "Fontes de receita",
                "revenue_mix": "Mix de receita por vertical",
                "target_customers": "Clientes-alvo",
                "customer_profile": "Perfil de clientes",
                "geographic_presence": "Presença geográfica",
                "distribution_channels": "Canais de distribuição",
                "competitive_advantages": "Vantagens competitivas",
                "differentiation": "Diferenciação",
                "moat": "Moat (barreira competitiva)",
                "customer_concentration": "Concentração de clientes",
            }
        )
        
        # ===== EXTRAI INFORMAÇÕES CHAVE =====
        company_name = get_name_safe(facts, "identification", "company_name", "[nome da empresa]")
        
        founding_year = get_text_safe(facts, "identification", "company_founding_year")
        location = get_text_safe(facts, "identification", "company_location")
        business_description = get_text_safe(facts, "identification", "business_description")
        
        # Placeholders apenas para validação do prompt
        if founding_year is None:
            founding_year = "[ano de fundação]"
        if location is None:
            location = "[localização]"
        if business_description is None:
            business_description = "[descrição do negócio]"

        # ===== SYSTEM PROMPT =====
        system_prompt = f"""Você é um analista sênior de Private Equity com 15 anos de experiência escrevendo a seção "Empresa" de um Short Memo de Co-investimento para o comitê de investimento da Spectra Capital.

═══════════════════════════════════════════════════════════════════════
ESTRUTURA OBRIGATÓRIA - 3-5 PARÁGRAFOS
═══════════════════════════════════════════════════════════════════════

§ PARÁGRAFO 1 - Fundação e Porte (2-3 frases):
  - Abertura típica: "Fundada em {founding_year} e sediada em {location}, a **{company_name}** é uma empresa..."
  - Porte atual: "Com receita de {currency_symbol} Xm e Y funcionários, a companhia se posiciona como..."
  - IMPORTANTE: Se campos estiverem ausentes, omita ou use "informação não divulgada"

§ PARÁGRAFO 2 - Produtos e Serviços (3-4 frases):
  - Detalhar core business: o que oferece, principais linhas de receita
  - Mix de receita por vertical se disponível: "Serviços (68% da receita), Hardware (23%)"
  - Como gera valor para clientes

§ PARÁGRAFO 3 - Evolução e Crescimento (2-3 frases):
  - Histórico de crescimento: "Entre [período], o faturamento apresentou CAGR de X%"
  - Drivers: "sustentado por [fatores principais]"
  - Mudanças estratégicas relevantes

§ PARÁGRAFO 4 - Base de Clientes (opcional, 2-3 frases):
  - Perfil de clientes, canais, geografia
  - Concentração se relevante: "Os 10 maiores clientes representam X% da receita"

§ PARÁGRAFO 5 - Modelo e Margens (opcional, 2-3 frases):
  - Dinâmica de margens: "A margem bruta tem se mantido em X%"
  - Conversão de caixa se disponível
  - Intensidade de capital ou características operacionais relevantes

═══════════════════════════════════════════════════════════════════════
VOCABULÁRIO ESPECÍFICO DE EMPRESA (USE NATURALMENTE)
═══════════════════════════════════════════════════════════════════════

✅ "one-stop-shop", "integração vertical", "verticalmente integrado"
✅ "base pulverizada", "alta recorrência", "receita recorrente"
✅ "switching costs elevados", "lock-in de clientes"
✅ "baixa intensidade de capital", "asset-light"
✅ Mix de receita: "Serviços (68% da receita), Hardware (23% da receita)"
✅ "atuação nacional", "presença capilarizada", "footprint geográfico"

═══════════════════════════════════════════════════════════════════════
REGRAS DE ESTILO (NÃO NEGOCIÁVEIS)
═══════════════════════════════════════════════════════════════════════

✅ Tom profissional e analítico
✅ Quantifique TUDO: receita, CAGR (com período), margem, número de funcionários
✅ Use **negrito** para: empresa ({company_name}), valores ({currency_symbol} Xm), percentuais
✅ Seja específico sobre modelo de negócio e fontes de receita
✅ Cada parágrafo: 3-5 frases, bem conectadas
✅ NÃO invente dados: se campo estiver vazio, omita ou marque como "não divulgado"
✅ NÃO use bullets, numerações ou títulos - apenas parágrafos fluidos
✅ Separe parágrafos com linha em branco

**OUTPUT:** Apenas os 3-5 parágrafos, sem título de seção."""

        # ===== USER PROMPT =====
        rag_section = ""
        if rag_context:
            rag_section = f"""
═══════════════════════════════════════════════════════════════════════
CONTEXTO ADICIONAL DO DOCUMENTO (RAG)
═══════════════════════════════════════════════════════════════════════

Use este contexto para ENRIQUECER a descrição da empresa (não para sobrescrever facts).
Se houver conflito entre facts estruturados e RAG, PRIORIZE os facts.

Contexto pode incluir:
- História da fundação e fundadores
- Detalhes de produtos e serviços
- Base de clientes e geografia
- Evolução histórica e marcos importantes

{rag_context}
"""

        user_prompt = f"""
═══════════════════════════════════════════════════════════════════════
DADOS ESTRUTURADOS (FACTS) - USE EXATAMENTE COMO FORNECIDO
═══════════════════════════════════════════════════════════════════════

[IDENTIFICAÇÃO]
{identification_section}

[FINANCIALS HISTÓRICO]
{financials_section}

[MODELO DE NEGÓCIO E ASPECTOS QUALITATIVOS]
{qualitative_section}
{rag_section}
═══════════════════════════════════════════════════════════════════════
INSTRUÇÕES FINAIS
═══════════════════════════════════════════════════════════════════════

1. Escreva 3-5 parágrafos seguindo a estrutura obrigatória
2. Use os números EXATOS dos facts - NÃO invente ou arredonde
3. Se algum campo estiver ausente, omita ou marque como "não divulgado"
4. Primeira frase típica: "Fundada em [ano] e sediada em [local], a **[Empresa]** é..."
5. Mantenha tom profissional e analítico

Comece AGORA com o primeiro parágrafo (fundação e porte):"""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        response = llm.invoke(messages)
        return fix_number_formatting(response.content.strip())
