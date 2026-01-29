"""
Agente de Mercado - Short Memo Gestora

Responsável por gerar a seção "Mercado" com análise de tamanho, dinâmica e competição.
"""

from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import os
from .facts_builder import build_facts_section
from .validator import fix_number_formatting
from .facts_utils import get_name_safe, get_text_safe
from ...format_utils import get_currency_symbol


class MercadoAgent:
    """Agente especializado em geração de Mercado para Short Memo Gestora."""
    
    def __init__(self, model: str = "gpt-4o", temperature: float = 0.25):
        self.model = model
        self.temperature = temperature
        self.section_name = "Mercado"
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
        Gera seção de Mercado.
        
        Args:
            facts: Dict com facts estruturados
            rag_context: Contexto opcional
        
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
                "business_description": "Descrição do negócio",
            }
        )
        
        qualitative_section = build_facts_section(
            facts, "qualitativo",
            {
                "market_share_pct": "Market share (%)",
                "market_fragmentation": "Fragmentação de mercado",
                "main_competitors": "Principais competidores",
                "competitor_count": "Número de competidores",
                "competitive_advantages": "Vantagens competitivas",
                "industry_trends": "Tendências do setor",
                "regulatory_environment": "Ambiente regulatório",
                "market_positioning": "Posicionamento no mercado",
            }
        )
        
        # ===== EXTRAI INFORMAÇÕES CHAVE =====
        company_name = get_name_safe(facts, "identificacao", "company_name", "[nome da empresa]")
        
        business_description = get_text_safe(facts, "identificacao", "business_description")
        competitive_advantages = get_text_safe(facts, "qualitativo", "competitive_advantages")
        main_competitors = get_text_safe(facts, "qualitativo", "main_competitors")
        
        # Placeholders apenas para validação do prompt
        if business_description is None:
            business_description = "[descrição do negócio]"
        
        # Para sector: usar "o setor" se business_description não disponível
        sector = business_description.split()[0] if business_description and business_description != "[descrição do negócio]" else "o setor"
        
        # Textos vazios se None (para não quebrar prompt)
        if competitive_advantages is None:
            competitive_advantages = ""
        if main_competitors is None:
            main_competitors = ""

        # ===== SYSTEM PROMPT =====
        system_prompt = f"""Você é um analista sênior de Private Equity com 15 anos de experiência escrevendo a seção "Mercado" de um Short Memo de Co-investimento para o comitê de investimento da Spectra Capital.

═══════════════════════════════════════════════════════════════════════
ESTRUTURA OBRIGATÓRIA - 2-3 PARÁGRAFOS
═══════════════════════════════════════════════════════════════════════

§ PARÁGRAFO 1 - Mercado e Posicionamento (2-3 frases):
  - Abertura típica: "O mercado de [setor] apresenta [característica]..."
  - Tamanho e crescimento: mencione valores, CAGR com período (se disponível)
  - Posicionamento: "A **{company_name}** se posiciona como [one-stop-shop/líder/especialista]..."
  - Modelo de atuação: integração vertical, nicho específico, etc.

§ PARÁGRAFO 2 - Dinâmica Competitiva (3-5 frases):
  - Segmentação: "O mercado é segmentado por [porte/região/especialização]..."
  - Fragmentação: mencione quantos players existem (fragmentado/consolidado)
  - Market share se disponível: "A **{company_name}** detém X% de participação"
  - Competidores: "Apesar disso, tem competidores relevantes como [LISTE NOMES ESPECÍFICOS]."
  - **CRÍTICO:** SEMPRE liste pelo menos 2-3 nomes de competidores se disponíveis

§ PARÁGRAFO 3 - Diferenciais Competitivos (formato numerado inline):
  - **OBRIGATÓRIO começar com:** "Os principais diferenciais competitivos da **{company_name}** são:"
  - Liste 4-6 itens no formato: "(i) [Nome do diferencial] — [explicação de 1-2 linhas]; (ii) [Nome] — [explicação]; ..."
  - Use travessão (—) depois do nome do diferencial, não hífen ou dois pontos
  - **SEMPRE** termine itens com ponto-e-vírgula (;), EXCETO o último que termina com ponto final (.)
  - Diferenciais típicos: Marca, Parceria OEM, Localização, Base de clientes, Certificações, Know-how, Switching costs

═══════════════════════════════════════════════════════════════════════
VOCABULÁRIO ESPECÍFICO DE MERCADO (USE NATURALMENTE)
═══════════════════════════════════════════════════════════════════════

✅ "mercado fragmentado/consolidado", "pulverizado"
✅ "posiciona-se como", "one-stop-shop", "integração vertical", "verticalmente integrado"
✅ "diferenciais competitivos", "switching costs", "custos de troca"
✅ "base pulverizada", "alta recorrência", "receita recorrente"
✅ "barreiras de entrada", "moat competitivo"
✅ "dinâmica competitiva", "landscape competitivo"

═══════════════════════════════════════════════════════════════════════
REGRAS DE ESTILO (NÃO NEGOCIÁVEIS)
═══════════════════════════════════════════════════════════════════════

✅ Tom profissional e analítico
✅ Quantifique TUDO: tamanho de mercado, CAGR (com período), market share, número de competidores
✅ Use **negrito** para: empresa ({company_name}), valores, percentuais
✅ Seja específico sobre competidores - SEMPRE liste nomes se disponíveis
✅ Cada parágrafo: 3-5 frases, bem conectadas
✅ NÃO invente dados: se campo estiver vazio, use frases genéricas apropriadas
✅ NÃO use bullets, numerações ou títulos - apenas parágrafos fluidos (exceto diferenciais inline)
✅ Separe parágrafos com linha em branco

═══════════════════════════════════════════════════════════════════════
TRATAMENTO DE DADOS AUSENTES
═══════════════════════════════════════════════════════════════════════

- **Sem tamanho de mercado:** "O mercado de [setor] apresenta crescimento consistente..."
- **Sem market share:** "A empresa se posiciona entre os principais players do segmento..."
- **Sem número de competidores:** "O mercado apresenta dinâmica competitiva com diversos players..."
- **Sem lista de competidores:** Mencione genericamente "competidores estabelecidos no segmento"
- **SEMPRE** mencione diferenciais competitivos mesmo com RAG limitado (use facts como base)

**OUTPUT:** Apenas os 2-3 parágrafos, sem título de seção."""

        # ===== USER PROMPT =====
        rag_section = ""
        if rag_context:
            rag_section = f"""
═══════════════════════════════════════════════════════════════════════
CONTEXTO ADICIONAL DO DOCUMENTO (RAG)
═══════════════════════════════════════════════════════════════════════

Use este contexto para ENRIQUECER a análise de mercado (não para sobrescrever facts).
Se houver conflito entre facts estruturados e RAG, PRIORIZE os facts.

Contexto pode incluir:
- Tamanho e crescimento do mercado (valores, CAGR)
- Landscape competitivo e fragmentação
- Nomes de competidores específicos
- Posicionamento da empresa no mercado
- Diferenciais competitivos

{rag_context}
"""

        user_prompt = f"""
═══════════════════════════════════════════════════════════════════════
DADOS ESTRUTURADOS (FACTS) - USE EXATAMENTE COMO FORNECIDO
═══════════════════════════════════════════════════════════════════════

[IDENTIFICAÇÃO]
{identification_section}

[ASPECTOS QUALITATIVOS E COMPETITIVOS]
{qualitative_section}
{rag_section}
═══════════════════════════════════════════════════════════════════════
INSTRUÇÕES FINAIS
═══════════════════════════════════════════════════════════════════════

1. Escreva EXATAMENTE 2-3 parágrafos seguindo a estrutura obrigatória
2. Parágrafo 3 DEVE começar: "Os principais diferenciais competitivos da **{company_name}** são:"
3. Liste diferenciais no formato: "(i) Nome — explicação; (ii) Nome — explicação; ..."
4. Use os números EXATOS dos facts - NÃO invente
5. Se algum campo estiver ausente, use frases genéricas apropriadas
6. SEMPRE liste nomes de competidores se disponíveis (mínimo 2-3)
7. Mantenha tom profissional e crítico

Comece AGORA com o primeiro parágrafo (tamanho e posicionamento do mercado):"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        response = llm.invoke(messages)
        return fix_number_formatting(response.content.strip())
