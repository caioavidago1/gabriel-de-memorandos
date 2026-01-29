"""
Módulo de integração com ChromaDB para armazenamento persistente de embeddings.

Implementa vector store com isolamento por memorando usando collections,
permitindo versionamento e busca filtrada por seção.
"""

import os
from typing import Optional, List, Dict, Any
import chromadb
from chromadb.config import Settings
from core.logger import get_logger
from langchain_openai import OpenAIEmbeddings

logger = get_logger(__name__)

# Cliente global ChromaDB (persistente)
_chroma_client = None
_collection_name = "memorandos-embeddings"


def get_chroma_client():
    """
    Retorna cliente ChromaDB (singleton).
    
    Lê variáveis de ambiente:
    - CHROMA_DB_PATH: Caminho para persistência (default: "./chroma_db")
    
    Returns:
        chromadb.Client: Cliente ChromaDB configurado
    """
    global _chroma_client
    
    if _chroma_client is None:
        db_path = os.getenv("CHROMA_DB_PATH", "./chroma_db")
        
        logger.info(f"🔌 Inicializando ChromaDB client (path: {db_path})")
        
        try:
            _chroma_client = chromadb.PersistentClient(
                path=db_path,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            logger.info(f"✅ ChromaDB client inicializado")
            
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar ChromaDB: {e}")
            raise
    
    return _chroma_client


def get_or_create_collection(collection_name: str = None) -> chromadb.Collection:
    """
    Obtém ou cria collection no ChromaDB.
    
    Args:
        collection_name: Nome da collection (default: "memorandos-embeddings")
        
    Returns:
        chromadb.Collection: Collection configurada
    """
    if collection_name is None:
        collection_name = _collection_name
    
    client = get_chroma_client()
    
    try:
        # Tentar obter collection existente
        collection = client.get_collection(name=collection_name)
        logger.info(f"✅ Collection '{collection_name}' encontrada")
        
    except Exception:
        # Criar collection se não existir
        logger.info(f"📦 Collection '{collection_name}' não encontrada. Criando...")
        
        collection = client.create_collection(
            name=collection_name,
            metadata={"description": "Embeddings de memorandos Spectra"}
        )
        
        logger.info(f"✅ Collection '{collection_name}' criada com sucesso")
    
    return collection


def upsert_memo_chunks(
    collection: chromadb.Collection,
    memo_id: str,
    chunks: List[Dict[str, Any]],
    embeddings: List[List[float]],
    memo_type: str,
    version: int = 1,
    batch_size: int = 500
) -> None:
    """
    Faz upsert de chunks de um memorando no ChromaDB em batches para melhor performance.
    
    Args:
        collection: Collection do ChromaDB
        memo_id: ID único do memorando (usado como filtro)
        chunks: Lista de dicts com estrutura:
            {
                "id": str,
                "text": str,
                "metadata": {
                    "section_title": str,
                    "section_level": int,
                    "parent_section": str | None,
                    "full_path": str,
                    "has_table": bool,
                    "chunk_index": int,
                    "total_chunks": int
                }
            }
        embeddings: Lista de vetores (list[float]) correspondentes aos chunks
        memo_type: Tipo do memorando (ex: "Short Memo - Co-investimento (Search Fund)")
        version: Versão do memorando (para versionamento)
        batch_size: Tamanho do batch para upsert (default: 500, otimizado para volumes grandes)
        
    Raises:
        ValueError: Se número de chunks != número de embeddings
        Exception: Se houver erro no upsert
    """
    if len(chunks) != len(embeddings):
        raise ValueError(
            f"Número de chunks ({len(chunks)}) != número de embeddings ({len(embeddings)})"
        )
    
    total_chunks = len(chunks)
    total_batches = (total_chunks - 1) // batch_size + 1
    
    logger.info(
        f"📤 Upserting {total_chunks} chunks para memo '{memo_id}' "
        f"(version: {version}) em {total_batches} batches de {batch_size}"
    )
    
    try:
        import time
        start_time = time.time()
        
        # Processar em batches
        for batch_idx in range(0, total_chunks, batch_size):
            batch_end = min(batch_idx + batch_size, total_chunks)
            batch_chunks = chunks[batch_idx:batch_end]
            batch_embeddings = embeddings[batch_idx:batch_end]
            
            current_batch = (batch_idx // batch_size) + 1
            
            # Preparar dados para este batch
            ids = []
            documents = []
            metadatas = []
            
            for i, chunk in enumerate(batch_chunks):
                chunk_metadata = chunk.get("metadata", {})
                global_idx = batch_idx + i
                
                # ID único: memo_id + chunk_id
                chunk_id = chunk.get("id", f"{memo_id}_chunk_{global_idx}")
                ids.append(chunk_id)
                
                # Documento (texto completo)
                documents.append(chunk.get("text", ""))
                
                # Metadata completo
                metadata = {
                    "memo_id": memo_id,
                    "memo_type": memo_type,
                    "version": version,
                    "section": chunk_metadata.get("full_path") or "unknown",
                    "section_title": chunk_metadata.get("section_title") or "",
                    "section_level": chunk_metadata.get("section_level") or 0,
                    "parent_section": chunk_metadata.get("parent_section") or "",
                    "has_table": bool(chunk_metadata.get("has_table", False)),
                    "chunk_index": chunk_metadata.get("chunk_index") or global_idx,
                    "total_chunks": chunk_metadata.get("total_chunks") or total_chunks,
                }
                
                metadatas.append(metadata)
            
            # Upsert deste batch no ChromaDB
            collection.upsert(
                ids=ids,
                embeddings=batch_embeddings,
                documents=documents,
                metadatas=metadatas
            )
            
            # Log de progresso detalhado
            progress_pct = (current_batch * 100) // total_batches
            elapsed = time.time() - start_time
            rate = current_batch / elapsed if elapsed > 0 else 0
            remaining_batches = total_batches - current_batch
            eta_seconds = remaining_batches / rate if rate > 0 else 0
            
            logger.info(
                f"  ✓ Batch {current_batch}/{total_batches} ({progress_pct}%): "
                f"{len(batch_chunks)} chunks salvos | "
                f"Taxa: {rate:.1f} batches/s | "
                f"ETA: {int(eta_seconds)}s"
            )
        
        total_time = time.time() - start_time
        logger.info(
            f"✅ Upsert completo: {total_chunks} chunks salvos para memo '{memo_id}' "
            f"em {total_time:.1f}s ({total_chunks/total_time:.1f} chunks/s)"
        )
        
    except Exception as e:
        logger.error(f"❌ Erro ao fazer upsert no ChromaDB: {e}")
        raise


def query_memo_chunks(
    collection: chromadb.Collection,
    memo_id: str,
    query_embedding: List[float],
    top_k: int = 10,
    section: Optional[str] = None,
    version: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Busca chunks similares de um memorando.
    
    Args:
        collection: Collection do ChromaDB
        memo_id: ID do memorando (filtro)
        query_embedding: Vetor de embedding da query (1536-dim)
        top_k: Número de resultados a retornar
        section: Filtro opcional por seção (ex: "Fund Overview > Team")
        version: Filtro opcional por versão
        
    Returns:
        Lista de dicts com estrutura:
        [
            {
                "id": str,
                "score": float,
                "metadata": dict,
                "document": str
            },
            ...
        ]
        
    Raises:
        Exception: Se houver erro na busca
    """
    logger.info(
        f"🔍 Buscando {top_k} chunks no memo '{memo_id}' "
        f"(section: {section}, version: {version})"
    )
    
    try:
        # Construir filtro
        where_clause = {"memo_id": {"$eq": memo_id}}
        
        if section:
            where_clause["section"] = {"$eq": section}
        
        if version is not None:
            where_clause["version"] = {"$eq": version}
        
        # Query no ChromaDB
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_clause,
            include=["documents", "metadatas", "distances"]
        )
        
        # Formatar resultados (ChromaDB retorna em formato diferente)
        formatted_results = []
        
        if results["ids"] and len(results["ids"][0]) > 0:
            for i in range(len(results["ids"][0])):
                formatted_results.append({
                    "id": results["ids"][0][i],
                    "score": 1.0 - results["distances"][0][i],  # Converter distância para score (cosine similarity)
                    "metadata": results["metadatas"][0][i],
                    "document": results["documents"][0][i]
                })
        
        logger.info(
            f"✅ Encontrados {len(formatted_results)} chunks "
            f"(score médio: {sum(r['score'] for r in formatted_results) / len(formatted_results) if formatted_results else 0:.3f})"
        )
        
        return formatted_results
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar chunks no ChromaDB: {e}")
        raise


def reset_memo(collection: chromadb.Collection, memo_id: str) -> None:
    """
    Apaga TODOS os chunks de um memorando específico.
    
    Útil quando usuário sobe PDF errado ou quer reprocessar do zero.
    
    Args:
        collection: Collection do ChromaDB
        memo_id: ID do memorando (filtro)
        
    Raises:
        Exception: Se houver erro na deleção
    """
    logger.warning(f"🗑️ Deletando TODOS os chunks do memo '{memo_id}'...")
    
    try:
        # Deletar todos os chunks com memo_id específico
        collection.delete(
            where={"memo_id": {"$eq": memo_id}}
        )
        
        logger.info(f"✅ Chunks do memo '{memo_id}' deletados com sucesso")
        
    except Exception as e:
        logger.error(f"❌ Erro ao deletar chunks do memo '{memo_id}': {e}")
        raise


def get_memo_stats(collection: chromadb.Collection, memo_id: str) -> Dict[str, Any]:
    """
    Retorna estatísticas de um memorando específico.
    
    Args:
        collection: Collection do ChromaDB
        memo_id: ID do memorando
        
    Returns:
        Dict com estatísticas:
        {
            "vector_count": int,
            "memo_id": str
        }
    """
    try:
        # Contar chunks com memo_id específico
        count_result = collection.count(
            where={"memo_id": {"$eq": memo_id}}
        )
        
        return {
            "vector_count": count_result,
            "memo_id": memo_id
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar estatísticas do memo '{memo_id}': {e}")
        return {
            "vector_count": 0,
            "memo_id": memo_id
        }


def search_memo_chunks(
    collection: chromadb.Collection,
    query: str,
    memo_id: Optional[str] = None,
    n_results: int = 5
) -> List[Dict[str, Any]]:
    """
    Busca chunks relevantes usando busca semântica por texto.
    
    Args:
        collection: Collection do ChromaDB
        query: Texto da query/pergunta do usuário
        memo_id: ID do memorando (opcional, para filtrar)
        n_results: Número de resultados a retornar
        
    Returns:
        Lista de dicts com estrutura:
        [
            {
                "text": str,
                "metadata": dict,
                "score": float
            },
            ...
        ]
    """
    try:
        # Gerar embedding da query
        embeddings_model = OpenAIEmbeddings(model="text-embedding-3-small")
        query_embedding = embeddings_model.embed_query(query)
        
        # Construir filtro se memo_id fornecido
        where_clause = None
        if memo_id:
            where_clause = {"memo_id": {"$eq": memo_id}}
        
        # Buscar no ChromaDB
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_clause,
            include=["documents", "metadatas", "distances"]
        )
        
        # Formatar resultados
        formatted_results = []
        
        if results["ids"] and len(results["ids"][0]) > 0:
            for i in range(len(results["ids"][0])):
                formatted_results.append({
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "score": 1.0 - results["distances"][0][i]  # Converter distância para score
                })
        
        logger.info(f"🔍 Busca RAG: {len(formatted_results)} chunks encontrados para query: '{query[:50]}...'")
        
        return formatted_results
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar chunks com RAG: {e}")
        return []
