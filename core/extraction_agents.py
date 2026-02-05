import asyncio
import os
from typing import Dict, Any, Optional, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import json
from tipo_memorando.registry import get_fatos_config, get_fatos_module
from core.logger import get_logger
from core.extraction_schemas import get_schema_for_section

logger = get_logger(__name__)


def clean_extracted_value(field_key: str, value: Any) -> Any | None:
    """Limpa e converte valores extraídos"""
    if not value or value == "null":
        return None

    # Preservar listas e dicts (projections_table, returns_table, board_cap_table)
    if isinstance(value, (list, dict)):
        return value

    if field_key.endswith("_mm"):
        if isinstance(value, str):
            cleaned = value.replace("M", "").replace("$", "").replace(",", "").strip()
            return float(cleaned) if cleaned and cleaned.replace(".", "").replace("-", "").isdigit() else None
        return float(value) if value else None
    
    if "_pct" in field_key or "percentage" in field_key:
        if isinstance(value, str):
            cleaned = value.replace("%", "").replace(",", ".").strip()
            return float(cleaned) if cleaned and cleaned.replace(".", "").replace("-", "").isdigit() else None
        return float(value) if value else None
    
    if "year" in field_key:
        return int(value) if str(value).isdigit() else None
    
    if "multiple" in field_key:
        if isinstance(value, str):
            cleaned = value.replace("x", "").replace("X", "").replace(",", ".").strip()
            return float(cleaned) if cleaned and cleaned.replace(".", "").replace("-", "").isdigit() else None
        return float(value) if value else None
    
    if isinstance(value, (int, float)):
        return value
    
    return str(value).strip() if value else None


