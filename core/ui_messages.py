"""
Módulo de mensagens padronizadas para UI.

Fornece funções helper para exibir mensagens consistentes sem emoji,
seguindo padrão visual uniforme em toda a aplicação.
"""

import streamlit as st
from typing import Optional


def show_success(message: str, use_toast: bool = False) -> None:
    """
    Exibe mensagem de sucesso padronizada (sem emoji).
    
    Args:
        message: Texto da mensagem
        use_toast: Se True, usa st.toast (para ações rápidas < 3s)
                  Se False, usa st.success (para ações importantes)
    """
    if use_toast:
        st.toast(message, icon="✅")
    else:
        st.success(message)


def show_error(message: str, details: Optional[str] = None) -> None:
    """
    Exibe mensagem de erro padronizada (sem emoji).
    
    Args:
        message: Texto da mensagem de erro
        details: Detalhes técnicos opcionais (exibidos em expander)
    """
    st.error(message)
    
    if details:
        with st.expander("Ver detalhes do erro"):
            st.code(details)


def show_warning(message: str) -> None:
    """
    Exibe mensagem de aviso padronizada (sem emoji).
    
    Args:
        message: Texto da mensagem de aviso
    """
    st.warning(message)


def show_info(message: str, use_toast: bool = False) -> None:
    """
    Exibe mensagem informativa padronizada (sem emoji).
    
    Args:
        message: Texto da mensagem
        use_toast: Se True, usa st.toast (para informações rápidas)
                  Se False, usa st.info (para informações importantes)
    """
    if use_toast:
        st.toast(message, icon="ℹ️")
    else:
        st.info(message)
