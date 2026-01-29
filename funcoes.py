import streamlit as st
from time import time
import unicodedata
import re


def sanitize_memo_id(text: str) -> str:
    """
    Sanitiza texto para uso como ID no ChromaDB.
    
    ChromaDB aceita caracteres alfanuméricos e underscores (remove acentos, espaços especiais, etc).
    
    Args:
        text: Texto a ser sanitizado (ex: "Short Memo - Primário")
    
    Returns:
        String sanitizada (ex: "Short_Memo_Primario")
    
    Exemplos:
        "Short Memo - Primário" -> "Short_Memo_Primario"
        "Memo - Co-investimento (Search Fund)" -> "Memo_Co_investimento_Search_Fund"
    """
    # Remover acentos e normalizar para NFD (decomposição)
    text = unicodedata.normalize('NFD', text)
    
    # Remover diacríticos (acentos)
    text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')
    
    # Converter para minúsculas
    text = text.lower()
    
    # Substituir espaços e caracteres especiais por underscore
    text = re.sub(r'[^a-z0-9]+', '_', text)
    
    # Remover underscores duplicados
    text = re.sub(r'_+', '_', text)
    
    # Remover underscores no início e fim
    text = text.strip('_')
    
    # Garantir que não está vazio
    if not text:
        text = "memo"
    
    return text


def safe_str_conversion(value):
    """Converte qualquer valor para string de forma segura para Streamlit widgets.
    
    Args:
        value: Qualquer tipo de valor (str, int, float, list, dict, bool, None, etc.)
        
    Returns:
        str: Representação em string segura para widgets Streamlit
    """
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        # Converter lista para string formatada: ["A", "B"] -> "A, B"
        return ", ".join(str(item) for item in value) if value else ""
    if isinstance(value, dict):
        # Converter dict para string JSON-like ou simples
        return str(value)
    if isinstance(value, (tuple, set)):
        # Converter tuple/set para string formatada
        return ", ".join(str(item) for item in value) if value else ""
    # Para objetos desconhecidos, tentar conversão segura
    try:
        return str(value)
    except Exception:
        return ""


