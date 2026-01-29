"""
Configuração de Modelos de IA
Define modelos disponíveis e suas características
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class ModelInfo:
    """Informações de um modelo de IA"""
    id: str
    display_name: str
    provider: str
    description: str


# Catálogo de modelos suportados
AVAILABLE_MODELS: Dict[str, ModelInfo] = {
    "gpt-4o": ModelInfo(
        id="gpt-4o",
        display_name="GPT-4o",
        provider="openai",
        description="Balanceado, rápido e eficiente."
    ),
    "gpt-4o-mini": ModelInfo(
        id="gpt-4o-mini",
        display_name="GPT-4o Mini",
        provider="openai",
        description="Versão compacta e econômica. Ideal para tarefas simples e rápidas."
    ),
    "claude-sonnet-4": ModelInfo(
        id="claude-sonnet-4",
        display_name="Claude Sonnet 4.5",
        provider="anthropic",
        description="Máxima qualidade em análise."
    ),
}


def get_model_display_name(model_id: str) -> str:
    """
    Retorna nome formatado para exibição no seletor
    
    Args:
        model_id: ID do modelo
        
    Returns:
        Nome formatado
    """
    model = AVAILABLE_MODELS.get(model_id)
    if model:
        return model.display_name
    return model_id


def get_default_model() -> str:
    """Retorna o modelo padrão"""
    return "gpt-4o"
