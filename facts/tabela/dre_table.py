"""
Lógica para geração de tabelas DRE (Demonstração do Resultado do Exercício).

Este módulo contém a estrutura de dados e lógica para criar tabelas DRE
com histórico real e projeções.
"""

import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class DRELineItem:
    """
    Representa uma linha da DRE.
    
    Args:
        name: Nome da linha (ex: "Receita Bruta")
        key: Chave única para identificação (ex: "receita_bruta")
        is_calculated: Se True, o valor é calculado automaticamente
        formula: Fórmula de cálculo (ex: "receita_bruta - deducoes")
        order: Ordem de exibição na tabela
    """
    name: str
    key: str
    is_calculated: bool = False
    formula: Optional[str] = None
    order: int = 0


class DRETableGenerator:
    """
    Gerador de tabelas DRE com histórico e projeções.
    
    Cria uma estrutura de dados para DRE com as seguintes linhas:
    - Receita Bruta
    - Receita Líquida
    - Lucro Bruto
    - Margem Bruta
    - EBITDA
    - Margem EBITDA
    - EBIT
    - Margem EBIT
    - Lucro Líquido
    - Margem Líquida
    - Capex
    - Capex - % Receita Líquida
    - Dívida Líquida
    - DV/EBITDA
    - Geração de Caixa Operacional
    - Geração de Caixa Operacional % EBITDA
    - Geração de Caixa
    - Geração de Caixa % EBITDA
    """
    
    # Estrutura padrão de linhas da DRE
    DEFAULT_LINE_ITEMS: List[DRELineItem] = [
        DRELineItem("Receita Bruta", "receita_bruta", False, None, 1),
        DRELineItem("Receita Líquida", "receita_liquida", False, None, 2),
        DRELineItem("Lucro Bruto", "lucro_bruto", False, None, 3),
        DRELineItem("Margem Bruta", "margem_bruta", True, "(lucro_bruto / receita_liquida) * 100", 4),
        DRELineItem("EBITDA", "ebitda", False, None, 5),
        DRELineItem("Margem EBITDA", "margem_ebitda", True, "(ebitda / receita_liquida) * 100", 6),
        DRELineItem("EBIT", "ebit", False, None, 7),
        DRELineItem("Margem EBIT", "margem_ebit", True, "(ebit / receita_liquida) * 100", 8),
        DRELineItem("Lucro Líquido", "lucro_liquido", False, None, 9),
        DRELineItem("Margem Líquida", "margem_liquida", True, "(lucro_liquido / receita_liquida) * 100", 10),
        DRELineItem("Capex", "capex", False, None, 11),
        DRELineItem("Capex - % Receita Líquida", "capex_pct_receita_liquida", True, "(capex / receita_liquida) * 100", 12),
        DRELineItem("Dívida Líquida", "divida_liquida", False, None, 13),
        DRELineItem("DV/EBITDA", "dv_ebitda", True, "divida_liquida / ebitda", 14),
        DRELineItem("Geração de Caixa Operacional", "geracao_caixa_operacional", False, None, 15),
        DRELineItem("Geração de Caixa Operacional % EBITDA", "geracao_caixa_operacional_pct_ebitda", True, "(geracao_caixa_operacional / ebitda) * 100", 16),
        DRELineItem("Geração de Caixa", "geracao_caixa", False, None, 17),
        DRELineItem("Geração de Caixa % EBITDA", "geracao_caixa_pct_ebitda", True, "(geracao_caixa / ebitda) * 100", 18),
    ]
    
    def __init__(
        self,
        ano_referencia: int,
        primeiro_ano_historico: int,
        ultimo_ano_projecao: int
    ):
        """
        Inicializa o gerador de tabela DRE.
        
        Args:
            ano_referencia: Ano de referência para os dados
            primeiro_ano_historico: Primeiro ano do histórico (ex: 2020)
            ultimo_ano_projecao: Último ano de projeção (ex: 2030)
        """
        self.ano_referencia = ano_referencia
        self.primeiro_ano_historico = primeiro_ano_historico
        self.ultimo_ano_projecao = ultimo_ano_projecao
        
        # Gerar lista de anos (histórico + projeções)
        self.anos = list(range(primeiro_ano_historico, ultimo_ano_projecao + 1))
        
        # Inicializar estrutura de dados da tabela
        self.table_data: Dict[str, Dict[int, Optional[float]]] = {}
        for item in self.DEFAULT_LINE_ITEMS:
            self.table_data[item.key] = {ano: None for ano in self.anos}
        
        logger.info(
            f"DRETableGenerator inicializado: "
            f"referência={ano_referencia}, "
            f"histórico={primeiro_ano_historico}-{ultimo_ano_projecao}, "
            f"total_anos={len(self.anos)}"
        )
    
    def get_line_items(self) -> List[DRELineItem]:
        """
        Retorna a lista de linhas da DRE ordenadas.
        
        Returns:
            Lista de DRELineItem ordenada por ordem
        """
        return sorted(self.DEFAULT_LINE_ITEMS, key=lambda x: x.order)
    
    def get_years(self) -> List[int]:
        """
        Retorna a lista de anos da tabela.
        
        Returns:
            Lista de anos do histórico até as projeções
        """
        return self.anos
    
    def set_value(self, line_key: str, year: int, value: Optional[float]) -> None:
        """
        Define um valor na tabela.
        
        Args:
            line_key: Chave da linha (ex: "receita_bruta")
            year: Ano
            value: Valor a ser definido (None para limpar)
        """
        if line_key not in self.table_data:
            logger.warning(f"Chave de linha desconhecida: {line_key}")
            return
        
        if year not in self.anos:
            logger.warning(f"Ano fora do range: {year}")
            return
        
        self.table_data[line_key][year] = value
        logger.debug(f"Valor definido: {line_key}[{year}] = {value}")
    
    def get_value(self, line_key: str, year: int) -> Optional[float]:
        """
        Obtém um valor da tabela.
        
        Args:
            line_key: Chave da linha
            year: Ano
            
        Returns:
            Valor armazenado ou None
        """
        if line_key not in self.table_data:
            return None
        
        return self.table_data[line_key].get(year)
    
    def calculate_line(self, line_item: DRELineItem, year: int) -> Optional[float]:
        """
        Calcula o valor de uma linha calculada.
        
        Args:
            line_item: Item da linha a ser calculado
            year: Ano para o qual calcular
            
        Returns:
            Valor calculado ou None se não for possível calcular
        """
        if not line_item.is_calculated or not line_item.formula:
            return None
        
        try:
            # Parse seguro da fórmula (ex: "receita_bruta - deducoes_impostos")
            formula = line_item.formula.strip()
            
            # Extrair apenas as chaves que aparecem na fórmula
            formula_keys = re.findall(r'\b[a-z_]+[a-z0-9_]*\b', formula)
            
            # Mapear apenas as chaves necessárias para valores
            values_map = {}
            for key in formula_keys:
                if key in self.table_data:
                    value = self.get_value(key, year)
                    if value is None:
                        # Se algum valor necessário for None, não é possível calcular
                        return None
                    values_map[key] = value
            
            # Verificar divisão por zero antes de substituir
            # Para fórmulas com divisão, verificar se algum divisor é zero
            if '/' in formula:
                # Encontrar padrões de divisão: "variavel1 / variavel2"
                division_pattern = r'(\w+)\s*/\s*(\w+)'
                divisions = re.findall(division_pattern, formula)
                for divisor_key, _ in divisions:
                    if divisor_key in values_map and values_map[divisor_key] == 0:
                        # Divisão por zero detectada
                        return None
            
            # Substituir chaves pelos valores na fórmula
            for key, value in values_map.items():
                formula = re.sub(rf'\b{re.escape(key)}\b', str(value), formula)
            
            # Avaliar fórmula de forma segura (apenas operações matemáticas básicas)
            # Remover espaços
            formula = formula.replace(" ", "")
            
            # Validar que contém apenas números, operadores e parênteses
            if not re.match(r'^[0-9+\-*/().\s]+$', formula):
                logger.warning(f"Fórmula contém caracteres inválidos: {formula}")
                return None
            
            # Avaliar usando eval (seguro pois validamos o conteúdo)
            try:
                result = eval(formula)
                return float(result) if result is not None else None
            except ZeroDivisionError:
                return None
            
        except Exception as e:
            logger.error(f"Erro ao calcular {line_item.key} para {year}: {e}")
            return None
    
    def get_table_dict(self) -> Dict[str, Dict[int, Optional[float]]]:
        """
        Retorna a tabela completa com valores calculados.
        
        Returns:
            Dicionário com estrutura {line_key: {year: value}}
        """
        result = {}
        
        for line_item in self.get_line_items():
            line_data = {}
            for year in self.anos:
                if line_item.is_calculated:
                    # Calcular valor
                    calculated_value = self.calculate_line(line_item, year)
                    line_data[year] = calculated_value
                else:
                    # Usar valor armazenado
                    line_data[year] = self.get_value(line_item.key, year)
            
            result[line_item.key] = line_data
        
        return result
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Serializa a tabela para um dicionário.
        
        Returns:
            Dicionário serializável com todos os dados da tabela
        """
        return {
            "ano_referencia": self.ano_referencia,
            "primeiro_ano_historico": self.primeiro_ano_historico,
            "ultimo_ano_projecao": self.ultimo_ano_projecao,
            "anos": self.anos,
            "table_data": self.table_data,
        }
    
