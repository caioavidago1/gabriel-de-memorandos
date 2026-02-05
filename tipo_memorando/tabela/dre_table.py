"""
Lógica para geração de tabelas DRE (Demonstração do Resultado do Exercício).

Este módulo contém a estrutura de dados e lógica para criar tabelas DRE
com histórico real e projeções.
"""

import math
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from core.logger import get_logger

logger = get_logger(__name__)


def _cagr_percent(valor_inicial: float, valor_final: float, n_anos: int) -> Optional[float]:
    """
    Calcula a taxa de crescimento anual composta (CARG) em percentual.

    Args:
        valor_inicial: Valor no ano inicial.
        valor_final: Valor no ano final.
        n_anos: Número de anos entre inicial e final (ex.: 2020 a 2022 → 2).

    Returns:
        CARG em percentual (ex.: 15.5 para 15,5%) ou None se não for possível calcular.

    Examples:
        >>> _cagr_percent(100, 121, 2)
        10.0
    """
    if n_anos <= 0:
        return None
    if valor_inicial is None or valor_final is None:
        return None
    try:
        vi, vf = float(valor_inicial), float(valor_final)
    except (TypeError, ValueError):
        return None
    if vi <= 0:
        return None
    if vf <= 0:
        return None
    try:
        ratio = vf / vi
        cagr = (math.pow(ratio, 1 / n_anos) - 1) * 100
        return round(cagr, 2)
    except (ZeroDivisionError, ValueError):
        return None


@dataclass
class DRELineItem:
    """
    Representa uma linha da DRE.

    Args:
        name: Nome da linha (ex: "Receita Bruta")
        key: Chave única para identificação (ex: "receita_bruta")
        is_calculated: Se True, o valor é calculado automaticamente
        formula: Fórmula de cálculo (ex: "(lucro_bruto / receita_liquida) * 100")
        order: Ordem de exibição na tabela
        formula_display: Fórmula legível para exibição (ex: "Lucro Bruto / Receita Líquida")
    """
    name: str
    key: str
    is_calculated: bool = False
    formula: Optional[str] = None
    order: int = 0
    formula_display: Optional[str] = None


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
        DRELineItem("Receita Bruta", "receita_bruta", False, None, 1, None),
        DRELineItem("Receita Líquida", "receita_liquida", False, None, 2, None),
        DRELineItem("Lucro Bruto", "lucro_bruto", False, None, 3, None),
        DRELineItem("Margem Bruta", "margem_bruta", True, "(lucro_bruto / receita_liquida) * 100", 4, None),
        DRELineItem("EBITDA", "ebitda", False, None, 5, None),
        DRELineItem("Margem EBITDA", "margem_ebitda", True, "(ebitda / receita_liquida) * 100", 6, None),
        DRELineItem("EBIT", "ebit", False, None, 7, None),
        DRELineItem("Margem EBIT", "margem_ebit", True, "(ebit / receita_liquida) * 100", 8, None),
        DRELineItem("Lucro Líquido", "lucro_liquido", False, None, 9, None),
        DRELineItem("Margem Líquida", "margem_liquida", True, "(lucro_liquido / receita_liquida) * 100", 10, None),
        DRELineItem("Capex", "capex", False, None, 11, None),
        DRELineItem("Capex - % Receita Líquida", "capex_pct_receita_liquida", True, "(capex / receita_liquida) * 100", 12, None),
        DRELineItem("Dívida Líquida", "divida_liquida", False, None, 13, None),
        DRELineItem("Alavancagem (DV/EBITDA)", "dv_ebitda", True, "divida_liquida / ebitda", 14, None),
        DRELineItem("Geração de Caixa Operacional", "geracao_caixa_operacional", False, None, 15, None),
        DRELineItem("Geração de Caixa Operacional % EBITDA", "geracao_caixa_operacional_pct_ebitda", True, "(geracao_caixa_operacional / ebitda) * 100", 16, None),
        DRELineItem("Geração de Caixa", "geracao_caixa", False, None, 17, None),
        DRELineItem("Geração de Caixa % EBITDA", "geracao_caixa_pct_ebitda", True, "(geracao_caixa / ebitda) * 100", 18, None),
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
            
            # Verificar divisão por zero antes de substituir (denominador = segundo grupo)
            if '/' in formula:
                division_pattern = r'(\w+)\s*/\s*(\w+)'
                divisions = re.findall(division_pattern, formula)
                for _num_key, den_key in divisions:
                    den_val = values_map.get(den_key)
                    if den_val is not None and (den_val == 0 or (isinstance(den_val, float) and abs(den_val) < 1e-12)):
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
    
    def get_display_value(self, line_item: DRELineItem, year: int) -> Optional[float]:
        """
        Retorna o valor exibido para uma linha em um ano (calculado ou bruto).

        Args:
            line_item: Item da linha.
            year: Ano.

        Returns:
            Valor calculado se a linha for calculada, senão valor armazenado; None se indisponível.
        """
        if line_item.is_calculated:
            return self.calculate_line(line_item, year)
        return self.get_value(line_item.key, year)

    def get_carg_historico(self, line_item: DRELineItem) -> Optional[float]:
        """
        Calcula o CARG histórico (do primeiro ano histórico ao ano de referência).

        Returns:
            CARG em percentual (ex.: 15.5 para 15,5%) ou None se não for possível calcular.
        """
        n_anos = self.ano_referencia - self.primeiro_ano_historico
        if n_anos <= 0:
            return None
        v_inicial = self.get_display_value(line_item, self.primeiro_ano_historico)
        v_final = self.get_display_value(line_item, self.ano_referencia)
        return _cagr_percent(v_inicial, v_final, n_anos)

    def get_carg_projetado(self, line_item: DRELineItem) -> Optional[float]:
        """
        Calcula o CARG projetado (do ano de referência ao último ano de projeção).

        Returns:
            CARG em percentual (ex.: 12.0 para 12%) ou None se não for possível calcular.
        """
        n_anos = self.ultimo_ano_projecao - self.ano_referencia
        if n_anos <= 0:
            return None
        v_inicial = self.get_display_value(line_item, self.ano_referencia)
        v_final = self.get_display_value(line_item, self.ultimo_ano_projecao)
        return _cagr_percent(v_inicial, v_final, n_anos)

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
        Inclui dados brutos (table_data), tabela resolvida (valores calculados por ano),
        CARG histórico e projetado por linha, e metadados das linhas.
        
        Returns:
            Dicionário serializável com todos os dados da tabela
        """
        line_items = self.get_line_items()
        carg_historico = {item.key: self.get_carg_historico(item) for item in line_items}
        carg_projetado = {item.key: self.get_carg_projetado(item) for item in line_items}
        return {
            "ano_referencia": self.ano_referencia,
            "primeiro_ano_historico": self.primeiro_ano_historico,
            "ultimo_ano_projecao": self.ultimo_ano_projecao,
            "anos": self.anos,
            "table_data": self.table_data,
            "table_resolved": self.get_table_dict(),
            "carg_historico": carg_historico,
            "carg_projetado": carg_projetado,
            "line_items": [
                {
                    "key": item.key,
                    "name": item.name,
                    "order": item.order,
                    "is_calculated": item.is_calculated,
                    "formula": item.formula,
                }
                for item in line_items
            ],
        }
    
