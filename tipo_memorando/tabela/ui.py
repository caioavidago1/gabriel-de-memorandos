"""
Interface Streamlit para inputs e exibição da tabela DRE.

Este módulo fornece componentes de UI para:
- Coletar inputs do usuário (ano referência, 1º ano histórico, último ano de projeção)
- Exibir e editar a tabela DRE gerada
- Valores monetários padronizados em milhões (R$ Xm)
"""

import streamlit as st
from typing import Optional, List, Dict, Any
from tipo_memorando.tabela.dre_table import DRETableGenerator
from core.logger import get_logger

logger = get_logger(__name__)

# Linhas cujo valor é múltiplo (ex.: DV/EBITDA → "3,5x"); demais monetários = "R$ Xm", margens/pct = "X%"
_LINE_KEYS_MULTIPLE = {"dv_ebitda"}
_LINE_KEYS_PERCENT = {
    "margem_bruta", "margem_ebitda", "margem_ebit", "margem_liquida",
    "capex_pct_receita_liquida", "geracao_caixa_operacional_pct_ebitda", "geracao_caixa_pct_ebitda",
}


def _format_dre_cell(line_key: str, value: Optional[float]) -> str:
    """
    Formata valor da célula DRE: milhões (R$ Xm), percentual (X%) ou múltiplo (Xx).
    Padrão Spectra: vírgula para decimais.
    """
    if value is None:
        return "-"
    if line_key in _LINE_KEYS_PERCENT:
        s = str(value).replace(".", ",") if value % 1 != 0 else str(int(value))
        return f"{s}%"
    if line_key in _LINE_KEYS_MULTIPLE:
        s = str(value).replace(".", ",") if value % 1 != 0 else str(int(value))
        return f"{s}x"
    # Monetário em milhões
    s = str(value).replace(".", ",") if value % 1 != 0 else str(int(value))
    return f"R$ {s}m"


def _format_carg(val: Optional[float]) -> str:
    """Formata CARG em percentual (vírgula decimais)."""
    if val is None:
        return "-"
    s = str(val).replace(".", ",") if val % 1 != 0 else str(int(val))
    return f"{s}%"


