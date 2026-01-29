"""
Template Loader para Short Memo - Co-investimento (Search Fund)

Carrega templates estruturados de seções e fornece helpers
para validação e uso nos agentes de geração.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class SectionTemplate:
    """Representa um template de seção"""
    title: str
    structure: Dict[str, Any]
    tone: str
    must_include: List[str]
    recommended_include: List[str]
    writing_guidelines: List[str]
    examples: List[Dict[str, str]]
    
    def get_prompt_context(self) -> str:
        """Retorna contexto formatado para incluir em prompts"""
        context = f"""
ESTRUTURA DA SEÇÃO "{self.title}":
{self.structure.get('description', 'N/A')}

TOM: {self.tone}

DIRETRIZES DE ESCRITA:
{chr(10).join(f"• {guideline}" for guideline in self.writing_guidelines)}

CAMPOS OBRIGATÓRIOS:
{', '.join(self.must_include)}

CAMPOS RECOMENDADOS:
{', '.join(self.recommended_include)}
"""
        return context.strip()
    
    def get_examples_text(self, max_examples: int = 2) -> str:
        """Retorna exemplos formatados para few-shot learning"""
        if not self.examples:
            return ""
        
        examples_text = "\n\nEXEMPLOS DE QUALIDADE (SHORT MEMOS REAIS):\n"
        examples_text += "=" * 60 + "\n"
        
        for i, example in enumerate(self.examples[:max_examples], 1):
            context = example.get('context', 'Geral')
            text = example.get('text', '')
            
            # Se for uma lista de bullets, formatar adequadamente
            if isinstance(text, list):
                text = '\n'.join(f"  {bullet}" for bullet in text)
            
            examples_text += f"\n[Exemplo {i}: {context}]\n{text}\n"
            if i < len(self.examples[:max_examples]):
                examples_text += "\n" + "-" * 60 + "\n"
        
        return examples_text
    
    def validate_facts(self, facts: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida se os facts contêm os campos necessários
        
        Returns:
            Dict com 'missing_must' e 'missing_recommended'
        """
        all_facts_keys = set()
        for section_facts in facts.values():
            if isinstance(section_facts, dict):
                all_facts_keys.update(section_facts.keys())
        
        missing_must = [
            field for field in self.must_include
            if field not in all_facts_keys
        ]
        
        missing_recommended = [
            field for field in self.recommended_include
            if field not in all_facts_keys
        ]
        
        return {
            'missing_must': missing_must,
            'missing_recommended': missing_recommended,
            'coverage_pct': (
                (len(self.must_include) - len(missing_must)) / 
                len(self.must_include) * 100
            ) if self.must_include else 100.0
        }


class TemplateLoader:
    """Carrega e gerencia templates de seções"""
    
    def __init__(self, template_file: Optional[Path] = None):
        if template_file is None:
            # Default: buscar no diretório atual
            current_dir = Path(__file__).parent
            template_file = current_dir / "section_templates.json"
        
        self.template_file = Path(template_file)
        self.templates = self._load_templates()
        self.global_guidelines = self._load_global_guidelines()
    
    def _load_templates(self) -> Dict[str, SectionTemplate]:
        """Carrega templates do arquivo JSON"""
        if not self.template_file.exists():
            raise FileNotFoundError(
                f"Template file not found: {self.template_file}"
            )
        
        with open(self.template_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        templates = {}
        for section_key, section_data in data.get('templates', {}).items():
            templates[section_key] = SectionTemplate(
                title=section_data.get('title', section_key),
                structure=section_data.get('structure', {}),
                tone=section_data.get('tone', 'profissional'),
                must_include=section_data.get('must_include', []),
                recommended_include=section_data.get('recommended_include', []),
                writing_guidelines=section_data.get('writing_guidelines', []),
                examples=section_data.get('examples', [])
            )
        
        return templates
    
    def _load_global_guidelines(self) -> Dict[str, Any]:
        """Carrega guidelines globais"""
        with open(self.template_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('global_guidelines', {})
    
    def get_template(self, section: str) -> Optional[SectionTemplate]:
        """Retorna template de uma seção específica"""
        return self.templates.get(section)
    
    def get_all_sections(self) -> List[str]:
        """Retorna lista de todas as seções disponíveis"""
        return list(self.templates.keys())
    
    def validate_all_facts(self, facts: Dict[str, Any]) -> Dict[str, Dict]:
        """
        Valida facts contra todos os templates
        
        Returns:
            Dict com validação por seção
        """
        validation_results = {}
        
        for section, template in self.templates.items():
            validation_results[section] = template.validate_facts(facts)
        
        return validation_results
    
    def get_global_guidelines(self) -> Dict[str, Any]:
        """Retorna guidelines globais do template"""
        return self.global_guidelines
    
    def enrich_prompt(
        self, 
        section: str, 
        base_prompt: str,
        include_examples: bool = True,
        max_examples: int = 2
    ) -> str:
        """
        Enriquece um prompt base com template context
        
        Args:
            section: Nome da seção (ex: 'intro', 'mercado')
            base_prompt: Prompt original
            include_examples: Se deve incluir exemplos
            max_examples: Número máximo de exemplos
            
        Returns:
            Prompt enriquecido com template guidelines
        """
        template = self.get_template(section)
        if not template:
            return base_prompt
        
        enriched = base_prompt + "\n\n"
        enriched += "=" * 60 + "\n"
        enriched += "TEMPLATE ESTRUTURADO:\n"
        enriched += "=" * 60 + "\n"
        enriched += template.get_prompt_context()
        
        if include_examples:
            enriched += "\n" + template.get_examples_text(max_examples)
        
        # Adicionar guidelines globais de tom e formato
        tone_guidelines = self.global_guidelines.get('tone', {})
        if tone_guidelines:
            enriched += "\n\n" + "=" * 60 + "\n"
            enriched += "DIRETRIZES GLOBAIS DE TOM:\n"
            enriched += f"• Perspectiva: {tone_guidelines.get('perspective', 'terceira pessoa')}\n"
            enriched += f"• Estilo: {tone_guidelines.get('style', 'analítico')}\n"
            
            avoid_list = tone_guidelines.get('avoid', [])
            if avoid_list:
                enriched += f"\nEVITAR:\n"
                for item in avoid_list:
                    enriched += f"  ❌ {item}\n"
            
            prefer_list = tone_guidelines.get('prefer', [])
            if prefer_list:
                enriched += f"\nPREFERIR:\n"
                for item in prefer_list:
                    enriched += f"  ✅ {item}\n"
        
        return enriched


# Singleton global para uso fácil
_template_loader = None

def get_template_loader() -> TemplateLoader:
    """Retorna instância global do TemplateLoader"""
    global _template_loader
    if _template_loader is None:
        _template_loader = TemplateLoader()
    return _template_loader


# Helper functions para uso direto
def get_template(section: str) -> Optional[SectionTemplate]:
    """Helper: retorna template de uma seção"""
    return get_template_loader().get_template(section)


def enrich_prompt(section: str, prompt: str, include_examples: bool = True) -> str:
    """Helper: enriquece prompt com template"""
    return get_template_loader().enrich_prompt(section, prompt, include_examples)


def validate_facts(facts: Dict[str, Any]) -> Dict[str, Dict]:
    """Helper: valida facts contra templates"""
    return get_template_loader().validate_all_facts(facts)


def get_global_guidelines() -> Dict[str, Any]:
    """Helper: retorna guidelines globais"""
    return get_template_loader().get_global_guidelines()
