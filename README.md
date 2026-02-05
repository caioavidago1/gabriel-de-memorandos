# 📊 Sistema de Geração de Memorandos de Investimento

---

## 📋 Índice

1. [Visão Geral](#-visão-geral)
2. [Arquitetura da Plataforma](#-arquitetura-da-plataforma)
3. [Fluxo Completo do Usuário](#-fluxo-completo-do-usuário)
4. [Parsing e Cache](#-parsing-e-cache)
5. [Processamento de Documentos e RAG](#-processamento-de-documentos-e-rag)
6. [Extração de Facts (LangGraph)](#-extração-de-facts-langgraph)
7. [Registry e Tipos de Memorando](#-registry-e-tipos-de-memorando)
8. [Geração de Memorandos](#-geração-de-memorandos)
9. [Facts: Visibilidade e Filtragem](#-facts-visibilidade-e-filtragem)
10. [Chat com RAG](#-chat-com-rag)
11. [Histórico e Exportação](#-histórico-e-exportação)
12. [Modelos de IA](#-modelos-de-ia)
13. [Tecnologias e Stack](#-tecnologias-e-stack)
14. [Instalação e Uso](#-instalação-e-uso)
15. [Configuração](#-configuração)
16. [Métricas](#-métricas)

---

## 🎯 Visão Geral

Sistema automatizado de geração de memorandos de investimento usando **agentes especializados** orquestrados via **LangGraph**. A plataforma processa documentos (CIMs, teasers, PDFs), extrai fatos estruturados e gera memorandos por tipo de investimento, com edição assistida por IA e exportação para Word.

### Tipos de Memo Suportados

| Tipo | Descrição |
|------|-----------|
| **Short Memo - Co-investimento (Search Fund)** | Investimentos diretos em empresas via search fund (6 seções fixas) |
| **Short Memo - Co-investimento (Gestora)** | Análise de fund managers / gestoras |
| **Short Memo - Primário** | Commitments em fundos de PE/VC (4 seções: Resumo, Gestora, Portfolio, Fundo) |
| **Memorando - Co-investimento (Search Fund)** | Memo completo com 9 seções (inclui Board/Cap Table, Projeções, Retornos, etc.) |

### Recursos Principais

- **Upload e parsing** de múltiplos PDFs (LlamaParse), com **cache** por hash para evitar reprocessamento
- **Chunking inteligente** com metadata (MarkdownChunker), **embeddings** (OpenAI) e armazenamento em **ChromaDB** por `memo_id`
- **Extração de facts** por tipo de memo via **LangGraph** (seções em paralelo, retry automático, schemas Pydantic)
- **Tabela DRE** (Histórico e Projeções) para tipos Search Fund e Gestora: parâmetros configuráveis, preenchimento automático a partir dos documentos
- **Geração de seções** por **orchestrators** específicos (estrutura fixa por tipo), com RAG por seção e validação/retry
- **Edição de parágrafos** com **chat RAG** por seção (perguntas sobre o documento, sugestões de texto)
- **Filtro de facts**: campos habilitados/desabilitados por tipo; apenas facts habilitados são enviados aos agentes
- **Histórico** de memos (salvar/carregar) e **exportação DOCX**
- **Múltiplos modelos** (OpenAI e Anthropic) configuráveis em `model_config.py`

---

## 🏗️ Arquitetura da Plataforma

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  app.py (Streamlit)                                                         │
│  - Páginas: home | field_editor | memo_history                               │
│  - Session state: memo_type, parsed_documents, document_embeddings,        │
│    extracted_facts, facts_edited, disabled_facts, custom_fields,            │
│    field_paragraphs, dre_table_generator, selected_model                    │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────┐    ┌─────────────────────┐   ┌──────────────────────┐
│ parser.py     │    │ core/                │   │ tipo_memorando/      │
│ LlamaParse    │    │ document_processor   │   │ registry.py          │
│ PDF → MD      │    │ ChromaDB, extract    │   │ MEMO_TYPE_TO_TIPO    │
└───────────────┘    │ extract_all_facts    │   │ get_fatos_config     │
                     └─────────────────────┘   │ uses_dre_table        │
        │                       │              └───────────┬───────────┘
        │                       │                          │
        ▼                       ▼                          ▼
┌───────────────┐    ┌─────────────────────┐   ┌──────────────────────┐
│ .cache/       │    │ core/               │   │ short_searchfund/     │
│ parsed_docs   │    │ langgraph_          │   │ short_gestora/         │
│ (hash → JSON) │    │ orchestrator        │   │ short_primario/       │
└───────────────┘    │ LangGraphExtractor  │   │ memo_searchfund/      │
                     │ ExtractionAgent     │   │ (orchestrator +       │
                     └─────────────────────┘   │  agents + fatos)      │
                                │              └──────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────┐    ┌─────────────────────┐   ┌──────────────────────┐
│ facts/        │    │ chat/               │   │ history/             │
│ filtering     │    │ RAGChatAgent        │   │ MemoHistoryManager   │
│ builder       │    │ ChromaDB            │   │ memo_history.json     │
└───────────────┘    └─────────────────────┘   └──────────────────────┘
                                │
                                ▼
                     ┌─────────────────────┐
                     │ docx_edit/formatter │
                     │ export_memo_to_docx │
                     └─────────────────────┘
```

- **Registry** (`tipo_memorando/registry.py`): mapeia o `memo_type` (string da UI) para a pasta do tipo (`short_searchfund`, `short_gestora`, etc.), fornece `get_fatos_config(memo_type)`, `get_fatos_module(memo_type)` e `uses_dre_table(memo_type)`.
- **Core**: parsing não fica no core; **DocumentProcessor** faz chunking, embeddings, ChromaDB e chama **LangGraphExtractor** para extração. **ExtractionAgent** (por seção) usa prompts e schemas do tipo.
- **Tipos**: cada tipo tem `fatos/` (config, extraction, prompts, render_tab_*), `agents/`, `orchestrator.py` (`generate_full_memo`) e, quando usa LangGraph, `langgraph_orchestrator.py` (herda de `_base/base_langgraph_orchestrator`).

---

## 🔄 Fluxo Completo do Usuário

1. **Home**  
   Usuário escolhe **Tipo de Memorando** e faz **upload** de um ou mais PDFs.

2. **Validações**  
   Máximo de arquivos e tamanho (ex.: 30 arquivos, 500 MB por arquivo, 5 GB total). Se o tipo usar DRE, é exibida a **configuração da tabela DRE** (ano referência, primeiro/último ano); o botão "Processar Documentos e Extrair Fatos" só aparece após confirmar os parâmetros.

3. **Parsing**  
   Para cada arquivo: calcula hash MD5; se existir cache em `.cache/parsed_documents/{hash}.json` (e não expirado, ex.: 30 dias), usa cache; senão, salva em `temp_uploads/`, chama `DocumentProcessor().parse_document()` (LlamaParse) e grava resultado no cache. Parsing pode ser **paralelo** (ex.: semáforo 4) com retry para rate limit. Resultados são reunidos em `st.session_state.parsed_documents`.

4. **Embedding**  
   Gera `memo_id` (ex.: `short_memo_co_investimento_search_fund_20250205_123456`). `DocumentProcessor.create_embeddings_with_chromadb()`: para cada documento, usa **MarkdownChunker** (chunk_size/overlap), gera embeddings (OpenAI `text-embedding-3-small`) e persiste no ChromaDB com metadata (memo_id, memo_type, source, etc.). Progresso/ETA via callback. `document_embeddings = { "memo_id": memo_id, "vector_store": "chromadb" }`.

5. **Extração de facts**  
   `processor.extract_all_facts(parsed_documents, memo_type, document_embeddings)`. Internamente: `extract_facts_parallel` → **LangGraphExtractor**. Texto combinado dos docs + `memo_type` + `embeddings_data`. O grafo: **extract_all_parallel** (seções do tipo em paralelo via `get_fatos_config(memo_type).get_sections_for_memo_type()` e **ExtractionAgent** por seção) → **validate_results** → **should_retry** (retry seletivo ou finalize). Resultado é um dict por seção (ex.: identification, transaction_structure, financials_history, saida, qualitative, opinioes; ou para Primário: gestora, fundo, estrategia, spectra_context, opinioes). Para "Memorando - Co-investimento (Search Fund)", após extração padrão pode haver **regeneração** com **TableExtractor** (projections_table, returns_table, board_cap_table).  
   Facts preenchem `extracted_facts` e `facts_edited`; widgets são populados com `safe_str_conversion`. Para tipos com DRE, a **tabela DRE** é preenchida automaticamente a partir dos documentos (`fill_dre_table_from_documents`). Status passa a **ready**.

6. **Fatos na UI**  
   Tabs por tipo: Primário tem Gestora, Fundo, Estratégia, Contexto Spectra, Opiniões; outros têm Identificação, Transação, Saída, Qualitativo. Campos têm **visibilidade** por tipo (FIELD_VISIBILITY em `tipo_memorando/_base/fatos/config.py` e sobrescritas por tipo). Checkboxes habilitam/desabilitam campos; desabilitados entram em `disabled_facts` (set de `section.field_key`).

7. **Gerar Memorando**  
   Usuário ajusta **Criatividade** (temperature) e **Modelo de IA**. Ao clicar "Gerar Memorando":  
   - Facts são filtrados: `filter_disabled_facts(facts_edited, disabled_facts)`.  
   - Se o tipo usar DRE e houver `dre_table_generator`, `filtered_facts["dre_table"] = dre_table_generator.to_dict()`.  
   - Por tipo, chama o **orchestrator** correspondente:  
     - Short Memo Search Fund → `tipo_memorando.short_searchfund.orchestrator.generate_full_memo()`  
     - Memorando Search Fund → `tipo_memorando.memo_searchfund.orchestrator.generate_full_memo()`  
     - Short Memo Gestora → `tipo_memorando.short_gestora.orchestrator.generate_full_memo()`  
     - Short Memo Primário → `tipo_memorando.short_primario.orchestrator.generate_full_memo()`  
   - Cada orchestrator usa **estrutura fixa** de seções e **LangGraph** (base em `_base/base_langgraph_orchestrator`): para cada seção, nó **prepare_section** (RAG no ChromaDB com query específica da seção), **generate_with_agent** (agente especializado com facts + RAG), **validate_output**, **should_retry** (retry/finalize), **finalize**.  
   - Seções geradas são convertidas para o formato do app (`paragraphs`, quality_score/examples_used placeholders) e adicionadas a `custom_fields` e `field_paragraphs`.

8. **Editor de Seção (field_editor)**  
   Sidebar lista seções; ao clicar numa seção, abre a página do editor com parágrafos à esquerda e **chat fixo** à direita. Parágrafos podem ser editados, reordenados, removidos ou novos adicionados. O **chat** usa **RAGChatAgent**: busca no ChromaDB por `memo_id`, usa facts como contexto e permite perguntas sobre o documento e sugestões para o parágrafo focado.

9. **Exportação e Histórico**  
   - **Gerar DOCX** (sidebar): `export_memo_to_docx(memo_type, custom_fields, field_paragraphs)` gera Word (capa Spectra, tipo, data, seções/parágrafos justificados, Calibri 12). Download via **Baixar DOCX**.  
   - **Salvar**: abre formulário com nome do memo (default: empresa + tipo); **MemoHistoryManager.save_memo()** persiste tipo, seções, parágrafos, facts_snapshot em `history/memo_history.json`.  
   - **Ver Histórico**: lista memos; para cada um, **Carregar** (restaura session_state), **Exportar DOCX** (gera e permite download), **Deletar**.

---

## 📄 Parsing e Cache

- **parser.py**: usa **LlamaParse** (LLAMA_CLOUD_API_KEY), `result_type="markdown"`, `language="pt"`, system prompt para documentos financeiros. Concatena páginas em um único texto com marcadores `=== PAGE i ===`. Retorna dict com `filename`, `text`, `length`, `pages`.
- **Cache**: `get_file_hash(file_content)` (MD5). Cache em `.cache/parsed_documents/{hash}.json` com `result`, `filename`, `cached_at`, `file_hash`. Cache expira em 30 dias. Em **app.py**, antes de parsear verifica `load_from_cache(file_hash)`; se hit, não salva em temp e não chama parser. Após parse bem-sucedido, `save_to_cache(file_hash, result, filename)`.

---

## 📚 Processamento de Documentos e RAG

- **DocumentProcessor** (`core/document_processor.py`):
  - **parse_document(path)**: delega para `parser.parse()`.
  - **chunk_text** / **create_embeddings**: chunking simples ou com metadata.
  - **create_embeddings_with_chromadb(parsed_docs, memo_id, memo_type, version, progress_callback)**: por documento, usa **MarkdownChunker** para `chunk_with_metadata`; gera embeddings em batches (50); persiste no **ChromaDB** (core/chromadb_store) com metadata (memo_id, source, etc.). Retorna `memo_id`.
  - **search_chromadb_chunks(memo_id, query, top_k, section)**: embedding da query, busca na collection filtrada por `memo_id`, opcionalmente por `section`; retorna lista de chunks com score e metadata.

- **MarkdownChunker** (`core/markdown_chunker.py`): preserva hierarquia (h1–h6), títulos, tabelas; gera chunks com metadata (section_title, section_level, has_table, full_path).

- **ChromaDB**: coleção persistente; documentos armazenados com embedding e metadata; queries por `memo_id` para isolar contexto de cada memo.

---

## 🔍 Extração de Facts (LangGraph)

- **LangGraphExtractor** (`core/langgraph_orchestrator.py`):
  - Grafo: **extract_all_parallel** → **validate_results** → **should_retry** (retry_failed_sections ou finalize) → **finalize** → END.
  - **extract_all_parallel**: obtém seções com `get_fatos_config(memo_type).get_sections_for_memo_type(memo_type)`; cria um **ExtractionAgent** por seção; executa `agent.extract(document_text, memo_type, embeddings_data)` em paralelo (asyncio.gather). Cada agente usa prompt e schema da seção (arquivos em `tipo_memorando/<tipo>/fatos/prompts/` e schemas em extraction/schemas).
  - **ExtractionAgent** (`core/extraction_agents.py`): carrega prompt do tipo, opcionalmente busca RAG (ChromaDB) se `embeddings_data` tiver memo_id, invoca LLM com structured output (Pydantic). Retorna dict de campos da seção.
  - **validate_results** / **retry_failed_sections**: valida preenchimento; seções com falha podem ser reexecutadas até `max_retries`.
  - **extract_all_facts** em DocumentProcessor: `asyncio.run(extract_facts_parallel(...))` → resultado por seção.

- **Memo Completo Search Fund**: após `extract_all_facts`, `regenerate_facts_for_memo_type` pode chamar **TableExtractor** para preencher projections_table, returns_table, board_cap_table (board_members, cap_table) se ausentes.

- **DRE**: tipos que usam DRE (Short Memo Search Fund, Short Memo Gestora, Memorando Search Fund) têm UI em `tipo_memorando/tabela/ui.py` (**render_dre_table_inputs**). Parâmetros (ano referência, primeiro ano histórico, último ano projeção) ficam em `st.session_state.dre_table_inputs_confirmed` e `dre_table_generator`. Após extração, **fill_dre_table_from_documents** preenche a tabela a partir dos documentos. O dict da DRE é enviado aos agentes como `filtered_facts["dre_table"]` na geração.

---

## 📁 Registry e Tipos de Memorando

- **registry.py**:
  - `MEMO_TYPE_TO_TIPO`: mapeia string da UI para pasta (`short_searchfund`, `short_gestora`, `short_primario`, `memo_searchfund`).
  - `uses_dre_table(memo_type)`: True para Search Fund (short e memo) e Gestora.
  - `get_fatos_config(memo_type)`: importa `tipo_memorando.<tipo>.fatos.config` e retorna o módulo.
  - `get_fatos_module(memo_type)`: importa `tipo_memorando.<tipo>.fatos` (para render_tab_* no app).
  - `get_prompts_path(memo_type, section)`: path para `fatos/prompts/<section>.txt`.

- Cada tipo em **tipo_memorando/** contém:
  - **fatos/**: `config.py` (SECTIONS, FIELD_VISIBILITY, get_sections_for_memo_type, get_relevant_fields_for_memo_type, get_field_count_for_memo_type), `extraction.py`, prompts em `prompts/*.txt`, e módulos de render (identificacao, transacao, saida, qualitativo, opinioes; ou gestora, fundo, estrategia, spectra_context para Primário).
  - **agents/**: um agente por seção do memo (ex.: IntroAgent, MercadoAgent, EmpresaAgent, FinancialsAgent, TransacaoAgent, PontosAprofundarAgent para short_searchfund).
  - **orchestrator.py**: função `generate_full_memo(facts, rag_context, memo_id, processor, model, temperature)` que instancia o LangGraph orchestrator do tipo, percorre a estrutura fixa, chama prepare → generate → validate → retry/finalize por seção e retorna `{ section_title: [paragraphs] }`.
  - **langgraph_orchestrator.py** (onde aplicável): herda de **BaseLangGraphOrchestrator** (`_base/base_langgraph_orchestrator`), define `fixed_structure` (dict section → agent) e `section_queries` (queries RAG por seção). Grafo: prepare_section (RAG ChromaDB) → generate_with_agent → validate_output → should_retry → retry_section ou finalize.

---

## ✍️ Geração de Memorandos

- **Orchestrators por tipo**: cada tipo tem estrutura fixa (ex.: 6 seções para Short Search Fund, 4 para Primário, 9 para Memo Search Fund). O orchestrator compila o grafo LangGraph e, para cada seção:
  1. **prepare_section**: se houver `memo_id` e `processor`, busca no ChromaDB com `section_queries[section_title]` e top_k (ex.: 10); coloca resultado em state como `section_rag_context`.
  2. **generate_with_agent**: chama `agent.set_llm(llm)` (se existir) e `agent.generate(facts, section_rag_context)`; o agente monta system/user prompt com facts (build_facts_section, format_facts_for_prompt) e RAG, invoca LLM, aplica formatação (ex.: números).
  3. **validate_output**: verifica texto não vazio, tamanho mínimo, ausência de mensagens de erro, número mínimo de parágrafos.
  4. **should_retry**: sem erros → finalize; com erros e retry_count < max_retries → retry_section; senão → finalize.
  5. **finalize**: divide texto em parágrafos, aplica formatação e retorna `{ section_title: [paragraphs] }`.

- **LLM**: todos os agentes usam **model_config.get_llm_for_agents(model, temperature)** (OpenAI ou Anthropic conforme cadastro). O modelo e a temperatura vêm da UI (selected_model, slider Criatividade).

- **Fallback**: se o tipo não for um dos quatro mapeados, o app usa **core/generation_orchestrator.MemoGenerationOrchestrator** e **SECTION_MAPPING** do core para gerar seção a seção (sem estrutura fixa por tipo).

---

## 🧩 Facts: Visibilidade e Filtragem

- **FIELD_VISIBILITY** (`tipo_memorando/_base/fatos/config.py` e sobrescritas por tipo): por seção e campo, define `"ALL"` ou lista de memo_types para os quais o campo é relevante. Na UI, ao selecionar tipo, **apply_auto_uncheck_for_memo_type** marca como desabilitados os campos não relevantes (adiciona `section.field_key` a `st.session_state.disabled_facts`).

- **filter_disabled_facts** (`facts/filtering.py`): antes de enviar facts aos orchestrators, remove entradas cujo `section.field_key` está em `disabled_facts` e valores vazios/nulos. Assim a IA não recebe campos desabilitados.

- **facts.builder** / **facts.utils**: `build_facts_section`, `format_facts_for_prompt`, `clean_facts`; helpers como `get_fact_safe`, `get_numeric_safe` para montar blocos de contexto nos prompts.

---

## 💬 Chat com RAG

- **ChatHandler** + **render_fixed_chat_panel** (`chat/ui_components.py`): no editor de seção, painel fixo à direita com histórico de mensagens e input. Ao enviar mensagem, usa **RAGChatAgent** (`chat/rag_chat_agent.py`).

- **RAGChatAgent**:
  - System prompt com **facts** formatados e instruções (responder com base em facts + documentos, citar fonte).
  - Se houver **memo_id**, busca no ChromaDB com a pergunta do usuário (top_k chunks); concatena chunks no contexto.
  - Histórico de mensagens (Human/AI) é enviado ao LLM para continuidade.
  - LLM via **get_llm_for_agents** (model_config); modelo pode ser o selecionado na UI (selected_model).

- Uso: usuário pode focar um parágrafo e pedir sugestões, resumos ou esclarecimentos com base nos documentos e facts.

---

## 📂 Histórico e Exportação

- **MemoHistoryManager** (`history/history_manager.py`): armazenamento em JSON (`history/memo_history.json`). Estrutura: lista de memos com id, memo_type, company_name, memo_name, saved_at, sections (section_name, paragraphs, generation_metadata), facts_snapshot, statistics. **save_memo**, **load_memo**, **list_memos**, **delete_memo**, **get_statistics**.

- **export_memo_to_docx** (`docx_edit/formatter.py`): recebe memo_type, custom_fields, field_paragraphs; cria Document (python-docx); capa com Spectra, tipo, mês/ano; para cada seção, título e parágrafos justificados (Calibri 12); remove markdown (**). Retorna BytesIO. Download no app usa session_state.docx_bytes e docx_filename.

- No histórico, **Exportar DOCX** gera o DOCX a partir do memo carregado (custom_fields/field_paragraphs reconstruídos) e opcionalmente cacheia em session_state por memo id para evitar regenerar a cada render.

---

## 🤖 Modelos de IA

- **model_config.py**:
  - **GerenciadorModelos.MODELOS_DISPONIVEIS**: dicionário de modelo_id → **ModeloConfig** (id, nome, provedor OPENAI/ANTHROPIC, descricao, max_tokens). Ex.: gpt-5.2, gpt-5.1, gpt-5-mini (OpenAI), claude-opus-4.5, claude-sonnet-4.5 (Anthropic).
  - **get_default_model()**: ex. `"claude-opus-4.5"`.
  - **get_llm_for_agents(model_id, temperature)**: retorna ChatOpenAI ou ChatAnthropic conforme ModeloConfig; fallback se provider não disponível.
  - **get_model_display_name(model_id)**: nome para exibição no selectbox.
  - **AVAILABLE_MODELS** = MODELOS_DISPONIVEIS para compatibilidade na UI (Gerar Memorando e modelo do chat).

Todos os agentes que produzem texto (orchestrators, RAG chat, generation_orchestrator) devem usar **get_llm_for_agents()** para manter provedor e parâmetros consistentes.

---

## 🔧 Tecnologias e Stack

```
┌─────────────────────────────────────────────┐
│  Frontend: Streamlit                         │
├─────────────────────────────────────────────┤
│  LLMs: OpenAI GPT-5.x / Anthropic Claude    │
│  Embeddings: text-embedding-3-small (1536d)  │
├─────────────────────────────────────────────┤
│  Orchestration: LangGraph + LangChain        │
│  Parsing: LlamaParse                         │
│  Validation: Pydantic 2.x                    │
│  Vector Store: ChromaDB (persistente)         │
│  Export: python-docx                         │
└─────────────────────────────────────────────┘
```

---

## 📦 Instalação e Uso

### Pré-requisitos

- Python 3.11+
- OpenAI API Key (e opcionalmente Anthropic para Claude)
- LlamaParse: LLAMA_CLOUD_API_KEY no .env

### Setup

```bash
# Clonar / entrar no repositório
cd gabriel-de-memorandos

# Ambiente virtual
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # Linux/Mac

# Dependências
pip install -r requirements.txt

# .env na raiz
# OPENAI_API_KEY=...
# LLAMA_CLOUD_API_KEY=...
# ANTHROPIC_API_KEY=...  # se usar Claude
```

### Executar

```bash
streamlit run app.py
```

Acessar: http://localhost:8501

### Workflow resumido

1. Escolher **Tipo de Memorando** e fazer upload de PDF(s). Se o tipo usar DRE, configurar parâmetros e confirmar.
2. Clicar em **Processar Documentos e Extrair Fatos**: parsing (com cache) → embedding → ChromaDB → extração de facts.
3. Revisar/editar **Fatos** nas tabs; habilitar/desabilitar campos conforme necessidade.
4. Ajustar **Criatividade** e **Modelo de IA** e clicar em **Gerar Memorando**.
5. Editar seções na sidebar (abrir seção → editor com parágrafos e chat RAG).
6. **Gerar DOCX** e **Baixar DOCX**; ou **Salvar** no histórico e depois **Ver Histórico** para carregar/exportar/deletar.

---

## ⚙️ Configuração

- **Visibilidade de campos**: `tipo_memorando/_base/fatos/config.py` (base) e `tipo_memorando/<tipo>/fatos/config.py` (sobrescritas). FIELD_VISIBILITY e funções get_sections_for_memo_type, get_relevant_fields_for_memo_type, get_field_count_for_memo_type.
- **Seções por tipo**: definidas em cada config (SECTIONS ou equivalente); o registry não define seções, apenas carrega o módulo config do tipo.
- **Modelos**: adicionar ou alterar em `model_config.py` (GerenciadorModelos.MODELOS_DISPONIVEIS e get_llm_for_agents para novo provedor se necessário).
- **ChromaDB**: path e configuração em core/chromadb_store (persistência).
- **Cache de parsing**: `.cache/parsed_documents`; expiração em 30 dias em app.py (load_from_cache).

---

## 📊 Métricas

- **Parsing**: tempo por documento varia (15–30 s típico sem cache); cache evita reprocessamento.
- **Embedding**: batches de 50 chunks; progresso com ETA na UI.
- **Extração**: seções em paralelo; 1–2 retries por seção em caso de falha.
- **Geração**: uma seção por vez no LangGraph (prepare → generate → validate → retry/finalize); tempo total depende do número de seções e do modelo.
- **RAG**: busca por memo_id no ChromaDB; top_k (ex.: 10) por seção ou por pergunta no chat.

---

## 📄 Licença

Propriedade de Spectra Investimentos.
