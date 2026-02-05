"""
Chat UI Components - Componentes de interface para o chat com IA
"""
import streamlit as st
from typing import Dict, Optional, List
from .chat_handler import ChatHandler
from model_config import AVAILABLE_MODELS, get_model_display_name, get_default_model
from core.ui_messages import show_warning, show_error, show_success


def _handle_chat_message(
    user_query: str,
    field_name: str,
    paragraph_idx: int,
    current_paragraph: str,
    all_section_paragraphs: List[str],
    facts: Dict,
    memo_type: str,
    memo_id: Optional[str],
    chat_history_key: str,
    model: str = "gpt-4o",
    temperature: float = 0.3
):
    """Processa mensagem do chat"""
    with st.spinner(f"🤖 Processando com {model}..."):
        try:
            # Inicializar handler com modelo e temperatura selecionados
            chat_handler = ChatHandler(model=model, temperature=temperature)
            
            # Processar mensagem com contexto completo
            result = chat_handler.process_chat_message(
                user_query=user_query,
                current_paragraph=current_paragraph,
                section_name=field_name,
                all_section_paragraphs=all_section_paragraphs,
                current_paragraph_idx=paragraph_idx,
                facts=facts,
                memo_type=memo_type,
                memo_id=memo_id,
                conversation_history=st.session_state[chat_history_key]
            )
            
            if not result["success"]:
                show_error("Erro ao processar", details=result.get("error", ""))
                return
            
            # Adicionar query do usuário ao histórico
            st.session_state[chat_history_key].append({
                "role": "user",
                "content": user_query
            })
            
            # Processar resultado baseado no tipo
            if result["type"] == "modification":
                # Atualizar parágrafo existente
                st.session_state.field_paragraphs[field_name][paragraph_idx] = result["content"]
                
                # CRÍTICO: Incrementar versão para forçar Streamlit a recriar widget com novo valor
                version_key = f"{field_name}_{paragraph_idx}"
                if "paragraph_versions" not in st.session_state:
                    st.session_state.paragraph_versions = {}
                if version_key not in st.session_state.paragraph_versions:
                    st.session_state.paragraph_versions[version_key] = 0
                st.session_state.paragraph_versions[version_key] += 1
                
                st.session_state[chat_history_key].append({
                    "role": "assistant",
                    "content": result.get("message", "Parágrafo modificado conforme solicitado.")
                })
                
                show_success("✅ Parágrafo atualizado!", use_toast=True)
            
            elif result["type"] == "new_paragraph":
                # Adicionar novo parágrafo ao final da seção
                st.session_state.field_paragraphs[field_name].append(result["content"])
                
                st.session_state[chat_history_key].append({
                    "role": "assistant",
                    "content": result.get("message", "Novo parágrafo criado e adicionado à seção.")
                })
                
                show_success(f"✅ Novo parágrafo adicionado! (Total: {len(st.session_state.field_paragraphs[field_name])})", use_toast=True)
            
            else:  # question
                # Responder pergunta
                st.session_state[chat_history_key].append({
                    "role": "assistant",
                    "content": result["content"]
                })
            
            st.rerun()
            
        except Exception as e:
            show_error("Erro ao processar", details=str(e))


def _handle_regenerate_paragraph(
    field_name: str,
    paragraph_idx: int,
    current_paragraph: str,
    all_section_paragraphs: List[str],
    facts: Dict,
    memo_type: str,
    memo_id: Optional[str],
    model: str = "gpt-4o",
    temperature: float = 0.3
):
    """Regenera parágrafo com otimizações"""
    with st.spinner(f"✨ Otimizando com {model}..."):
        try:
            chat_handler = ChatHandler(model=model, temperature=temperature)
            
            result = chat_handler.regenerate_paragraph(
                current_paragraph=current_paragraph,
                section_name=field_name,
                all_section_paragraphs=all_section_paragraphs,
                current_paragraph_idx=paragraph_idx,
                facts=facts,
                memo_type=memo_type,
                memo_id=memo_id
            )
            
            if result["success"]:
                st.session_state.field_paragraphs[field_name][paragraph_idx] = result["content"]
                
                # CRÍTICO: Incrementar versão para forçar Streamlit a recriar widget com novo valor
                version_key = f"{field_name}_{paragraph_idx}"
                if "paragraph_versions" not in st.session_state:
                    st.session_state.paragraph_versions = {}
                if version_key not in st.session_state.paragraph_versions:
                    st.session_state.paragraph_versions[version_key] = 0
                st.session_state.paragraph_versions[version_key] += 1
                
                show_success("✅ Parágrafo otimizado!", use_toast=True)
                st.rerun()
            else:
                show_error("Erro ao otimizar parágrafo", details=result.get("error", ""))
                
        except Exception as e:
            show_error("Erro ao otimizar parágrafo", details=str(e))


