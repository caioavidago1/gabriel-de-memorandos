import streamlit as st
import traceback
import base64
import hashlib
import asyncio
import json
from datetime import datetime
from pathlib import Path
from docx_edit.formatter import export_memo_to_docx
from funcoes import (
    add_custom_field,
    navigate_to_home,
    save_field_name,
    delete_field,
    add_paragraph,
    delete_paragraph,
    handle_field_click,
    safe_str_conversion,
    sanitize_memo_id,
    move_field_up,
    move_field_down,
    move_paragraph_up,
    move_paragraph_down
)
from facts import (
    render_tab_identification,
    render_tab_transaction,
    render_tab_financials,
    render_tab_returns,
    render_tab_qualitative,
    render_tab_opinioes,
    render_tab_gestora,
    render_tab_fundo,
    render_tab_estrategia_fundo,
    render_tab_spectra_context,
    filter_disabled_facts,
)
from facts.tabela.ui import render_dre_table_inputs, fill_dre_table_from_documents
from facts_config import FIELD_VISIBILITY, get_sections_for_memo_type
from core.document_processor import DocumentProcessor
from core.logger import get_logger
from core.ui_messages import show_success, show_error, show_warning, show_info
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from chat.model_config import AVAILABLE_MODELS, get_default_model, get_model_display_name
import logging

logger = get_logger(__name__)

# Suprimir avisos de WebSocket do Tornado (erros inofensivos quando clientes desconectam)
logging.getLogger("tornado.websocket").setLevel(logging.ERROR)
logging.getLogger("tornado.iostream").setLevel(logging.ERROR)

from PIL import Image
image = Image.open("static/logo.png")
st.set_page_config(
    page_title="Memorandos", 
    page_icon=image,
    layout="wide"
)

# CSS customizado para melhorar UX
st.markdown(
    """
    <style>
    /* Desabilitar renderização de KaTeX/LaTeX */
    .stMarkdown [data-testid="stMarkdownContainer"] p {
        white-space: pre-wrap;
    }
    .katex, .katex-display {
        display: none !important;
    }
    
    /* Melhorar feedback visual dos botões */
    .stButton button {
        transition: all 0.2s ease-in-out;
    }
    .stButton button:hover {
        transform: scale(1.05);
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .stButton button:active {
        transform: scale(0.98);
    }
    
    /* Melhorar animação de toasts */
    .stToast {
        animation: slideIn 0.3s ease-out;
    }
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(-20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* Melhorar área de texto com foco */
    .stTextArea textarea:focus {
        border-color: #0066CC;
        box-shadow: 0 0 0 2px rgba(0, 102, 204, 0.1);
    }
    
    /* Reduzir padding entre botões de controle */
    div[data-testid="column"] > div[data-testid="stVerticalBlock"] > div:has(.stButton) {
        gap: 0.25rem !important;
    }
    
    /* Estilos para chat fixo à direita */
    .fixed-chat-container {
        position: sticky;
        top: 1rem;
        max-height: calc(100vh - 2rem);
        overflow-y: auto;
        padding: 1rem;
        background: #f8f9fa;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
    }
    
    /* Melhorar scroll do histórico do chat */
    [data-testid="stChatMessage"] {
        margin-bottom: 0.75rem;
    }
    
    /* Destacar parágrafo focado */
    .focused-paragraph {
        border-left: 4px solid #1f77b4;
        padding-left: 12px;
        background-color: #f0f8ff;
        border-radius: 4px;
        margin: 8px 0;
        padding-top: 8px;
        padding-bottom: 8px;
    }
    
    /* Espaçamento entre parágrafos */
    .paragraph-separator {
        margin: 24px 0;
        border-bottom: 1px solid #e0e0e0;
    }
    
    /* Borda ao redor do assistente de IA */
    .assistant-ia-panel {
        border: 2px solid #e0e0e0 !important;
        border-radius: 8px !important;
        padding: 16px !important;
        background-color: #fafafa !important;
        margin-bottom: 16px !important;
    }
    
    /* Aplicar borda ao container pai quando contém assistant-ia-panel */
    div:has(> #assistant-panel-),
    div:has(.assistant-ia-panel) {
        border: 2px solid #e0e0e0 !important;
        border-radius: 8px !important;
        padding: 16px !important;
        background-color: #fafafa !important;
        margin-bottom: 16px !important;
    }
    </style>
    <script>
    // Desabilitar processamento de matemática do Streamlit
    window.MathJax = {
        skipStartupTypeset: true
    };
    </script>
    """,
    unsafe_allow_html=True
)

def apply_auto_uncheck_for_memo_type(memo_type):
    count_unmarked = 0
    count_marked = 0
    
    for section, fields in FIELD_VISIBILITY.items():
        for field_key, visibility_config in fields.items():
            field_id = f"{section}.{field_key}"
            is_relevant = False
            
            if visibility_config == "ALL":
                is_relevant = True
            elif isinstance(visibility_config, list) and memo_type in visibility_config:
                is_relevant = True
            
            if not is_relevant:
                st.session_state.disabled_facts.add(field_id)
                count_unmarked += 1
            else:
                st.session_state.disabled_facts.discard(field_id)
                count_marked += 1
    
    show_info(f"Filtro aplicado: {count_marked} campos marcados, {count_unmarked} desmarcados", use_toast=True)




# Inicializar session_state
# ===== CACHE DE RESULTADOS DE PARSING =====
CACHE_DIR = Path(".cache/parsed_documents")
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def get_file_hash(file_content: bytes) -> str:
    """
    Calcula hash MD5 do conteúdo do arquivo para usar como chave de cache.
    
    Args:
        file_content: Conteúdo binário do arquivo
    
    Returns:
        Hash MD5 em hexadecimal
    """
    return hashlib.md5(file_content).hexdigest()


def get_cache_path(file_hash: str) -> Path:
    """
    Retorna o caminho do arquivo de cache para um hash específico.
    
    Args:
        file_hash: Hash MD5 do arquivo
    
    Returns:
        Path do arquivo de cache
    """
    return CACHE_DIR / f"{file_hash}.json"


def load_from_cache(file_hash: str) -> dict | None:
    """
    Carrega resultado parseado do cache se existir.
    
    Args:
        file_hash: Hash MD5 do arquivo
    
    Returns:
        Resultado parseado ou None se não existir no cache
    """
    cache_path = get_cache_path(file_hash)
    if cache_path.exists():
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
                # Validar que o cache não está muito antigo (opcional: 30 dias)
                cache_age_days = (datetime.now() - datetime.fromisoformat(cached_data.get('cached_at', '2000-01-01'))).days
                if cache_age_days > 30:
                    logger.info(f"Cache expirado para hash {file_hash[:8]}... (idade: {cache_age_days} dias)")
                    cache_path.unlink()  # Remover cache expirado
                    return None
                logger.info(f"✅ Cache hit para arquivo (hash: {file_hash[:8]}...)")
                return cached_data.get('result')
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Erro ao carregar cache para {file_hash[:8]}...: {e}")
            cache_path.unlink()  # Remover cache corrompido
            return None
    return None


def save_to_cache(file_hash: str, result: dict, filename: str) -> None:
    """
    Salva resultado parseado no cache.
    
    Args:
        file_hash: Hash MD5 do arquivo
        result: Resultado do parsing
        filename: Nome do arquivo original
    """
    cache_path = get_cache_path(file_hash)
    try:
        cache_data = {
            'result': result,
            'filename': filename,
            'cached_at': datetime.now().isoformat(),
            'file_hash': file_hash
        }
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        logger.info(f"💾 Cache salvo para {filename} (hash: {file_hash[:8]}...)")
    except Exception as e:
        logger.warning(f"Erro ao salvar cache para {file_hash[:8]}...: {e}")


def _convert_memo_sections_to_format(memo_sections: dict, generated: dict) -> tuple[int, int]:
    """
    Converte memo_sections do formato do orchestrator para formato esperado pelo app.
    
    Args:
        memo_sections: Dict com estrutura {section_title: [paragraph1, paragraph2, ...]}
        generated: Dict de saída (modificado in-place)
    
    Returns:
        Tuple (total_quality, total_examples) calculados
    """
    quality_sum = 0
    examples_sum = 0
    
    for section_title, paragraphs in memo_sections.items():
        generated[section_title] = {
            "paragraphs": paragraphs,
            "quality_score": 85,  # Placeholder (orchestrator especializado não retorna score)
            "examples_used": 3    # Placeholder
        }
        quality_sum += 85
        examples_sum += 3
    
    return quality_sum, examples_sum


