"""
Agente especializado em TRACK RECORD para Short Memo Gestora

RESPONSABILIDADE:
- Gerar seção "Track Record" apresentando performance histórica
- Contexto: IRR, MOIC, DPI, exits realizados, vintages

ESTRUTURA:
- 2-3 parágrafos
- Parágrafo 1: Métricas consolidadas (IRR, MOIC, DPI)
- Parágrafo 2: Detalhamento por vintage/fundo
- Parágrafo 3: Exits notáveis e realizações

VERSÃO: 1.0
"""

from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import os
from .facts_builder import build_facts_section
from .validator import fix_number_formatting


class TrackRecordAgent:
    """Agente especializado em gerar Track Record para Short Memo Gestora"""
    
    def __init__(self, model: str = "gpt-4o", temperature: float = 0.25):
        """
        Inicializa agente de Track Record.
        
        Args:
            model: Modelo OpenAI a usar
            temperature: Criatividade (0.0 = determinístico, 1.0 = criativo)
        """
        self.model = model
        self.temperature = temperature
        self.section_name = "Track Record"
        self.llm = None  # Será injetado pelo LangGraph orchestrator
    
    def set_llm(self, llm):
        """Injeta LLM compartilhado (usado pelo LangGraph orchestrator)"""
        self.llm = llm
    
    def generate(self, facts: Dict[str, Any], rag_context: Optional[str] = None) -> str:
        """
        Gera seção de Track Record.
        
        Args:
            facts: Facts extraídos do CIM
            rag_context: Contexto opcional do documento original
        
        Returns:
            Texto da seção (parágrafos separados por \\n\\n)
        """
        # 1. Query de facts relevantes
        returns_section = build_facts_section(facts, "retornos", [
            "irr_net", "irr_gross", "moic_gross", "moic_net",
            "dpi_realized", "tvpi_total", "num_investments",
            "num_exits", "num_active_investments"
        ])
        
        vintages_section = build_facts_section(facts, "retornos", [
            "fund_vintage", "vintage_performance", "fund_size",
            "committed_capital", "deployed_capital"
        ])
        
        exits_section = build_facts_section(facts, "qualitativo", [
            "notable_exits", "exit_multiples", "exit_strategies",
            "realized_value", "successful_cases"
        ])
        
        # System prompt especializado
        system_prompt = f"""Você é um analista de Private Equity escrevendo a seção de TRACK RECORD de um Short Memo sobre uma gestora.

CONTEXTO: Short Memo Gestora - análise de performance histórica e realizações.

ESTRUTURA OBRIGATÓRIA (2-3 parágrafos):
1. Métricas consolidadas (IRR net, MOIC gross, DPI)
2. Detalhamento por vintage ou fundo
3. Exits notáveis e casos de sucesso

REGRAS:
- Tom factual e baseado em dados
- SEMPRE apresente métricas com precisão: "IRR net de XX%", "MOIC de XXx"
- Use "R$ XX milhões/bilhões" para valores realizados
- Diferencie claramente: IRR net vs gross, MOIC vs DPI
- Se houver múltiplos fundos: compare vintages
- Mencione número de exits, investimentos ativos, realizações
- Destaque casos de sucesso específicos (empresa, setor, múltiplo)
- Seja transparente sobre estágio de maturação (realizações vs não realizados)

OUTPUT: Retorne APENAS os parágrafos, sem títulos ou marcadores."""
        
        # 4. Human prompt com facts
        human_prompt = f"""Gere a seção de TRACK RECORD para esta gestora:

{returns_section}

{vintages_section}

{exits_section}

Lembre-se: 2-3 parágrafos, foco em métricas (IRR, MOIC, DPI), vintages e exits notáveis."""
        
        # 5. Gerar com LLM
        # Usar LLM injetado se disponível, senão criar novo (compatibilidade)
        if not self.llm:
            apikey = os.getenv("OPENAI_API_KEY")
            if not apikey:
                raise ValueError("OPENAI_API_KEY não encontrada no ambiente")
            self.llm = ChatOpenAI(model=self.model, api_key=apikey, temperature=self.temperature)
        
        llm = self.llm
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]
        
        response = llm.invoke(messages)
        
        # 6. Pós-processamento
        return fix_number_formatting(response.content.strip())