def render_fixed_chat_panel(
    field_name: str,
    paragraph_idx: int,
    current_paragraph: str,
    all_section_paragraphs: List[str],
    facts: Dict,
    memo_type: str,
    memo_id: Optional[str]
):
    """
    Renderiza painel de chat fixo à direita para edição de parágrafo
    
    Args:
        field_name: Nome do campo/seção
        paragraph_idx: Índice do parágrafo focado
        current_paragraph: Conteúdo atual do parágrafo
        all_section_paragraphs: Lista com todos os parágrafos da seção
        facts: Fatos extraídos
        memo_type: Tipo de memorando
        memo_id: ID do memo para busca RAG
    """
    # Usar container do Streamlit
    with st.container():

        # Cabeçalho do chat 
        st.markdown("### Assistente de IA")
        st.caption(f"**{field_name}** • Parágrafo {paragraph_idx + 1}")
        
        # Configurações compactas 
        with st.expander("Configurações", expanded=False):
            # Inicializar configurações no session_state
            chat_config_key = f"chat_config_{field_name}_{paragraph_idx}"
            if chat_config_key not in st.session_state:
                st.session_state[chat_config_key] = {
                    "model": get_default_model(),
                    "temperature": 0.3
                }
            
            # Seletor de modelo compacto
            model_options = list(AVAILABLE_MODELS.keys())
            selected_model = st.selectbox(
                "Modelo:",
                options=model_options,
                format_func=get_model_display_name,
                index=model_options.index(st.session_state[chat_config_key]["model"]) if st.session_state[chat_config_key]["model"] in model_options else 0,
                key=f"model_select_fixed_{field_name}_{paragraph_idx}",
                help="Escolha o modelo de IA"
            )
            
            # Slider de temperatura compacto
            temperature = st.slider(
                "Criatividade:",
                min_value=0.0,
                max_value=1.0,
                value=st.session_state[chat_config_key]["temperature"],
                step=0.1,
                key=f"temp_select_fixed_{field_name}_{paragraph_idx}",
                help="0.0 = preciso | 1.0 = criativo"
            )
            
            # Atualizar configurações
            st.session_state[chat_config_key]["model"] = selected_model
            st.session_state[chat_config_key]["temperature"] = temperature
        
        # Parágrafo Original (para referência)
        with st.expander("Parágrafo Original", expanded=False):
            # Obter parágrafo original
            original_para_key = f"original_paragraph_{field_name}_{paragraph_idx}"
            original_paragraph = st.session_state.get(original_para_key, current_paragraph)
            
            # Se ainda não há original salvo, salvar o atual como original
            if original_para_key not in st.session_state:
                st.session_state[original_para_key] = current_paragraph
                original_paragraph = current_paragraph
            
            if not original_paragraph.strip():
                st.caption("*Vazio*")
            else:
                st.text_area(
                    "Parágrafo original (somente leitura)",
                    value=original_paragraph,
                    height=150,
                    key=f"original_display_{field_name}_{paragraph_idx}",
                    disabled=True,
                    label_visibility="collapsed",
                )
        
        # Contexto da seção 
        with st.expander(f"Todos os Parágrafos ({len(all_section_paragraphs)})", expanded=False):
            for idx, para in enumerate(all_section_paragraphs):
                if para.strip():
                    marker = "**" if idx == paragraph_idx else ""
                    end_marker = "**" if idx == paragraph_idx else ""
                    st.caption(f"{marker}P{idx+1}:{end_marker} {para[:60]}...")
        
        # Inicializar histórico de conversa se não existir
        chat_history_key = f"chat_history_{field_name}_{paragraph_idx}"
        if chat_history_key not in st.session_state:
            st.session_state[chat_history_key] = []
        
        # Área de mensagens 
        st.markdown("**Conversa**")
        
        if st.session_state[chat_history_key]:
            # Container com scroll para mensagens (últimas 8)
            for msg in st.session_state[chat_history_key][-8:]:
                if msg["role"] == "user":
                    with st.chat_message("user"):
                        st.write(msg["content"])
                else:
                    with st.chat_message("assistant"):
                        st.write(msg["content"])
        else:
            st.info("**Exemplos:**\n- Seja mais conciso\n- Crie parágrafo sobre riscos\n- Qual é a receita?")
        
        # Input de comando
        user_query = st.text_input(
            "Instrução:",
            key=f"chat_input_fixed_{field_name}_{paragraph_idx}",
            placeholder="Ex: seja mais técnico",
            label_visibility="collapsed"
        )
        
        # Botões de ação 
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Enviar", key=f"send_{field_name}_{paragraph_idx}", width='stretch', type="primary"):
                if user_query.strip():
                    chat_config = st.session_state.get(chat_config_key, {"model": "gpt-4o", "temperature": 0.3})
                    _handle_chat_message(
                        user_query, field_name, paragraph_idx, current_paragraph,
                        all_section_paragraphs, facts, memo_type, memo_id,
                        chat_history_key, chat_config["model"], chat_config["temperature"]
                    )
                else:
                    show_warning("Digite uma instrução")
        
        with col2:
            if st.button("Otimizar", key=f"opt_{field_name}_{paragraph_idx}", width='stretch', help="Melhora o parágrafo automaticamente"):
                chat_config = st.session_state.get(chat_config_key, {"model": "gpt-4o", "temperature": 0.3})
                _handle_regenerate_paragraph(
                    field_name, paragraph_idx, current_paragraph,
                    all_section_paragraphs, facts, memo_type, memo_id,
                    chat_config["model"], chat_config["temperature"]
                )
        
        # Botão limpar histórico 
        if st.session_state[chat_history_key]:
            if st.button("Limpar Histórico", key=f"clear_{field_name}_{paragraph_idx}", width='stretch', help="Limpar histórico de conversa"):
                st.session_state[chat_history_key] = []
                st.rerun()
