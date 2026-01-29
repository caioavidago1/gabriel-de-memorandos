"""
Extrator de Tabelas Específicas para Memorandos Search Fund

Extrai tabelas estruturadas de documentos para:
- Projeções financeiras (cenários base/upside/downside)
- Retornos esperados (IRR/MOIC por cenário)
- Board composition
- Cap table de investidores
"""

import re
from typing import List, Dict, Optional, Any
from core.logger import get_logger

logger = get_logger(__name__)


class TableExtractor:
    """Classe especializada para extrair tabelas de memorandos Search Fund"""
    
    def __init__(self):
        self.table_pattern = re.compile(r'^\|.+\|$', re.MULTILINE)
    
    def extract_projections_table(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extrai tabelas de projeções financeiras do texto.
        
        Procura por tabelas que contenham:
        - Anos (2023, 2024, etc)
        - Receita/Revenue
        - EBITDA
        - Margem
        
        Returns:
            Dict com estrutura de projeções ou None
        """
        # Buscar seção de projeções
        projections_section = self._extract_section(text, [
            "projeções financeiras",
            "financial projections",
            "cenário base",
            "base case",
            "projections"
        ])
        
        if not projections_section:
            return None
        
        # Extrair tabelas da seção
        tables = self._extract_tables_from_text(projections_section)
        
        # Identificar qual tabela é qual cenário
        result = {}
        
        for table in tables:
            # Verificar se é tabela de projeções (tem anos e valores financeiros)
            if self._is_projections_table(table):
                # Identificar cenário
                scenario = self._identify_scenario(table, projections_section)
                
                # Extrair dados da tabela
                table_data = self._parse_projections_table(table)
                
                if scenario and table_data:
                    result[f"projections_{scenario}_case"] = table_data
        
        return result if result else None
    
    def extract_returns_table(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extrai tabelas de retornos (IRR/MOIC) do texto.
        
        Procura por tabelas que contenham:
        - IRR/TIR
        - MOIC
        - Exit year
        - Exit multiple
        
        Returns:
            Dict com estrutura de retornos ou None
        """
        # Buscar seção de retornos
        returns_section = self._extract_section(text, [
            "retornos esperados",
            "expected returns",
            "returns",
            "IRR",
            "MOIC",
            "sensibilidade"
        ])
        
        if not returns_section:
            return None
        
        # Extrair tabelas da seção
        tables = self._extract_tables_from_text(returns_section)
        
        result = {}
        
        for table in tables:
            # Verificar se é tabela de retornos (tem IRR/MOIC)
            if self._is_returns_table(table):
                # Identificar tipo de tabela
                table_type = self._identify_returns_table_type(table, returns_section)
                
                # Extrair dados da tabela
                table_data = self._parse_returns_table(table)
                
                if table_type and table_data:
                    result[table_type] = table_data
        
        return result if result else None
    
    def extract_board_table(self, text: str) -> Optional[List[Dict[str, str]]]:
        """
        Extrai composição do board do texto.
        
        Returns:
            Lista de membros do board ou None
        """
        # Buscar seção de board
        board_section = self._extract_section(text, [
            "board",
            "conselho",
            "board members",
            "board of directors"
        ])
        
        if not board_section:
            return None
        
        # Extrair tabelas ou listas
        tables = self._extract_tables_from_text(board_section)
        
        for table in tables:
            if self._is_board_table(table):
                return self._parse_board_table(table)
        
        # Se não encontrou tabela, tentar extrair de texto estruturado
        return self._parse_board_from_text(board_section)
    
    def extract_cap_table(self, text: str) -> Optional[List[Dict[str, Any]]]:
        """
        Extrai cap table de investidores do texto.
        
        Returns:
            Lista de investidores ou None
        """
        # Buscar seção de cap table
        cap_table_section = self._extract_section(text, [
            "cap table",
            "investidores",
            "investors",
            "base de investidores"
        ])
        
        if not cap_table_section:
            return None
        
        # Extrair tabelas da seção
        tables = self._extract_tables_from_text(cap_table_section)
        
        for table in tables:
            if self._is_cap_table(table):
                return self._parse_cap_table(table)
        
        # Se não encontrou tabela, tentar extrair de texto estruturado
        return self._parse_cap_table_from_text(cap_table_section)
    
    def _extract_section(self, text: str, keywords: List[str]) -> Optional[str]:
        """Extrai seção do texto baseado em keywords"""
        text_lower = text.lower()
        
        for keyword in keywords:
            # Buscar título de seção com keyword
            pattern = re.compile(
                rf'(?:^|\n)(?:#+\s*)?(?:.*{re.escape(keyword)}.*?)(?:\n|$)',
                re.IGNORECASE | re.MULTILINE
            )
            
            matches = list(pattern.finditer(text))
            if matches:
                # Pegar contexto após o match (próximas 2000 caracteres)
                start = matches[0].start()
                end = min(start + 2000, len(text))
                return text[start:end]
        
        return None
    
    def _extract_tables_from_text(self, text: str) -> List[List[str]]:
        """Extrai todas as tabelas markdown do texto"""
        tables = []
        lines = text.split('\n')
        
        current_table = []
        in_table = False
        
        for line in lines:
            if self.table_pattern.match(line.strip()):
                if not in_table:
                    in_table = True
                    current_table = [line.strip()]
                else:
                    current_table.append(line.strip())
            elif in_table:
                # Fim da tabela
                if len(current_table) >= 2:  # Header + separator mínimo
                    tables.append(current_table)
                in_table = False
                current_table = []
        
        # Última tabela se o texto terminar com ela
        if in_table and len(current_table) >= 2:
            tables.append(current_table)
        
        return tables
    
    def _is_projections_table(self, table: List[str]) -> bool:
        """Verifica se a tabela é de projeções financeiras"""
        if len(table) < 2:
            return False
        
        header = table[0].lower()
        # Deve ter ano e valores financeiros
        has_year = any(keyword in header for keyword in ['ano', 'year', '202', '2023', '2024'])
        has_financial = any(keyword in header for keyword in ['receita', 'revenue', 'ebitda', 'margem', 'margin'])
        
        return has_year and has_financial
    
    def _is_returns_table(self, table: List[str]) -> bool:
        """Verifica se a tabela é de retornos"""
        if len(table) < 2:
            return False
        
        header = table[0].lower()
        has_returns = any(keyword in header for keyword in ['irr', 'tir', 'moic', 'retorno', 'return'])
        
        return has_returns
    
    def _is_board_table(self, table: List[str]) -> bool:
        """Verifica se a tabela é de board"""
        if len(table) < 2:
            return False
        
        header = table[0].lower()
        has_board = any(keyword in header for keyword in ['nome', 'name', 'membro', 'member', 'background', 'indicação'])
        
        return has_board
    
    def _is_cap_table(self, table: List[str]) -> bool:
        """Verifica se a tabela é de cap table"""
        if len(table) < 2:
            return False
        
        header = table[0].lower()
        has_investor = any(keyword in header for keyword in ['investidor', 'investor', 'contribution', 'contribuição', 'pct', '%'])
        
        return has_investor
    
    def _identify_scenario(self, table: List[str], context: str) -> Optional[str]:
        """Identifica qual cenário a tabela representa"""
        context_lower = context.lower()
        
        # Verificar contexto antes/depois da tabela
        if 'base' in context_lower or 'cenário base' in context_lower:
            return 'base'
        elif 'upside' in context_lower or 'otimista' in context_lower:
            return 'upside'
        elif 'downside' in context_lower or 'pessimista' in context_lower:
            return 'downside'
        
        return 'base'  # Default
    
    def _identify_returns_table_type(self, table: List[str], context: str) -> Optional[str]:
        """Identifica o tipo de tabela de retornos"""
        context_lower = context.lower()
        
        if 'sensibilidade' in context_lower or 'sensitivity' in context_lower:
            return 'returns_sensitivity_table'
        elif 'cenário' in context_lower or 'scenario' in context_lower:
            return 'returns_exit_scenarios'
        else:
            return 'returns_base_case'
    
    def _parse_projections_table(self, table: List[str]) -> Optional[List[Dict]]:
        """Parse de tabela de projeções"""
        if len(table) < 3:  # Header + separator + pelo menos uma linha
            return None
        
        # Parse header
        headers = [h.strip() for h in table[0].split('|') if h.strip()]
        
        # Encontrar índices das colunas relevantes
        year_idx = None
        revenue_idx = None
        ebitda_idx = None
        margin_idx = None
        
        for i, header in enumerate(headers):
            header_lower = header.lower()
            if 'ano' in header_lower or 'year' in header_lower:
                year_idx = i
            elif 'receita' in header_lower or 'revenue' in header_lower:
                revenue_idx = i
            elif 'ebitda' in header_lower:
                ebitda_idx = i
            elif 'margem' in header_lower or 'margin' in header_lower:
                margin_idx = i
        
        if year_idx is None:
            return None
        
        # Parse linhas (pular header e separator)
        rows = []
        for line in table[2:]:  # Pular header e separator
            cells = [c.strip() for c in line.split('|') if c.strip()]
            if len(cells) <= year_idx:
                continue
            
            row = {}
            
            # Extrair ano
            year_str = cells[year_idx] if year_idx < len(cells) else ""
            year_match = re.search(r'20\d{2}', year_str)
            if year_match:
                try:
                    row['year'] = int(year_match.group())
                except:
                    pass
            
            # Extrair receita
            if revenue_idx is not None and revenue_idx < len(cells):
                revenue_str = cells[revenue_idx]
                revenue_val = self._extract_number(revenue_str)
                if revenue_val:
                    row['revenue_mm'] = revenue_val
            
            # Extrair EBITDA
            if ebitda_idx is not None and ebitda_idx < len(cells):
                ebitda_str = cells[ebitda_idx]
                ebitda_val = self._extract_number(ebitda_str)
                if ebitda_val:
                    row['ebitda_mm'] = ebitda_val
            
            # Extrair margem
            if margin_idx is not None and margin_idx < len(cells):
                margin_str = cells[margin_idx]
                margin_val = self._extract_number(margin_str)
                if margin_val:
                    row['ebitda_margin_pct'] = margin_val
            
            if row:
                rows.append(row)
        
        return rows if rows else None
    
    def _parse_returns_table(self, table: List[str]) -> Optional[Dict]:
        """Parse de tabela de retornos"""
        if len(table) < 3:
            return None
        
        headers = [h.strip() for h in table[0].split('|') if h.strip()]
        
        # Encontrar índices
        irr_idx = None
        moic_idx = None
        exit_year_idx = None
        exit_multiple_idx = None
        
        for i, header in enumerate(headers):
            header_lower = header.lower()
            if 'irr' in header_lower or 'tir' in header_lower:
                irr_idx = i
            elif 'moic' in header_lower:
                moic_idx = i
            elif 'exit' in header_lower and 'year' in header_lower:
                exit_year_idx = i
            elif 'exit' in header_lower and 'multiple' in header_lower:
                exit_multiple_idx = i
        
        result = {}
        
        # Parse primeira linha de dados (pular header e separator)
        if len(table) >= 3:
            cells = [c.strip() for c in table[2].split('|') if c.strip()]
            
            if irr_idx is not None and irr_idx < len(cells):
                irr_val = self._extract_number(cells[irr_idx])
                if irr_val:
                    result['irr_pct'] = irr_val
            
            if moic_idx is not None and moic_idx < len(cells):
                moic_val = self._extract_number(cells[moic_idx])
                if moic_val:
                    result['moic'] = moic_val
            
            if exit_year_idx is not None and exit_year_idx < len(cells):
                year_match = re.search(r'20\d{2}', cells[exit_year_idx])
                if year_match:
                    try:
                        result['exit_year'] = int(year_match.group())
                    except:
                        pass
            
            if exit_multiple_idx is not None and exit_multiple_idx < len(cells):
                multiple_val = self._extract_number(cells[exit_multiple_idx])
                if multiple_val:
                    result['exit_multiple'] = multiple_val
        
        return result if result else None
    
    def _parse_board_table(self, table: List[str]) -> Optional[List[Dict[str, str]]]:
        """Parse de tabela de board"""
        # Implementação similar às outras, adaptada para estrutura de board
        # Por simplicidade, retornar None e deixar LLM extrair do texto
        return None
    
    def _parse_cap_table(self, table: List[str]) -> Optional[List[Dict[str, Any]]]:
        """Parse de tabela de cap table"""
        # Implementação similar às outras, adaptada para estrutura de cap table
        # Por simplicidade, retornar None e deixar LLM extrair do texto
        return None
    
    def _parse_board_from_text(self, text: str) -> Optional[List[Dict[str, str]]]:
        """Extrai board de texto estruturado (não tabela)"""
        # Deixar LLM extrair via structured output
        return None
    
    def _parse_cap_table_from_text(self, text: str) -> Optional[List[Dict[str, Any]]]:
        """Extrai cap table de texto estruturado (não tabela)"""
        # Deixar LLM extrair via structured output
        return None
    
    def _extract_number(self, text: str) -> Optional[float]:
        """Extrai número de uma string (remove formatação)"""
        if not text:
            return None
        
        # Remover caracteres não numéricos exceto ponto e vírgula
        cleaned = re.sub(r'[^\d.,\-]', '', text.replace(',', '.'))
        
        # Remover múltiplos pontos (manter apenas o último)
        parts = cleaned.split('.')
        if len(parts) > 2:
            cleaned = ''.join(parts[:-1]) + '.' + parts[-1]
        
        try:
            return float(cleaned)
        except:
            return None
