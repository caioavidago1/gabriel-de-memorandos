"""
Agente especializado em INTRODUÇÃO para Short Memo Gestora

RESPONSABILIDADE:
- Contextualizar a gestora (Spectra + gestora líder), o ativo e resumir a transação

SAÍDA:
- 2-3 parágrafos, seguindo o template "A [gestora] nos apresentou a oportunidade de co-investir..."

VERSÃO: 2.0
"""

from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import os
from .facts_builder import build_facts_section
from .validator import fix_number_formatting
from .facts_utils import get_name_safe, get_currency_safe, get_numeric_safe, get_text_safe
from ...format_utils import get_currency_symbol, get_currency_label


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
        gestora_section = build_facts_section(
            facts, "gestora",
            {
                "gestora_nome": "Nome da gestora",
                "gestora_ano_fundacao": "Ano de fundação",
                "gestora_aum_total_mm": "AUM Total (R$ MM)",
            }
        )
        
        identification_section = build_facts_section(
            facts, "identificacao",
            {
                "company_name": "Nome da empresa",
                "business_description": "Descrição do negócio",
                "company_location": "Localização",
            }
        )
        
        # Obtém moeda da transação
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
            }
        )
        
        # ===== EXTRAI INFORMAÇÕES CHAVE =====
        gestora_name = get_name_safe(facts, "gestora", "gestora_nome", "[nome da gestora]")
        company_name = get_name_safe(facts, "identificacao", "company_name", "[nome da empresa]")
        
        # Textos retornam None se desabilitados
        business_description = get_text_safe(facts, "identificacao", "business_description")
        if business_description is None:
            business_description = "[descrição do negócio]"
        
        # ===== SYSTEM PROMPT =====
        system_prompt = f"""Você é um analista sênior de Private Equity com 15 anos de experiência escrevendo a seção "Introdução" de um Short Memo de Co-investimento apresentado por gestora para o comitê de investimento da Spectra Capital.

═══════════════════════════════════════════════════════════════════════
PADRÃO OBRIGATÓRIO - PRIMEIRA FRASE
═══════════════════════════════════════════════════════════════════════

"A {gestora_name} nos apresentou a oportunidade de co-investir na {company_name}, uma companhia especializada em {business_description}."

**REGRA CRÍTICA:** Use EXATAMENTE essa estrutura, substituindo apenas os valores entre {{}} pelos facts fornecidos.

═══════════════════════════════════════════════════════════════════════
ESTRUTURA OBRIGATÓRIA - 2-3 PARÁGRAFOS
═══════════════════════════════════════════════════════════════════════

§ PARÁGRAFO 1 - Contexto do Co-investimento:
  - Primeira frase segue o padrão obrigatório acima
  - Mencione imediatamente: participação proposta, EV ({currency_symbol}m), múltiplo de entrada
  - Inclua período de referência do múltiplo (ex: "LTM mai/25")
  - Contexto breve sobre a gestora líder (anos de experiência, foco setorial, AUM se relevante)

§ PARÁGRAFO 2 - Resumo da Oportunidade:
  - Contexto estratégico: por que a gestora está apresentando esta oportunidade
  - Características principais do ativo (porte, setor, posicionamento)
  - Tese de investimento resumida (1-2 frases)

§ PARÁGRAFO 3 - Estrutura da Transação (opcional se houver espaço):
  - EV, múltiplo EV/EBITDA, % equity proposto
  - Estrutura de pagamento básica (à vista, seller note, earnout se mencionado)
  - Timeline e próximos passos

═══════════════════════════════════════════════════════════════════════
REGRAS DE ESTILO (NÃO NEGOCIÁVEIS)
═══════════════════════════════════════════════════════════════════════

✅ Tom profissional, primeira pessoa plural: "nos apresentou", "estamos avaliando", "entendemos que"
✅ Quantifique TUDO: valores exatos, múltiplos, percentuais
✅ Use **negrito** para: gestora, empresa, valores ({currency_symbol} Xm), múltiplos (Xx)
✅ Seja específico: "{currency_symbol} 45m" não "valor significativo"
✅ Cada parágrafo: 3-5 frases, bem conectadas
✅ NÃO invente dados: se campo estiver vazio, trate como "ainda em discussão" ou "não disponível"
✅ NÃO use bullets, numerações ou títulos - apenas parágrafos fluidos
✅ Separe parágrafos com linha em branco

**OUTPUT:** Apenas os 2-3 parágrafos, sem título de seção."""

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
DADOS ESTRUTURADOS (FACTS) - USE EXATAMENTE COMO FORNECIDO
═══════════════════════════════════════════════════════════════════════

[GESTORA]
{gestora_section}

[IDENTIFICAÇÃO]
{identification_section}

[TRANSAÇÃO]
{transaction_section}
{rag_section}
═══════════════════════════════════════════════════════════════════════
INSTRUÇÕES FINAIS
═══════════════════════════════════════════════════════════════════════

1. Escreva EXATAMENTE 2-3 parágrafos seguindo a estrutura obrigatória
2. Use os números EXATOS dos facts - NÃO invente ou arredonde
3. Se algum campo estiver ausente, marque como "ainda em discussão" ou omita
4. Siga o padrão da primeira frase sem exceções
5. Mantenha tom profissional e analítico

Comece AGORA com o primeiro parágrafo (primeira frase obrigatória):"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        response = llm.invoke(messages)
        return fix_number_formatting(response.content.strip())