def render_field_with_toggle(label, field_key, section, current_value=None, help_text=None, input_type="text", memo_type=None, **kwargs):
    """Renderiza um campo com toggle, priorizando valores de facts_edited"""
    field_id = f"{section}.{field_key}"
    widget_key = f"input_{field_id}"
    
    # Verificar se o campo está desabilitado
    is_disabled = field_id in st.session_state.disabled_facts
    
    # Buscar valor de facts_edited (PRIORIDADE)
    actual_value = None
    if section in st.session_state.facts_edited and field_key in st.session_state.facts_edited[section]:
        actual_value = st.session_state.facts_edited[section][field_key]
    
    # Se não há valor em facts_edited E há um default, usar o default
    if actual_value is None and current_value is not None:
        actual_value = current_value
    
    # CRUCIAL: Se temos um valor mas a key do widget não existe, popular a key
    if actual_value is not None and widget_key not in st.session_state:
        # Converter para tipo apropriado baseado no tipo do input
        if input_type == "number":
            # Para number_input, manter como número
            try:
                if isinstance(actual_value, str):
                    cleaned = actual_value.replace("M", "").replace("$", "").replace(",", ".").replace("%", "").strip()
                    st.session_state[widget_key] = float(cleaned) if cleaned else 0.0
                else:
                    st.session_state[widget_key] = float(actual_value)
            except (ValueError, TypeError):
                st.session_state[widget_key] = 0.0
        else:
            # Para text_input/text_area, usar safe_str_conversion para garantir tipo seguro
            st.session_state[widget_key] = safe_str_conversion(actual_value)
    
    col_toggle, col_input = st.columns([0.5, 9.5])
    
    with col_toggle:
        is_enabled = field_id not in st.session_state.disabled_facts
        checkbox_key = f"toggle_{field_id}_{st.session_state.get('memo_type', '')}"
        
        enabled = st.checkbox("Enable field", value=is_enabled, key=checkbox_key, label_visibility="collapsed")
        
        if not enabled and field_id not in st.session_state.disabled_facts:
            st.session_state.disabled_facts.add(field_id)
        elif enabled and field_id in st.session_state.disabled_facts:
            st.session_state.disabled_facts.remove(field_id)
    
    with col_input:
        if not enabled:
            disabled_key = f"disabled_{field_id}"
            # CRÍTICO: widgets também têm estado próprio; garantir que a key disabled_* seja string
            if disabled_key in st.session_state and not isinstance(st.session_state[disabled_key], str):
                st.session_state[disabled_key] = safe_str_conversion(st.session_state[disabled_key])
            st.text_input(
                label,
                value=safe_str_conversion(actual_value),
                disabled=True,
                help=help_text,
                key=disabled_key,
            )
            return actual_value
        else:
            if input_type == "number":
                # Determinar se deve ser int ou float baseado no step
                step = kwargs.get("step", 0.1)
                is_integer = isinstance(step, int) and step == 1
                
                # Obter min_value para usar como padrão se necessário
                min_val = kwargs.get("min_value", 0 if is_integer else 0.0)
                default_fallback = int(min_val) if is_integer else float(min_val)
                
                # Converter actual_value (pode ser string como "14.9M")
                if actual_value is not None:
                    try:
                        # Limpar strings monetárias
                        if isinstance(actual_value, str):
                            cleaned = actual_value.replace("M", "").replace("$", "").replace(",", ".").replace("%", "").strip()
                            actual_value = float(cleaned) if cleaned else None
                        
                        default_value = int(actual_value) if is_integer else float(actual_value)
                    except (ValueError, TypeError):
                        default_value = default_fallback
                else:
                    default_value = default_fallback
                
                # Converter todos os kwargs numéricos para o tipo correto
                numeric_kwargs = {}
                for key, val in kwargs.items():
                    if key in ("min_value", "max_value", "step") and val is not None:
                        numeric_kwargs[key] = int(val) if is_integer else float(val)
                    else:
                        numeric_kwargs[key] = val
                
                # CRÍTICO: Garantir que default_value seja sempre numérico (nunca string)
                if not isinstance(default_value, (int, float)):
                    default_value = default_fallback

                # CRÍTICO: Streamlit pode preferir o valor existente da session_state para widgets.
                # Se houver estado antigo (ex: string "14.9"), normalizar antes de criar o widget.
                if widget_key in st.session_state and not isinstance(st.session_state[widget_key], (int, float)):
                    try:
                        if isinstance(st.session_state[widget_key], str):
                            cleaned = (
                                st.session_state[widget_key]
                                .replace("M", "")
                                .replace("$", "")
                                .replace(",", ".")
                                .replace("%", "")
                                .strip()
                            )
                            coerced = float(cleaned) if cleaned not in (None, "", "null") else default_fallback
                        else:
                            coerced = float(st.session_state[widget_key])
                        st.session_state[widget_key] = int(coerced) if is_integer else float(coerced)
                    except (ValueError, TypeError):
                        st.session_state[widget_key] = int(default_value) if is_integer else float(default_value)
                
                value = st.number_input(label, value=default_value, help=help_text, key=f"input_{field_id}", **numeric_kwargs)
            elif input_type == "text_area":
                text_value = safe_str_conversion(actual_value)
                
                # CRÍTICO: Corrigir a key na session_state ANTES de criar o widget
                if widget_key in st.session_state and not isinstance(st.session_state[widget_key], str):
                    st.session_state[widget_key] = safe_str_conversion(st.session_state[widget_key])
                
                value = st.text_area(label, value=text_value, help=help_text, key=f"input_{field_id}", **kwargs)
            elif input_type == "date":
                value = st.date_input(label, value=actual_value, help=help_text, key=f"input_{field_id}", **kwargs)
            elif input_type == "select":
                # Selectbox requer lista de opções
                options = kwargs.pop("options", [])
                text_value = safe_str_conversion(actual_value)
                
                # CRÍTICO: Corrigir a key na session_state ANTES de criar o widget
                if widget_key in st.session_state and not isinstance(st.session_state[widget_key], str):
                    st.session_state[widget_key] = safe_str_conversion(st.session_state[widget_key])
                
                # Determinar index baseado no valor atual
                index = 0
                if text_value and text_value in options:
                    index = options.index(text_value)
                
                value = st.selectbox(label, options=options, index=index, help=help_text, key=f"input_{field_id}", **kwargs)
            else:
                # Usar safe_str_conversion para garantir tipo string seguro
                text_value = safe_str_conversion(actual_value)
                
                # CRÍTICO: Corrigir a key na session_state ANTES de criar o widget
                # Streamlit lê widget_state.value da session_state ANTES de executar st.text_input()
                if widget_key in st.session_state and not isinstance(st.session_state[widget_key], str):
                    st.session_state[widget_key] = safe_str_conversion(st.session_state[widget_key])
                
                value = st.text_input(label, value=text_value, help=help_text, key=f"input_{field_id}", **kwargs)
            
            # Atualizar facts_edited com o novo valor (se o campo estiver habilitado)
            if not is_disabled:
                if section not in st.session_state.facts_edited:
                    st.session_state.facts_edited[section] = {}
                st.session_state.facts_edited[section][field_key] = value
            
            return value


def add_custom_field():
    field_name = f"Campo {len(st.session_state.custom_fields) + 1}"
    st.session_state.custom_fields.append(field_name)
    st.session_state.field_paragraphs[field_name] = [""]


def navigate_to_field(field_name):
    st.session_state.current_page = "field_editor"
    st.session_state.selected_field = field_name


def navigate_to_home():
    st.session_state.current_page = "home"
    st.session_state.selected_field = None