class ExtractionAgent:
    """Agente especializado para extrair uma seção específica"""
    
    def __init__(self, llm: ChatOpenAI, section_name: str):
        self.llm = llm
        self.section_name = section_name
        self.max_retries = 3
    
    async def extract(
        self, 
        text: str, 
        memo_type: str,
        embeddings_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Extrai facts de uma seção específica"""
        # Usar busca smart se embeddings_data tiver metadata
        if embeddings_data and "metadata" in embeddings_data:
            relevant_context = await self._get_relevant_context_smart(
                embeddings_data, 
                self.section_name
            )
        elif embeddings_data:
            relevant_context = await self._get_relevant_context(
                embeddings_data, 
                self.section_name
            )
        else:
            relevant_context = text

        # Seções que costumam estar no início do doc: incluir capa/header quando usamos busca por chunks
        if text and embeddings_data and self.section_name in ("identification", "gestora"):
            head = text[:10000].strip()
            if head:
                relevant_context = head + "\n\n---\n\n" + (relevant_context or "")
                logger.info(f"📄 {self.section_name}: início do documento (capa/header) incluído no contexto")

        # Módulo de extração do tipo (lógica completa: system message e prompt)
        fatos_module = get_fatos_module(memo_type)
        extraction = getattr(fatos_module, "extraction", None)
        self._extraction_module = extraction
        if extraction is None or not hasattr(extraction, "get_system_message") or not hasattr(extraction, "get_prompt"):
            logger.error(
                f"Módulo extraction do tipo não encontrado ou incompleto para '{memo_type}'. "
                f"Necessário: get_system_message(section, memo_type) e get_prompt(section, memo_type)."
            )
            return {}

        config = get_fatos_config(memo_type)
        relevant_fields = self._get_relevant_fields(memo_type)
        prompt = extraction.get_prompt(self.section_name, memo_type)
        
        # Log economia de tokens
        total_fields_section = len(getattr(config, "FIELD_VISIBILITY", {}).get(self.section_name, {}))
        fields_to_extract = len(relevant_fields)
        fields_skipped = total_fields_section - fields_to_extract
        
        if fields_skipped > 0:
            logger.info(
                f"🎯 Otimização para '{memo_type}' | "
                f"Seção '{self.section_name}': "
                f"Extraindo {fields_to_extract}/{total_fields_section} campos "
                f"(economia de {fields_skipped} campos)"
            )
        
        if not relevant_fields:
            logger.warning(
                f"⚠️ Nenhum campo relevante para seção '{self.section_name}' "
                f"no tipo '{memo_type}' - pulando extração"
            )
            return {}
        
        # Obter schema Pydantic para structured output (tipo pode sobrescrever com get_schema)
        schema_class = None
        if hasattr(extraction, "get_schema"):
            schema_class = extraction.get_schema(self.section_name, memo_type)
        if schema_class is None:
            try:
                schema_class = get_schema_for_section(self.section_name)
            except ValueError as e:
                # ❌ ERRO CRÍTICO: Schema não encontrado
                logger.critical(
                    f"❌ ERRO CRÍTICO: Schema não encontrado para seção '{self.section_name}'\n"
                    f"   Detalhes: {e}\n"
                    f"   Ação necessária: Adicione o schema em core/extraction_schemas.py"
                )
                if os.getenv("EXTRACTION_STRICT_MODE", "false").lower() == "true":
                    logger.critical(f"🛑 EXTRACTION_STRICT_MODE=true: Interrompendo extração")
                    raise ValueError(
                        f"Extração impossível sem schema para seção: {self.section_name}\n"
                        f"Configure o schema em extraction_schemas.py ou desabilite EXTRACTION_STRICT_MODE"
                    )
                logger.warning(
                    f"⚠️  Caindo em modo degradado (qualidade reduzida)\n"
                    f"   Dica: Para forçar erro, configure EXTRACTION_STRICT_MODE=true"
                )
                return {}
        
        # Para seções de tabelas, usar TableExtractor para encontrar tabelas
        table_context = ""
        if self.section_name in ["projections_table", "returns_table"]:
            try:
                from core.table_extractor import TableExtractor
                extractor = TableExtractor()
                
                if self.section_name == "projections_table":
                    table_data = extractor.extract_projections_table(text)
                    if table_data:
                        import json
                        table_context = f"\n\nTABELAS DE PROJEÇÕES ENCONTRADAS NO DOCUMENTO:\n{json.dumps(table_data, indent=2, ensure_ascii=False)}\n\nUse estas tabelas para preencher os campos de projeções."
                
                elif self.section_name == "returns_table":
                    table_data = extractor.extract_returns_table(text)
                    if table_data:
                        import json
                        table_context = f"\n\nTABELAS DE RETORNOS ENCONTRADAS NO DOCUMENTO:\n{json.dumps(table_data, indent=2, ensure_ascii=False)}\n\nUse estas tabelas para preencher os campos de retornos."
            except Exception as e:
                logger.warning(f"Erro ao extrair tabelas para {self.section_name}: {e}")
        
        system_message = extraction.get_system_message(self.section_name, memo_type)

        user_message = f"""{prompt}

DOCUMENTO (CONTEXTO RELEVANTE - busca semântica otimizada):
{relevant_context}
{table_context}

Extraia os dados seguindo RIGOROSAMENTE o schema estruturado."""

        for attempt in range(self.max_retries):
            try:
                messages = [
                    SystemMessage(content=system_message),
                    HumanMessage(content=user_message)
                ]
                
                # STRUCTURED OUTPUT - OpenAI valida automaticamente o schema
                # O strict=True já está configurado no ChatOpenAI (document_processor.py)
                response = await self.llm.with_structured_output(schema_class).ainvoke(messages)
                
                # Converter Pydantic model para dict
                extracted_dict = response.model_dump(exclude_none=True)
                
                logger.info(
                    f"✅ Extração estruturada de '{self.section_name}': "
                    f"{len(extracted_dict)} campos encontrados"
                )
                
                # Aplicar limpeza adicional se necessário
                cleaned = {
                    field_key: clean_extracted_value(field_key, field_value)
                    for field_key, field_value in extracted_dict.items()
                }
                
                return cleaned
                
            except Exception as e:
                logger.warning(
                    f"Tentativa {attempt + 1}/{self.max_retries} falhou para "
                    f"'{self.section_name}': {str(e)[:100]}"
                )
                if attempt == self.max_retries - 1:
                    logger.error(f"❌ Falha total na extração de {self.section_name}: {e}")
                    return {}
                await asyncio.sleep(2 ** attempt)
        
        return {}
    
    def _get_section_queries_hierarchical(self, section: str) -> Dict[str, List[str]]:
        """
        Retorna queries hierárquicas e específicas para cada seção.
        Estrutura: queries primárias (mais específicas) e secundárias (mais amplas).
        Se o tipo tiver get_section_queries(section), usa esse dict; senão usa o interno.
        """
        ext = getattr(self, "_extraction_module", None)
        if ext is not None and hasattr(ext, "get_section_queries"):
            custom = ext.get_section_queries(section)
            if custom and isinstance(custom, dict):
                return custom
        queries_config = {
            "identification": {
                "primary": [
                    "empresa alvo target companhia nome codinome Project Baja TSE Disktrans Oca Hero Seguros Bridge One aquisição está avaliando",
                    "localização empresa alvo cidade região país sede São Paulo Brasil Baja California México",
                    "descrição negócio especializada em MGA seguros viagem automação industrial software logística",
                    "gestora nome fundação AUM total fundo específico veículo coinvestimento FIP SPE data oportunidade apresentado por",
                    "capa título início documento MEMORANDO DE INVESTIMENTO CIM Novembro 2025 confidencial Sumário Executivo"
                ],
                "secondary": [
                    "negócio atividade setor segmento core business operação produtos serviços",
                    "contexto oportunidade deal origem relacionamento vendedor sucessão fundador",
                    "gestora apresentação AUM bilhões milhões fundo veículo data setor localização"
                ],
                "search_fund": [
                    "searcher nome liderado Pedro Dorea Fernando Ponce Eduardo Haro Hunibert Tuch Guilherme Ferrari período de busca",
                    "FIP casca veículo jurídico Minerva Capital Eunoia Redfoot Entrevo Capital capta recursos investimento empresa alvo",
                    "nacionalidade search mexicano brasileiro search fund segundo semestre 2S2024 1S2023 início período busca",
                    "capa título cover deal CIM memo início documento SEARCH FUND nome casca Atlante Atalante"
                ]
            },
            "transaction_structure": {
                "primary": [
                    "valuation enterprise value EV equity value equity value milhões",
                    "múltiplo EV EBITDA multiple transação entrada período referência",
                    "estrutura pagamento cash seller note earnout à vista",
                    "valor total transação incluindo custos step-up search capital chega a"
                ],
                "secondary": [
                    "stake percentual participação adquirida 100% equity",
                    "dívida equity ratio financiamento acquisition debt",
                    "estruturados percentual à vista acquisition debt negociação",
                    "múltiplo total EBITDA considerando custos 4,9x 3,6x"
                ]
            },
            "financials_history": {
                "primary": [
                    "receita faturamento revenue histórico crescimento CAGR",
                    "EBITDA margem lucro operacional histórico",
                    "dívida net debt alavancagem leverage histórico"
                ],
                "secondary": [
                    "margem bruta gross margin conversão caixa",
                    "funcionários employees opex despesas operacionais"
                ]
            },
            "saida": {
                "primary": [
                    "projeções receita futura revenue exit",
                    "EBITDA projetado saída exit múltiplo",
                    "ano saída exit year estratégia saída"
                ],
                "secondary": [
                    "drivers crescimento value creation",
                    "cenário projeção scenario type"
                ]
            },
            "returns": {
                "primary": [
                    "IRR TIR retorno esperado internal rate return",
                    "MOIC múltiplo dinheiro money multiple",
                    "holding period período retenção anos"
                ],
                "secondary": [
                    "entry multiple múltiplo entrada",
                    "retorno esperado retornos projetados"
                ]
            },
            "qualitative": {
                "primary": [
                    "modelo negócio business model operação",
                    "vantagens competitivas competitive advantages diferenciais",
                    "riscos principais key risks investimento"
                ],
                "secondary": [
                    "mercado concorrentes market share",
                    "próximos passos next steps"
                ]
            },
            # Queries para Memo Completo Search Fund
            "gestor": {
                "primary": [
                    "searcher nome formação histórico profissional experiência",
                    "assessment psicológico perfil complementaridade dupla",
                    "referências validações track record deals anteriores"
                ],
                "secondary": [
                    "empreendedor busca período início background",
                    "experiência empresas anteriores cargos"
                ]
            },
            "searcher": {
                "primary": [
                    "searcher nome formação histórico profissional experiência",
                    "assessment psicológico perfil complementaridade dupla",
                    "referências validações track record deals anteriores"
                ],
                "secondary": [
                    "empreendedor busca período início background",
                    "experiência empresas anteriores cargos"
                ]
            },
            "projections_table": {
                "primary": [
                    "projeções financeiras tabela cenário base upside downside",
                    "receita EBITDA projetado ano a ano tabela",
                    "premissas projeções crescimento margem drivers"
                ],
                "secondary": [
                    "financial projections table scenario",
                    "revenue EBITDA forecast year by year"
                ]
            },
            "returns_table": {
                "primary": [
                    "retornos esperados IRR MOIC cenário base upside downside",
                    "tabela sensibilidade múltiplo saída timing",
                    "returns table IRR MOIC scenario sensitivity"
                ],
                "secondary": [
                    "retorno esperado waterfall distribuição",
                    "exit scenarios multiple year"
                ]
            },
            "board_cap_table": {
                "primary": [
                    "board membros composição investidores cap table",
                    "board members investors contribution percentual",
                    "governança direitos veto tag-along drag-along"
                ],
                "secondary": [
                    "investidores participantes search investor gap investor",
                    "qualidade board cap table análise"
                ]
            },
            "gestora": {
                "primary": [
                    "track record fundos TVPI DPI IRR vintage performance histórica",
                    "gestora GP general partner nome sócios equipe gestão",
                    "exits realizados principais vendas múltiplos saída empresas",
                    "AUM assets under management capital sob gestão fundo específico"
                ],
                "secondary": [
                    "equipe gestão sócios principais anos experiência background",
                    "estratégia investimento tese gestora filosofia foco setorial",
                    "performance histórica IRR MOIC fundos anteriores comparação",
                    "Spectra relacionamento anterior co-investimentos operações"
                ]
            },
            "fundo": {
                "primary": [
                    "fundo nome target captação hard cap",
                    "vintage year closing primeiro closing",
                    "capital levantado captado commitment Spectra"
                ],
                "secondary": [
                    "portfolio investimentos estratégia fundo",
                    "moeda currency período investimento vida fundo"
                ]
            },
            "estrategia": {
                "primary": [
                    "tese investimento investment thesis estratégia",
                    "setores foco geografia alvo",
                    "ticket médio número ativos tipo participação"
                ],
                "secondary": [
                    "estágio investimento stage alocação",
                    "diferenciação estratégia peers"
                ]
            },
            "spectra_context": {
                "primary": [
                    "Spectra relacionamento histórico gestora",
                    "contexto rationale oportunidade investimento Spectra",
                    "due diligence termos negociados fees governance"
                ],
                "secondary": [
                    "coinvestidores LPs outros investidores",
                    "alocação estratégia Spectra"
                ]
            },
            "opinioes": {
                "primary": [
                    "opinião análise recomendação Spectra",
                    "pontos positivos strengths preocupações concerns",
                    "próximos passos next steps racional investimento"
                ],
                "secondary": [
                    "conclusão parecer avaliação final",
                    "founders track record posicionamento empresa"
                ]
            },
            "estrutura_veiculo": {
                "primary": [
                    "estrutura veículo coinvestimento regulamento fundo",
                    "duração fundo anos capital autorizado taxa gestão performance",
                    "hurdle rate catch-up preferência distribuição waterfall",
                    "chamadas capital chamada capital timing valores",
                    "quórum destituição gestor evento equipe chave"
                ],
                "secondary": [
                    "regulamento pontos atenção governança",
                    "taxa administração taxa performance carry"
                ]
            },
        }
        
        return queries_config.get(section, {
            "primary": [section.replace("_", " ")],
            "secondary": []
        })
    
    async def _get_relevant_context(
        self, 
        embeddings_data: Dict, 
        section: str
    ) -> str:
        """Busca chunks mais relevantes para a seção (método legado com queries hierárquicas)"""
        from core.document_processor import DocumentProcessor
        
        processor = DocumentProcessor()
        
        # Obter queries hierárquicas
        queries_config = self._get_section_queries_hierarchical(section)
        
        # Buscar com queries primárias primeiro (mais específicas)
        all_results = []
        seen_chunks = set()
        
        # 1. Buscar com queries primárias (prioridade alta)
        for query in queries_config.get("primary", []):
            results = processor.search_relevant_chunks(query, embeddings_data, top_k=5)
            for r in results:
                chunk_id = hash(r["chunk"][:100])  # ID único baseado no início do chunk
                if chunk_id not in seen_chunks:
                    all_results.append(r)
                    seen_chunks.add(chunk_id)
        
        # 2. Se não encontrou o suficiente, buscar com queries secundárias
        if len(all_results) < 8:
            for query in queries_config.get("secondary", []):
                results = processor.search_relevant_chunks(query, embeddings_data, top_k=3)
                for r in results:
                    chunk_id = hash(r["chunk"][:100])
                    if chunk_id not in seen_chunks:
                        all_results.append(r)
                        seen_chunks.add(chunk_id)
        
        # 3. Para Search Fund, adicionar queries específicas
        if section == "identification":
            for query in queries_config.get("search_fund", []):
                results = processor.search_relevant_chunks(query, embeddings_data, top_k=3)
                for r in results:
                    chunk_id = hash(r["chunk"][:100])
                    if chunk_id not in seen_chunks:
                        all_results.append(r)
                        seen_chunks.add(chunk_id)
        
        # Ordenar por score e pegar os melhores
        all_results.sort(key=lambda x: x["score"], reverse=True)
        
        # OTIMIZAÇÃO: identification e gestora costumam estar no início do doc
        top_k = 15 if section in ("identification", "gestora") else 10
        final_results = all_results[:top_k]
        
        # Combinar chunks
        context = "\n\n".join([r["chunk"] for r in final_results])
        
        logger.info(
            f"🔍 Busca hierárquica '{section}': "
            f"{len(final_results)} chunks únicos de {len(all_results)} encontrados"
        )
        
        return context
    
    async def _get_relevant_context_smart(
        self,
        embeddings_data: Dict,
        section: str
    ) -> str:
        """
        Busca inteligente com suporte a ChromaDB OU NumPy usando queries hierárquicas.
        
        Detecta automaticamente se embeddings_data vem do ChromaDB ou NumPy:
        - ChromaDB: Usa query vetorial direta no index persistente
        - NumPy: Busca em memória com metadata boost
        
        Usa queries hierárquicas: primeiro tenta queries primárias (específicas),
        depois expande com queries secundárias se necessário.
        
        Args:
            embeddings_data: Dados com embeddings (ChromaDB ou NumPy)
            section: Nome da seção a extrair
            
        Returns:
            Contexto relevante concatenado
        """
        from core.document_processor import DocumentProcessor
        processor = DocumentProcessor()
        
        # Obter queries hierárquicas
        queries_config = self._get_section_queries_hierarchical(section)
        
        # OTIMIZAÇÃO: identification e gestora costumam estar no início do doc
        top_k = 15 if section in ("identification", "gestora") else 10
        
        # DETECTAR MODO: ChromaDB ou NumPy
        if embeddings_data.get("vector_store") == "chromadb":
            # MODO CHROMADB: Busca persistente com queries hierárquicas
            memo_id = embeddings_data["memo_id"]
            
            logger.info(f"🎯 Busca ChromaDB hierárquica para '{section}' (memo: {memo_id})")
            
            # Buscar com queries primárias primeiro (mais específicas)
            all_results = []
            seen_chunks = set()
            
            # 1. Buscar com queries primárias (prioridade alta)
            for query in queries_config.get("primary", []):
                results = processor.search_chromadb_chunks(
                    memo_id=memo_id,
                    query=query,
                    top_k=5,
                    section=None
                )
                for r in results:
                    chunk_id = hash(r["chunk"][:100])  # ID único baseado no início do chunk
                    if chunk_id not in seen_chunks:
                        all_results.append(r)
                        seen_chunks.add(chunk_id)
            
            # 2. Se não encontrou o suficiente, buscar com queries secundárias
            if len(all_results) < 8:
                for query in queries_config.get("secondary", []):
                    results = processor.search_chromadb_chunks(
                        memo_id=memo_id,
                        query=query,
                        top_k=3,
                        section=None
                    )
                    for r in results:
                        chunk_id = hash(r["chunk"][:100])
                        if chunk_id not in seen_chunks:
                            all_results.append(r)
                            seen_chunks.add(chunk_id)
            
            # 3. Para Search Fund, adicionar queries específicas
            if section == "identification":
                for query in queries_config.get("search_fund", []):
                    results = processor.search_chromadb_chunks(
                        memo_id=memo_id,
                        query=query,
                        top_k=3,
                        section=None
                    )
                    for r in results:
                        chunk_id = hash(r["chunk"][:100])
                        if chunk_id not in seen_chunks:
                            all_results.append(r)
                            seen_chunks.add(chunk_id)
            
            if not all_results:
                logger.warning(
                    f"⚠️ Busca ChromaDB hierárquica não retornou resultados para '{section}'. "
                    f"Fallback para busca legado."
                )
                return await self._get_relevant_context(embeddings_data, section)
            
            # Ordenar por score e pegar os melhores
            all_results.sort(key=lambda x: x["score"], reverse=True)
            final_results = all_results[:top_k]
            
            # Combinar chunks
            context = "\n\n".join([r["chunk"] for r in final_results])
            
            # Log estatísticas
            avg_score = sum(r["score"] for r in final_results) / len(final_results) if final_results else 0
            sections_found = set(
                r.get("metadata", {}).get("section_title", "Unknown")
                for r in final_results
            )
            
            logger.info(
                f"✅ Busca ChromaDB hierárquica '{section}': "
                f"{len(final_results)} chunks únicos (de {len(all_results)} encontrados) | "
                f"score médio: {avg_score:.3f} | "
                f"seções: {', '.join(list(sections_found)[:3])}"
            )
            
            return context
        
        else:
            # MODO NUMPY: Busca em memória (fallback) com queries hierárquicas
            # Verificar se tem metadata
            if "metadata" not in embeddings_data:
                logger.warning(
                    f"⚠️ embeddings_data sem metadata. "
                    f"Fallback para busca legado."
                )
                return await self._get_relevant_context(embeddings_data, section)
            
            # Buscar com queries hierárquicas
            all_results = []
            seen_chunks = set()
            
            # 1. Buscar com queries primárias (prioridade alta)
            for query in queries_config.get("primary", []):
                results = processor.search_relevant_chunks_with_metadata(
                    query=query,
                    embeddings_data=embeddings_data,
                    section_filter=None,
                    top_k=5
                )
                for r in results:
                    chunk_id = hash(r["chunk"][:100])
                    if chunk_id not in seen_chunks:
                        all_results.append(r)
                        seen_chunks.add(chunk_id)
            
            # 2. Se não encontrou o suficiente, buscar com queries secundárias
            if len(all_results) < 8:
                for query in queries_config.get("secondary", []):
                    results = processor.search_relevant_chunks_with_metadata(
                        query=query,
                        embeddings_data=embeddings_data,
                        section_filter=None,
                        top_k=3
                    )
                    for r in results:
                        chunk_id = hash(r["chunk"][:100])
                        if chunk_id not in seen_chunks:
                            all_results.append(r)
                            seen_chunks.add(chunk_id)
            
            # 3. Para Search Fund, adicionar queries específicas
            if section == "identification":
                for query in queries_config.get("search_fund", []):
                    results = processor.search_relevant_chunks_with_metadata(
                        query=query,
                        embeddings_data=embeddings_data,
                        section_filter=None,
                        top_k=3
                    )
                    for r in results:
                        chunk_id = hash(r["chunk"][:100])
                        if chunk_id not in seen_chunks:
                            all_results.append(r)
                            seen_chunks.add(chunk_id)
            
            if not all_results:
                logger.warning(
                    f"⚠️ Busca smart hierárquica não retornou resultados para '{section}'. "
                    f"Tentando busca legado..."
                )
                return await self._get_relevant_context(embeddings_data, section)
            
            # Ordenar por score e pegar os melhores
            all_results.sort(key=lambda x: x.get("boosted_score", x["score"]), reverse=True)
            final_results = all_results[:top_k]
            
            # Log estatísticas
            avg_score = sum(r["score"] for r in final_results) / len(final_results) if final_results else 0
            sections_found = set(
                r.get("metadata", {}).get("section_title", "Unknown")
                for r in final_results
            )
            
            logger.info(
                f"🎯 Busca semântica hierárquica para '{section}': "
                f"{len(final_results)} chunks únicos (de {len(all_results)} encontrados) | "
                f"score médio: {avg_score:.3f} | "
                f"seções encontradas: {', '.join(list(sections_found)[:3])}"
            )
        
            # Combinar chunks (menos contexto, mais preciso)
            context = "\n\n".join([r["chunk"] for r in final_results])
        
        # Log economia de tokens
        old_method_chars = 60000  # Método antigo pegava ~60k chars
        new_method_chars = len(context)
        savings_pct = ((old_method_chars - new_method_chars) / old_method_chars) * 100
        
        logger.info(
            f"💰 Economia de tokens: {new_method_chars} chars "
            f"(vs {old_method_chars} antigo) = {savings_pct:.1f}% redução"
        )
        
        return context
    
    def _get_relevant_fields(self, memo_type: str) -> Dict:
        """
        Retorna apenas os campos relevantes para o tipo de memorando.

        Usa get_fatos_config(memo_type).get_relevant_fields_for_memo_type().
        """
        config = get_fatos_config(memo_type)
        all_relevant = config.get_relevant_fields_for_memo_type(memo_type)
        
        # Filtrar apenas os campos da seção atual
        if self.section_name not in all_relevant:
            logger.warning(f"Seção '{self.section_name}' não tem campos relevantes para '{memo_type}'")
            return {}
        
        section_fields = all_relevant[self.section_name]
        
        # Criar dict com labels amigáveis
        relevant = {}
        for field_key in section_fields:
            # Converter field_key em label (ex: "gestora_nome" → "Gestora Nome")
            label = field_key.replace("_", " ").title()
            relevant[field_key] = label
        
        logger.info(f"Seção '{self.section_name}' para '{memo_type}': {len(relevant)} campos relevantes")
        
        return relevant