def initialize_session_state():
    """Inicializa todas as variáveis do session_state se não existirem"""
    defaults = {
        "custom_fields": [],
        "current_page": "home",
        "selected_field": None,
        "field_paragraphs": {},
        "paragraph_versions": {},
        "last_click": {},
        "click_count": {},
        "expanded_generation": {},
        "disabled_facts": set(),
        "facts_edited": {},
        "memo_type": None,
        "parsed_documents": [],
        "document_embeddings": None,
        "processing_status": "idle",
        "extracted_facts": {},
        "docx_bytes": None,
        "docx_filename": None,
        "confirm_delete_section": None,
        "confirm_delete_paragraph": None,
        "selected_model": get_default_model()
    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

initialize_session_state()

# ===== SIDEBAR =====
with st.sidebar:
    st.image("static/imagem.png", width='stretch')
    st.header("Seções")

    if st.button("Adicionar Seção", width='stretch', type="primary", on_click=add_custom_field):
        pass  # on_click já faz rerun automaticamente

    if st.session_state.custom_fields:
        st.subheader("Suas Seções:")

        for idx, field_name in enumerate(st.session_state.custom_fields):
            if st.session_state.get(f"editing_{idx}", False):
                col_input, col_close = st.columns([4, 1])
                with col_input:
                    new_name = st.text_input(
                        "Novo nome:",
                        value=field_name,
                        key=f"rename_input_{idx}",
                        label_visibility="collapsed",
                        on_change=save_field_name,
                        args=(idx, field_name),
                        help="Pressione Enter ou clique ✓ para salvar"
                    )
                with col_close:
                    if st.button("✓", key=f"close_edit_{idx}", help="Confirmar", width='stretch', on_click=save_field_name, args=(idx, field_name)):
                        st.rerun()

            else:
                col1, col_arrows, col2 = st.columns([3, 1, 1])

                with col1:
                    if st.button(
                        field_name,
                        key=f"nav_btn_{idx}",
                        width='stretch',
                        help="1 clique: abrir seção | 2 cliques: editar nome"
                    ):
                        handle_field_click(idx, field_name)
                        st.rerun()

                with col_arrows:
                    col_up, col_down = st.columns(2)
                    with col_up:
                        if st.button("↑", key=f"up_{idx}", help="Mover para cima", disabled=(idx == 0)):
                            move_field_up(idx)
                            st.rerun()
                    with col_down:
                        if st.button("↓", key=f"down_{idx}", help="Mover para baixo", disabled=(idx == len(st.session_state.custom_fields) - 1)):
                            move_field_down(idx)
                            st.rerun()

                with col2:
                    delete_key = f"del_btn_{idx}"
                    confirm_key = f"confirm_delete_section_{idx}"
                    
                    # Verificar se já está confirmando
                    if st.session_state.get(confirm_key) == field_name:
                        col_confirm, col_cancel = st.columns(2)
                        with col_confirm:
                            if st.button("Confirmar", key=f"confirm_{idx}", type="primary", width='stretch'):
                                delete_field(field_name)
                                if st.session_state.selected_field == field_name:
                                    navigate_to_home()
                                st.session_state[confirm_key] = None
                                st.rerun()
                        with col_cancel:
                            if st.button("Cancelar", key=f"cancel_{idx}", width='stretch'):
                                st.session_state[confirm_key] = None
                                st.rerun()
                    else:
                        if st.button("X", key=delete_key, help="Deletar seção"):
                            st.session_state[confirm_key] = field_name
                            st.rerun()

    else:
        st.info("Adicione uma seção. Clique em 'Adicionar Seção' para começar.")
    
    # Botão de exportação DOCX (sempre visível se há seções)
    if st.session_state.custom_fields:
        st.markdown("---")
        st.subheader("Exportar")
        
        # Botão para gerar DOCX
        if st.button("Gerar DOCX", width='stretch', type="secondary", help="Gerar documento Word para download"):
            with st.spinner("Gerando documento Word..."):
                try:
                    # Gerar DOCX
                    docx_bytes = export_memo_to_docx(
                        memo_type=st.session_state.memo_type,
                        custom_fields=st.session_state.custom_fields,
                        field_paragraphs=st.session_state.field_paragraphs
                    )
                    
                    # Ler bytes do BytesIO
                    docx_bytes.seek(0)
                    docx_data = docx_bytes.read()
                    
                    # Nome do arquivo (sanitizado para consistência)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    memo_type_slug = sanitize_memo_id(st.session_state.memo_type)
                    filename = f"{memo_type_slug}_{timestamp}.docx"
                    
                    # Salvar no session_state para download
                    st.session_state.docx_bytes = docx_data
                    st.session_state.docx_filename = filename
                    
                    show_success(f"Documento gerado: {filename}")
                    show_info("Documento gerado! Clique em 'Baixar DOCX' para fazer o download", use_toast=True)
                    st.rerun()
                    
                except Exception as e:
                    show_error("Erro ao gerar DOCX", details=str(e))
                    import traceback
                    with st.expander("Ver detalhes do erro"):
                        st.code(traceback.format_exc())
        
        # Botão de download
        if st.session_state.get("docx_bytes") and st.session_state.get("docx_filename"):
            st.download_button(
                label="Baixar DOCX",
                data=st.session_state.docx_bytes,
                file_name=st.session_state.docx_filename,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                width='stretch',
                type="primary",
                help="Baixar o documento Word gerado"
            )
    
    # Botões de Histórico 
    st.subheader("Histórico")
    
    col_save, col_view = st.columns(2)
    
    with col_save:
        # Botão salvar só ativo se tiver seções
        if st.button("Salvar", width='stretch', type="secondary", disabled=not st.session_state.custom_fields, help="Salvar memorando no histórico"):
            st.session_state.show_save_dialog = True
    
    with col_view:
        # Botão ver histórico sempre ativo
        if st.button("Ver Histórico", width='stretch'):
            st.session_state.current_page = "memo_history"
            st.rerun()
    
    # Dialog para salvar (só aparece se houver seções E botão foi clicado)
    if st.session_state.custom_fields and st.session_state.get("show_save_dialog", False):
        with st.form("save_memo_form"):
            st.markdown("#### Salvar Memo no Histórico")
            
            # Extrair nome da empresa dos facts
            company_name = ""
            if st.session_state.facts_edited:
                id_facts = st.session_state.facts_edited.get("identification", {})
                company_name = id_facts.get("company_name", "") or ""
            
            # Gerar nome padrão: "Nome da Empresa - Tipo de Memo"
            memo_type = st.session_state.memo_type
            default_name = f"{company_name} - {memo_type}" if company_name else memo_type
            
            memo_name = st.text_input(
                "Nome do Memo",
                value=default_name,
                help="Nome que será usado para identificar este memo no histórico"
            )
            
            col_submit, col_cancel = st.columns(2)
            
            with col_submit:
                submit = st.form_submit_button("Salvar", width='stretch', type="primary")
            
            with col_cancel:
                cancel = st.form_submit_button("Cancelar", width='stretch')
            
            if submit:
                from history.history_manager import MemoHistoryManager
                
                try:
                    history_manager = MemoHistoryManager()
                    
                    # Salvar 
                    memo_id = history_manager.save_memo(
                        memo_type=st.session_state.memo_type,
                        custom_fields=st.session_state.custom_fields,
                        field_paragraphs=st.session_state.field_paragraphs,
                        facts_edited=st.session_state.facts_edited,
                        tags=None,
                        notes="",
                        memo_name=memo_name
                    )
                    
                    show_info(f"Memo salvo! ID: {memo_id[:8]}...", use_toast=True)
                    st.session_state.show_save_dialog = False
                    st.rerun()
                    
                except Exception as e:
                    show_error("Erro ao salvar", details=str(e))
                    with st.expander("Ver detalhes do erro"):
                        st.code(traceback.format_exc())
            
            if cancel:
                st.session_state.show_save_dialog = False
                st.rerun()

# Home 
if st.session_state.current_page == "home":
    st.title("Gabriel - Seu Assistente para Criação de Memorandos")
    
    memo_options = ["Short Memo - Co-investimento (Search Fund)", "Short Memo - Co-investimento (Gestora)" ,"Short Memo - Primário", "Memorando - Co-investimento (Search Fund)"]
    
    # Adicionar opção "Selecione..." no início para permitir nenhum tipo selecionado por padrão
    select_placeholder = "Selecione..."
    options_with_placeholder = [select_placeholder] + memo_options
    
    # Determinar índice inicial: 0 (Selecione...) se não há tipo selecionado, senão o índice do tipo atual + 1
    if st.session_state.memo_type and st.session_state.memo_type in memo_options:
        initial_index = memo_options.index(st.session_state.memo_type) + 1
    else:
        initial_index = 0
    
    memo_type = st.selectbox(
        "Tipo de Memorando",
        options=options_with_placeholder,
        key="memo_type_select",
        index=initial_index,
        help="Selecione o tipo de memorando primeiro para otimizar a extração de fatos"
    )
    
    # Atualizar memo_type apenas se foi selecionado (não se for o placeholder)
    if memo_type and memo_type != select_placeholder and memo_type != st.session_state.memo_type:
        st.session_state.memo_type = memo_type
        apply_auto_uncheck_for_memo_type(memo_type)
        
        # Se mudou para Memo Completo Search Fund, marcar para regenerar facts
        if memo_type == "Memorando - Co-investimento (Search Fund)":
            if st.session_state.get("parsed_documents"):
                st.session_state.should_regenerate_facts = True
                st.session_state.regenerate_memo_type = memo_type
                st.info("ℹ️ Tipo de memo alterado. Os facts serão regenerados com tabelas específicas ao processar.")
        # Rerun necessário para atualizar campos visíveis baseado no tipo
        st.rerun()
    elif memo_type == select_placeholder:
        # Se selecionou o placeholder, limpar memo_type
        st.session_state.memo_type = None

    # Só mostrar Passo 2 se um tipo foi selecionado
    if st.session_state.memo_type and st.session_state.memo_type in memo_options:
        uploaded_files = st.file_uploader(
            "Adicionar Documentos",
            accept_multiple_files=True,
            type=['pdf'],
            help="Faça upload dos documentos para análise"
        )

        if uploaded_files:
            # Validações de tamanho e número de arquivos
            MAX_FILES = 30
            MAX_FILE_SIZE_MB = 500  # 500MB por arquivo (aumentado para suportar PDFs grandes)
            MAX_TOTAL_SIZE_MB = 5000  # 5000MB (5GB) total (aumentado para suportar múltiplos arquivos grandes)
            
            total_size_mb = sum(f.size for f in uploaded_files) / (1024 * 1024)
            
            # Validar número de arquivos
            if len(uploaded_files) > MAX_FILES:
                show_error(f"Máximo de {MAX_FILES} arquivos permitidos. Você enviou {len(uploaded_files)}.")
                show_info("Dica: Processe os arquivos em lotes menores para melhor performance.")
                st.stop()
            
            # Validar tamanho total
            if total_size_mb > MAX_TOTAL_SIZE_MB:
                show_error(f"Tamanho total excede {MAX_TOTAL_SIZE_MB}MB. Total: {total_size_mb:.1f}MB")
                show_info("Dica: Reduza o número de arquivos ou o tamanho dos PDFs.")
                st.stop()
            
            # Validar arquivos individuais
            oversized = [f for f in uploaded_files if f.size > MAX_FILE_SIZE_MB * 1024 * 1024]
            if oversized:
                oversized_names = ", ".join(f.name for f in oversized[:3])
                if len(oversized) > 3:
                    oversized_names += f" e mais {len(oversized) - 3} arquivo(s)"
                show_error(f"Arquivos muito grandes (> {MAX_FILE_SIZE_MB}MB): {oversized_names}")
                show_info("Dica: Comprima os PDFs ou divida em arquivos menores.")
                st.stop()
            
            show_success(f"{len(uploaded_files)} documento(s) carregado(s) ({total_size_mb:.1f}MB total)")
            with st.expander("📁 Ver arquivos"):
                for file in uploaded_files:
                    file_size_mb = file.size / (1024 * 1024)
                    st.caption(f"{file.name} ({file_size_mb:.1f}MB)")

            # Seção de Tabela DRE (apenas configuração quando status idle)
            # Apenas para Short Memo - Co-investimento (Search Fund)
            if st.session_state.get("memo_type") == "Short Memo - Co-investimento (Search Fund)":
                if st.session_state.processing_status == "idle":
                    # Mostrar apenas configuração de parâmetros (sem tabela)
                    render_dre_table_inputs(show_table=False)
                    
                    # Botão aparece apenas se parâmetros foram configurados
                    if st.session_state.dre_table_inputs_confirmed:
                        if st.button("Processar Documentos e Extrair Fatos", type="primary", width='stretch'):
                            st.session_state.processing_status = "parsing"
                            st.rerun()
            
            # Para outros tipos de memo, botão aparece normalmente
            if (st.session_state.get("memo_type") != "Short Memo - Co-investimento (Search Fund)" and 
                st.session_state.processing_status == "idle"):
                if st.button("Processar Documentos e Extrair Fatos", type="primary", width='stretch'):
                    st.session_state.processing_status = "parsing"
                    st.rerun()

            if st.session_state.processing_status == "parsing":
                processor = DocumentProcessor()
                
                # Salvar arquivos temporariamente
                temp_dir = Path("temp_uploads")
                temp_dir.mkdir(exist_ok=True)
                
                # Preparar arquivos e verificar cache
                temp_paths = []
                file_hashes = []
                cached_results = {}
                
                for uploaded_file in uploaded_files:
                    # Ler conteúdo do arquivo
                    file_content = uploaded_file.read()
                    file_hash = get_file_hash(file_content)
                    file_hashes.append(file_hash)
                    
                    # Verificar cache
                    cached_result = load_from_cache(file_hash)
                    if cached_result:
                        cached_results[file_hash] = cached_result
                        logger.info(f"📦 Usando cache para {uploaded_file.name}")
                    else:
                        # Salvar arquivo temporariamente apenas se não estiver em cache
                        temp_path = temp_dir / uploaded_file.name
                        temp_path.write_bytes(file_content)
                        temp_paths.append((temp_path, uploaded_file.name, file_hash))
                
                # Progress bar e status
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Combinar resultados do cache com arquivos que precisam ser processados
                # Manter ordem original dos arquivos
                parsed_results = [None] * len(uploaded_files)  # Lista com tamanho fixo
                total_files = len(uploaded_files)
                files_to_process = len(temp_paths)
                cached_count = len(cached_results)
                
                # Preencher resultados do cache nas posições corretas
                for i, (uploaded_file, file_hash) in enumerate(zip(uploaded_files, file_hashes)):
                    if file_hash in cached_results:
                        cached_result = cached_results[file_hash].copy()
                        cached_result['filename'] = uploaded_file.name  # Garantir nome correto
                        cached_result['from_cache'] = True
                        parsed_results[i] = cached_result
                        logger.info(f"✅ [{i+1}/{total_files}] Cache: {uploaded_file.name}")
                
                # Se todos os arquivos estão em cache, pular processamento
                if files_to_process == 0:
                    logger.info(f"Todos os {cached_count} arquivos foram carregados do cache!")
                    progress_bar.empty()
                    status_text.empty()
                else:
                    # Função com retry para rate limits
                    @retry(
                        stop=stop_after_attempt(3),
                        wait=wait_exponential(multiplier=1, min=4, max=30),
                        retry=retry_if_exception_type((Exception,)),
                        reraise=True
                    )
                    def parse_with_retry(processor, temp_path, filename, file_hash):
                        """Parse com retry automático para rate limits"""
                        try:
                            result = processor.parse_document(temp_path)
                            # Salvar no cache após parsing bem-sucedido
                            save_to_cache(file_hash, result, filename)
                            return result
                        except Exception as e:
                            error_str = str(e).lower()
                            # Detectar rate limit
                            if "rate limit" in error_str or "429" in error_str or "too many requests" in error_str:
                                logger.warning(f"Rate limit detectado para {filename}, aguardando retry...")
                                raise  # Retry
                            # Outros erros também podem ser temporários
                            if "timeout" in error_str or "connection" in error_str:
                                logger.warning(f"Erro temporário para {filename}, tentando novamente...")
                                raise  # Retry
                            # Erros permanentes não devem fazer retry
                            raise
                    
                    # Função auxiliar para parsear um documento
                    import time
                    parsing_start_time = time.time()
                    files_processed_times = []
                    
                    async def parse_one_document(temp_path, filename, file_hash, index, total):
                        try:
                            file_start_time = time.time()
                            status_text.text(f"Processando {index + 1}/{total}: {filename}")
                            # Executar parse em thread pool (LlamaParse não é async)
                            loop = asyncio.get_event_loop()
                            result = await loop.run_in_executor(
                                None, 
                                parse_with_retry,
                                processor,
                                temp_path,
                                filename,
                                file_hash
                            )
                            
                            # Calcular tempo decorrido e ETA
                            file_elapsed = time.time() - file_start_time
                            files_processed_times.append(file_elapsed)
                            total_elapsed = time.time() - parsing_start_time
                            
                            # Calcular ETA baseado em média de tempo por arquivo
                            if files_processed_times:
                                avg_time_per_file = sum(files_processed_times) / len(files_processed_times)
                                remaining_files = total - (index + 1)
                                eta_seconds = avg_time_per_file * remaining_files
                                
                                # Formatar tempo
                                def format_time(seconds):
                                    if seconds < 60:
                                        return f"{int(seconds)}s"
                                    else:
                                        mins = int(seconds // 60)
                                        secs = int(seconds % 60)
                                        return f"{mins}m {secs}s"
                                
                                elapsed_str = format_time(total_elapsed)
                                eta_str = format_time(eta_seconds)
                                
                                status_text.text(
                                    f"Processando {index + 1}/{total}: {filename} | "
                                    f"Tempo: {elapsed_str} | ETA: {eta_str}"
                                )
                            
                            progress_bar.progress((cached_count + index + 1) / total_files)
                            return result
                        except Exception as e:
                            logger.error(f"Erro ao parsear {filename} após retries: {e}")
                            # Retornar resultado vazio em caso de erro após retries
                            return {
                                "filename": filename,
                                "text": "",
                                "length": 0,
                                "pages": 0,
                                "error": str(e)
                            }
                    
                    # Parsear em paralelo (limitado a 4 simultâneos para evitar rate limits)
                    async def parse_all_parallel():
                        semaphore = asyncio.Semaphore(4)  # Máximo 4 paralelos
                        
                        async def parse_with_semaphore(temp_path, filename, file_hash, index, total):
                            async with semaphore:
                                return await parse_one_document(temp_path, filename, file_hash, index, total)
                        
                        tasks = [
                            parse_with_semaphore(temp_path, filename, file_hash, i, files_to_process)
                            for i, (temp_path, filename, file_hash) in enumerate(temp_paths)
                        ]
                        return await asyncio.gather(*tasks)
                    
                    # Executar parsing paralelo apenas para arquivos não em cache
                    try:
                        new_parsed_results = asyncio.run(parse_all_parallel())
                        
                        # Preencher resultados processados nas posições corretas
                        result_idx = 0
                        for i, (uploaded_file, file_hash) in enumerate(zip(uploaded_files, file_hashes)):
                            if file_hash not in cached_results:
                                # Este arquivo foi processado, usar resultado correspondente
                                if result_idx < len(new_parsed_results):
                                    parsed_results[i] = new_parsed_results[result_idx]
                                    result_idx += 1
                        
                        # Limpar progress bar
                        progress_bar.empty()
                        status_text.empty()
                        
                    except Exception as e:
                        progress_bar.empty()
                        status_text.empty()
                        show_error("Erro durante parsing", details=str(e))
                        logger.error(f"Erro no parsing paralelo: {e}", exc_info=True)
                        st.session_state.processing_status = "idle"
                        st.stop()
                
                # Validar que todos os resultados foram preenchidos
                if any(r is None for r in parsed_results):
                    missing_indices = [i for i, r in enumerate(parsed_results) if r is None]
                    logger.error(f"Erro: {len(missing_indices)} resultado(s) não foram preenchidos (índices: {missing_indices})")
                    show_error(f"Erro: {len(missing_indices)} arquivo(s) não foram processados corretamente")
                    st.session_state.processing_status = "idle"
                    st.stop()
                
                # Verificar se houve erros
                errors = [r for r in parsed_results if r and r.get("error")]
                if errors:
                    show_warning(f"{len(errors)} arquivo(s) tiveram erros no parsing. Continuando com os demais...")
                
                # Mostrar estatísticas de cache
                if cached_count > 0:
                    show_info(f"{cached_count} arquivo(s) carregado(s) do cache | {files_to_process} processado(s)")
                
                st.session_state.parsed_documents = parsed_results
                
                # ===== PRÉ-VISUALIZAÇÃO E DOWNLOAD DOS DOCUMENTOS PARSEADOS =====
                # Tabs para cada documento
                if parsed_results:
                    doc_tabs = st.tabs([doc.get('filename', f'Doc {i+1}') for i, doc in enumerate(parsed_results)])
                    
                    for idx, (tab, doc) in enumerate(zip(doc_tabs, parsed_results)):
                        with tab:
                            filename = doc.get('filename', f'Documento {idx+1}')
                            text = doc.get('text', '')
                            pages = doc.get('pages', 0)
                            length = doc.get('length', 0)
                            from_cache = doc.get('from_cache', False)
                            
                            # Informações do documento
                            col_info1, col_info2, col_info3 = st.columns(3)
                            with col_info1:
                                st.metric("Páginas", pages)
                            with col_info2:
                                st.metric("Caracteres", f"{length:,}")
                            with col_info3:
                                cache_badge = "Cache" if from_cache else "Novo"
                                st.markdown(f"**Status:** {cache_badge}")
                            
                            # Pré-visualização do texto
                            st.markdown("### 📖 Conteúdo Extraído:")
                            preview_text = text[:5000] if len(text) > 5000 else text
                            st.text_area(
                                "Pré-visualização (primeiros 5000 caracteres):",
                                value=preview_text,
                                height=300,
                                disabled=True,
                                key=f"preview_{idx}"
                            )
                            if len(text) > 5000:
                                st.caption(f"Mostrando apenas os primeiros 5000 caracteres de {len(text):,} totais")
                            
                            # Botões de download
                            st.markdown("### 💾 Download")
                            col_dl1, col_dl2 = st.columns(2)
                            
                            with col_dl1:
                                # Download como TXT
                                txt_content = text.encode('utf-8')
                                txt_filename = f"{Path(filename).stem}_extraido.txt"
                                st.download_button(
                                    label="Baixar como TXT",
                                    data=txt_content,
                                    file_name=txt_filename,
                                    mime="text/plain",
                                    width='stretch',
                                    key=f"download_txt_{idx}"
                                )
                            
                            with col_dl2:
                                # Download como JSON (completo)
                                json_data = json.dumps(doc, ensure_ascii=False, indent=2)
                                json_filename = f"{Path(filename).stem}_extraido.json"
                                st.download_button(
                                    label="Baixar como JSON",
                                    data=json_data,
                                    file_name=json_filename,
                                    mime="application/json",
                                    width='stretch',
                                    key=f"download_json_{idx}"
                                )
                    
                    # Botão para baixar todos os documentos em um único JSON
                    if st.button("Baixar Todos os Documentos (JSON)", width='stretch', type="primary"):
                        all_docs_json = json.dumps(parsed_results, ensure_ascii=False, indent=2)
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        all_filename = f"documentos_extraidos_{timestamp}.json"
                        
                        b64 = base64.b64encode(all_docs_json.encode('utf-8')).decode()
                        href = f'<a href="data:application/json;base64,{b64}" download="{all_filename}" id="download-all-link"></a>'
                        st.markdown(href, unsafe_allow_html=True)
                        st.markdown(
                            f"""
                            <script>
                                document.getElementById('download-all-link').click();
                            </script>
                            """,
                            unsafe_allow_html=True
                        )
                        show_info(f"Arquivo baixado: {all_filename}", use_toast=True)
                
                st.markdown("---")
                
                st.session_state.processing_status = "embedding"
                st.rerun()

            if st.session_state.get("processing_status") == "embedding":
                # Gerar memo_id único (se ainda não existe)
                if "memo_id" not in st.session_state:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    # Sanitizar memo_type para ChromaDB (remove acentos e caracteres especiais)
                    memo_type = st.session_state.get("memo_type", "tipo_desconhecido")
                    memo_type_slug = sanitize_memo_id(memo_type)
                    st.session_state.memo_id = f"{memo_type_slug}_{timestamp}"
                
                # Criar elementos de UI para progresso
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Callback para atualizar progresso na UI
                import time
                embedding_start_time = time.time()
                
                def update_progress(current: int, total: int, message: str):
                    """Atualiza barra de progresso e status text com ETA"""
                    progress = current / total if total > 0 else 0
                    progress_bar.progress(progress)
                    
                    # Calcular tempo decorrido e ETA
                    elapsed = time.time() - embedding_start_time
                    if current > 0 and elapsed > 0:
                        rate = current / elapsed  # progresso por segundo
                        remaining = total - current
                        eta_seconds = remaining / rate if rate > 0 else 0
                        
                        # Formatar tempo
                        def format_time(seconds):
                            if seconds < 60:
                                return f"{int(seconds)}s"
                            else:
                                mins = int(seconds // 60)
                                secs = int(seconds % 60)
                                return f"{mins}m {secs}s"
                        
                        elapsed_str = format_time(elapsed)
                        eta_str = format_time(eta_seconds)
                        status_text.text(f"{message} ({current}%) | Tempo: {elapsed_str} | ETA: {eta_str}")
                    else:
                        status_text.text(f"{message} ({current}%)")
                
                processor = DocumentProcessor()
                
                # Salvar no ChromaDB (passar documentos completos, não apenas textos)
                memo_id = processor.create_embeddings_with_chromadb(
                    parsed_docs=st.session_state.parsed_documents,
                    memo_id=st.session_state.memo_id,
                    memo_type=st.session_state.memo_type,
                    version=1,
                    progress_callback=update_progress
                )
                
                # Limpar elementos de progresso
                progress_bar.empty()
                status_text.empty()
                
                # Salvar memo_id no session_state
                st.session_state.document_embeddings = {
                    "memo_id": memo_id,
                    "vector_store": "chromadb"
                }
                
                show_success("Embeddings salvos com sucesso")
                
                st.session_state.processing_status = "extracting"
                st.rerun()

            if st.session_state.processing_status == "extracting":
                # Criar barra de progresso e status text
                progress_bar = st.progress(0)
                status_text = st.empty()
                import time
                extraction_start_time = time.time()
                status_text.text("Iniciando extração de fatos...")
                progress_bar.progress(0.1)
                
                processor = DocumentProcessor()
                
                # Obter número de seções a extrair para mostrar progresso
                from facts_config import get_sections_for_memo_type
                sections_to_extract = get_sections_for_memo_type(st.session_state.memo_type)
                total_sections = len(sections_to_extract)
                
                # Atualizar status durante extração (aproximado, já que é paralelo)
                status_text.text(f"Extraindo seções...")
                progress_bar.progress(0.3)
                
                # Extração paralela de todos os facts
                with st.spinner("Extraindo fatos dos documentos..."):
                    extracted = processor.extract_all_facts(
                        st.session_state.parsed_documents,
                        st.session_state.memo_type,
                        st.session_state.document_embeddings
                    )
                
                # Calcular tempo decorrido
                elapsed = time.time() - extraction_start_time
                def format_time(seconds):
                    if seconds < 60:
                        return f"{int(seconds)}s"
                    else:
                        mins = int(seconds // 60)
                        secs = int(seconds % 60)
                        return f"{mins}m {secs}s"
                
                # Atualizar progresso quando extração terminar
                progress_bar.progress(0.9)
                status_text.text(f"Extração concluída em {format_time(elapsed)}! Processando resultados...")
                
                st.session_state.extracted_facts = extracted
                st.session_state.facts_edited = {}
                
                # Preencher tabela DRE automaticamente se configurada
                if (st.session_state.get("memo_type") == "Short Memo - Co-investimento (Search Fund)" and
                    st.session_state.get("dre_table_generator") is not None):
                    try:
                        generator = st.session_state.dre_table_generator
                        generator = fill_dre_table_from_documents(
                            st.session_state.parsed_documents,
                            generator
                        )
                        st.session_state.dre_table_generator = generator
                        logger.info("Tabela DRE preenchida automaticamente após extração")
                    except Exception as e:
                        logger.error(f"Erro ao preencher tabela DRE automaticamente: {e}")
                
                filled_count = 0
                for section, facts in extracted.items():
                    st.session_state.facts_edited[section] = {
                        field_key: field_value
                        for field_key, field_value in facts.items()
                        if field_value and str(field_value).lower() != "null"
                    }
                    filled_count += len(st.session_state.facts_edited[section])
                
                # POPULAR DIRETAMENTE AS KEYS DOS WIDGETS PARA APARECER NOS CAMPOS
                # Usar safe_str_conversion para garantir tipos compatíveis com widgets
                for section, facts in st.session_state.facts_edited.items():
                    for field_key, field_value in facts.items():
                        widget_key = f"input_{section}.{field_key}"
                        
                        # Heurística simples: campos com "_mm", "_pct", "_years", "count" são numéricos
                        is_numeric_field = any(suffix in field_key for suffix in ["_mm", "_pct", "_years", "_count", "_ratio", "moic", "irr", "multiple", "stake", "leverage", "margin", "cagr"])
                        
                        # Converter para tipo apropriado
                        if isinstance(field_value, (int, float)):
                            # ✅ Se já é número, manter como número (nunca converter para string)
                            st.session_state[widget_key] = float(field_value)
                        elif is_numeric_field and isinstance(field_value, str):
                            # Tentar converter string numérica
                            try:
                                cleaned = field_value.replace("M", "").replace("$", "").replace(",", ".").replace("%", "").strip()
                                st.session_state[widget_key] = float(cleaned) if cleaned else 0.0
                            except (ValueError, TypeError):
                                # Se falhar, usar como string
                                st.session_state[widget_key] = safe_str_conversion(field_value)
                        else:
                            # Para text_input/text_area, usar safe_str_conversion
                            st.session_state[widget_key] = safe_str_conversion(field_value)
                
                # Limpar barra de progresso e status text
                progress_bar.empty()
                status_text.empty()
                
                # Mostrar resumo da extração
                total_fields = sum(len(facts) for facts in extracted.values())
                
                show_success(f"Extração concluída! {filled_count}/{total_fields} campos preenchidos")
                st.session_state.processing_status = "ready"
                st.rerun()
        
            if st.session_state.processing_status == "ready":
                show_success("Documentos processados e fatos extraídos!")
                
                # ===== PRÉ-VISUALIZAÇÃO E DOWNLOAD DOS DOCUMENTOS PARSEADOS =====
                with st.expander("Ver e Baixar Documentos Extraídos", expanded=False):
                    parsed_docs = st.session_state.get("parsed_documents", [])
                    
                    if parsed_docs:
                        # Tabs para cada documento
                        doc_tabs = st.tabs([f"{doc.get('filename', f'Doc {i+1}')}" for i, doc in enumerate(parsed_docs)])
                    
                    for idx, (tab, doc) in enumerate(zip(doc_tabs, parsed_docs)):
                        with tab:
                            filename = doc.get('filename', f'Documento {idx+1}')
                            text = doc.get('text', '')
                            pages = doc.get('pages', 0)
                            length = doc.get('length', 0)
                            from_cache = doc.get('from_cache', False)
                            
                            # Informações do documento
                            col_info1, col_info2, col_info3 = st.columns(3)
                            with col_info1:
                                st.metric("Páginas", pages)
                            with col_info2:
                                st.metric("Caracteres", f"{length:,}")
                            with col_info3:
                                cache_badge = "Cache" if from_cache else "Novo"
                                st.markdown(f"**Status:** {cache_badge}")
                            
                            # Pré-visualização do texto
                            st.markdown("### Conteúdo Extraído:")
                            preview_text = text[:5000] if len(text) > 5000 else text
                            st.text_area(
                                "Pré-visualização (primeiros 5000 caracteres):",
                                value=preview_text,
                                height=300,
                                disabled=True,
                                key=f"preview_ready_{idx}"
                            )
                            if len(text) > 5000:
                                st.caption(f"Mostrando apenas os primeiros 5000 caracteres de {len(text):,} totais")
                            
                            # Botões de download
                            st.markdown("### Download")
                            col_dl1, col_dl2 = st.columns(2)
                            
                            with col_dl1:
                                # Download como TXT
                                txt_content = text.encode('utf-8')
                                txt_filename = f"{Path(filename).stem}_extraido.txt"
                                st.download_button(
                                    label="Baixar como TXT",
                                    data=txt_content,
                                    file_name=txt_filename,
                                    mime="text/plain",
                                    width='stretch',
                                    key=f"download_txt_ready_{idx}"
                                )
                            
                            with col_dl2:
                                # Download como JSON (completo)
                                json_data = json.dumps(doc, ensure_ascii=False, indent=2)
                                json_filename = f"{Path(filename).stem}_extraido.json"
                                st.download_button(
                                    label="Baixar como JSON",
                                    data=json_data,
                                    file_name=json_filename,
                                    mime="application/json",
                                    width='stretch',
                                    key=f"download_json_ready_{idx}"
                                )
                    
                    # Botão para baixar todos os documentos em um único JSON
                    if st.button("Baixar Todos os Documentos (JSON)", width='stretch', type="primary", key="download_all_ready"):
                        all_docs_json = json.dumps(parsed_docs, ensure_ascii=False, indent=2)
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        all_filename = f"documentos_extraidos_{timestamp}.json"
                        
                        b64 = base64.b64encode(all_docs_json.encode('utf-8')).decode()
                        href = f'<a href="data:application/json;base64,{b64}" download="{all_filename}" id="download-all-ready-link"></a>'
                        st.markdown(href, unsafe_allow_html=True)
                        st.markdown(
                            f"""
                            <script>
                                document.getElementById('download-all-ready-link').click();
                            </script>
                            """,
                            unsafe_allow_html=True
                        )
                        show_info(f"Arquivo baixado: {all_filename}", use_toast=True)
                    else:
                        show_info("Nenhum documento parseado disponível.")
                
                # DEBUG VISUAL
                with st.expander("DEBUG: Ver dados extraídos"):
                    st.markdown("### Dados retornados pela IA:")
                    st.json(st.session_state.extracted_facts)
                    
                    st.markdown("### Dados em facts_edited:")
                    st.json(st.session_state.facts_edited)
                
                # Mostrar resumo detalhado
                with st.expander("Resumo da Extração"):
                    for section, facts in st.session_state.extracted_facts.items():
                        st.markdown(f"**{section}**")
                        filled = [k for k, v in facts.items() if v not in (None, "", "null")]
                        st.caption(f"{len(filled)}/{len(facts)} campos preenchidos")
                        if filled:
                            for field in filled:
                                st.caption(f"  ✓ {field}: {facts[field]}")
                
                if st.button("Processar Novos Documentos", width='stretch'):
                    st.session_state.processing_status = "idle"
                    st.session_state.parsed_documents = []
                    st.session_state.document_embeddings = None
                    st.rerun()

    # Exibir tabela DRE após processamento completo (status ready)
    if (st.session_state.get("memo_type") == "Short Memo - Co-investimento (Search Fund)" and
        st.session_state.get("processing_status") == "ready" and
        st.session_state.get("dre_table_generator") is not None):
        render_dre_table_inputs(show_table=True)
    
    # Seção de Fatos Extraídos (aparece apenas após processamento)
    if st.session_state.processing_status == "ready":
        st.header("Fatos Extraídos do Documento")
        st.info(
"""
Os box selecionados são preenchidos automaticamente. Os boxes não selecionados podem ser hábilitados manualmente em caso de necessidade.
Caso a informação não tenha sido encontrada insira o valor diretamente (ex: 15%) ou desabilite o box.
"""
)
        # Tabs diferentes para Short Memo - Primário (investimento em fundos)
        if st.session_state.memo_type == "Short Memo - Primário":
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "Gestora",
                "Fundo", 
                "Estratégia",
                "Contexto Spectra",
                "Opiniões"
            ])
            
            with tab1:
                render_tab_gestora(st.session_state.memo_type)
            
            with tab2:
                render_tab_fundo(st.session_state.memo_type)
            
            with tab3:
                render_tab_estrategia_fundo(st.session_state.memo_type)
            
            with tab4:
                render_tab_spectra_context(st.session_state.memo_type)
            
            with tab5:
                render_tab_opinioes(st.session_state.memo_type)
        
        else:
            # Tabs padrão para outros tipos de memo
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "Identificação", 
                "Transação", 
                "Financials e Projeções", 
                "Retornos",
                "Qualitativo"
            ])
            
            with tab1:
                render_tab_identification(st.session_state.memo_type)

            with tab2:
                render_tab_transaction(st.session_state.memo_type)
            
            with tab3:
                render_tab_financials(st.session_state.memo_type)
            
            with tab4:
                render_tab_returns(st.session_state.memo_type)
            
            with tab5:
                render_tab_qualitative(st.session_state.memo_type)
    
    # SEÇÃO: GERAR MEMORANDO PROFISSIONAL COM IA
    if st.session_state.processing_status == "ready":
        st.subheader("Gerar Memorando")
        
        col1, col2 = st.columns(2)
        
        with col1:
            temperature = st.slider(
                "Criatividade",
                min_value=0.0,
                max_value=1.0,
                value=0.3,
                step=0.1,
                help="0.0 = mais conservador e preciso | 1.0 = mais criativo"
            )
        
        with col2:
            # Preparar opções de modelo para o selectbox
            model_options = list(AVAILABLE_MODELS.keys())
            model_display_names = [get_model_display_name(model_id) for model_id in model_options]
            
            # Obter índice do modelo atual
            current_model = st.session_state.get("selected_model", get_default_model())
            current_index = model_options.index(current_model) if current_model in model_options else 0
            
            selected_model_display = st.selectbox(
                "Modelo de IA",
                options=model_display_names,
                index=current_index,
                key="model_selectbox",
                help=AVAILABLE_MODELS.get(current_model, AVAILABLE_MODELS[model_options[0]]).description
            )
            
            # Atualizar session_state com o ID do modelo selecionado
            selected_model_index = model_display_names.index(selected_model_display)
            selected_model_id = model_options[selected_model_index]
            st.session_state.selected_model = selected_model_id
            
            # Atualizar help text dinamicamente (usando o modelo selecionado)
            if selected_model_id in AVAILABLE_MODELS:
                model_info = AVAILABLE_MODELS[selected_model_id]
                st.caption(f"ℹ️ {model_info.description}")
        
        if st.button(
            "Gerar Memorando",
            width='stretch',
            type="primary",
            help="Usar IA + LangGraph + RAG na biblioteca para gerar todas as seções"
        ):
                # UI melhorada: mostra status de carregamento e tempo decorrido
                import time
                start_time = time.time()
                
                with st.status("Gerando memorando...", expanded=True, state="running") as status:
                    st.caption("Estimativa: 30-60 segundos")
                    
                    try:
                        memo_type = st.session_state.memo_type
                        generated = {}
                        total_quality = 0
                        total_examples = 0
                        
                        # FILTRAR facts desabilitados ANTES de gerar
                        filtered_facts = filter_disabled_facts(
                            st.session_state.facts_edited,
                            st.session_state.disabled_facts
                        )
                        
                        # Obter memo_id e processor para busca RAG no ChromaDB (se disponível)
                        memo_id = None
                        processor = None
                        if "document_embeddings" in st.session_state and st.session_state.document_embeddings:
                            memo_id = st.session_state.document_embeddings.get("memo_id")
                            if memo_id:
                                processor = DocumentProcessor()
                        
                        # ===== SEARCH FUND: Usa orchestrator especializado com estrutura fixa =====
                        if memo_type == "Short Memo - Co-investimento (Search Fund)":
                            from shortmemo.searchfund.orchestrator import generate_full_memo
                            
                            # Gerar todas as seções com a estrutura fixa do Search Fund
                            memo_sections = generate_full_memo(
                                facts=filtered_facts,
                                rag_context=None,  # Deprecated - usar memo_id/processor se disponível
                                memo_id=memo_id,
                                processor=processor,
                                model=st.session_state.selected_model,
                                temperature=temperature
                            )
                            
                            # Converter para formato esperado pelo app
                            q, e = _convert_memo_sections_to_format(memo_sections, generated)
                            total_quality += q
                            total_examples += e
                        
                        # ===== MEMO COMPLETO SEARCH FUND: Usa orchestrator completo com 9 seções =====
                        elif memo_type == "Memorando - Co-investimento (Search Fund)":
                            from memo.searchfund.orchestrator import generate_full_memo
                            
                            # Gerar todas as 9 seções com a estrutura fixa do Memo Completo
                            memo_sections = generate_full_memo(
                                facts=filtered_facts,
                                rag_context=None,  # Deprecated - usar memo_id/processor se disponível
                                memo_id=memo_id,
                                processor=processor,
                                model=st.session_state.selected_model,
                                temperature=temperature
                            )
                            
                            # Converter para formato esperado pelo app
                            q, e = _convert_memo_sections_to_format(memo_sections, generated)
                            total_quality += q
                            total_examples += e
                        
                        # ===== GESTORA: Usa orchestrator especializado com estrutura fixa =====
                        elif memo_type == "Short Memo - Co-investimento (Gestora)":
                            from shortmemo.gestora.orchestrator import generate_full_memo
                            
                            # Gerar todas as seções com a estrutura fixa da Gestora
                            memo_sections = generate_full_memo(
                                facts=filtered_facts,
                                rag_context=None,  # Deprecated - usar memo_id/processor se disponível
                                memo_id=memo_id,
                                processor=processor,
                                model=st.session_state.selected_model,
                                temperature=temperature
                            )
                            
                            # Converter para formato esperado pelo app
                            q, e = _convert_memo_sections_to_format(memo_sections, generated)
                            total_quality += q
                            total_examples += e
                        
                        # ===== PRIMÁRIO: Usa orchestrator especializado com estrutura fixa =====
                        elif memo_type == "Short Memo - Primário":
                            from shortmemo.primario.orchestrator import generate_full_memo
                            
                            # Gerar todas as seções com a estrutura fixa do Primário
                            memo_sections = generate_full_memo(
                                facts=filtered_facts,
                                rag_context=None,  # Deprecated - usar memo_id/processor se disponível
                                memo_id=memo_id,
                                processor=processor,
                                model=st.session_state.selected_model,
                                temperature=temperature
                            )
                            
                            # Converter para formato esperado pelo app
                            q, e = _convert_memo_sections_to_format(memo_sections, generated)
                            total_quality += q
                            total_examples += e
                        
                        # ===== SECUNDÁRIO: Usa orchestrator especializado com estrutura fixa =====
                        elif memo_type == "Short Memo - Secundário":
                            from shortmemo.secundario.orchestrator import generate_full_memo
                            
                            # Gerar todas as seções com a estrutura fixa do Secundário
                            memo_sections = generate_full_memo(
                                facts=filtered_facts,
                                rag_context=None,  # Deprecated - usar memo_id/processor se disponível
                                memo_id=memo_id,
                                processor=processor,
                                model=st.session_state.selected_model,
                                temperature=temperature
                            )
                            
                            # Converter para formato esperado pelo app
                            q, e = _convert_memo_sections_to_format(memo_sections, generated)
                            total_quality += q
                            total_examples += e
                        
                        # ===== OUTROS TIPOS: Usa orchestrator genérico =====
                        else:
                            from core.generation_orchestrator import MemoGenerationOrchestrator
                            from core.memo_generator import SECTION_MAPPING
                            
                            orchestrator = MemoGenerationOrchestrator(
                                model=st.session_state.selected_model,
                                temperature=temperature,
                                max_retries=2
                            )
                            
                            # Gerar cada seção
                            for fact_key, config in SECTION_MAPPING.items():
                                section_title = config["title"]
                                section_facts = filtered_facts.get(fact_key, {})
                                
                                if section_facts:  # Só gerar se tiver facts
                                    result = orchestrator.generate_section_sync(
                                        section_name=section_title,
                                        facts=section_facts,
                                        memo_type=st.session_state.memo_type,
                                        temperature=temperature
                                    )
                                    
                                    generated[section_title] = result
                                    total_quality += result.get("quality_score", 0)
                                    total_examples += result.get("examples_used", 0)
                        
                        # Adicionar seções geradas à sidebar
                        for section_title, data in generated.items():
                            if section_title not in st.session_state.custom_fields:
                                st.session_state.custom_fields.append(section_title)
                            
                            st.session_state.field_paragraphs[section_title] = data["paragraphs"]
                        
                        # Calcular tempo total
                        elapsed_time = time.time() - start_time
                        
                        # Atualizar status para completo
                        status.update(
                            label=f"Memorando gerado com sucesso em {elapsed_time:.0f}s",
                            state="complete",
                            expanded=False
                        )
                        
                        # Feedback com métricas
                        avg_quality = total_quality / len(generated) if generated else 0
                        show_info(f"{len(generated)} seções geradas | Qualidade: {avg_quality:.0f}/100 | Exemplos: {total_examples}", use_toast=True)
                        st.rerun()
                        
                    except Exception as e:
                        elapsed_time = time.time() - start_time
                        status.update(
                            label=f"Erro ao gerar memorando (após {elapsed_time:.0f}s)",
                            state="error",
                            expanded=False
                        )
                        show_error("Erro ao gerar memorando", details=traceback.format_exc())

