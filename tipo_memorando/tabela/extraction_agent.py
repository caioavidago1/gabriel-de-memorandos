"""
Agente de IA para extração de valores DRE dos documentos parseados.

Este agente usa LLM para extrair valores financeiros necessários para
preencher a tabela DRE, superando limitações de regex.
"""

import asyncio
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from core.logger import get_logger
from tipo_memorando.tabela.dre_extraction_schema import DRETableExtractionResult

logger = get_logger(__name__)


class DRETableExtractionAgent:
    """
    Agente especializado para extrair valores financeiros da tabela DRE.
    
    Usa LLM para extrair valores financeiros dos documentos parseados,
    identificando automaticamente anos e valores associados.
    """
    
    def __init__(self, llm: ChatOpenAI):
        """
        Inicializa o agente de extração DRE.
        
        Args:
            llm: Instância do LLM para extração
        """
        self.llm = llm
        self.max_retries = 3
    
    async def extract_dre_values(
        self,
        parsed_documents: List[Dict],
        years: List[int],
        ano_referencia: int
    ) -> Dict[str, Dict[int, Optional[float]]]:
        """
        Extrai valores financeiros dos documentos para todos os anos.
        
        Args:
            parsed_documents: Lista de documentos parseados (com campo "text")
            years: Lista de anos para buscar
            ano_referencia: Ano de referência
            
        Returns:
            Dicionário com estrutura {field_key: {year: value}}
        """
        if not parsed_documents:
            return {}
        
        # Combinar todo o texto dos documentos
        combined_text = "\n\n".join(doc.get("text", "") for doc in parsed_documents)
        
        # Carregar prompt
        prompt = self._load_prompt()
        
        # Construir system message
        system_message = self._build_system_message(years, ano_referencia, prompt)
        
        # Construir user message
        user_message = self._build_user_message(combined_text, years, ano_referencia)
        
        # Tentar extrair com retries
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Tentativa {attempt + 1}/{self.max_retries} de extração DRE")
                
                # Chamar LLM
                messages = [
                    SystemMessage(content=system_message),
                    HumanMessage(content=user_message)
                ]
                
                # STRUCTURED OUTPUT - OpenAI valida automaticamente o schema
                result = await self.llm.with_structured_output(DRETableExtractionResult).ainvoke(messages)
                
                # Converter resultado para formato esperado
                extracted_values = self._convert_result_to_dict(result, years)
                
                logger.info(
                    f"Extração DRE concluída: {len(extracted_values)} campos, "
                    f"{sum(len(v) for v in extracted_values.values())} valores encontrados"
                )
                
                return extracted_values
                
            except Exception as e:
                logger.warning(f"Erro na tentativa {attempt + 1}: {e}")
                if attempt == self.max_retries - 1:
                    logger.error(f"Falha após {self.max_retries} tentativas")
                    return self._empty_result(years)
        
        return self._empty_result(years)
    
    def _load_prompt(self) -> str:
        """
        Carrega prompt específico para extração DRE.
        
        Returns:
            Prompt carregado do arquivo ou prompt padrão
        """
        prompt_file = Path(__file__).parent / "prompts" / "dre_extraction.txt"
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            logger.warning(f"Prompt não encontrado: {prompt_file}, usando prompt padrão")
            return "Extraia valores financeiros para a tabela DRE mencionados no documento."
    
    def _build_system_message(
        self,
        years: List[int],
        ano_referencia: int,
        prompt: str
    ) -> str:
        """
        Constrói system message para o LLM.
        
        Args:
            years: Lista de anos para buscar
            ano_referencia: Ano de referência
            prompt: Prompt carregado do arquivo
            
        Returns:
            System message formatado
        """
        years_str = ", ".join(map(str, years))
        
        system_message = f"""Você é um especialista em análise de documentos financeiros de Private Equity.
Sua tarefa é extrair valores financeiros para a tabela DRE com MÁXIMA PRECISÃO.

REGRAS CRÍTICAS:
1. Extraia APENAS valores EXPLICITAMENTE mencionados no documento
2. Use null para campos não encontrados - NUNCA invente valores
3. Valores monetários: APENAS números decimais em milhões (ex: 100.5, não "R$ 100,5M")
4. Se encontrar "R$ 100M", extraia 100.0
5. Se encontrar "100 milhões", extraia 100.0
6. Valores podem ser negativos (ex: -10.5 para prejuízo)
7. Anos: Use string do ano (ex: "2024", "2023")
8. Procure por valores associados a anos específicos mencionados: {years_str}
9. Ano de referência principal: {ano_referencia}
10. Se um valor não tiver ano explícito mas estiver no contexto do ano de referência, use {ano_referencia}

IMPORTANTE: Você DEVE retornar um objeto JSON válido seguindo o schema DRETableExtractionResult.
Campos que você não encontrar devem ser null ou omitidos.

PROMPT DETALHADO:
{prompt}"""
        
        return system_message
    
    def _build_user_message(
        self,
        text: str,
        years: List[int],
        ano_referencia: int
    ) -> str:
        """
        Constrói user message para o LLM.
        
        Args:
            text: Texto completo dos documentos
            years: Lista de anos para buscar
            ano_referencia: Ano de referência
            
        Returns:
            User message formatado
        """
        years_str = ", ".join(map(str, years))
        
        # Limitar tamanho do texto para evitar token limit
        max_chars = 50000
        if len(text) > max_chars:
            logger.warning(f"Texto muito grande ({len(text)} chars), truncando para {max_chars}")
            text = text[:max_chars] + "\n\n[... texto truncado ...]"
        
        user_message = f"""DOCUMENTO PARA ANÁLISE:

{text}

═══════════════════════════════════════════════════════════════════
INSTRUÇÕES:
═══════════════════════════════════════════════════════════════════

Extraia valores financeiros mencionados acima para os seguintes anos: {years_str}

Ano de referência: {ano_referencia}

Procure por:
- Tabelas financeiras (DRE, P&L, demonstrativos)
- Projeções financeiras por ano
- Análises históricas com valores por ano
- Textos que mencionem valores com anos específicos

Para cada ano encontrado, extraia todos os valores disponíveis.
Se um valor não tiver ano explícito mas estiver claramente no contexto de um ano, use esse ano.
Se não houver ano claro mas o documento menciona valores atuais/recentes, use o ano de referência ({ano_referencia}).

Retorne APENAS valores explicitamente mencionados no documento.
Use null para campos não encontrados."""
        
        return user_message
    
    def _convert_result_to_dict(
        self,
        result: DRETableExtractionResult,
        years: List[int]
    ) -> Dict[str, Dict[int, Optional[float]]]:
        """
        Converte resultado do Pydantic para formato esperado.
        
        Args:
            result: Resultado da extração em formato Pydantic
            years: Lista de anos esperados
            
        Returns:
            Dicionário com estrutura {field_key: {year: value}}
        """
        # Inicializar estrutura vazia
        extracted_values = {
            "receita_bruta": {},
            "receita_liquida": {},
            "lucro_bruto": {},
            "ebitda": {},
            "ebit": {},
            "lucro_liquido": {},
            "capex": {},
            "divida_liquida": {},
            "geracao_caixa_operacional": {},
            "geracao_caixa": {},
        }
        
        # Mapear campos do schema para keys esperadas
        field_mapping = {
            "receita_bruta": "receita_bruta",
            "receita_liquida": "receita_liquida",
            "lucro_bruto": "lucro_bruto",
            "ebitda": "ebitda",
            "ebit": "ebit",
            "lucro_liquido": "lucro_liquido",
            "capex": "capex",
            "divida_liquida": "divida_liquida",
            "geracao_caixa_operacional": "geracao_caixa_operacional",
            "geracao_caixa": "geracao_caixa",
        }
        
        # Converter valores por ano
        for year_str, values in result.values_by_year.items():
            try:
                year = int(year_str)
                if year not in years:
                    logger.debug(f"Ano {year} extraído mas não está na lista esperada {years}")
                    continue
                
                # Mapear valores do schema para estrutura esperada
                for schema_field, dict_key in field_mapping.items():
                    value = getattr(values, schema_field, None)
                    extracted_values[dict_key][year] = value
                    
            except ValueError:
                logger.warning(f"Ano inválido extraído: {year_str}")
                continue
        
        return extracted_values
    
    def _empty_result(self, years: List[int]) -> Dict[str, Dict[int, Optional[float]]]:
        """
        Retorna estrutura vazia para todos os campos e anos.
        
        Args:
            years: Lista de anos
            
        Returns:
            Dicionário com todos os valores None
        """
        return {
            "receita_bruta": {year: None for year in years},
            "receita_liquida": {year: None for year in years},
            "lucro_bruto": {year: None for year in years},
            "ebitda": {year: None for year in years},
            "ebit": {year: None for year in years},
            "lucro_liquido": {year: None for year in years},
            "capex": {year: None for year in years},
            "divida_liquida": {year: None for year in years},
            "geracao_caixa_operacional": {year: None for year in years},
            "geracao_caixa": {year: None for year in years},
        }
    
    def extract_dre_values_sync(
        self,
        parsed_documents: List[Dict],
        years: List[int],
        ano_referencia: int
    ) -> Dict[str, Dict[int, Optional[float]]]:
        """
        Wrapper síncrono para extração assíncrona.
        
        Args:
            parsed_documents: Lista de documentos parseados
            years: Lista de anos para buscar
            ano_referencia: Ano de referência
            
        Returns:
            Dicionário com estrutura {field_key: {year: value}}
        """
        return asyncio.run(
            self.extract_dre_values(parsed_documents, years, ano_referencia)
        )