def rename_field(old_name, new_name, idx=None):
    if not (new_name and new_name.strip()) or new_name == old_name:
        return

    custom_fields = st.session_state.custom_fields

    # Preferir o idx (mais estável em callbacks)
    if idx is not None and 0 <= idx < len(custom_fields) and custom_fields[idx] == old_name:
        custom_fields[idx] = new_name
    elif old_name in custom_fields:
        i = custom_fields.index(old_name)
        custom_fields[i] = new_name
    else:
        # Nada a renomear (callback ficou "stale")
        return

    if old_name in st.session_state.field_paragraphs:
        st.session_state.field_paragraphs[new_name] = st.session_state.field_paragraphs.pop(old_name)
    
    # Atualizar selected_field se o campo renomeado for o que está aberto no editor
    if st.session_state.get("selected_field") == old_name:
        st.session_state.selected_field = new_name



def save_field_name(idx, field_name):
    new_name = st.session_state.get(f"rename_input_{idx}", field_name)
    if new_name and new_name.strip():
        rename_field(field_name, new_name, idx=idx)
    st.session_state[f"editing_{idx}"] = False


def delete_field(field_name):
    st.session_state.custom_fields.remove(field_name)
    if field_name in st.session_state.field_paragraphs:
        del st.session_state.field_paragraphs[field_name]


def move_field_up(idx):
    """Move uma seção para cima na lista"""
    if idx > 0 and idx < len(st.session_state.custom_fields):
        st.session_state.custom_fields[idx], st.session_state.custom_fields[idx - 1] = \
            st.session_state.custom_fields[idx - 1], st.session_state.custom_fields[idx]


def move_field_down(idx):
    """Move uma seção para baixo na lista"""
    if idx >= 0 and idx < len(st.session_state.custom_fields) - 1:
        st.session_state.custom_fields[idx], st.session_state.custom_fields[idx + 1] = \
            st.session_state.custom_fields[idx + 1], st.session_state.custom_fields[idx]


def add_paragraph(field_name, insert_after_idx=None):
    if field_name not in st.session_state.field_paragraphs:
        st.session_state.field_paragraphs[field_name] = []
    
    if insert_after_idx is not None:
        st.session_state.field_paragraphs[field_name].insert(insert_after_idx + 1, "")
    else:
        st.session_state.field_paragraphs[field_name].append("")


def delete_paragraph(field_name, paragraph_idx):
    if field_name in st.session_state.field_paragraphs:
        if len(st.session_state.field_paragraphs[field_name]) > 1:
            st.session_state.field_paragraphs[field_name].pop(paragraph_idx)


def move_paragraph_up(field_name, paragraph_idx):
    """Move um parágrafo para cima na lista"""
    if field_name in st.session_state.field_paragraphs:
        paragraphs = st.session_state.field_paragraphs[field_name]
        if paragraph_idx > 0 and paragraph_idx < len(paragraphs):
            paragraphs[paragraph_idx], paragraphs[paragraph_idx - 1] = \
                paragraphs[paragraph_idx - 1], paragraphs[paragraph_idx]
            
            # Atualizar índice do parágrafo focado se necessário
            focused_para_key = f"focused_paragraph_{field_name}"
            if focused_para_key in st.session_state:
                if st.session_state[focused_para_key] == paragraph_idx:
                    st.session_state[focused_para_key] = paragraph_idx - 1
                elif st.session_state[focused_para_key] == paragraph_idx - 1:
                    st.session_state[focused_para_key] = paragraph_idx


def move_paragraph_down(field_name, paragraph_idx):
    """Move um parágrafo para baixo na lista"""
    if field_name in st.session_state.field_paragraphs:
        paragraphs = st.session_state.field_paragraphs[field_name]
        if paragraph_idx >= 0 and paragraph_idx < len(paragraphs) - 1:
            paragraphs[paragraph_idx], paragraphs[paragraph_idx + 1] = \
                paragraphs[paragraph_idx + 1], paragraphs[paragraph_idx]
            
            # Atualizar índice do parágrafo focado se necessário
            focused_para_key = f"focused_paragraph_{field_name}"
            if focused_para_key in st.session_state:
                if st.session_state[focused_para_key] == paragraph_idx:
                    st.session_state[focused_para_key] = paragraph_idx + 1
                elif st.session_state[focused_para_key] == paragraph_idx + 1:
                    st.session_state[focused_para_key] = paragraph_idx


def handle_field_click(idx, field_name):
    current_time = time()
    last_click_time = st.session_state.last_click.get(idx, 0)
    time_diff = current_time - last_click_time
    
    if time_diff < 0.5:
        st.session_state[f"editing_{idx}"] = True
        st.session_state.click_count[idx] = 0
        st.session_state.last_click[idx] = 0
    else:
        navigate_to_field(field_name)
        st.session_state.last_click[idx] = current_time