# Página do Editor de Campo Personalizado
elif st.session_state.current_page == "field_editor":

    # Botão de voltar
    if st.button("← Voltar", type="secondary"):
        navigate_to_home()
        st.rerun()

    st.title(f"{st.session_state.selected_field}")

    field_name = st.session_state.selected_field

    # Garantir que o campo existe no dicionário
    if field_name not in st.session_state.field_paragraphs:
        st.session_state.field_paragraphs[field_name] = [""]

    # Inicializar parágrafo focado se não existir
    focused_para_key = f"focused_paragraph_{field_name}"
    if focused_para_key not in st.session_state:
        st.session_state[focused_para_key] = 0  # Primeiro parágrafo por padrão

    # Layout de duas colunas: parágrafos à esquerda (60%), chat fixo à direita (40%)
    col_left, col_right = st.columns([3, 2], gap="large")

    # COLUNA ESQUERDA: Parágrafos
    with col_left:
        # Renderizar cada parágrafo com estilo Jupyter
        paragraphs = st.session_state.field_paragraphs[field_name]

        for idx, paragraph_content in enumerate(paragraphs):

            # Cabeçalho do parágrafo
            col_num, col_arrows, col_controls = st.columns([5, 1, 2])

            with col_num:
                # Indicador visual se está focado
                is_focused = st.session_state.get(focused_para_key, 0) == idx
                focus_marker = "**" if is_focused else ""
                end_marker = "**" if is_focused else ""
                st.markdown(f"### {focus_marker}Parágrafo {idx + 1}{end_marker}")

            with col_arrows:
                col_up, col_down = st.columns(2)
                with col_up:
                    if st.button("↑", key=f"para_up_{field_name}_{idx}", help="Mover parágrafo para cima", disabled=(idx == 0), width='stretch'):
                        # IMPORTANTE: Sincronizar valor atual ANTES de mover
                        version_key = f"{field_name}_{idx}"
                        widget_key = f"paragraph_{field_name}_{idx}_v{st.session_state.paragraph_versions.get(version_key, 0)}"
                        st.session_state.field_paragraphs[field_name][idx] = st.session_state.get(widget_key, paragraph_content)
                        move_paragraph_up(field_name, idx)
                        st.rerun()
                with col_down:
                    if st.button("↓", key=f"para_down_{field_name}_{idx}", help="Mover parágrafo para baixo", disabled=(idx == len(paragraphs) - 1), width='stretch'):
                        # IMPORTANTE: Sincronizar valor atual ANTES de mover
                        version_key = f"{field_name}_{idx}"
                        widget_key = f"paragraph_{field_name}_{idx}_v{st.session_state.paragraph_versions.get(version_key, 0)}"
                        st.session_state.field_paragraphs[field_name][idx] = st.session_state.get(widget_key, paragraph_content)
                        move_paragraph_down(field_name, idx)
                        st.rerun()

            with col_controls:
                # Botão de deletar parágrafo
                if len(paragraphs) > 1:
                    delete_para_key = f"del_para_{field_name}_{idx}"
                    confirm_para_key = f"confirm_delete_paragraph_{field_name}_{idx}"
                    
                    # Verificar se já está confirmando
                    if st.session_state.get(confirm_para_key) == idx:
                        col_confirm, col_cancel = st.columns(2)
                        with col_confirm:
                            if st.button("Confirmar", key=f"confirm_para_{field_name}_{idx}", type="primary", help="Confirmar exclusão", width='stretch'):
                                # IMPORTANTE: Sincronizar valor atual ANTES de deletar
                                version_key = f"{field_name}_{idx}"
                                widget_key = f"paragraph_{field_name}_{idx}_v{st.session_state.paragraph_versions.get(version_key, 0)}"
                                st.session_state.field_paragraphs[field_name][idx] = st.session_state.get(widget_key, paragraph_content)
                                delete_paragraph(field_name, idx)
                                st.session_state[confirm_para_key] = None
                                st.rerun()
                        with col_cancel:
                            if st.button("Cancelar", key=f"cancel_para_{field_name}_{idx}", help="Cancelar", width='stretch'):
                                st.session_state[confirm_para_key] = None
                                st.rerun()
                    else:
                        if st.button("X", key=delete_para_key, help="Deletar parágrafo", width='stretch'):
                            st.session_state[confirm_para_key] = idx
                            st.rerun()

            # Campo de texto do parágrafo (com key versionada para forçar atualização visual)
            version_key = f"{field_name}_{idx}"
            if version_key not in st.session_state.paragraph_versions:
                st.session_state.paragraph_versions[version_key] = 0
            
            widget_key = f"paragraph_{field_name}_{idx}_v{st.session_state.paragraph_versions[version_key]}"
            
            # Container com estilo se focado
            is_focused = st.session_state.get(focused_para_key, 0) == idx
            if is_focused:
                st.markdown('<div class="focused-paragraph">', unsafe_allow_html=True)
            
            paragraph_text = st.text_area(
                "Conteúdo:",
                value=paragraph_content,
                height=180,
                key=widget_key,
                placeholder=f"Digite o conteúdo do parágrafo {idx + 1}...",
                label_visibility="collapsed"
            )
            
            if is_focused:
                st.markdown('</div>', unsafe_allow_html=True)

            # Atualizar o conteúdo do parágrafo
            st.session_state.field_paragraphs[field_name][idx] = paragraph_text

            # Botões de ação
            col_btn1, col_btn2 = st.columns([1, 1])

            with col_btn1:
                # Botão para focar neste parágrafo (destacar visualmente se está focado)
                is_focused = st.session_state.get(focused_para_key, 0) == idx
                button_label = "Focado" if is_focused else "Focar"
                button_type = "primary" if is_focused else "secondary"
                
                if st.button(
                    button_label,
                    key=f"focus_{field_name}_{idx}",
                    help="Focar neste parágrafo para edição com IA",
                    width='stretch',
                    type=button_type,
                    disabled=is_focused
                ):
                    # IMPORTANTE: Salvar texto atual antes de focar
                    version_key = f"{field_name}_{idx}"
                    widget_key = f"paragraph_{field_name}_{idx}_v{st.session_state.paragraph_versions.get(version_key, 0)}"
                    st.session_state.field_paragraphs[field_name][idx] = st.session_state.get(widget_key, paragraph_content)
                    
                    # Salvar parágrafo original quando focado pela primeira vez
                    original_para_key = f"original_paragraph_{field_name}_{idx}"
                    if original_para_key not in st.session_state:
                        st.session_state[original_para_key] = paragraph_content
                    
                    st.session_state[focused_para_key] = idx
                    st.rerun()

            with col_btn2:
                if st.button(
                    "Adicionar Abaixo",
                    key=f"add_para_{field_name}_{idx}",
                    help="Adicionar parágrafo abaixo",
                    width='stretch'
                ):
                    # IMPORTANTE: Salvar texto atual antes de adicionar novo parágrafo
                    version_key = f"{field_name}_{idx}"
                    widget_key = f"paragraph_{field_name}_{idx}_v{st.session_state.paragraph_versions.get(version_key, 0)}"
                    st.session_state.field_paragraphs[field_name][idx] = st.session_state.get(widget_key, paragraph_content)
                    add_paragraph(field_name, idx)
                    # Rerun necessário para mostrar novo parágrafo
                    st.rerun()

            # Separador visual entre parágrafos
            st.markdown('<div class="paragraph-separator"></div>', unsafe_allow_html=True)

    # COLUNA DIREITA: Chat fixo
    with col_right:
        from chat import render_fixed_chat_panel
        
        # Obter dados necessários
        facts = st.session_state.get("facts_edited", {})
        memo_type = st.session_state.get("memo_type", "")
        
        # Obter memo_id se disponível (para filtrar busca RAG)
        memo_id = None
        if "memo_id" in st.session_state:
            memo_id = st.session_state.memo_id
        elif "document_embeddings" in st.session_state and st.session_state.document_embeddings:
            memo_id = st.session_state.document_embeddings.get("memo_id")
        
        # Obter parágrafo focado
        focused_idx = st.session_state.get(focused_para_key, 0)
        if focused_idx >= len(paragraphs):
            focused_idx = 0
            st.session_state[focused_para_key] = 0
        
        current_para = paragraphs[focused_idx] if paragraphs else ""
        
        # Obter TODOS os parágrafos da seção para contexto
        all_section_paragraphs = st.session_state.field_paragraphs.get(field_name, [])
        
        # Renderizar chat fixo
        render_fixed_chat_panel(
            field_name=field_name,
            paragraph_idx=focused_idx,
            current_paragraph=current_para,
            all_section_paragraphs=all_section_paragraphs,
            facts=facts,
            memo_type=memo_type,
            memo_id=memo_id
        )


