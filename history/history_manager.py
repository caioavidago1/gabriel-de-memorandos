"""
Sistema de Gerenciamento de Histórico de Memos

Permite salvar, carregar, listar e buscar memos gerados anteriormente.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any


class MemoHistoryManager:
    """Gerencia histórico de memos com CRUD completo"""
    
    def __init__(self, storage_path: str = "history/memo_history.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Inicializar storage se não existir
        if not self.storage_path.exists():
            self._save_store({
                "version": "1.0",
                "created_at": datetime.now().isoformat(),
                "memos": []
            })
    
    # === CRUD OPERATIONS ===
    
    def save_memo(
        self,
        memo_type: str,
        custom_fields: List[str],
        field_paragraphs: Dict[str, List[str]],
        facts_edited: Dict[str, Dict],
        generation_metadata: Optional[Dict] = None,
        tags: List[str] = None,
        notes: str = "",
        memo_name: Optional[str] = None
    ) -> str:
        """
        Salva um memo no histórico
        
        Returns:
            memo_id (str): ID único do memo salvo
        """
        store = self._load_store()
        
        # Gerar ID único
        memo_id = str(uuid.uuid4())
        
        # Extrair company name dos facts
        company_name = self._extract_company_name(facts_edited)
        
        # Construir seções
        sections = []
        total_paragraphs = 0
        total_words = 0
        
        for field_name in custom_fields:
            paragraphs = field_paragraphs.get(field_name, [])
            sections.append({
                "section_name": field_name,
                "paragraphs": paragraphs,
                "generation_metadata": generation_metadata or {}
            })
            total_paragraphs += len(paragraphs)
            total_words += sum(len(p.split()) for p in paragraphs)
        
        # Tags não são mais usadas, manter como None para compatibilidade
        if tags is None:
            tags = []
        
        # Calcular estatísticas
        examples_used = []
        
        if generation_metadata:
            for section in sections:
                meta = section.get("generation_metadata", {})
                if "examples_used" in meta:
                    examples_used.append(meta["examples_used"])
        
        total_examples = sum(examples_used) if examples_used else 0
        
        # Criar memo object
        memo = {
            "id": memo_id,
            "memo_type": memo_type,
            "company_name": company_name,
            "memo_name": memo_name or f"{company_name} - {memo_type}",
            "saved_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "sections": sections,
            "facts_snapshot": facts_edited,
            "statistics": {
                "total_sections": len(sections),
                "total_paragraphs": total_paragraphs,
                "word_count": total_words,
                "total_examples_used": total_examples
            },
            "tags": tags,
            "notes": notes
        }
        
        # Adicionar ao store
        store["memos"].append(memo)
        self._save_store(store)
        
        return memo_id
    
    def load_memo(self, memo_id: str) -> Optional[Dict]:
        """Carrega um memo por ID"""
        store = self._load_store()
        
        for memo in store["memos"]:
            if memo["id"] == memo_id:
                return memo
        
        return None
    
    def update_memo(
        self,
        memo_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Atualiza campos específicos de um memo
        
        Args:
            memo_id: ID do memo
            updates: Dict com campos a atualizar (tags, notes, sections, etc)
        
        Returns:
            bool: True se atualizado com sucesso
        """
        store = self._load_store()
        
        for memo in store["memos"]:
            if memo["id"] == memo_id:
                # Atualizar campos permitidos
                allowed_fields = ["tags", "notes", "sections", "field_paragraphs", "memo_type"]
                for key, value in updates.items():
                    if key in allowed_fields:
                        memo[key] = value
                
                memo["updated_at"] = datetime.now().isoformat()
                
                self._save_store(store)
                return True
        
        return False
    
    def delete_memo(self, memo_id: str) -> bool:
        """Deleta um memo do histórico"""
        store = self._load_store()
        
        original_length = len(store["memos"])
        store["memos"] = [m for m in store["memos"] if m["id"] != memo_id]
        
        if len(store["memos"]) < original_length:
            self._save_store(store)
            return True
        
        return False
    
    # === LISTING & FILTERING ===
    
    def list_memos(
        self,
        memo_type: Optional[str] = None,
        company_name: Optional[str] = None,
        tags: Optional[List[str]] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        sort_by: str = "saved_at",
        limit: int = 50
    ) -> List[Dict]:
        """
        Lista memos com filtros opcionais
        
        Args:
            memo_type: Filtrar por tipo
            company_name: Buscar por nome (case-insensitive partial match)
            tags: Filtrar por tags (qualquer match)
            date_from: Data inicial (ISO format)
            date_to: Data final (ISO format)
            sort_by: Campo para ordenar ("saved_at", "company_name", "quality_score")
            limit: Máximo de resultados
        
        Returns:
            Lista de memos (summary, não full object)
        """
        store = self._load_store()
        memos = store["memos"]
        
        # Filtros
        if memo_type:
            memos = [m for m in memos if memo_type.lower() in m["memo_type"].lower()]
        
        if company_name:
            memos = [m for m in memos if company_name.lower() in m["company_name"].lower()]
        
        if tags:
            memos = [m for m in memos if any(tag in m.get("tags", []) for tag in tags)]
        
        if date_from:
            memos = [m for m in memos if m["saved_at"] >= date_from]
        
        if date_to:
            memos = [m for m in memos if m["saved_at"] <= date_to]
        
        # Ordenar
        reverse = True  # Mais recente primeiro por padrão
        
        if sort_by == "saved_at":
            memos.sort(key=lambda m: m["saved_at"], reverse=reverse)
        elif sort_by == "company_name":
            memos.sort(key=lambda m: m["company_name"].lower())
            reverse = False
        elif sort_by == "quality_score":
            memos.sort(key=lambda m: m["statistics"].get("avg_quality_score", 0), reverse=reverse)
        
        # Limitar
        memos = memos[:limit]
        
        # Retornar summary
        return [self._memo_summary(m) for m in memos]
    
    def search_memos(self, query: str) -> List[Dict]:
        """Busca full-text em company name, tags, notes"""
        store = self._load_store()
        query_lower = query.lower()
        
        results = []
        for memo in store["memos"]:
            # Buscar em múltiplos campos
            searchable = " ".join([
                memo["company_name"],
                " ".join(memo.get("tags", [])),
                memo.get("notes", "")
            ]).lower()
            
            if query_lower in searchable:
                results.append(self._memo_summary(memo))
        
        return results
    
    # === STATISTICS ===
    
    def get_statistics(self) -> Dict:
        """Retorna estatísticas agregadas do histórico"""
        store = self._load_store()
        memos = store["memos"]
        
        if not memos:
            return {
                "total_memos": 0,
                "by_type": {},
                "avg_quality": 0,
                "total_sections": 0,
                "total_paragraphs": 0
            }
        
        # Agregações
        by_type = {}
        quality_scores = []
        total_sections = 0
        total_paragraphs = 0
        
        for memo in memos:
            # Por tipo
            memo_type = memo["memo_type"]
            by_type[memo_type] = by_type.get(memo_type, 0) + 1
            
            # Qualidade
            avg_q = memo["statistics"].get("avg_quality_score", 0)
            if avg_q > 0:
                quality_scores.append(avg_q)
            
            # Contadores
            total_sections += memo["statistics"].get("total_sections", 0)
            total_paragraphs += memo["statistics"].get("total_paragraphs", 0)
        
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        return {
            "total_memos": len(memos),
            "by_type": by_type,
            "avg_quality": round(avg_quality, 1),
            "total_sections": total_sections,
            "total_paragraphs": total_paragraphs,
            "latest_save": memos[-1]["saved_at"] if memos else None
        }
    
    def get_memo_details(self, memo_id: str) -> Optional[Dict]:
        """Retorna detalhes completos de um memo (incluindo facts)"""
        return self.load_memo(memo_id)
    
    # === EXPORT/IMPORT ===
    
    def export_memo_json(self, memo_id: str) -> Optional[str]:
        """Exporta um memo como JSON string"""
        memo = self.load_memo(memo_id)
        if memo:
            return json.dumps(memo, indent=2, ensure_ascii=False)
        return None
    
    def import_memo_json(self, json_str: str) -> Optional[str]:
        """
        Importa um memo de JSON string
        
        Returns:
            novo memo_id se sucesso, None se erro
        """
        try:
            memo_data = json.loads(json_str)
            
            # Gerar novo ID (evitar conflitos)
            new_id = str(uuid.uuid4())
            memo_data["id"] = new_id
            memo_data["saved_at"] = datetime.now().isoformat()
            memo_data["updated_at"] = datetime.now().isoformat()
            
            # Adicionar ao store
            store = self._load_store()
            store["memos"].append(memo_data)
            self._save_store(store)
            
            return new_id
        
        except Exception as e:
            print(f"Erro ao importar memo: {e}")
            return None
    
    # === INTERNAL HELPERS ===
    
    def _load_store(self) -> Dict:
        """Carrega o arquivo JSON de storage"""
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar storage: {e}")
            return {"version": "1.0", "memos": []}
    
    def _save_store(self, data: Dict) -> None:
        """Salva o arquivo JSON de storage"""
        try:
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar storage: {e}")
    
    def _extract_company_name(self, facts: Dict) -> str:
        """Extrai o nome da empresa dos facts"""
        # Tentar múltiplos campos
        if "identification" in facts:
            id_facts = facts["identification"]
            if isinstance(id_facts, dict):
                return (
                    id_facts.get("company_name") or
                    id_facts.get("nome_empresa") or
                    id_facts.get("target_name") or
                    "Unnamed Company"
                )
        
        # Fallback
        for section in facts.values():
            if isinstance(section, dict):
                for key in ["company_name", "nome_empresa", "target", "empresa"]:
                    if key in section and section[key]:
                        return section[key]
        
        return "Unnamed Company"
    
    def _generate_tags(self, facts: Dict, memo_type: str) -> List[str]:
        """Auto-gera tags baseado em facts e tipo"""
        tags = []
        
        # Tag do tipo
        if "Primário" in memo_type or "primario" in memo_type.lower():
            tags.append("Primário")
        elif "Search Fund" in memo_type or "searchfund" in memo_type.lower():
            tags.append("Search Fund")
        elif "Secundário" in memo_type or "secundario" in memo_type.lower():
            tags.append("Secundário")
        elif "Gestora" in memo_type:
            tags.append("Gestora")
        
        # Tags de setor (buscar em identification)
        if "identification" in facts:
            id_facts = facts["identification"]
            if isinstance(id_facts, dict):
                sector = id_facts.get("sector") or id_facts.get("setor") or ""
                if sector:
                    tags.append(sector)
                
                # Detectar SaaS/Tech
                business = str(id_facts.get("business_model", "")).lower()
                if "saas" in business or "software" in business:
                    tags.append("SaaS")
                if "tech" in business or "tecnologia" in business:
                    tags.append("Tech")
                if "b2b" in business:
                    tags.append("B2B")
                if "b2c" in business:
                    tags.append("B2C")
        
        return tags[:6]  # Limitar a 6 tags
    
    def _memo_summary(self, memo: Dict) -> Dict:
        """Retorna versão resumida do memo para listagem"""
        return {
            "id": memo["id"],
            "company_name": memo["company_name"],
            "memo_type": memo["memo_type"],
            "saved_at": memo["saved_at"],
            "updated_at": memo["updated_at"],
            "tags": memo.get("tags", []),
            "notes": memo.get("notes", ""),
            "statistics": memo.get("statistics", {}),
            "section_count": len(memo.get("sections", [])),
            "has_facts": bool(memo.get("facts_snapshot"))
        }
