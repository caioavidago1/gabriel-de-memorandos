"""
Chat Module - Gerencia interações de chat com IA para edição de parágrafos
"""

from .ui_components import render_fixed_chat_panel
from .chat_handler import ChatHandler
from model_config import AVAILABLE_MODELS, get_model_display_name, get_default_model

__all__ = ['render_fixed_chat_panel', 'ChatHandler', 'AVAILABLE_MODELS', 'get_model_display_name', 'get_default_model']