# Página de Histórico de Memos
elif st.session_state.current_page == "memo_history":
    from history.history_manager import MemoHistoryManager
    
    # Botão de voltar
    if st.button("← Voltar", type="secondary"):
        navigate_to_home()
        st.rerun()
    
    st.title("Histórico de Memos")
    st.markdown("Memos salvos anteriormente. Carregue para editar ou exporte novamente.")
    
    history_manager = MemoHistoryManager()
    
    # Estatísticas
    stats = history_manager.get_statistics()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total de Memos", stats["total_memos"])
    
    # Breakdown por tipo
    if stats["by_type"]:
        st.markdown("**Por Tipo:**")
        type_cols = st.columns(len(stats["by_type"]))
        for idx, (memo_type, count) in enumerate(stats["by_type"].items()):
            with type_cols[idx]:
                st.metric(memo_type.replace("Short Memo - ", ""), count)
    
    # Obter lista de memos
    memos = history_manager.list_memos()
    
    st.subheader(f"Histórico de Memorandos ({len(memos)})")
    
    if not memos:
        st.info("Nenhum memo encontrado. Ajuste os filtros ou salve novos memos.")
    else:
        # Listar memos
        for memo in memos:
            # Usar memo_name se disponível, senão usar company_name - memo_type
            display_name = memo.get("memo_name") or f"{memo['company_name']} - {memo['memo_type']}"
            
            with st.expander(
                f"**{display_name}** | {memo['saved_at'][:10]}"
            ):
               
                # Ações
                col_a1, col_a2, col_a3 = st.columns(3)
                
                with col_a1:
                    if st.button("Carregar", key=f"load_{memo['id']}", width='stretch', type="primary"):
                        # Carregar memo completo
                        full_memo = history_manager.load_memo(memo['id'])
                        
                        if full_memo:
                            # Restaurar session_state
                            st.session_state.memo_type = full_memo["memo_type"]
                            
                            # Reconstruir custom_fields e field_paragraphs
                            st.session_state.custom_fields = []
                            st.session_state.field_paragraphs = {}
                            
                            for section in full_memo.get("sections", []):
                                section_name = section["section_name"]
                                paragraphs = section["paragraphs"]
                                
                                st.session_state.custom_fields.append(section_name)
                                st.session_state.field_paragraphs[section_name] = paragraphs
                            
                            # Restaurar facts
                            st.session_state.facts_edited = full_memo.get("facts_snapshot", {})
                            
                            # Salvar ID do memo carregado
                            st.session_state.loaded_memo_id = memo["id"]
                            
                            show_success(f"Memo '{memo['company_name']}' carregado!")
                            st.session_state.current_page = "home"
                            st.rerun()
                        else:
                            show_error("Erro ao carregar memo")
                
                with col_a2:
                    # Cache key para DOCX gerado
                    docx_cache_key = f"docx_cache_{memo['id']}"
                    
                    # Verificar se já está em cache
                    if docx_cache_key not in st.session_state:
                        # Gerar DOCX apenas quando necessário
                        try:
                            full_memo = history_manager.load_memo(memo['id'])
                            
                            if full_memo:
                                # Reconstruir estrutura para export
                                custom_fields = [s["section_name"] for s in full_memo["sections"]]
                                field_paragraphs = {
                                    s["section_name"]: s["paragraphs"] 
                                    for s in full_memo["sections"]
                                }
                                
                                # Gerar DOCX
                                docx_bytes = export_memo_to_docx(
                                    memo_type=full_memo["memo_type"],
                                    custom_fields=custom_fields,
                                    field_paragraphs=field_paragraphs
                                )
                                
                                # Ler bytes
                                docx_bytes.seek(0)
                                docx_data = docx_bytes.read()
                                
                                # Nome do arquivo
                                company_clean = memo['company_name'].replace(" ", "_").replace("/", "_")
                                filename = f"{company_clean}_{memo['saved_at'][:10]}.docx"
                                
                                # Salvar em cache
                                st.session_state[docx_cache_key] = {
                                    "data": docx_data,
                                    "filename": filename
                                }
                            else:
                                show_error("Erro ao carregar memo para exportação")
                                st.session_state[docx_cache_key] = None
                                
                        except Exception as e:
                            show_error("Erro ao exportar", details=str(e))
                            st.session_state[docx_cache_key] = None
                            with st.expander("Ver detalhes do erro"):
                                st.code(traceback.format_exc())
                    
                    # Mostrar botão de download se DOCX foi gerado
                    if st.session_state.get(docx_cache_key):
                        cached_docx = st.session_state[docx_cache_key]
                        st.download_button(
                            label="Exportar DOCX",
                            data=cached_docx["data"],
                            file_name=cached_docx["filename"],
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            width='stretch',
                            key=f"download_{memo['id']}",
                            type="secondary"
                        )
                
                with col_a3:
                    if st.button("X", key=f"delete_{memo['id']}", width='stretch'):
                        if history_manager.delete_memo(memo['id']):
                            show_success("Memo deletado!")
                            st.rerun()
                        else:
                            show_error("Erro ao deletar")

