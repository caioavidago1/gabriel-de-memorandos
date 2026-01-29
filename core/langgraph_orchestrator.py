from typing import TypedDict, Annotated, Literal, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
import asyncio
from datetime import datetime
from core.logger import get_logger

logger = get_logger(__name__)


class ExtractionState(TypedDict, total=False):
    """
    Estado compartilhado entre todos os agentes no grafo.
    
    Campos obrigatórios: document_text, memo_type, extraction_attempts, 
                          failed_sections, validation_errors, is_complete, max_retries
    
    Seções dinâmicas (adicionadas em runtime baseadas no tipo de memo):
    - Para Short Memo - Primário: gestora, fundo, estrategia, spectra_context, opinioes
    - Para Short Memo - Secundário: identification, transaction_structure, financials_history, returns, qualitative, opinioes, portfolio_secundario
    - Para outros: identification, transaction_structure, financials_history, saida, returns, qualitative, opinioes
    """
    # Campos obrigatórios
    document_text: str
    memo_type: str
    embeddings_data: dict | None
    extraction_attempts: dict
    failed_sections: list
    validation_errors: list
    is_complete: bool
    max_retries: int
    
    # Seções dinâmicas - campos opcionais (adicionados em runtime)
    # Seções para investimento em empresas
    identification: dict
    transaction_structure: dict
    financials_history: dict
    saida: dict
    returns: dict
    qualitative: dict
    
    # Seções para investimento em fundos (Short Memo - Primário)
    gestora: dict
    fundo: dict
    estrategia: dict
    spectra_context: dict
    
    # Seção específica para Short Memo - Secundário
    portfolio_secundario: dict
    
    # Seção comum a todos
    opinioes: dict