def render_dre_table_inputs(show_table: bool = True) -> Optional[DRETableGenerator]:
    """
    Renderiza a interface para inputs e geração da tabela DRE.
    
    Args:
        show_table: Se True, exibe a tabela DRE após configuração. Se False, apenas configura parâmetros.
    
    Returns:
        Instância de DRETableGenerator se os inputs foram confirmados, None caso contrário
    """
    if show_table:
        st.markdown("### Histórico e Projeções")
        st.info(
            "Configure os parâmetros para gerar a tabela DRE. "
            "Após confirmar, uma tabela será criada automaticamente com as colunas de histórico e projeções."
        )
    
    # Inicializar session_state se necessário
    if "dre_table_generator" not in st.session_state:
        st.session_state.dre_table_generator = None
    
    if "dre_table_inputs_confirmed" not in st.session_state:
        st.session_state.dre_table_inputs_confirmed = False
    
    # Seção de inputs
    with st.expander("Configurar Parâmetros da Tabela", expanded=not st.session_state.dre_table_inputs_confirmed):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            ano_referencia = st.number_input(
                "Ano Referência",
                min_value=2000,
                max_value=2050,
                value=st.session_state.get("dre_ano_referencia", 2024),
                step=1,
                help="Ano de referência para os dados",
                key="dre_ano_referencia_input"
            )
        
        with col2:
            primeiro_ano_historico = st.number_input(
                "1º Ano Histórico",
                min_value=2000,
                max_value=2050,
                value=st.session_state.get("dre_primeiro_ano_historico", 2020),
                step=1,
                help="Primeiro ano do histórico (ex: 2020)",
                key="dre_primeiro_ano_historico_input"
            )
        
        with col3:
            ultimo_ano_projecao = st.number_input(
                "Último Ano de Projeção",
                min_value=2000,
                max_value=2050,
                value=st.session_state.get("dre_ultimo_ano_projecao", 2030),
                step=1,
                help="Último ano de projeção (ex: 2030)",
                key="dre_ultimo_ano_projecao_input"
            )
        
        # Validação
        if primeiro_ano_historico >= ultimo_ano_projecao:
            st.error("⚠️ O 1º ano histórico deve ser anterior ao último ano de projeção.")
            return None
        
        # Salvar inputs no session_state
        st.session_state.dre_ano_referencia = ano_referencia
        st.session_state.dre_primeiro_ano_historico = primeiro_ano_historico
        st.session_state.dre_ultimo_ano_projecao = ultimo_ano_projecao
        
        # Criar ou recriar gerador de tabela se ainda não existe ou se parâmetros mudaram
        needs_recreation = False
        if st.session_state.dre_table_generator is None:
            needs_recreation = True
        else:
            existing_gen = st.session_state.dre_table_generator
            # Verificar se algum parâmetro mudou
            if (existing_gen.ano_referencia != ano_referencia or
                existing_gen.primeiro_ano_historico != primeiro_ano_historico or
                existing_gen.ultimo_ano_projecao != ultimo_ano_projecao):
                needs_recreation = True
        
        if needs_recreation:
            generator = DRETableGenerator(
                ano_referencia=ano_referencia,
                primeiro_ano_historico=primeiro_ano_historico,
                ultimo_ano_projecao=ultimo_ano_projecao
            )
            st.session_state.dre_table_generator = generator
            st.session_state.dre_table_inputs_confirmed = True
    
    # Se os inputs foram confirmados, exibir a tabela (apenas se show_table=True)
    if show_table and st.session_state.dre_table_inputs_confirmed and st.session_state.dre_table_generator:
        generator = st.session_state.dre_table_generator
        
        st.markdown("### DRE")
        
        # Informações da tabela
        col_info1, col_info2, col_info3 = st.columns(3)
        with col_info1:
            st.caption(f"**Ano Referência:** {generator.ano_referencia}")
        with col_info2:
            st.caption(f"**Período:** {generator.primeiro_ano_historico} - {generator.ultimo_ano_projecao}")
        with col_info3:
            st.caption(f"**Total de Anos:** {len(generator.anos)}")
        
        # Tabela editável: valores monetários em R$ milhões; margens em %; Alavancagem em x
        st.caption(
            "💡 **Dica:** Valores monetários em **R$ milhões** (ex.: 100 = R$ 100m). "
            "Altere os valores nas linhas editáveis; margens, múltiplos e CARG recalculam ao vivo. Divisão por zero exibe \"-\"."
        )

        def _on_dre_cell_change(line_key: str, ano: int) -> None:
            """Atualiza o gerador com o novo valor e força rerun para recalcular linhas e CARG."""
            gen = st.session_state.get("dre_table_generator")
            if not gen:
                return
            key = f"dre_input_{line_key}_{ano}"
            val = st.session_state.get(key)
            if val is not None:
                gen.set_value(line_key, ano, val)
            st.rerun()

        line_items = generator.get_line_items()
        anos = generator.get_years()

        # Cabeçalho da tabela (anos + CARG Histórico + CARG Projetado)
        header_cols = st.columns([2] + [1] * len(anos) + [1, 1])
        with header_cols[0]:
            st.markdown("**Linha**")
        for idx, ano in enumerate(anos):
            with header_cols[idx + 1]:
                label = f"**{ano}**"
                if ano == generator.ano_referencia:
                    label += " ⭐"
                st.markdown(label)
        with header_cols[len(anos) + 1]:
            st.markdown("**CARG Histórico**")
        with header_cols[len(anos) + 2]:
            st.markdown("**CARG Projetado**")

        # Linhas da tabela
        for line_item in line_items:
            row_cols = st.columns([2] + [1] * len(anos) + [1, 1])

            with row_cols[0]:
                line_name = line_item.name
                if line_item.is_calculated:
                    line_name += " ✓"
                st.markdown(line_name)

            for idx, ano in enumerate(anos):
                with row_cols[idx + 1]:
                    if line_item.is_calculated:
                        value = generator.calculate_line(line_item, ano)
                        _val_key = f"{value:.4f}" if value is not None else "nil"
                        st.text_input(
                            f"Valor calculado para {line_item.name} em {ano}",
                            value=_format_dre_cell(line_item.key, value),
                            disabled=True,
                            key=f"dre_display_{line_item.key}_{ano}_{_val_key}",
                            label_visibility="collapsed"
                        )
                    else:
                        current_value = generator.get_value(line_item.key, ano)
                        st.number_input(
                            f"Valor para {line_item.name} em {ano}",
                            value=float(current_value) if current_value is not None else 0.0,
                            step=0.01,
                            format="%.2f",
                            key=f"dre_input_{line_item.key}_{ano}",
                            label_visibility="collapsed",
                            on_change=_on_dre_cell_change,
                            args=(line_item.key, ano),
                        )

            with row_cols[len(anos) + 1]:
                carg_hist = generator.get_carg_historico(line_item)
                _carg_hist_key = f"{carg_hist:.4f}" if carg_hist is not None else "nil"
                st.text_input(
                    f"CARG Histórico {line_item.name}",
                    value=_format_carg(carg_hist),
                    disabled=True,
                    key=f"dre_carg_hist_{line_item.key}_{_carg_hist_key}",
                    label_visibility="collapsed"
                )
            with row_cols[len(anos) + 2]:
                carg_proj = generator.get_carg_projetado(line_item)
                _carg_proj_key = f"{carg_proj:.4f}" if carg_proj is not None else "nil"
                st.text_input(
                    f"CARG Projetado {line_item.name}",
                    value=_format_carg(carg_proj),
                    disabled=True,
                    key=f"dre_carg_proj_{line_item.key}_{_carg_proj_key}",
                    label_visibility="collapsed"
                )
        
        # Visualização da tabela formatada
        st.markdown("#### Visualização da Tabela")
        
        # Preparar dados para DataFrame
        try:
            import pandas as pd
        except ImportError:
            st.error("⚠️ Pandas não está instalado. Instale com: pip install pandas")
            return generator
        
        table_data = []
        for line_item in line_items:
            row = {"Linha": line_item.name}
            for ano in anos:
                if line_item.is_calculated:
                    value = generator.calculate_line(line_item, ano)
                else:
                    value = generator.get_value(line_item.key, ano)
                row[ano] = value if value is not None else None
            row["CARG Histórico"] = generator.get_carg_historico(line_item)
            row["CARG Projetado"] = generator.get_carg_projetado(line_item)
            table_data.append(row)

        df = pd.DataFrame(table_data)
        df = df.set_index("Linha")

        # Formatar por tipo de linha: R$ Xm (milhões), X% (margens), Xx (múltiplos)
        df_formatted = df.copy().astype(object)
        for i, line_item in enumerate(line_items):
            for col in df_formatted.columns:
                val = df.iloc[i][col]
                if col in ("CARG Histórico", "CARG Projetado"):
                    df_formatted.iloc[i, df_formatted.columns.get_loc(col)] = _format_carg(val)
                else:
                    df_formatted.iloc[i, df_formatted.columns.get_loc(col)] = _format_dre_cell(line_item.key, val)
        
        # Exibir tabela
        st.dataframe(
            df_formatted,
            width='stretch',
            height=400
        )
        
        # Botão para exportar
        col_export1, col_export2 = st.columns(2)
        
        with col_export1:
            # Exportar como CSV
            csv = df.to_csv(index=True)
            st.download_button(
                label="Baixar como CSV",
                data=csv,
                file_name=f"dre_table_{generator.primeiro_ano_historico}_{generator.ultimo_ano_projecao}.csv",
                mime="text/csv",
                key="dre_export_csv"
            )
        
        with col_export2:
            # Exportar como JSON
            import json
            json_data = json.dumps(generator.to_dict(), indent=2, ensure_ascii=False)
            st.download_button(
                label="Baixar como JSON",
                data=json_data,
                file_name=f"dre_table_{generator.primeiro_ano_historico}_{generator.ultimo_ano_projecao}.json",
                mime="application/json",
                key="dre_export_json"
            )
        
        return generator
    
    return None


def fill_dre_table_from_documents(
    parsed_documents: List[Dict],
    generator: DRETableGenerator
) -> DRETableGenerator:
    """
    Preenche a tabela DRE automaticamente a partir dos documentos parseados.
    
    Args:
        parsed_documents: Lista de documentos parseados
        generator: Gerador de tabela DRE
        
    Returns:
        Gerador de tabela DRE preenchido
    """
    from tipo_memorando.tabela.extractor import extract_dre_values
    from tipo_memorando.tabela.calculos import calcular_todos_valores_calculados
    
    if not parsed_documents:
        return generator
    
    # Extrair valores dos documentos
    extracted_values = extract_dre_values(
        parsed_documents,
        generator.get_years(),
        generator.ano_referencia
    )
    
    # Calcular valores calculados
    all_values = calcular_todos_valores_calculados(extracted_values)
    
    # Atualizar tabela
    for line_key, year_data in all_values.items():
        for year, value in year_data.items():
            generator.set_value(line_key, year, value)
    
    logger.info(f"Tabela DRE preenchida automaticamente com {len(extracted_values)} campos")
    
    return generator
