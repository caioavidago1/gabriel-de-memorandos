"""
Configuração central de Modelos de IA e agentes que produzem textos.

Define modelos disponíveis para:
- UI (Gerar Memorando, Modelo de IA no chat)
- Agentes de geração (LangGraph orchestrators, RAG chat, generation_orchestrator)

Todos os agentes que produzem texto devem usar get_llm_for_agents() para
garantir provedor (OpenAI/Anthropic) e parâmetros consistentes.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any

# Imports condicionais para múltiplos providers (usados em get_llm_for_agents)
try:
    from langchain_openai import ChatOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    ChatOpenAI = None

try:
    from langchain_anthropic import ChatAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    ChatAnthropic = None

try:
    from core.logger import get_logger
except ImportError:
    def get_logger(name: str):
        import logging
        return logging.getLogger(name)

logger = get_logger(__name__)


class TipoModelo(str, Enum):
    """Provedor do modelo de IA."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


@dataclass
class ModeloConfig:
    """
    Configuração de um modelo de IA disponível na plataforma.

    Attributes:
        id: Identificador técnico (ex: gpt-5.2).
        nome: Nome para exibição (ex: GPT-5.2).
        provedor: Provedor do modelo (OPENAI ou ANTHROPIC).
        descricao: Descrição orientada ao uso em memorandos Spectra.
        max_tokens: Limite de contexto em tokens.
    """

    id: str
    nome: str
    provedor: TipoModelo
    descricao: str
    max_tokens: int

    @property
    def description(self) -> str:
        """Alias para compatibilidade com código que usa .description."""
        return self.descricao


class GerenciadorModelos:
    """Gerencia modelos de IA disponíveis para geração e edição de memorandos."""

    MODELOS_DISPONIVEIS: Dict[str, ModeloConfig] = {
        # OpenAI - Modelos Premium 2026
        "gpt-5.2": ModeloConfig(
            id="gpt-5.2",
            nome="GPT-5.2",
            provedor=TipoModelo.OPENAI,
            descricao="Entrada $1,75 / Saída $14 por 1M tokens.",
            max_tokens=400000,
        ),
        "gpt-5.1": ModeloConfig(
            id="gpt-5.1",
            nome="GPT-5.1",
            provedor=TipoModelo.OPENAI,
            descricao="Entrada e saída conforme tabela OpenAI.",
            max_tokens=400000,
        ),
        # OpenAI - Modelos Econômicos 2026
        "gpt-5-mini": ModeloConfig(
            id="gpt-5-mini",
            nome="GPT-5 Mini",
            provedor=TipoModelo.OPENAI,
            descricao="Entrada $0,25 / Saída $2 por 1M tokens.",
            max_tokens=128000,
        ),
        # Anthropic - Modelos Claude 2026
        "claude-opus-4.5": ModeloConfig(
            id="claude-opus-4-5",
            nome="Claude Opus 4.5",
            provedor=TipoModelo.ANTHROPIC,
            descricao="Entrada $5 / Saída $25 por 1M tokens.",
            max_tokens=200000,
        ),
        "claude-sonnet-4.5": ModeloConfig(
            id="claude-sonnet-4-5",
            nome="Claude Sonnet 4.5",
            provedor=TipoModelo.ANTHROPIC,
            descricao="Entrada $3 / Saída $15 por 1M tokens.",
            max_tokens=400000,
        ),
    }


# Compatibilidade retroativa: expor mesmo dicionário usado em "Gerar Memorando" e "Modelo de IA"
AVAILABLE_MODELS: Dict[str, ModeloConfig] = GerenciadorModelos.MODELOS_DISPONIVEIS


def get_model_display_name(model_id: str) -> str:
    """
    Retorna nome formatado para exibição no seletor.

    Args:
        model_id: ID do modelo.

    Returns:
        Nome para exibição (ex: GPT-5.2).
    """
    modelo = AVAILABLE_MODELS.get(model_id)
    if modelo:
        return modelo.nome
    return model_id


def get_default_model() -> str:
    """Retorna o modelo padrão para geração de memorandos."""
    return "claude-opus-4.5"


def get_llm_for_agents(model_id: str, temperature: float = 0.3) -> Any:
    """
    Retorna instância LangChain do LLM (ChatOpenAI ou ChatAnthropic) para uso
    pelos agentes que produzem textos (orchestrators, RAG chat, etc.).

    Usa ModeloConfig.provedor para escolher o provider; modelos não cadastrados
    usam o modelo padrão com fallback para OpenAI.

    Args:
        model_id: ID do modelo (ex: gpt-5.2, claude-sonnet-4.5).
        temperature: Criatividade (0-1).

    Returns:
        Instância de ChatOpenAI ou ChatAnthropic.

    Raises:
        ImportError: Se o provider necessário não estiver instalado e não houver fallback.
    """
    config = GerenciadorModelos.MODELOS_DISPONIVEIS.get(model_id)
    if not config:
        logger.warning("Modelo '%s' não encontrado em MODELOS_DISPONIVEIS; usando padrão.", model_id)
        model_id = get_default_model()
        config = GerenciadorModelos.MODELOS_DISPONIVEIS.get(model_id)
        if not config:
            model_id = next(iter(GerenciadorModelos.MODELOS_DISPONIVEIS))
            config = GerenciadorModelos.MODELOS_DISPONIVEIS[model_id]

    if config.provedor == TipoModelo.OPENAI:
        if not OPENAI_AVAILABLE or ChatOpenAI is None:
            raise ImportError("langchain-openai não está instalado. Execute: pip install langchain-openai")
        return ChatOpenAI(model=config.id, temperature=temperature)

    if config.provedor == TipoModelo.ANTHROPIC:
        if not ANTHROPIC_AVAILABLE or ChatAnthropic is None:
            logger.warning(
                "Modelo Anthropic '%s' solicitado mas langchain-anthropic não está instalado. "
                "Usando modelo padrão OpenAI como fallback.",
                config.id,
            )
            if not OPENAI_AVAILABLE or ChatOpenAI is None:
                raise ImportError("langchain-openai não está instalado. Execute: pip install langchain-openai")
            default_id = GerenciadorModelos.MODELOS_DISPONIVEIS[get_default_model()].id
            return ChatOpenAI(model=default_id, temperature=temperature)
        return ChatAnthropic(model=config.id, temperature=temperature)

    raise ValueError(f"Provedor não suportado: {config.provedor}")
