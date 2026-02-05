"""
Agente especializado em INTRODUÇÃO para Short Memo Gestora

"""

from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import os
from ..facts_builder import build_facts_section
from ..validator import fix_number_formatting
from ..facts_utils import get_name_safe, get_currency_safe, get_numeric_safe, get_text_safe
from ..._base.format_utils import get_currency_symbol, get_currency_label


class IntroAgent:
    """Agente especializado em gerar Introdução para Short Memo Gestora"""
    
    def __init__(self, model: str = "gpt-4o", temperature: float = 0.25):
        """
        Inicializa agente de Introdução.
        
        Args:
            model: Modelo OpenAI a usar
            temperature: Criatividade (0.0 = determinístico, 1.0 = criativo)
        """
        self.model = model
        self.temperature = temperature
        self.section_name = "Introdução"
        self.llm = None  # Será injetado pelo LangGraph orchestrator
    
    def set_llm(self, llm):
        """Injeta LLM compartilhado (usado pelo LangGraph orchestrator)"""
        self.llm = llm
    
    def generate(self, facts: Dict[str, Any], rag_context: Optional[str] = None) -> str:
        """
        Gera seção de Introdução contextualizando gestora, ativo e transação.
        
        Args:
            facts: Facts extraídos do CIM
            rag_context: Contexto opcional do documento original
        
        Returns:
            Texto da seção (parágrafos separados por \\n\\n)
        """
        # Usar LLM injetado se disponível, senão criar novo (compatibilidade)
        if not self.llm:
            apikey = os.getenv("OPENAI_API_KEY")
            if not apikey:
                raise ValueError("OPENAI_API_KEY não encontrada no ambiente")
            self.llm = ChatOpenAI(model=self.model, api_key=apikey, temperature=self.temperature)
        
        llm = self.llm

        # ===== QUERY DOS FACTS =====
        # Seção gestora: track record, equipe, tese, performance (extraídos pelo prompt gestora.txt)
        gestora_section = build_facts_section(
            facts, "gestora",
            {
                "track_record": "Track Record",
                "principais_exits": "Principais Exits",
                "equipe": "Equipe",
                "estrategia_investimento": "Estratégia de Investimento",
                "tese_gestora": "Tese da Gestora",
                "performance_historica": "Performance Histórica",
                "relacionamento_anterior_spectra": "Relacionamento com a Spectra",
            }
        )
        
        identification_section = build_facts_section(
            facts, "identification",
            {
                "gestora_name": "Gestora",
                "gestora_fundacao": "Fundação da Gestora",
                "aum_total": "AUM Total",
                "company_name": "Empresa Alvo",
                "business_description": "Descrição do Negócio",
                "company_location": "Localização",
                "setor": "Setor",
            }
        )
        
        # Obtém moeda da transação
        currency = get_currency_safe(facts, section="transaction_structure", field="currency")
        currency_symbol = get_currency_symbol(currency)
        currency_label = get_currency_label(currency)
        
        transaction_section = build_facts_section(
            facts, "transaction_structure",
            {
                "valuation_total_empresa": "Valuation Total da Empresa",
                "participacao_total_adquirida": "Participação Total (%)",
                "participacao_fundo_gestora": "Participação Fundo (%)",
                "participacao_coinvestimento": "Participação Coinvestimento (%)",
                "multiple_ev_ebitda": "Múltiplo EV/EBITDA",
                "multiple_reference_period": "Período do múltiplo (ex: 2025E)",
                "stake_pct": "Participação (%)",
                "ev_mm": f"EV ({currency_label})",
                "cash_payment_mm": "À vista (milhões)",
                "seller_note_mm": "Seller note (milhões)",
                "seller_note_tenor_years": "Prazo seller note (anos)",
                "seller_note_index": "Indexador (ex: IPCA)",
                "compensacao_dividendos": "Compensação via dividendos",
                "alocacao_fundo": "Alocação pelo fundo da gestora",
                "disponivel_coinvestidores": "Disponível para co-investidores",
            }
        )
        
        # ===== EXTRAI INFORMAÇÕES CHAVE =====
        # Nome da gestora fica em identification para Short Memo Co-investimento (Gestora)
        gestora_name = get_name_safe(facts, "identification", "gestora_name", "[nome da gestora]")
        company_name = get_name_safe(facts, "identification", "company_name", "[nome da empresa]")
        
        # Textos retornam None se desabilitados
        business_description = get_text_safe(facts, "identification", "business_description")
        if business_description is None:
            business_description = "[descrição do negócio]"
        
        # ===== SYSTEM PROMPT =====
        system_prompt = f"""Você é um analista sênior de Private Equity escrevendo a seção "Introdução" de um Short Memo de Co-investimento (gestora) para o comitê da Spectra.

**OBRIGATÓRIO: EXATAMENTE 2 PARÁGRAFOS. Nada mais.**

═══════════════════════════════════════════════════════════════════════
PARÁGRAFO 1 (contexto e negócio)
═══════════════════════════════════════════════════════════════════════
- Primeira frase: "[{gestora_name}] nos apresentou a oportunidade de co-investir na [{company_name}]." (use os nomes dos facts).
- Em seguida: "A [empresa] é uma empresa que [descrição do negócio em 2-4 frases]." Descreva o que a empresa faz, como opera, posicionamento (use business_description e contexto dos facts). Ex.: "A Hero é uma empresa que opera o seguro na ponta: desenvolve o produto, define preços e critérios de aceitação, distribui nos canais e gerencia a operação, enquanto a seguradora parceira carrega o risco e responde pelos sinistros."

═══════════════════════════════════════════════════════════════════════
PARÁGRAFO 2 (transação e alocação)
═══════════════════════════════════════════════════════════════════════
- Comece: "A transação consiste em comprar [X]% da companhia, por [valor] ([múltiplo] EBITDA [período])."
- Detalhe o montante: "Desse montante, [valor] seriam pagos à vista ([múltiplo]x EBITDA), [valor] em [prazo], [indexador], e [valor] via compensação de dividendos" (ou o que constar nos facts: à vista, seller note, earn-out).
- Feche: "A ideia da gestora é alocar [valor/faixa] pelo fundo e captar o restante junto a co-investidores." Use os facts de alocação/coinvestimento quando disponíveis.

═══════════════════════════════════════════════════════════════════════
REGRAS
═══════════════════════════════════════════════════════════════════════
✅ Use os números EXATOS dos facts ({currency_symbol}, milhões, %, múltiplos)
✅ Tom profissional, primeira pessoa plural
✅ NÃO use bullets, títulos ou numeração
✅ NÃO invente dados; se faltar dado, omita ou use "a definir"
✅ Separe os dois parágrafos com uma linha em branco

**OUTPUT:** Apenas os 2 parágrafos, sem título "Introdução"."""

        # ===== USER PROMPT =====
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
DADOS ESTRUTURADOS (FACTS)
═══════════════════════════════════════════════════════════════════════

[GESTORA]
{gestora_section}

[IDENTIFICAÇÃO]
{identification_section}

[TRANSAÇÃO]
{transaction_section}
{rag_section}
═══════════════════════════════════════════════════════════════════════
INSTRUÇÃO
═══════════════════════════════════════════════════════════════════════

Gere EXATAMENTE 2 parágrafos conforme o modelo:
- Parágrafo 1: "[Gestora] nos apresentou a oportunidade de co-investir na [Empresa]. A [Empresa] é uma empresa que [descrição do negócio]."
- Parágrafo 2: "A transação consiste em comprar [X]% da companhia, por [valor] ([múltiplo] EBITDA). Desse montante, [à vista], [parcelado], [dividendos]. A ideia da gestora é alocar [valor] pelo fundo e captar o restante junto a co-investidores."

Use os números e nomes EXATOS dos facts. Comece agora:"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        response = llm.invoke(messages)
        return fix_number_formatting(response.content.strip())
