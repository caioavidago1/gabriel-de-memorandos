import asyncio
import os
from typing import Dict, Any, Optional, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import json
from facts_config import FIELD_VISIBILITY, get_relevant_fields_for_memo_type
from core.logger import get_logger
from core.extraction_schemas import get_schema_for_section

logger = get_logger(__name__)


def clean_extracted_value(field_key: str, value: Any) -> Any | None:
    """Limpa e converte valores extraídos"""
    if not value or value == "null":
        return None
    
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
        
        prompt = self._load_prompt(self.section_name)
        relevant_fields = self._get_relevant_fields(memo_type)
        
        # Log economia de tokens
        total_fields_section = len(FIELD_VISIBILITY.get(self.section_name, {}))
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
        
        # Obter schema Pydantic para structured output
        try:
            schema_class = get_schema_for_section(self.section_name)
        except ValueError as e:
            # ❌ ERRO CRÍTICO: Schema não encontrado
            logger.critical(
                f"❌ ERRO CRÍTICO: Schema não encontrado para seção '{self.section_name}'\n"
                f"   Detalhes: {e}\n"
                f"   Ação necessária: Adicione o schema em core/extraction_schemas.py"
            )
            
            # Em modo STRICT (produção), falhar imediatamente
            if os.getenv("EXTRACTION_STRICT_MODE", "false").lower() == "true":
                logger.critical(f"🛑 EXTRACTION_STRICT_MODE=true: Interrompendo extração")
                raise ValueError(
                    f"Extração impossível sem schema para seção: {self.section_name}\n"
                    f"Configure o schema em extraction_schemas.py ou desabilite EXTRACTION_STRICT_MODE"
                )
            
            # Em modo compatibilidade (dev), retornar vazio com aviso
            logger.warning(
                f"⚠️  Caindo em modo degradado (qualidade reduzida)\n"
                f"   Dica: Para forçar erro, configure EXTRACTION_STRICT_MODE=true"
            )
            return {}  # Retornar dict vazio ao invés de fallback degradado
        
        # Detectar se é Search Fund para adicionar instruções específicas
        is_search_fund = "Search Fund" in memo_type or "Co-investimento" in memo_type
        
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
        
        system_message = f"""Você é um especialista em análise de documentos financeiros de Private Equity.
Sua tarefa é extrair informações estruturadas da seção '{self.section_name}' com MÁXIMA PRECISÃO.

REGRAS CRÍTICAS:
1. Extraia APENAS informações EXPLICITAMENTE mencionadas no documento
2. Use null para campos não encontrados - NUNCA invente valores
3. Mantenha formatação original de números
4. Para percentuais: use valor decimal (ex: 15.5 para "15,5%")
5. Para valores monetários: extraia apenas o número (ex: 45.5 para "R$ 45,5M")
6. Anos: formato YYYY (ex: 2023)
7. Se houver ambiguidade, prefira null a chutar

ATENÇÃO ESPECIAL PARA NOMES DE EMPRESAS (seção identification):
- O nome da empresa pode NÃO ter label explícito como "Nome:" ou "Empresa:"
- Procure por nomes próprios no título, cabeçalho ou primeiras frases
- Nomes próprios que aparecem repetidamente são candidatos fortes
- Exemplos: "Hero Seguros", "Bridge One Capital", "Project Phoenix"
- Se o documento menciona "a empresa" ou "o target", o nome geralmente está perto"""

        if is_search_fund and self.section_name == "identification":
            system_message += """

ATENÇÃO CRÍTICA PARA SEARCH FUND (seção identification):
- searcher_name: É OBRIGATÓRIO extrair se mencionado. Procure por:
  * "search liderado por [NOME]"
  * "searcher [NOME]"
  * "empreendedor [NOME]"
  * Nomes próprios seguidos de "search" ou "busca"
  * Pode ser múltiplos nomes (ex: "Fernando Ponce e Eduardo Haro")
- search_start_date: É OBRIGATÓRIO extrair se mencionado. Procure por:
  * "iniciou o search em", "busca iniciada em", "período de busca"
  * Formatos: "1S2023", "Janeiro 2023", "2023", "1º semestre 2023"
- investor_nationality: É OBRIGATÓRIO extrair se mencionado. Procure por:
  * "brasileiro", "mexicano", "americano", "nacionalidade", "origem"
  
NÃO DEIXE DE EXTRAIR esses campos se estiverem no documento!"""

        # Instruções específicas para seções de tabelas
        if self.section_name == "projections_table":
            system_message += """

ATENÇÃO CRÍTICA PARA PROJEÇÕES (seção projections_table):
- Procure por TABELAS de projeções financeiras no documento
- Extraia dados ano a ano para cada cenário (base, upside, downside)
- Cada linha da tabela deve ter: year, revenue_mm, ebitda_mm, ebitda_margin_pct
- Se houver múltiplas tabelas, identifique qual é qual cenário pelo contexto (título, texto próximo)
- projections_years: Lista de todos os anos projetados
- projections_assumptions: Premissas detalhadas mencionadas para cada cenário

FORMATO ESPERADO:
projections_base_case: [
  {"year": 2024, "revenue_mm": 100.0, "ebitda_mm": 35.0, "ebitda_margin_pct": 35.0},
  {"year": 2025, "revenue_mm": 120.0, "ebitda_mm": 45.0, "ebitda_margin_pct": 37.5},
  ...
]"""

        if self.section_name == "returns_table":
            system_message += """

ATENÇÃO CRÍTICA PARA RETORNOS (seção returns_table):
- Procure por TABELAS de retornos (IRR/MOIC) no documento
- Extraia retornos para cada cenário (base, upside, downside)
- Se houver tabela de sensibilidade, extraia múltiplos cenários variando múltiplo de saída ou ano
- returns_base_case: {irr_pct: float, moic: float, exit_year: int, exit_multiple: float}
- returns_sensitivity_table: Lista de cenários com diferentes combinações de múltiplo/ano

FORMATO ESPERADO:
returns_base_case: {"irr_pct": 39.8, "moic": 5.3, "exit_year": 2028, "exit_multiple": 6.0}
returns_sensitivity_table: [
  {"exit_year": 2028, "exit_multiple": 5.5, "irr_pct": 36.7, "moic": 4.8},
  {"exit_year": 2028, "exit_multiple": 6.0, "irr_pct": 39.8, "moic": 5.3},
  ...
]"""

        if self.section_name in ["gestor", "searcher"]:
            system_message += """

ATENÇÃO CRÍTICA PARA GESTOR/SEARCHER (seção gestor):
- searcher_name: Nome(s) completo(s) do(s) searcher(s) - pode ser múltiplos separados por vírgula
- searcher_background: Formação acadêmica completa e histórico profissional detalhado
- searcher_experience: Anos de experiência, empresas anteriores, cargos ocupados
- searcher_assessment: Resultados de assessment psicológico se mencionado (perfil, características)
- searcher_complementarity: Como os searchers se complementam (se dupla), divisão de papéis
- searcher_references: Referências obtidas (ex-empregadores, mentores, validadores)
- searcher_track_record: Histórico de deals anteriores, experiências em M&A (se aplicável)

PROCURE POR:
- Seções como "2. Gestor", "Gestor", "Searchers", "Equipe"
- Texto sobre formação, experiência, assessment
- Comparações com outros searchers conhecidos
- Validações e referências"""

        if self.section_name == "board_cap_table":
            system_message += """

ATENÇÃO CRÍTICA PARA BOARD E CAP TABLE (seção board_cap_table):
- Procure por seções sobre composição do board e estrutura de investidores
- board_members: Lista de membros do board com nome, role, background, indication_source
- cap_table: Lista de investidores com nome, tipo, contribution, percentual, país
- governance_structure: Direitos de veto, tag-along, drag-along, composição do board
- board_commentary: Comentários sobre qualidade do board e cap table

FORMATO ESPERADO:
board_members: [
  {"name": "João Lima", "role": "Board Member", "background": "...", "indication_source": "Voke"},
  ...
]
cap_table: [
  {"investor_name": "Spectra", "investor_type": "Search Investor", "contribution_mm": 20.0, "contribution_pct": 22.0, "country": "Brazil"},
  ...
]

PROCURE POR:
- Seções como "Board e Cap Table", "Board", "Composição do Board"
- Tabelas de investidores
- Listas de membros do board com backgrounds"""

        system_message += """

IMPORTANTE: Você DEVE retornar um objeto JSON válido seguindo o schema fornecido.
Campos que você não encontrar devem ser null ou omitidos."""

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
        """
        queries_config = {
            "identification": {
                "primary": [
                    "nome oficial da empresa target companhia organização",
                    "localização sede cidade estado país fundação ano",
                ],
                "secondary": [
                    "negócio atividade setor descrição empresa",
                    "deal contexto oportunidade relacionamento vendedor"
                ],
                "search_fund": [
                    "searcher empreendedor nome busca período início",
                    "nacionalidade investidor searcher origem"
                ]
            },
            "transaction_structure": {
                "primary": [
                    "valuation enterprise value EV equity value",
                    "múltiplo EV EBITDA multiple transação",
                    "estrutura pagamento cash seller note earnout"
                ],
                "secondary": [
                    "stake percentual participação adquirida",
                    "dívida equity ratio financiamento estrutura"
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
                    "gestora GP general partner nome gestora",
                    "track record performance histórico exits",
                    "AUM assets under management capital sob gestão"
                ],
                "secondary": [
                    "equipe gestão sócios principais",
                    "filosofia investimento estratégia gestora"
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
            }
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
        
        # OTIMIZAÇÃO: Para identification, buscar MAIS chunks (incluir início do doc)
        top_k = 15 if section == "identification" else 10
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
        
        # OTIMIZAÇÃO: Para identification, buscar MAIS chunks (nomes geralmente no início)
        top_k = 15 if section == "identification" else 10
        
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
    
    def _load_prompt(self, section: str) -> str:
        """Carrega prompt específico da seção"""
        prompt_file = f"facts/prompts/{section}.txt"
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return f"Extraia informações relevantes para a seção {section}."
    
    def _get_relevant_fields(self, memo_type: str) -> Dict:
        """
        Retorna apenas os campos relevantes para o tipo de memorando.
        
        Usa get_relevant_fields_for_memo_type() de facts_config.py para obter
        a lista filtrada de campos que devem ser extraídos.
        
        Args:
            memo_type: Tipo de memorando selecionado
        
        Returns:
            Dict {field_key: field_label} com apenas campos relevantes
        """
        # Obter todos os campos relevantes para o tipo de memo
        all_relevant = get_relevant_fields_for_memo_type(memo_type)
        
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