class LangGraphExtractor:
    """
    Orquestrador de extração usando LangGraph
    
    Fluxo:
    1. Extrair todas as seções em paralelo
    2. Validar resultados
    3. Se houver erros e tentativas < max, fazer retry seletivo
    4. Retornar dados finais
    """
    
    def __init__(self, llm: ChatOpenAI, max_retries: int = 2):
        self.llm = llm
        self.max_retries = max_retries
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Constrói o grafo de estados para extração"""
        
        workflow = StateGraph(ExtractionState)
        
        # === NÓDULOS DE EXTRAÇÃO ===
        workflow.add_node("extract_all_parallel", self._extract_all_parallel)
        workflow.add_node("validate_results", self._validate_results)
        workflow.add_node("retry_failed_sections", self._retry_failed_sections)
        workflow.add_node("finalize", self._finalize)
        
        # === FLUXO ===
        # 1. Começar com extração paralela
        workflow.set_entry_point("extract_all_parallel")
        
        # 2. Após extração, validar
        workflow.add_edge("extract_all_parallel", "validate_results")
        
        # 3. Decisão condicional após validação
        workflow.add_conditional_edges(
            "validate_results",
            self._should_retry,
            {
                "retry": "retry_failed_sections",
                "finalize": "finalize",
                "end": END
            }
        )
        
        # 4. Retry volta para validação
        workflow.add_edge("retry_failed_sections", "validate_results")
        
        # 5. Finalize vai para END
        workflow.add_edge("finalize", END)
        
        return workflow.compile()
    
    async def _extract_all_parallel(self, state: ExtractionState) -> dict:
        """
        Extrai todas as seções em paralelo usando asyncio.gather.
        Seções são dinâmicas baseadas no tipo de memo.
        """
        from core.extraction_agents import ExtractionAgent
        from facts_config import get_sections_for_memo_type
        
        # Determinar seções a extrair baseado no tipo de memo
        sections = get_sections_for_memo_type(state["memo_type"])
        
        logger.info(f"🤖 [LangGraph] Extraindo {len(sections)} seções para '{state['memo_type']}'...")
        logger.info(f"📋 Seções: {', '.join(sections)}")
        
        # Criar agentes
        agents = [ExtractionAgent(self.llm, section) for section in sections]
        
        # Executar em paralelo
        tasks = [
            agent.extract(
                state["document_text"],
                state["memo_type"],
                state["embeddings_data"]
            )
            for agent in agents
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Organizar resultados
        extracted_data = {}
        failed = []
        
        # Merge attempts com o estado existente
        current_attempts = state.get("extraction_attempts", {})
        new_attempts = current_attempts.copy()
        
        for section, result in zip(sections, results):
            if isinstance(result, Exception):
                logger.error(f"{section}: Erro - {result}")
                extracted_data[section] = {}
                failed.append(section)
            else:
                filled_count = sum(1 for v in result.values() if v not in (None, "", "null"))
                logger.info(f"✓ {section}: {filled_count} campos extraídos")
                extracted_data[section] = result
            
            new_attempts[section] = new_attempts.get(section, 0) + 1
        
        return {
            **extracted_data,
            "extraction_attempts": new_attempts,
            "failed_sections": failed
        }
    
    async def _validate_results(self, state: ExtractionState) -> dict:
        """
        Valida se os dados extraídos fazem sentido.
        Validação é condicional baseada no tipo de memo.
        """
        from facts_config import get_sections_for_memo_type
        
        logger.info("🔍 [LangGraph] Validando resultados...")
        
        errors = []
        critical_errors = []
        
        relevant_sections = get_sections_for_memo_type(state["memo_type"])
        
        # === VALIDAR TRANSAÇÃO (apenas se relevante) ===
        trans = state.get("transaction_structure", {}) if "transaction_structure" in relevant_sections else {}
        
        # EV deve ser >= Equity
        if trans.get("ev_mm") and trans.get("equity_value_mm"):
            try:
                ev = float(trans["ev_mm"])
                equity = float(trans["equity_value_mm"])
                if ev < equity:
                    critical_errors.append("❌ EV não pode ser menor que Equity Value")
            except:
                pass
        
        # Múltiplo deve ser positivo
        if trans.get("multiple_ev_ebitda"):
            try:
                if float(trans["multiple_ev_ebitda"]) <= 0:
                    errors.append("⚠️  Múltiplo EV/EBITDA deve ser positivo")
            except:
                pass
        
        # Stake deve estar entre 0 e 100
        if trans.get("stake_pct"):
            try:
                stake = float(trans["stake_pct"])
                if not (0 <= stake <= 100):
                    errors.append("⚠️  Stake % deve estar entre 0 e 100")
            except:
                pass
        
        # === VALIDAR FINANCIALS ===
        fin = state.get("financials_history", {})
        
        # Margem EBITDA deve estar entre 0 e 100
        if fin.get("ebitda_margin_current_pct"):
            try:
                margin = float(fin["ebitda_margin_current_pct"])
                if not (0 <= margin <= 100):
                    errors.append("⚠️  Margem EBITDA deve estar entre 0 e 100")
            except:
                pass
        
        # CAGR não pode ser negativo (geralmente)
        if fin.get("revenue_cagr_pct"):
            try:
                cagr = float(fin["revenue_cagr_pct"])
                if cagr < -50:
                    errors.append("⚠️  CAGR de receita muito negativo")
            except:
                pass
        
        # === VALIDAR RETURNS ===
        ret = state.get("returns", {})
        
        # IRR negativo é suspeito
        if ret.get("irr_pct"):
            try:
                irr = float(ret["irr_pct"])
                if irr < 0:
                    errors.append("⚠️  IRR negativo detectado")
            except:
                pass
        
        # MOIC deve ser >= 1.0 normalmente
        if ret.get("moic"):
            try:
                moic = float(ret["moic"])
                if moic < 0.5:
                    errors.append("⚠️  MOIC muito baixo")
            except:
                pass
        
        # === VALIDAR SAÍDA ===
        saida = state.get("saida", {})
        
        # Ano de saída deve ser futuro
        if saida.get("exit_year"):
            try:
                exit_year = int(saida["exit_year"])
                current_year = datetime.now().year
                if exit_year < current_year:
                    errors.append("⚠️  Ano de saída está no passado")
            except:
                pass
        
        # === VERIFICAR CAMPOS CRÍTICOS VAZIOS (apenas se seções relevantes) ===
        if "identification" in relevant_sections:
            identification = state.get("identification", {})
            if not identification.get("company_name"):
                critical_errors.append("❌ Nome da empresa/fundo não foi extraído")
        
        if "transaction_structure" in relevant_sections:
            if not trans.get("ev_mm") and not trans.get("equity_value_mm"):
                critical_errors.append("❌ Nenhum valor de transação foi extraído")
        
        # Validação específica para fundos
        if "fundo" in relevant_sections:
            fundo = state.get("fundo", {})
            if not fundo.get("fundo_nome"):
                critical_errors.append("❌ Nome do fundo não foi extraído")
        
        if "gestora" in relevant_sections:
            gestora = state.get("gestora", {})
            if not gestora.get("gestora_nome"):
                critical_errors.append("❌ Nome da gestora não foi extraído")
        
        # === RESULTADO DA VALIDAÇÃO ===
        all_errors = critical_errors + errors
        
        if all_errors:
            logger.warning(f"{len(critical_errors)} erros críticos, {len(errors)} avisos")
            for error in all_errors:
                logger.warning(f"  {error}")
        else:
            logger.info("✅ Validação passou sem erros")
        
        # Só fazer retry se houver erros críticos e ainda temos tentativas
        # Ajustar limite baseado no número de seções relevantes
        num_sections = len(relevant_sections)
        total_attempts = sum(state["extraction_attempts"].values())
        should_retry = len(critical_errors) > 0 and total_attempts < (state["max_retries"] * num_sections)
        
        return {
            "validation_errors": all_errors,
            "is_complete": not should_retry
        }
    
    def _should_retry(self, state: ExtractionState) -> Literal["retry", "finalize", "end"]:
        """
        Decide o próximo passo baseado no estado
        """
        from facts_config import get_sections_for_memo_type
        
        relevant_sections = get_sections_for_memo_type(state["memo_type"])
        total_attempts = sum(state["extraction_attempts"].values())
        max_total_attempts = state["max_retries"] * len(relevant_sections)
        
        logger.info(f"🔄 [LangGraph] Decisão de retry: tentativas={total_attempts}/{max_total_attempts}")
        
        # Se completou ou atingiu máximo de tentativas
        if state["is_complete"] or total_attempts >= max_total_attempts:
            if state["validation_errors"]:
                logger.info(f"Finalizando com {len(state['validation_errors'])} avisos")
                return "finalize"
            else:
                logger.info("Concluído com sucesso")
                return "end"
        
        # Se há seções que falharam, fazer retry
        if state["failed_sections"]:
            logger.info(f"Retry de {len(state['failed_sections'])} seções: {state['failed_sections']}")
            return "retry"
        
        # Se há erros de validação mas não há seções falhadas, finalizar
        logger.info("Finalizando (sem seções falhadas)")
        return "finalize"
    
    async def _retry_failed_sections(self, state: ExtractionState) -> dict:
        """
        Re-executa apenas as seções que falharam.
        Respeita as seções relevantes para o tipo de memo.
        """
        from core.extraction_agents import ExtractionAgent
        from facts_config import get_sections_for_memo_type
        
        # Filtrar apenas seções falhadas que são relevantes para o tipo de memo
        relevant_sections = get_sections_for_memo_type(state["memo_type"])
        failed_sections = [s for s in state["failed_sections"] if s in relevant_sections]
        
        logger.info(f"🔁 [LangGraph] Retry de seções falhadas: {failed_sections}")
        
        # Criar agentes apenas para seções falhadas
        agents = [ExtractionAgent(self.llm, section) for section in failed_sections]
        
        # Executar retry em paralelo
        tasks = [
            agent.extract(
                state["document_text"],
                state["memo_type"],
                state["embeddings_data"]
            )
            for agent in agents
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Atualizar resultados
        updated_data = {}
        new_failed = []
        
        # Merge attempts com o estado existente
        current_attempts = state.get("extraction_attempts", {})
        new_attempts = current_attempts.copy()
        
        for section, result in zip(failed_sections, results):
            if isinstance(result, Exception):
                logger.error(f"{section}: Falhou novamente - {result}")
                new_failed.append(section)
            else:
                filled_count = sum(1 for v in result.values() if v not in (None, "", "null"))
                logger.info(f"✓ {section}: {filled_count} campos extraídos")
                updated_data[section] = result
            
            new_attempts[section] = new_attempts.get(section, 0) + 1
        
        return {
            **updated_data,
            "extraction_attempts": new_attempts,
            "failed_sections": new_failed
        }
    
    async def _finalize(self, state: ExtractionState) -> dict:
        """
        Finaliza a extração, preparando dados para retorno
        """
        logger.info("✅ [LangGraph] Finalizando extração...")
        
        total_attempts = sum(state["extraction_attempts"].values())
        logger.info(f"Total de tentativas: {total_attempts}")
        logger.info(f"Avisos: {len(state['validation_errors'])}")
        
        return {"is_complete": True}
    
    async def extract_all(
        self,
        document_text: str,
        memo_type: str,
        embeddings_data: dict = None
    ) -> dict:
        """
        Executa a extração completa usando o grafo LangGraph
        
        Returns:
            Dict com dados extraídos de todas as seções
        """
        from facts_config import get_field_count_for_memo_type, FIELD_VISIBILITY
        
        # Calcular estatísticas de otimização
        field_stats = get_field_count_for_memo_type(memo_type)
        total_possible = sum(len(fields) for fields in FIELD_VISIBILITY.values())
        economy = total_possible - field_stats['total']
        economy_pct = (economy / total_possible * 100) if total_possible > 0 else 0
        
        logger.info("="*70)
        logger.info("🚀 [LangGraph] INICIANDO EXTRAÇÃO OTIMIZADA")
        logger.info("="*70)
        logger.info(f"📋 Tipo de Memo: {memo_type}")
        logger.info(f"📊 Campos Relevantes: {field_stats['total']}/{total_possible}")
        logger.info(f"💰 Economia: {economy} campos (~{economy_pct:.1f}% menos tokens)")
        logger.info(f"\n📂 Breakdown por seção:")
        for section, count in field_stats['by_section'].items():
            logger.info(f"   • {section}: {count} campos")
        logger.info("="*70)
        
        from facts_config import get_sections_for_memo_type
        
        # Determinar seções relevantes para este tipo de memo
        relevant_sections = get_sections_for_memo_type(memo_type)
        
        # Estado inicial dinâmico - apenas seções relevantes
        initial_state: ExtractionState = {
            "document_text": document_text,
            "memo_type": memo_type,
            "embeddings_data": embeddings_data,
            "extraction_attempts": {},
            "failed_sections": [],
            "validation_errors": [],
            "is_complete": False,
            "max_retries": self.max_retries
        }
        
        # Adicionar seções relevantes como dicts vazios
        for section in relevant_sections:
            initial_state[section] = {}
        
        # Executar o grafo
        final_state = await self.graph.ainvoke(initial_state)
        
        # Estatísticas finais - apenas seções relevantes
        total_extracted = 0
        for section in relevant_sections:
            section_data = final_state.get(section, {})
            total_extracted += sum(1 for v in section_data.values() if v not in (None, "", "null"))
        
        logger.info("="*70)
        logger.info("✅ [LangGraph] EXTRAÇÃO CONCLUÍDA")
        logger.info("="*70)
        logger.info(f"📋 Seções Extraídas: {', '.join(relevant_sections)}")
        logger.info(f"📊 Total de Campos Extraídos: {total_extracted}/{field_stats['total']}")
        logger.info(f"💾 Taxa de Preenchimento: {(total_extracted/field_stats['total']*100):.1f}%")
        logger.info(f"🎯 Tokens Economizados: ~{economy_pct:.1f}% vs extração completa")
        logger.info("="*70)
        
        # Retornar apenas os dados extraídos das seções relevantes
        result = {}
        for section in relevant_sections:
            result[section] = final_state.get(section, {})
        
        return result
