"""
Markdown Chunker com Preservação de Estrutura Hierárquica

Chunka documentos markdown preservando metadata estrutural:
- Títulos de seções (h1, h2, h3...)
- Hierarquia (seção pai)
- Nível de profundidade
- Tabelas
- Caminho completo da seção

Usado para criar vector store enriquecido com metadata para extração precisa.
"""

import re
from typing import List, Dict, Optional, Tuple
from core.logger import get_logger

logger = get_logger(__name__)


class MarkdownChunker:
    """
    Chunka markdown PRESERVANDO estrutura hierárquica como metadata.
    
    Diferente de chunking burro (texto corrido), mantém informação sobre:
    - Em qual seção o chunk está
    - Qual o nível hierárquico (h1, h2, h3)
    - Qual a seção pai
    - Se contém tabelas
    """
    
    def __init__(self, chunk_size: int = 4000, overlap: int = 200):
        """
        Args:
            chunk_size: Tamanho máximo de cada chunk em caracteres
            overlap: Overlap entre chunks (para não perder contexto)
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        
        # Regex patterns
        self.header_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
        self.table_pattern = re.compile(r'^\|.+\|$', re.MULTILINE)
    
    def chunk_with_metadata(self, markdown_text: str) -> List[Dict]:
        """
        Chunka markdown preservando hierarquia como metadata.
        
        Args:
            markdown_text: Texto em formato markdown
        
        Returns:
            Lista de chunks com metadata:
            [
              {
                "text": "conteúdo do chunk...",
                "metadata": {
                  "section_title": "Fund Overview",
                  "section_level": 1,
                  "parent_section": None,
                  "full_path": "Fund Overview",
                  "has_table": False,
                  "chunk_index": 0
                }
              },
              ...
            ]
        """
        if not markdown_text or not markdown_text.strip():
            logger.warning("Markdown vazio recebido")
            return []
        
        # 1. Parse estrutura de seções
        sections = self._parse_sections(markdown_text)
        
        if not sections:
            # Fallback: documento sem headers, trata como uma seção única
            logger.warning("Nenhum header encontrado no markdown, criando seção única")
            sections = [{
                "title": "Document",
                "level": 1,
                "content": markdown_text,
                "parent": None,
                "start_pos": 0,
                "end_pos": len(markdown_text),
                "has_table": self._contains_table(markdown_text)
            }]
        
        logger.info(f"📄 Markdown parseado: {len(sections)} seções identificadas")
        
        # 2. Chunkar cada seção preservando metadata
        all_chunks = []
        
        for section in sections:
            section_chunks = self._chunk_section(section, sections)
            all_chunks.extend(section_chunks)
        
        logger.info(f"✂️ Total de {len(all_chunks)} chunks com metadata criados")
        
        return all_chunks
    
    def _parse_sections(self, markdown_text: str) -> List[Dict]:
        """
        Parse markdown identificando seções e hierarquia.
        
        Returns:
            Lista de seções com metadata hierárquica
        """
        sections = []
        section_stack = []  # Stack para tracking de hierarquia
        
        lines = markdown_text.split('\n')
        current_section = None
        current_content = []
        current_start = 0
        
        for i, line in enumerate(lines):
            # Detectar header
            header_match = self.header_pattern.match(line)
            
            if header_match:
                # Salvar seção anterior se existir
                if current_section:
                    content = '\n'.join(current_content)
                    sections.append({
                        "title": current_section["title"],
                        "level": current_section["level"],
                        "content": content,
                        "parent": current_section.get("parent"),
                        "start_pos": current_start,
                        "end_pos": current_start + len(content),
                        "has_table": self._contains_table(content)
                    })
                
                # Parse novo header
                level = len(header_match.group(1))  # Número de #
                title = header_match.group(2).strip()
                
                # Atualizar stack de hierarquia
                # Remove seções do stack com nível >= atual
                while section_stack and section_stack[-1]["level"] >= level:
                    section_stack.pop()
                
                # Determinar seção pai
                parent = section_stack[-1]["title"] if section_stack else None
                
                # Nova seção
                current_section = {
                    "title": title,
                    "level": level,
                    "parent": parent
                }
                
                # Adicionar ao stack
                section_stack.append({"title": title, "level": level})
                
                # Reset conteúdo
                current_content = []
                current_start = sum(len(l) + 1 for l in lines[:i+1])
            else:
                # Linha de conteúdo
                current_content.append(line)
        
        # Salvar última seção
        if current_section:
            content = '\n'.join(current_content)
            sections.append({
                "title": current_section["title"],
                "level": current_section["level"],
                "content": content,
                "parent": current_section.get("parent"),
                "start_pos": current_start,
                "end_pos": current_start + len(content),
                "has_table": self._contains_table(content)
            })
        
        return sections
    
    def _chunk_section(self, section: Dict, all_sections: List[Dict]) -> List[Dict]:
        """
        Chunka uma seção individual, preservando metadata.
        
        Args:
            section: Seção a ser chunkada
            all_sections: Todas as seções (para construir path)
        
        Returns:
            Lista de chunks com metadata dessa seção
        """
        content = section["content"]
        section_path = self._get_section_path(section, all_sections)
        
        chunks = []
        
        # Se conteúdo cabe em 1 chunk
        if len(content) <= self.chunk_size:
            chunks.append({
                "text": content.strip(),
                "metadata": {
                    "section_title": section["title"],
                    "section_level": section["level"],
                    "parent_section": section["parent"],
                    "full_path": section_path,
                    "has_table": section.get("has_table", False),
                    "chunk_index": 0,
                    "total_chunks": 1
                }
            })
        else:
            # Dividir em múltiplos chunks com overlap
            chunk_texts = self._split_with_overlap(content)
            
            for idx, chunk_text in enumerate(chunk_texts):
                chunks.append({
                    "text": chunk_text.strip(),
                    "metadata": {
                        "section_title": section["title"],
                        "section_level": section["level"],
                        "parent_section": section["parent"],
                        "full_path": section_path,
                        "has_table": section.get("has_table", False),
                        "chunk_index": idx,
                        "total_chunks": len(chunk_texts)
                    }
                })
        
        return chunks
    
    def _split_with_overlap(self, text: str) -> List[str]:
        """
        Divide texto em chunks com overlap.
        
        Args:
            text: Texto a ser dividido
        
        Returns:
            Lista de chunks com overlap
        """
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # Se não é o último chunk, tenta quebrar em espaço/newline
            if end < len(text):
                # Procura último espaço/newline antes do limite
                breakpoint = text.rfind('\n', start, end)
                if breakpoint == -1:
                    breakpoint = text.rfind(' ', start, end)
                if breakpoint > start:
                    end = breakpoint
            
            chunk = text[start:end]
            chunks.append(chunk)
            
            # Próximo chunk começa com overlap
            start = end - self.overlap if end - self.overlap > start else end
        
        return chunks
    
    def _get_section_path(self, section: Dict, all_sections: List[Dict]) -> str:
        """
        Retorna caminho completo da seção (ex: 'Fund Overview > Team > Partners').
        
        Args:
            section: Seção atual
            all_sections: Todas as seções (para encontrar pais)
        
        Returns:
            String com caminho hierárquico completo
        """
        path = [section["title"]]
        parent = section["parent"]
        
        # Subir na hierarquia até o topo
        while parent:
            path.insert(0, parent)
            # Encontrar seção pai
            parent_section = next(
                (s for s in all_sections if s["title"] == parent),
                None
            )
            parent = parent_section["parent"] if parent_section else None
        
        return " > ".join(path)
    
    def _contains_table(self, text: str) -> bool:
        """
        Verifica se o texto contém tabelas markdown.
        
        Args:
            text: Texto a verificar
        
        Returns:
            True se contém tabela
        """
        return bool(self.table_pattern.search(text))
    
    def extract_tables(self, markdown_text: str) -> List[Dict]:
        """
        Extrai todas as tabelas do markdown.
        
        Args:
            markdown_text: Texto markdown
        
        Returns:
            Lista de tabelas parseadas:
            [
              {
                "headers": ["Year", "IRR", "MOIC"],
                "rows": [
                  {"Year": "2020", "IRR": "25%", "MOIC": "2.1x"},
                  ...
                ]
              }
            ]
        """
        tables = []
        lines = markdown_text.split('\n')
        
        in_table = False
        table_lines = []
        
        for line in lines:
            if self.table_pattern.match(line):
                if not in_table:
                    in_table = True
                    table_lines = [line]
                else:
                    table_lines.append(line)
            elif in_table:
                # Fim da tabela
                parsed_table = self._parse_table(table_lines)
                if parsed_table:
                    tables.append(parsed_table)
                
                in_table = False
                table_lines = []
        
        # Última tabela se o documento terminou com ela
        if in_table and table_lines:
            parsed_table = self._parse_table(table_lines)
            if parsed_table:
                tables.append(parsed_table)
        
        return tables
    
    def _parse_table(self, table_lines: List[str]) -> Optional[Dict]:
        """
        Parse tabela markdown para estrutura dict.
        
        Args:
            table_lines: Linhas da tabela em markdown
        
        Returns:
            Dict com headers e rows, ou None se inválido
        """
        if len(table_lines) < 2:  # Precisa header + separator no mínimo
            return None
        
        try:
            # Header
            headers = [h.strip() for h in table_lines[0].split('|')[1:-1]]
            
            # Rows (pula linha de separação)
            rows = []
            for line in table_lines[2:]:
                if '|' in line:
                    cells = [c.strip() for c in line.split('|')[1:-1]]
                    if len(cells) == len(headers):
                        row = dict(zip(headers, cells))
                        rows.append(row)
            
            return {
                "headers": headers,
                "rows": rows
            }
        except Exception as e:
            logger.warning(f"Erro ao parsear tabela: {e}")
            return None
