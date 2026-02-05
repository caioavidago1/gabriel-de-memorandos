"""
Módulo de autenticação da plataforma Gabriel - Memorandos Spectra.

- **APP_PASSWORD**: senha de acesso ao site; se definida no .env, exige login antes de qualquer conteúdo.
"""
import hashlib
import os

import streamlit as st
from dotenv import load_dotenv

load_dotenv()


SESSION_KEY_APP_AUTH = "app_authenticated"


def obter_senha_app() -> str:
    """
    Obtém a senha de acesso ao site do arquivo .env.

    Returns:
        Senha da aplicação ou string vazia se não configurada
    """
    return os.getenv("APP_PASSWORD", "")


def verificar_senha(senha_digitada: str, senha_correta: str) -> bool:
    """
    Verifica se a senha digitada está correta.
    Usa comparação segura para evitar timing attacks.

    Args:
        senha_digitada: Senha fornecida pelo usuário
        senha_correta: Senha correta para comparação

    Returns:
        True se a senha estiver correta, False caso contrário
    """
    if not senha_correta:
        return True
    hash_digitado = hashlib.sha256(senha_digitada.encode()).hexdigest()
    hash_correto = hashlib.sha256(senha_correta.encode()).hexdigest()
    return hash_digitado == hash_correto


def esta_autenticado_app() -> bool:
    """
    Verifica se o usuário está autenticado para acessar o site.
    Retorna True se não houver APP_PASSWORD configurada.
    """
    if not obter_senha_app():
        return True

    return st.session_state.get(SESSION_KEY_APP_AUTH, False)


def autenticar_app(senha: str) -> bool:
    """
    Autentica o usuário com a senha de acesso ao site.

    Args:
        senha: Senha fornecida pelo usuário

    Returns:
        True se a autenticação foi bem-sucedida, False caso contrário
    """
    senha_correta = obter_senha_app()
    if verificar_senha(senha, senha_correta):
        st.session_state[SESSION_KEY_APP_AUTH] = True
        return True
    return False


def tela_login_inicial() -> bool:
    """
    Exibe tela de login de acesso ao site.
    Aparece antes de qualquer conteúdo se APP_PASSWORD estiver configurada no .env.

    Returns:
        True se o usuário está autenticado, False caso contrário
    """
    if not obter_senha_app():
        return True
    if esta_autenticado_app():
        return True

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.title("🔐 Acesso à Plataforma")

        with st.form("login_form", clear_on_submit=False):
            senha = st.text_input(
                "Senha de Acesso",
                type="password",
                key="input_senha_app",
                help="Digite a senha e pressione Enter ou clique em Entrar"
            )
            submitted = st.form_submit_button("Entrar", type="primary", use_container_width=True)

        if submitted:
            if senha:
                if autenticar_app(senha):
                    st.success("✅ Autenticação bem-sucedida!")
                    st.rerun()
                else:
                    st.error("❌ Senha incorreta. Tente novamente.")
            else:
                st.warning("⚠️ Digite a senha")

        st.markdown("<br>", unsafe_allow_html=True)
        st.caption("💡 Entre em contato com o administrador se você não possui a senha de acesso.")

    return False
