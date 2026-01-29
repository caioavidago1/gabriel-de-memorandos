import os
import asyncio
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
import numpy as np
from dotenv import load_dotenv
from parser import parse
from core.logger import get_logger
from core.markdown_chunker import MarkdownChunker
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

load_dotenv()
logger = get_logger(__name__)

class DocumentProcessor:
    def __init__(self):
        # LangChain LLM e Embeddings
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.1
        )
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small"
        )
    
    def parse_document(self, file_path: Path) -> Dict[str, Any]:
        """Parse documento usando LlamaParse"""
        return parse(file_path, output_dir=Path("parsed_outputs"))
    
    def chunk_text(self, text: str, chunk_size: int = 6000, overlap: int = 500) -> List[str]:
        """
        Divide texto em chunks com overlap (em caracteres, ~1500 tokens)
        
        Args:
            text: Texto completo
            chunk_size: Tamanho de cada chunk em caracteres (~1500 tokens)
            overlap: Overlap entre chunks
            
        Returns:
            Lista de chunks
        """
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = start + chunk_size
            chunk = text[start:end]
            
            if end < text_len and (last_space := chunk.rfind(' ')) > chunk_size * 0.8:
                chunk = chunk[:last_space]
                end = start + last_space
            
            chunks.append(chunk.strip())
            start = end - overlap
        
        return chunks
    
    def create_embeddings(self, texts: List[str]) -> Dict[str, Any]:
        """
        Gera embeddings para lista de textos (já chunkados)
        
        Args:
            texts: Lista de chunks de texto
            
        Returns:
            Dict com embeddings e metadados
        """
        all_chunks = []
        all_embeddings = []
        
        logger.info(f"🔄 Processando {len(texts)} documentos...")
        
        for doc_idx, text in enumerate(texts):
            logger.info(f"📄 Documento {doc_idx + 1}/{len(texts)}")
            chunks = self.chunk_text(text)
            logger.info(f"Dividido em {len(chunks)} chunks")
            
            batch_size = 50
            doc_embeddings = []
            
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i+batch_size]
                batch_num = i//batch_size + 1
                total_batches = (len(chunks)-1)//batch_size + 1
                logger.debug(f"Processando batch {batch_num}/{total_batches}...")
                
                try:
                    # Usar LangChain OpenAIEmbeddings
                    batch_embeddings = self.embeddings.embed_documents(batch)
                    doc_embeddings.extend(batch_embeddings)
                    logger.debug(f"Batch {batch_num}/{total_batches} processado ✓")
                    
                except Exception as e:
                    logger.error(f"Erro ao processar batch {batch_num}: {e}")
                    # Em caso de erro, adicionar embedding vazio
                    doc_embeddings.extend([[0.0] * 1536] * len(batch))
            
            all_chunks.extend(chunks)
            all_embeddings.extend(doc_embeddings)
        
        logger.info(f"✅ Total: {len(all_chunks)} chunks processados")
        
        return {
            "chunks": all_chunks,
            "embeddings": np.array(all_embeddings),
            "chunk_count": len(all_chunks)
        }
    
    def create_embeddings_with_metadata(self, texts: List[str]) -> Dict[str, Any]:
        """
        Gera embeddings preservando metadados estruturais do markdown.
        
        Usa MarkdownChunker para chunkar de forma inteligente, preservando:
        - Hierarquia de seções (h1, h2, h3, etc)
        - Títulos de seções e caminhos completos
        - Tabelas e suas estruturas
        - Relacionamentos pai-filho entre seções
        
        Args:
            texts: Lista de textos em markdown (geralmente 1 documento completo)
            
        Returns:
            Dict com embeddings, chunks e metadados estruturados:
            {
                "chunks": List[str],
                "embeddings": np.array,
                "metadata": List[Dict],  # Metadata por chunk
                "chunk_count": int
            }
        """
        chunker = MarkdownChunker(
            chunk_size=6000,
            overlap=500
        )
        
        all_chunks = []
        all_metadata = []
        all_embeddings = []
        
        logger.info(f"🔄 Processando {len(texts)} documentos com metadata...")
        
        for doc_idx, markdown_text in enumerate(texts):
            logger.info(f"📄 Documento {doc_idx + 1}/{len(texts)}")
            
            # Chunkar com metadata
            chunked_data = chunker.chunk_with_metadata(markdown_text)
            
            chunks_only = [item["text"] for item in chunked_data]
            metadata_only = [item["metadata"] for item in chunked_data]
            
            logger.info(
                f"Dividido em {len(chunks_only)} chunks com metadata estruturada "
                f"(seções, hierarquia, tabelas)"
            )
            
            # Gerar embeddings em batches
            batch_size = 50
            doc_embeddings = []
            
            for i in range(0, len(chunks_only), batch_size):
                batch = chunks_only[i:i+batch_size]
                batch_num = i//batch_size + 1
                total_batches = (len(chunks_only)-1)//batch_size + 1
                logger.debug(f"Processando batch {batch_num}/{total_batches}...")
                
                try:
                    batch_embeddings = self.embeddings.embed_documents(batch)
                    doc_embeddings.extend(batch_embeddings)
                    logger.debug(f"Batch {batch_num}/{total_batches} processado ✓")
                    
                except Exception as e:
                    logger.error(f"Erro ao processar batch {batch_num}: {e}")
                    # Fallback: embedding vazio
                    doc_embeddings.extend([[0.0] * 1536] * len(batch))
            
            all_chunks.extend(chunks_only)
            all_metadata.extend(metadata_only)
            all_embeddings.extend(doc_embeddings)
        
        # Log estatísticas
        sections_found = set(m["section_title"] for m in all_metadata if m.get("section_title"))
        logger.info(
            f"✅ Total: {len(all_chunks)} chunks | "
            f"{len(sections_found)} seções únicas | "
            f"Metadata preservada para busca inteligente"
        )
        
        return {
            "chunks": all_chunks,
            "embeddings": np.array(all_embeddings),
            "metadata": all_metadata,
            "chunk_count": len(all_chunks)
        }
    
    def search_relevant_chunks(
        self, 
        query: str, 
        embeddings_data: Dict, 
        top_k: int = 5
    ) -> List[Dict]:
        """
        Busca chunks mais relevantes para uma query
        Compatível com ChromaDB e NumPy.
        
        Args:
            query: Texto da busca
            embeddings_data: Dados retornados por create_embeddings() ou ChromaDB
            top_k: Número de chunks a retornar
            
        Returns:
            Lista de chunks mais relevantes com scores
        """
        # VERIFICAR SE É CHROMADB
        if embeddings_data.get("vector_store") == "chromadb":
            # Usar busca ChromaDB
            memo_id = embeddings_data["memo_id"]
            return self.search_chromadb_chunks(memo_id, query, top_k)
        
        # MODO NUMPY (fallback)
        if "embeddings" not in embeddings_data:
            logger.warning("⚠️ embeddings_data sem chave 'embeddings'. Retornando vazio.")
            return []
        
        query_embedding = np.array(self.embeddings.embed_query(query))
        embeddings = embeddings_data["embeddings"]
        similarities = np.dot(embeddings, query_embedding)
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            results.append({
                "chunk": embeddings_data["chunks"][idx],
                "score": float(similarities[idx]),
                "index": int(idx)
            })
        
        return results
    
    def search_relevant_chunks_with_metadata(
        self,
        query: str,
        embeddings_data: Dict,
        section_filter: Optional[List[str]] = None,
        top_k: int = 10
    ) -> List[Dict]:
        """
        Busca chunks relevantes COM FILTRO DE METADATA.
        Compatível com ChromaDB e NumPy.
        
        Args:
            query: Texto da busca
            embeddings_data: Dados com embeddings (ChromaDB ou NumPy)
            section_filter: Lista de keywords para filtrar seções
            top_k: Número de chunks a retornar
            
        Returns:
            Lista de chunks ordenados por relevância com metadata
        """
        # VERIFICAR SE É CHROMADB
        if embeddings_data.get("vector_store") == "chromadb":
            memo_id = embeddings_data["memo_id"]
            return self.search_chromadb_chunks(memo_id, query, top_k)
        
        # MODO NUMPY (fallback)
        if "embeddings" not in embeddings_data:
            logger.warning("⚠️ embeddings_data sem chave 'embeddings'. Retornando vazio.")
            return []
        
        # 1. Busca semântica base
        query_embedding = np.array(self.embeddings.embed_query(query))
        embeddings = embeddings_data["embeddings"]
        similarities = np.dot(embeddings, query_embedding)
        
        # 2. Aplicar filtro de metadata se fornecido
        if section_filter and "metadata" in embeddings_data:
            metadata_list = embeddings_data["metadata"]
            
            # Marcar chunks que passam no filtro
            valid_indices = []
            for idx, meta in enumerate(metadata_list):
                section_title = meta.get("section_title", "").lower()
                full_path = meta.get("full_path", "").lower()
                
                # Verificar se algum keyword aparece no título ou path
                matches_filter = any(
                    keyword.lower() in section_title or keyword.lower() in full_path
                    for keyword in section_filter
                )
                
                if matches_filter:
                    valid_indices.append(idx)
            
            # Se filtro não encontrou nada, usar tudo (fallback)
            if not valid_indices:
                logger.warning(
                    f"⚠️ Filtro de seção não encontrou matches para {section_filter}. "
                    "Usando busca semântica sem filtro."
                )
                valid_indices = list(range(len(similarities)))
        else:
            valid_indices = list(range(len(similarities)))
        
        # 3. Boost de score baseado em hierarquia
        boosted_scores = similarities.copy()
        if "metadata" in embeddings_data:
            for idx in valid_indices:
                meta = embeddings_data["metadata"][idx]
                
                # Chunks de nível h1/h2 têm boost (geralmente mais importantes)
                level = meta.get("section_level", 3)
                if level == 1:
                    boosted_scores[idx] *= 1.2
                elif level == 2:
                    boosted_scores[idx] *= 1.1
                
                # Chunks com tabelas têm boost (dados numéricos importantes)
                if meta.get("has_table", False):
                    boosted_scores[idx] *= 1.15
        
        # 4. Ordenar por score boosted
        filtered_scores = [(idx, boosted_scores[idx]) for idx in valid_indices]
        filtered_scores.sort(key=lambda x: x[1], reverse=True)
        top_indices = [idx for idx, _ in filtered_scores[:top_k]]
        
        # 5. Construir resultados com metadata
        results = []
        for idx in top_indices:
            result = {
                "chunk": embeddings_data["chunks"][idx],
                "score": float(similarities[idx]),
                "boosted_score": float(boosted_scores[idx]),
                "index": int(idx)
            }
            
            # Incluir metadata se disponível
            if "metadata" in embeddings_data:
                result["metadata"] = embeddings_data["metadata"][idx]
            
            results.append(result)
        
        logger.debug(
            f"🔍 Busca com metadata: {len(valid_indices)} chunks válidos, "
            f"retornando top {len(results)}"
        )
        
        return results
    
    def create_embeddings_with_chromadb(
        self, 
        parsed_docs: List[Dict[str, Any]],
        memo_id: str,
        memo_type: str,
        version: int = 1,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> str:
        """
        Gera embeddings e salva no ChromaDB (PERSISTENTE).
        
        Args:
            parsed_docs: Lista de dicts com estrutura:
                [{"filename": str, "text": str, "pages": int, ...}, ...]
            memo_id: ID único do memorando
            memo_type: Tipo do memo ("Short Memo - Co-investimento (Search Fund)", etc)
            version: Versão do memorando
            progress_callback: Callback opcional para progresso (current, total, message)
                Exemplo: callback(50, 100, "Gerando embeddings...")
            
        Returns:
            memo_id (str): ID usado no ChromaDB
        """
        from core.chromadb_store import get_or_create_collection, upsert_memo_chunks
        
        start_time = time.time()
        
        # 1. Combinar todos os textos com separadores claros e rastrear posições
        if progress_callback:
            progress_callback(0, 100, "Combinando documentos...")
        
        combined_parts = []
        doc_positions = []  # Rastrear onde cada documento começa no texto combinado
        current_offset = 0
        
        for i, doc in enumerate(parsed_docs):
            text = doc.get("text", "")
            if text:
                filename = doc.get("filename", f"doc_{i+1}")
                marker = f"=== DOCUMENTO {i+1}: {filename} ===\n\n"
                doc_start = current_offset + len(marker)
                doc_end = doc_start + len(text)
                
                combined_parts.append(f"{marker}{text}")
                doc_positions.append({
                    "index": i,
                    "filename": filename,
                    "marker": marker,
                    "start": doc_start,
                    "end": doc_end
                })
                current_offset = doc_end + len("\n\n")
        
        combined_text = "\n\n".join(combined_parts)
        
        if not combined_text:
            logger.warning(f"⚠️ Nenhum texto encontrado nos documentos para memo '{memo_id}'")
            return memo_id
        
        # 2. Chunking inteligente
        if progress_callback:
            progress_callback(5, 100, "Chunking documentos...")
        
        chunker = MarkdownChunker(chunk_size=6000, overlap=500)
        chunked_data = chunker.chunk_with_metadata(combined_text)
        
        # 3. Enriquecer metadata com informação do documento de origem
        # Atribuir documento de origem para cada chunk baseado na posição no texto combinado
        for chunk_item in chunked_data:
            chunk_text = chunk_item.get("text", "")
            # Tentar encontrar o chunk no texto combinado
            chunk_pos = combined_text.find(chunk_text[:100])  # Buscar pelos primeiros 100 chars para ser mais robusto
            
            if chunk_pos >= 0:
                # Encontrar qual documento contém esta posição
                for doc_info in doc_positions:
                    if doc_info["start"] <= chunk_pos < doc_info["end"]:
                        chunk_item["metadata"]["source_document"] = doc_info["filename"]
                        chunk_item["metadata"]["document_index"] = doc_info["index"]
                        break
                else:
                    # Chunk está fora dos documentos conhecidos (pode ser overlap)
                    # Atribuir ao documento mais próximo
                    if doc_positions:
                        # Encontrar documento mais próximo
                        closest_doc = min(doc_positions, key=lambda d: abs(d["start"] - chunk_pos))
                        chunk_item["metadata"]["source_document"] = closest_doc["filename"]
                        chunk_item["metadata"]["document_index"] = closest_doc["index"]
            else:
                # Fallback: procurar por marcador no texto do chunk
                for doc_info in doc_positions:
                    if doc_info["marker"].strip() in chunk_text:
                        chunk_item["metadata"]["source_document"] = doc_info["filename"]
                        chunk_item["metadata"]["document_index"] = doc_info["index"]
                        break
                else:
                    # Último fallback: primeiro documento
                    if doc_positions:
                        first_doc = doc_positions[0]
                        chunk_item["metadata"]["source_document"] = first_doc["filename"]
                        chunk_item["metadata"]["document_index"] = first_doc["index"]
        
        total_chunks = len(chunked_data)
        logger.info(f"📄 {total_chunks} chunks gerados para memo '{memo_id}'")
        
        # 4. Gerar embeddings com retry e progress callback
        chunks_only = [item["text"] for item in chunked_data]
        batch_size = 50
        all_embeddings = []
        total_batches = (len(chunks_only) - 1) // batch_size + 1
        
        # Função com retry para embeddings
        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=4, max=60),
            retry=retry_if_exception_type((Exception,)),
            reraise=True
        )
        def embed_batch_with_retry(batch: List[str], batch_num: int, total_batches: int) -> List[List[float]]:
            """Gera embeddings com retry automático para rate limits"""
            try:
                return self.embeddings.embed_documents(batch)
            except Exception as e:
                error_str = str(e).lower()
                # Detectar rate limit ou erro temporário
                if "rate limit" in error_str or "429" in error_str or "too many requests" in error_str:
                    logger.warning(f"⚠️ Rate limit detectado no batch {batch_num}/{total_batches}, aguardando retry...")
                    raise  # Retry
                if "timeout" in error_str or "connection" in error_str:
                    logger.warning(f"⚠️ Erro temporário no batch {batch_num}/{total_batches}, tentando novamente...")
                    raise  # Retry
                # Outros erros também podem ser temporários - deixar retry tentar
                raise
        
        for i in range(0, len(chunks_only), batch_size):
            batch = chunks_only[i:i+batch_size]
            batch_num = i // batch_size + 1
            
            # Calcular progresso (10% a 80% para embeddings)
            progress_pct = 10 + int((batch_num / total_batches) * 70)
            if progress_callback:
                progress_callback(
                    progress_pct,
                    100,
                    f"Gerando embeddings: batch {batch_num}/{total_batches} ({batch_num * 100 // total_batches}%)"
                )
            
            try:
                batch_embeddings = embed_batch_with_retry(batch, batch_num, total_batches)
                all_embeddings.extend(batch_embeddings)
                
                # Log detalhado a cada 10 batches ou no último
                if batch_num % 10 == 0 or batch_num == total_batches:
                    elapsed = time.time() - start_time
                    rate = batch_num / elapsed if elapsed > 0 else 0
                    remaining_batches = total_batches - batch_num
                    eta_seconds = remaining_batches / rate if rate > 0 else 0
                    
                    logger.info(
                        f"📊 Embeddings: {batch_num}/{total_batches} batches "
                        f"({batch_num * 100 // total_batches}%) | "
                        f"Taxa: {rate:.1f} batches/s | "
                        f"ETA: {int(eta_seconds)}s"
                    )
            except Exception as e:
                logger.error(f"❌ Erro crítico ao processar batch {batch_num}: {e}")
                # Em caso de erro crítico após retries, adicionar embedding vazio como fallback
                logger.warning(f"⚠️ Usando embedding vazio como fallback para batch {batch_num}")
                all_embeddings.extend([[0.0] * 1536] * len(batch))
        
        logger.info(f"✅ {len(all_embeddings)} embeddings gerados em {time.time() - start_time:.1f}s")
        
        # 5. Preparar chunks para ChromaDB
        if progress_callback:
            progress_callback(85, 100, "Preparando dados para ChromaDB...")
        
        chunks_for_chromadb = [
            {
                "id": f"{memo_id}_chunk_{i}",
                "text": chunked_data[i]["text"],
                "metadata": chunked_data[i]["metadata"]
            }
            for i in range(len(chunked_data))
        ]
        
        # 6. Inicializar ChromaDB e fazer upsert
        if progress_callback:
            progress_callback(90, 100, "Salvando no ChromaDB...")
        
        collection = get_or_create_collection()
        
        upsert_memo_chunks(
            collection=collection,
            memo_id=memo_id,
            chunks=chunks_for_chromadb,
            embeddings=all_embeddings,
            memo_type=memo_type,
            version=version
        )
        
        total_time = time.time() - start_time
        logger.info(f"🎉 Memo '{memo_id}' salvo no ChromaDB com sucesso ({total_time:.1f}s total)")
        
        if progress_callback:
            progress_callback(100, 100, "Concluído!")
        
        return memo_id
    
    def search_chromadb_chunks(
        self,
        memo_id: str,
        query: str,
        top_k: int = 10,
        section: Optional[str] = None
    ) -> List[Dict]:
        """
        Busca chunks relevantes no ChromaDB.
        
        Args:
            memo_id: ID do memorando
            query: Texto da busca
            top_k: Número de chunks a retornar
            section: Filtro opcional por seção
            
        Returns:
            Lista de chunks com score e metadata
        """
        from core.chromadb_store import get_or_create_collection, query_memo_chunks
        
        # Gerar embedding da query
        query_embedding = self.embeddings.embed_query(query)
        
        # Buscar no ChromaDB
        collection = get_or_create_collection()
        
        results = query_memo_chunks(
            collection=collection,
            memo_id=memo_id,
            query_embedding=query_embedding,
            top_k=top_k,
            section=section
        )
        
        # Formatar resultados (ChromaDB retorna "document" em vez de "text" no metadata)
        formatted_results = []
        for r in results:
            formatted_results.append({
                "chunk": r.get("document", ""),  # ChromaDB retorna "document"
                "score": r["score"],
                "metadata": r["metadata"]
            })
        
        return formatted_results
    
    async def extract_facts_parallel(
        self, 
        parsed_docs: List[Dict], 
        memo_type: str,
        embeddings_data: Dict = None
    ) -> Dict[str, Dict]:
        """
        Extrai facts usando LangGraph (com retry e validação automática)
        
        Args:
            parsed_docs: Lista de documentos parseados
            memo_type: Tipo de memorando
            embeddings_data: Dados de embeddings (opcional, para busca semântica)
            
        Returns:
            Dicionário com facts extraídos por seção
        """
        from core.langgraph_orchestrator import LangGraphExtractor
        
        extractor = LangGraphExtractor(self.llm, max_retries=2)
        combined_text = "\n\n".join(doc["text"] for doc in parsed_docs)
        
        results = await extractor.extract_all(combined_text, memo_type, embeddings_data)
        
        return results
    
    def extract_all_facts(
        self, 
        parsed_docs: List[Dict], 
        memo_type: str,
        embeddings_data: Dict = None
    ) -> Dict[str, Dict]:
        """
        Wrapper síncrono para extração paralela
        """
        return asyncio.run(
            self.extract_facts_parallel(parsed_docs, memo_type, embeddings_data)
        )
    
    def regenerate_facts_for_memo_type(
        self,
        parsed_docs: List[Dict],
        memo_type: str,
        embeddings_data: Dict = None
    ) -> Dict[str, Dict]:
        """
        Regenera facts quando o tipo de memo muda, especialmente para
        Memo Completo Search Fund que requer tabelas específicas.
        
        Args:
            parsed_docs: Lista de documentos parseados
            memo_type: Tipo de memorando
            embeddings_data: Dados de embeddings (opcional)
        
        Returns:
            Dict com facts completos incluindo tabelas
        """
        # Se for Memo Completo Search Fund, garantir extração de tabelas
        if memo_type == "Memorando - Co-investimento (Search Fund)":
            # Extrair facts padrão
            facts = self.extract_all_facts(parsed_docs, memo_type, embeddings_data)
            
            # Tentar extrair tabelas adicionais se não foram extraídas
            combined_text = "\n\n".join(doc["text"] for doc in parsed_docs)
            
            try:
                from core.table_extractor import TableExtractor
                extractor = TableExtractor()
                
                # Extrair tabelas de projeções se não existir
                if "projections_table" not in facts or not facts.get("projections_table"):
                    projections = extractor.extract_projections_table(combined_text)
                    if projections:
                        facts["projections_table"] = projections
                
                # Extrair tabelas de retornos se não existir
                if "returns_table" not in facts or not facts.get("returns_table"):
                    returns = extractor.extract_returns_table(combined_text)
                    if returns:
                        facts["returns_table"] = returns
                
                # Extrair board se não existir
                if "board_cap_table" not in facts or not facts.get("board_cap_table", {}).get("board_members"):
                    board = extractor.extract_board_table(combined_text)
                    if board and "board_cap_table" in facts:
                        if not facts["board_cap_table"]:
                            facts["board_cap_table"] = {}
                        facts["board_cap_table"]["board_members"] = board
                
                # Extrair cap table se não existir
                if "board_cap_table" not in facts or not facts.get("board_cap_table", {}).get("cap_table"):
                    cap_table = extractor.extract_cap_table(combined_text)
                    if cap_table and "board_cap_table" in facts:
                        if not facts["board_cap_table"]:
                            facts["board_cap_table"] = {}
                        facts["board_cap_table"]["cap_table"] = cap_table
                
            except Exception as e:
                logger.warning(f"Erro ao extrair tabelas adicionais: {e}")
            
            return facts
        else:
            # Para outros tipos, usar extração padrão
            return self.extract_all_facts(parsed_docs, memo_type, embeddings_data)
