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
from ..facts_builder import build_facts_section
from ..validator import fix_number_formatting


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
        # 1. Query de facts da seção GESTORA (extraídos pelo prompt gestora.txt)
        track_record_section = build_facts_section(
            facts, "gestora",
            {
                "track_record": "Track Record (fundos, ano, AUM, TVPI, DPI, IRR)",
                "principais_exits": "Principais Exits",
                "performance_historica": "Performance Histórica",
                "equipe": "Equipe",
                "estrategia_investimento": "Estratégia de Investimento",
                "tese_gestora": "Tese da Gestora",
                "relacionamento_anterior_spectra": "Relacionamento com a Spectra",
            }
        )
        
        # System prompt especializado
        system_prompt = f"""Você é um analista de Private Equity escrevendo a seção de TRACK RECORD de um Short Memo sobre uma gestora (co-investimento).

CONTEXTO: Short Memo Gestora - análise de performance histórica e realizações da gestora líder do deal.

ESTRUTURA OBRIGATÓRIA (2-3 parágrafos):
1. Track record e métricas consolidadas: fundos anteriores, AUM, TVPI, DPI, IRR quando disponíveis
2. Principais exits e realizações (empresas, setores, múltiplos de saída)
3. Equipe e experiência relevante; relacionamento com a Spectra se aplicável

REGRAS:
- Tom factual e baseado nos DADOS ESTRUTURADOS fornecidos
- Use os números EXATOS dos facts (IRR, MOIC, TVPI, DPI, múltiplos)
- Destaque exits notáveis com nome da empresa e múltiplo quando disponível
- Se houver vários fundos/vintages: compare ou resuma de forma clara
- NÃO invente dados: use apenas o que consta nos facts
- Se algum bloco de facts estiver vazio, foque nos que tiverem conteúdo

OUTPUT: Retorne APENAS os parágrafos, sem títulos ou marcadores."""
        
        # 4. Human prompt com facts
        human_prompt = f"""Gere a seção de TRACK RECORD para esta gestora usando os dados abaixo:

{track_record_section}

Lembre-se: 2-3 parágrafos, foco em track record (fundos, TVPI, DPI, IRR), principais exits e equipe/performance. Use apenas os dados fornecidos."""
        
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
