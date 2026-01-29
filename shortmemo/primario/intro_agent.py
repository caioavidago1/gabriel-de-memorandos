"""
Agente de Introdução - Short Memo Primário (Gestora)

Responsável por gerar a seção "Resumo da oportunidade" com contexto do investimento primário.
"""

from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import os
from .facts_builder import build_facts_section
from .facts_utils import get_currency_safe, get_name_safe, get_numeric_safe, get_text_safe
from .utils import get_currency_symbol, get_currency_label
from .validator import fix_number_formatting
from .templates import enrich_prompt


class IntroAgent:
    """Agente especializado em geração de Resumo da oportunidade para Short Memo Primário."""
    
    def __init__(self, model: str = "gpt-4o", temperature: float = 0.25):
        self.model = model
        self.temperature = temperature
        self.section_name = "Resumo da oportunidade"
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
        Gera seção de Resumo da oportunidade.
        
        Args:
            facts: Dict com facts estruturados (todas as seções)
            rag_context: Contexto extraído do documento (opcional)
        
        Returns:
            Texto da introdução (3 parágrafos)
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
                "gestora_tipo": "Tipo de investidor",
                "gestora_aum_mm": "AUM total (R$ MM)",
                "gestora_num_fundos": "Número de fundos",
                "gestora_socios_principais": "Sócios/GPs principais",
                "gestora_filosofia_investimento": "Filosofia de investimento",
            }
        )
        
        # Obtém moeda do fundo (sempre usa fallback "BRL" se desabilitado)
        currency = get_currency_safe(facts, section="fundo", field="fundo_moeda")
        currency_symbol = get_currency_symbol(currency)
        currency_label = get_currency_label(currency)
        
        fundo_section = build_facts_section(
            facts, "fundo",
            {
                "fundo_nome": "Nome do fundo",
                "fundo_vintage": "Vintage year",
                "fundo_target_mm": f"Target ({currency_label})",
                "fundo_hard_cap_mm": f"Hard cap ({currency_label})",
                "fundo_closing": "Status/número closing",
                "fundo_captado_mm": f"Capital captado ({currency_label})",
            }
        )
        
        estrategia_section = build_facts_section(
            facts, "estrategia",
            {
                "estrategia_tese": "Tese de investimento",
                "estrategia_setores": "Setores-alvo",
                "estrategia_geografia": "Geografia",
                "estrategia_num_investments_target": "Número de investimentos alvo",
                "estrategia_ticket_min_mm": f"Ticket mínimo ({currency_label})",
                "estrategia_ticket_max_mm": f"Ticket máximo ({currency_label})",
            }
        )
        
        spectra_context_section = build_facts_section(
            facts, "spectra_context",
            {
                "spectra_relacionamento": "Relacionamento histórico",
                "spectra_commitment_mm": f"Commitment Spectra ({currency_label})",
                "spectra_vehicle": "Veículo Spectra",
            }
        )
        
        # ===== EXTRAI INFORMAÇÕES CHAVE PARA VALIDAÇÃO =====
        # Nomes usam placeholder se desabilitados
        gestora_nome = get_name_safe(facts, "gestora", "gestora_nome", "[nome da gestora]")
        fundo_nome = get_name_safe(facts, "fundo", "fundo_nome", "[nome do fundo]")
        fundo_numero = get_name_safe(facts, "fundo", "fundo_vintage", "[número]")
        
        # Valores numéricos retornam None se desabilitados (devem ser omitidos)
        fundo_target = get_numeric_safe(facts, "fundo", "fundo_target_mm")
        if fundo_target is None:
            fundo_target = "[target]"  # Placeholder apenas para validação do prompt

        # ===== SYSTEM PROMPT (DETALHADO E GUIADO) =====
        system_prompt = f"""Você é um analista sênior de Private Equity com 15 anos de experiência escrevendo a seção "Resumo da oportunidade" de um Short Memo de investimento primário em fundo para o comitê de investimento da Spectra Capital.

═══════════════════════════════════════════════════════════════════════
PADRÃO OBRIGATÓRIO - PRIMEIRA FRASE
═══════════════════════════════════════════════════════════════════════

"Este documento apresenta a oportunidade de investimento no {fundo_nome}, [número ordinal] fundo da {gestora_nome}. A Spectra [não é/é] investidora do [fundo anterior]. Um eventual compromisso no {fundo_nome} seria via [Fundo X]."

**REGRA CRÍTICA:** Use EXATAMENTE essa estrutura, substituindo apenas os valores entre [] pelos facts fornecidos.

═══════════════════════════════════════════════════════════════════════
ESTRUTURA OBRIGATÓRIA - 3 PARÁGRAFOS
═══════════════════════════════════════════════════════════════════════

§ PARÁGRAFO 1 - Resumo/Contexto da Oportunidade:
  - Primeira frase segue o padrão obrigatório acima
  - Mencionar: gestora, fundo alvo, relacionamento Spectra, veículo
  - Status da captação: target, primeiro closing, timeline
  - Número de ativos planejados

§ PARÁGRAFO 2 - Visão Geral da Gestora:
  - Tipo de gestora (operator led, growth equity, etc)
  - Posicionamento de mercado (nicho entre VC e PE, etc)
  - Foco: ticket, estágio, setores
  - Filosofia de investimento
  - Track record resumido (AUM, fundos anteriores, se disponível)

§ PARÁGRAFO 3 - Fundo que Estamos Investindo:
  - Tamanho alvo e número de ativos
  - Estratégia de alocação (ex: "1-2 casos oportunísticos + 4-5 growth minoritário")
  - Tese de investimento resumida
  - Comparação com fundo anterior (se aplicável)

═══════════════════════════════════════════════════════════════════════
REGRAS DE ESTILO (NÃO NEGOCIÁVEIS)
═══════════════════════════════════════════════════════════════════════

✅ Tom profissional, primeira pessoa plural: "estamos avaliando", "um eventual compromisso seria"
✅ Quantifique TUDO: valores exatos, números de ativos, percentuais
✅ Use **negrito** para: gestora, fundo, valores ({currency_symbol} Xm)
✅ Seja específico: "R$ 150m" não "valor significativo"
✅ Cada parágrafo: 5-8 linhas, bem conectadas
✅ NÃO invente dados: se campo estiver vazio, trate como "ainda em discussão" ou "não disponível"
✅ NÃO use bullets, numerações ou títulos - apenas parágrafos fluidos
✅ Separe parágrafos com linha em branco

**OUTPUT:** Apenas os 3 parágrafos, sem título de seção."""

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

[GESTORA]
{gestora_section}

[FUNDO]
{fundo_section}

[ESTRATÉGIA]
{estrategia_section}

[CONTEXTO SPECTRA]
{spectra_context_section}
{rag_section}
═══════════════════════════════════════════════════════════════════════
INSTRUÇÕES FINAIS
═══════════════════════════════════════════════════════════════════════

1. Escreva EXATAMENTE 3 parágrafos seguindo a estrutura obrigatória
2. Use os números EXATOS dos facts - NÃO invente ou arredonde
3. Se algum campo estiver ausente, marque como "ainda em discussão" ou omita
4. Siga o padrão da primeira frase sem exceções
5. Mantenha tom profissional e analítico

Comece AGORA com o primeiro parágrafo (primeira frase obrigatória):"""

        # Enriquecer prompt com exemplos dos templates
        system_prompt = enrich_prompt("intro", system_prompt)

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        response = llm.invoke(messages)
        return fix_number_formatting(response.content.strip())
