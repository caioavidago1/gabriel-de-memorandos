"""
Interface Streamlit para inputs e exibição da tabela DRE.

Este módulo fornece componentes de UI para:
- Coletar inputs do usuário (ano referência, 1º ano histórico, último ano de projeção)
- Exibir e editar a tabela DRE gerada
"""

import streamlit as st
from typing import Optional, List, Dict
from facts.tabela.dre_table import DRETableGenerator
from core.logger import get_logger

logger = get_logger(__name__)


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
        
        # Tabela editável
        st.caption(
            "💡 **Dica:** Preencha os valores nas linhas não calculadas. "
            "As linhas calculadas (marcadas com ✓) serão atualizadas automaticamente."
        )
        
        # Criar formulário para edição
        with st.form("dre_table_edit_form", clear_on_submit=False):
            # Tabela de edição
            line_items = generator.get_line_items()
            anos = generator.get_years()
            
            # Cabeçalho da tabela
            header_cols = st.columns([2] + [1] * len(anos))
            with header_cols[0]:
                st.markdown("**Linha**")
            for idx, ano in enumerate(anos):
                with header_cols[idx + 1]:
                    # Marcar ano de referência
                    label = f"**{ano}**"
                    if ano == generator.ano_referencia:
                        label += " ⭐"
                    st.markdown(label)
            
            # Armazenar valores editados temporariamente
            edited_values = {}
            
            # Linhas da tabela
            for line_item in line_items:
                row_cols = st.columns([2] + [1] * len(anos))
                
                with row_cols[0]:
                    # Nome da linha com indicador de calculada
                    line_name = line_item.name
                    if line_item.is_calculated:
                        line_name += " ✓"
                    st.markdown(line_name)
                
                # Campos de input para cada ano
                for idx, ano in enumerate(anos):
                    with row_cols[idx + 1]:
                        if line_item.is_calculated:
                            # Linha calculada: mostrar valor calculado (readonly)
                            value = generator.calculate_line(line_item, ano)
                            if value is not None:
                                st.text_input(
                                    f"Valor calculado para {line_item.name} em {ano}",
                                    value=f"{value:,.2f}",
                                    disabled=True,
                                    key=f"dre_display_{line_item.key}_{ano}",
                                    label_visibility="collapsed"
                                )
                            else:
                                st.text_input(
                                    f"Valor calculado para {line_item.name} em {ano}",
                                    value="-",
                                    disabled=True,
                                    key=f"dre_display_{line_item.key}_{ano}",
                                    label_visibility="collapsed"
                                )
                        else:
                            # Linha editável: permitir input
                            current_value = generator.get_value(line_item.key, ano)
                            new_value = st.number_input(
                                f"Valor para {line_item.name} em {ano}",
                                value=float(current_value) if current_value is not None else 0.0,
                                step=0.01,
                                format="%.2f",
                                key=f"dre_input_{line_item.key}_{ano}",
                                label_visibility="collapsed"
                            )
                            # Armazenar valor editado (será aplicado ao submeter)
                            edited_values[(line_item.key, ano)] = new_value if new_value != 0.0 or current_value is not None else None
            
            # Botão de salvar
            submitted = st.form_submit_button("Salvar", type="primary")
            
            if submitted:
                # Aplicar valores editados ao gerador
                for (line_key, year), value in edited_values.items():
                    generator.set_value(line_key, year, value)
                
                # Atualizar session_state
                st.session_state.dre_table_generator = generator
                st.success("✅ Alterações salvas!")
                st.rerun()
        
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
            table_data.append(row)
        
        df = pd.DataFrame(table_data)
        df = df.set_index("Linha")
        
        # Formatar valores para exibição
        def format_value(val):
            if val is None:
                return "-"
            return f"R$ {val:,.2f}"
        
        # Aplicar formatação
        df_formatted = df.copy()
        for col in df_formatted.columns:
            df_formatted[col] = df_formatted[col].apply(format_value)
        
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
    from facts.tabela.extractor import extract_dre_values
    from facts.tabela.calculos import calcular_todos_valores_calculados
    
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
