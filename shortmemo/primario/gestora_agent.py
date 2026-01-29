"""
Agente de Gestora - Short Memo Primário (Gestora)

Responsável por gerar a seção "Gestora, time e forma de atuação".
"""

from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import os
from .facts_builder import build_facts_section
from .facts_utils import get_name_safe
from .validator import fix_number_formatting
from .templates import enrich_prompt


class GestoraAgent:
    """Agente especializado em geração de Gestora para Short Memo Primário."""
    
    def __init__(self, model: str = "gpt-4o", temperature: float = 0.25):
        self.model = model
        self.temperature = temperature
        self.section_name = "Gestora, time e forma de atuação"
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
        Gera seção de Gestora, time e forma de atuação.
        
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
        gestora_section = build_facts_section(
            facts, "gestora",
            {
                "gestora_nome": "Nome da gestora",
                "gestora_ano_fundacao": "Ano de fundação",
                "gestora_localizacao": "Localização",
                "gestora_tipo": "Tipo de investidor",
                "gestora_aum_mm": "AUM total (R$ MM)",
                "gestora_num_fundos": "Número de fundos",
                "gestora_socios_principais": "Sócios/GPs principais",
                "gestora_filosofia_investimento": "Filosofia de investimento",
            }
        )
        
        qualitative_section = build_facts_section(
            facts, "qualitative",
            {
                "competitive_advantages": "Vantagens competitivas",
                "value_creation_plan": "Plano de criação de valor",
                "business_model": "Modelo de negócio",
            }
        )
        
        # ===== EXTRAI INFORMAÇÕES CHAVE PARA VALIDAÇÃO =====
        # Nomes usam placeholder se desabilitados
        gestora_nome = get_name_safe(facts, "gestora", "gestora_nome", "[nome da gestora]")

        # ===== SYSTEM PROMPT (DETALHADO E GUIADO) =====
        system_prompt = f"""Você é um analista sênior de Private Equity com 15 anos de experiência escrevendo a seção "Gestora, time e forma de atuação" de um Short Memo de investimento primário em fundo para o comitê de investimento da Spectra Capital.

═══════════════════════════════════════════════════════════════════════
ESTRUTURA OBRIGATÓRIA - 3-4 PARÁGRAFOS
═══════════════════════════════════════════════════════════════════════

§ PARÁGRAFO 1 - Posicionamento de Mercado (3-4 frases):
  - Descrever posicionamento competitivo da **{gestora_nome}**
  - Nicho de atuação (ex: "meio campo onde VCs e PEs não exploram")
  - Perfil das empresas investidas (tamanho, estágio, setores)
  - Diferenciação vs peers

§ PARÁGRAFO 2 - Estilo de Atuação (3-5 frases):
  - Modelo de atuação (operator led, hands-on, board seats, etc)
  - Nível de envolvimento (parceiro recorrente, menos board apenas financeiro)
  - Capacidade de assumir liderança quando necessário
  - Experiência e credibilidade com empreendedores

§ PARÁGRAFO 3 - Percepção dos Fundadores (2-4 frases):
  - Referências de fundadores investidos (se disponível)
  - Como a gestora é vista pelos empreendedores
  - Valor agregado percebido
  - Se não houver referências: mencionar que serão conduzidas

§ PARÁGRAFO 4 - Time e Equipe (opcional, 2-3 frases):
  - Principais sócios/GPs e background
  - Tamanho da equipe
  - Experiência relevante

═══════════════════════════════════════════════════════════════════════
REGRAS DE ESTILO (NÃO NEGOCIÁVEIS)
═══════════════════════════════════════════════════════════════════════

✅ Tom profissional e analítico
✅ Quantifique quando possível: anos de experiência, número de deals, AUM
✅ Use **negrito** para: gestora ({gestora_nome}), valores, percentuais
✅ Seja específico sobre estilo de atuação
✅ Cada parágrafo: 3-5 frases, bem conectadas
✅ NÃO invente dados: se campo estiver vazio, use frases genéricas apropriadas
✅ NÃO use bullets, numerações ou títulos - apenas parágrafos fluidos
✅ Separe parágrafos com linha em branco

**OUTPUT:** Apenas os 3-4 parágrafos, sem título de seção."""

        # ===== USER PROMPT (COM TODOS OS FACTS + RAG) =====
        rag_section = ""
        if rag_context:
            rag_section = f"""
═══════════════════════════════════════════════════════════════════════
CONTEXTO ADICIONAL DO DOCUMENTO (RAG)
═══════════════════════════════════════════════════════════════════════

Use este contexto para ENRIQUECER a análise da gestora (não para sobrescrever facts).
Se houver conflito entre facts estruturados e RAG, PRIORIZE os facts.

Contexto pode incluir:
- Histórico da gestora e fundação
- Posicionamento de mercado e diferenciação
- Estilo de atuação e modelo operator led
- Percepção de fundadores investidos
- Time e equipe

{rag_context}
"""

        user_prompt = f"""
═══════════════════════════════════════════════════════════════════════
DADOS ESTRUTURADOS (FACTS) - USE EXATAMENTE COMO FORNECIDO
═══════════════════════════════════════════════════════════════════════

[GESTORA]
{gestora_section}

[ASPECTOS QUALITATIVOS]
{qualitative_section}
{rag_section}
═══════════════════════════════════════════════════════════════════════
INSTRUÇÕES FINAIS
═══════════════════════════════════════════════════════════════════════

1. Escreva EXATAMENTE 3-4 parágrafos seguindo a estrutura obrigatória
2. Use os números EXATOS dos facts - NÃO invente
3. Se algum campo estiver ausente, use frases genéricas apropriadas
4. Mantenha tom profissional e crítico

Comece AGORA com o primeiro parágrafo (posicionamento de mercado):"""

        # Enriquecer prompts com exemplos dos templates
        system_prompt = enrich_prompt("gestora", system_prompt)

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        response = llm.invoke(messages)
        return fix_number_formatting(response.content.strip())
