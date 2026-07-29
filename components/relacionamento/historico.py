"""
Componente da Aba 3 — 📋 Histórico de Interações

Exibe o histórico de interações registradas com filtros por cliente,
tipo, responsável e período. Tabela com coloração por resultado.

Responsabilidades:
- Renderizar filtros de consulta
- Exibir tabela de interações com destaque por resultado
"""

from datetime import date, timedelta

import streamlit as st
import pandas as pd

from services.relacionamento import TIPOS_INTERACAO, get_historico_interacoes


def exibir_historico(clientes_lista, clientes_dict):
    """
    Renderiza a aba de Histórico de Interações.

    Parâmetros:
        clientes_lista: list[str] — labels para selectbox
        clientes_dict: dict — mapeia label → id
    """
    st.subheader("📋 Histórico de Interações")

    with st.expander("🔍 Filtros", expanded=True):
        col_f1, col_f2, col_f3 = st.columns(3)

        with col_f1:
            hist_cliente = st.selectbox(
                "Cliente",
                options=["Todos"] + clientes_lista,
                key="hist_cliente",
            )

        with col_f2:
            hist_tipo = st.selectbox(
                "Tipo de Interação",
                options=["Todos"] + TIPOS_INTERACAO,
                key="hist_tipo",
            )

        with col_f3:
            hist_responsavel = st.text_input(
                "Responsável",
                key="hist_responsavel",
            )

        col_f4, col_f5 = st.columns(2)
        with col_f4:
            hist_data_ini = st.date_input(
                "Data início",
                value=date.today() - timedelta(days=90),
                key="hist_data_ini",
            )
        with col_f5:
            hist_data_fim = st.date_input(
                "Data fim",
                value=date.today(),
                key="hist_data_fim",
            )

    hist_params = {}

    if hist_cliente != "Todos":
        hist_params["cliente_id"] = clientes_dict[hist_cliente]
    if hist_tipo != "Todos":
        hist_params["tipo"] = hist_tipo
    if hist_responsavel:
        hist_params["responsavel"] = hist_responsavel

    hist_params["data_inicio"] = hist_data_ini.strftime("%Y-%m-%d")
    hist_params["data_fim"] = hist_data_fim.strftime("%Y-%m-%d")
    hist_params["limite"] = 500

    with st.spinner("Carregando histórico..."):
        df_historico = get_historico_interacoes(**hist_params)

    if df_historico.empty:
        st.info("Nenhuma interação encontrada com os filtros selecionados.")
    else:
        st.caption(f"📊 {len(df_historico)} interações encontradas.")

        def cor_resultado(row):
            if row["resultado"] == "Positivo":
                return ["background-color: #d4edda; color: #155724"] * len(row)
            elif row["resultado"] == "Negativo":
                return ["background-color: #f8d7da; color: #721c24"] * len(row)
            return [""] * len(row)

        st.dataframe(
            df_historico.style.apply(cor_resultado, axis=1),
            width="stretch",
            height=500,
            column_config={
                "data_interacao": st.column_config.DateColumn("Data"),
                "tipo_interacao": "Tipo",
                "assunto": "Assunto",
                "cliente": "Cliente",
                "contato_nome": "Contato",
                "contato_cargo": "Cargo",
                "responsavel": "Resp.",
                "descricao": "Descrição",
                "resultado": "Resultado",
                "tipo_prox_acao": "Próx. Ação",
                "data_proxima_acao": st.column_config.DateColumn("Data Próx."),
                "status_exibicao": "Status",
            },
        )