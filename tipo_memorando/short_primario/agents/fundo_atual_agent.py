"""
Agente de Fundo Atual - Short Memo Primário (Gestora)

Responsável por gerar a seção "Fundo que Estamos Investindo".
"""

from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import os
from ..facts_builder import build_facts_section
from ..facts_utils import get_currency_safe, get_name_safe, get_numeric_safe
from ..utils import get_currency_symbol, get_currency_label
from ..validator import fix_number_formatting
from ..templates import enrich_prompt


class FundoAtualAgent:
    """Agente especializado em geração de Fundo que Estamos Investindo para Short Memo Primário."""
    
    def __init__(self, model: str = "gpt-4o", temperature: float = 0.25):
        self.model = model
        self.temperature = temperature
        self.section_name = "Fundo que Estamos Investindo"
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
        Gera seção de Fundo que Estamos Investindo.
        
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

        # ===== QUERY DOS FACTS (COBERTURA COMPLETA) =====
        # Obtém moeda do fundo (sempre usa fallback "BRL" se desabilitado)
        currency = get_currency_safe(facts, section="fundo", field="fundo_moeda")
        currency_symbol = get_currency_symbol(currency)
        currency_label = get_currency_label(currency)
        
        fundo_section = build_facts_section(
            facts, "fundo",
            {
                "fundo_nome": "Nome do fundo",
                "fundo_target_mm": f"Target ({currency_label})",
                "fundo_hard_cap_mm": f"Hard cap ({currency_label})",
                "fundo_captado_mm": f"Capital captado ({currency_label})",
                "fundo_closing": "Status/número closing",
            }
        )
        
        estrategia_section = build_facts_section(
            facts, "estrategia",
            {
                "estrategia_tese": "Tese de investimento",
                "estrategia_num_investments_target": "Número de investimentos alvo",
                "estrategia_ticket_min_mm": f"Ticket mínimo ({currency_label})",
                "estrategia_ticket_max_mm": f"Ticket máximo ({currency_label})",
                "estrategia_tipo_participacao": "Tipo de participação",
                "estrategia_alocacao": "Estratégia de alocação",
            }
        )
        
        # ===== EXTRAI INFORMAÇÕES CHAVE PARA VALIDAÇÃO =====
        # Nomes usam placeholder se desabilitados
        fundo_nome = get_name_safe(facts, "fundo", "fundo_nome", "[nome do fundo]")
        
        # Valores numéricos retornam None se desabilitados (devem ser omitidos)
        fundo_target = get_numeric_safe(facts, "fundo", "fundo_target_mm")
        num_ativos = get_numeric_safe(facts, "estrategia", "estrategia_num_investments_target")
        
        # Placeholders apenas para validação do prompt
        if fundo_target is None:
            fundo_target = "[target]"
        if num_ativos is None:
            num_ativos = "[número de ativos]"

        # ===== SYSTEM PROMPT (DETALHADO E GUIADO) =====
        system_prompt = f"""Você é um analista sênior de Private Equity com 15 anos de experiência escrevendo a seção "Fundo que Estamos Investindo" de um Short Memo de investimento primário em fundo para o comitê de investimento da Spectra Capital.

═══════════════════════════════════════════════════════════════════════
ESTRUTURA OBRIGATÓRIA - 2-3 PARÁGRAFOS
═══════════════════════════════════════════════════════════════════════

§ PARÁGRAFO 1 - Tamanho Alvo, Número de Ativos e Estratégia de Alocação (4-6 frases):
  - Abertura: "O mandato é um fundo de {currency_symbol} {fundo_target} alvo, com ~{num_ativos} ativos."
  - Estratégia de alocação: "A gestora quer X casos de [tipo] e Y casos de [tipo]"
  - Ticket médio esperado (se disponível)
  - Comparação com fundo anterior (tamanho, número de ativos, se aplicável)

§ PARÁGRAFO 2 - Ideia do Fundo e Playbook (4-6 frases):
  - Como o fundo replica o playbook do fundo anterior
  - Estruturas de aquisição, governança e atuação
  - Diferenças vs fundo anterior (cheques maiores, maior stake, etc)
  - Implicações: necessidade de equipe, monitoramento, etc

§ PARÁGRAFO 3 - Riscos e Considerações (opcional, 2-4 frases):
  - Riscos específicos do fundo (escalabilidade, equipe, etc)
  - Pontos de atenção para análise

═══════════════════════════════════════════════════════════════════════
REGRAS DE ESTILO (NÃO NEGOCIÁVEIS)
═══════════════════════════════════════════════════════════════════════

✅ Tom profissional, objetivo e equilibrado
✅ Quantifique TUDO: valores, número de ativos, tickets
✅ Use **negrito** para: fundo ({fundo_nome}), valores ({currency_symbol} Xm)
✅ Seja específico sobre estratégia de alocação
✅ Mencione implicações e riscos de forma honesta
✅ Cada parágrafo: 4-6 frases, bem conectadas
✅ NÃO invente dados: se campo estiver vazio, trate como "ainda em discussão"
✅ NÃO use bullets, numerações ou títulos - apenas parágrafos fluidos
✅ Separe parágrafos com linha em branco

**OUTPUT:** Apenas os 2-3 parágrafos, sem título de seção."""

        # ===== USER PROMPT (COM TODOS OS FACTS + RAG) =====
        rag_section = ""
        if rag_context:
            rag_section = f"""
═══════════════════════════════════════════════════════════════════════
CONTEXTO ADICIONAL DO DOCUMENTO (RAG)
═══════════════════════════════════════════════════════════════════════

Use este contexto para ENRIQUECER a análise do fundo (não para sobrescrever facts).
Se houver conflito entre facts estruturados e RAG, PRIORIZE os facts.

Contexto pode incluir:
- Tamanho alvo e número de ativos
- Estratégia de alocação detalhada
- Ideia do fundo e playbook
- Implicações e riscos

{rag_context}
"""

        user_prompt = f"""
═══════════════════════════════════════════════════════════════════════
DADOS ESTRUTURADOS (FACTS) - USE EXATAMENTE COMO FORNECIDO
═══════════════════════════════════════════════════════════════════════

[FUNDO]
{fundo_section}

[ESTRATÉGIA]
{estrategia_section}
{rag_section}
═══════════════════════════════════════════════════════════════════════
INSTRUÇÕES FINAIS
═══════════════════════════════════════════════════════════════════════

1. Escreva EXATAMENTE 2-3 parágrafos seguindo a estrutura obrigatória
2. Primeira frase típica: "O mandato é um fundo de {currency_symbol} {fundo_target} alvo, com ~{num_ativos} ativos."
3. Use os números EXATOS dos facts - NÃO invente ou arredonde
4. Se algum campo estiver ausente, ajuste a frase ou omita (não invente)
5. Mantenha tom profissional e equilibrado

Comece AGORA com o primeiro parágrafo (tamanho alvo e estratégia de alocação):"""

        # Enriquecer prompts com exemplos dos templates
        system_prompt = enrich_prompt("fundo_atual", system_prompt)

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        response = llm.invoke(messages)
        return fix_number_formatting(response.content.strip())
