"""
Componente de Relacionamento na Central de Oportunidades.
Consome exclusivamente services/relacionamento.
Nenhum SQL é executado aqui.
"""

from datetime import date
import pandas as pd
import streamlit as st

from services.relacionamento import (
    get_alertas_relacionamento,
    get_pendencias,
    carregar_configs_relacionamento,
    get_proximas_acoes_consolidadas,
    get_contagem_proximas_acoes,
)


def exibir_acoes_relacionamento(unidade_param=None):
    """
    Renderiza a seção de Relacionamento (Alertas, Pendências, Próximas Ações)
    da Central de Oportunidades.

    Parâmetros:
        unidade_param: str or None — filtro de unidade
    """
    configs = carregar_configs_relacionamento()
    alertas_rel = get_alertas_relacionamento(unidade=unidade_param)

    tab_alertas, tab_pendencias, tab_acoes = st.tabs([
        "Alertas",
        "Pendências",
        "Próximas Ações",
    ])

    # ── Alertas ──
    with tab_alertas:
        st.subheader("Alertas de Relacionamento")
        if not alertas_rel:
            st.success("Nenhum alerta no momento.")
        else:
            df_alertas = pd.DataFrame(alertas_rel)
            st.dataframe(
                df_alertas[["cliente", "descricao", "severidade", "tipo"]].rename(
                    columns={
                        "cliente": "Cliente",
                        "descricao": "Descrição",
                        "severidade": "Severidade",
                        "tipo": "Tipo",
                    }
                ),
                width="stretch",
                height=400,
            )

    # ── Pendências ──
    with tab_pendencias:
        st.subheader("Pendências")
        df_pend_abertas = get_pendencias(status="ABERTA")
        if df_pend_abertas.empty:
            st.success("Nenhuma pendência aberta.")
        else:
            df_pend_exib = df_pend_abertas.rename(columns={
                "cliente": "Cliente",
                "descricao": "Descrição",
                "responsavel": "Responsável",
                "prioridade": "Prioridade",
                "data_limite": "Vencimento",
            })
            if "Vencimento" in df_pend_exib.columns:
                df_pend_exib["Vencimento"] = pd.to_datetime(df_pend_exib["Vencimento"], errors="coerce")
                df_pend_exib["Vencimento"] = df_pend_exib["Vencimento"].dt.strftime("%d/%m/%Y")

            st.dataframe(
                df_pend_exib[["Cliente", "Descrição", "Responsável", "Prioridade", "Vencimento"]],
                width="stretch",
                height=400,
            )

    # ── Próximas Ações ──
    with tab_acoes:
        st.subheader("Próximas Ações — Agenda")

        contagens = get_contagem_proximas_acoes()

        card_cols = st.columns(4)
        card_cols[0].metric("Atrasadas", contagens["atrasadas"])
        card_cols[1].metric("Hoje", contagens["hoje"])
        card_cols[2].metric("Próximos 7 dias", contagens["proximos_7"])
        card_cols[3].metric("Próximos 30 dias", contagens["proximos_30"])

        st.markdown("---")

        filtros_col1, filtros_col2, filtros_col3, filtros_col4 = st.columns(4)

        df_resp = get_pendencias(status="ABERTA")
        responsables = ["Todos"]
        if not df_resp.empty and "responsavel" in df_resp.columns:
            resp_list = df_resp["responsavel"].dropna().unique().tolist()
            responsables = ["Todos"] + sorted(resp_list)

        filtro_resp_acoes = filtros_col1.selectbox(
            "Responsável", options=responsables, key="filtro_resp_acoes"
        )

        filtro_cliente_acoes = filtros_col2.text_input(
            "Cliente", placeholder="Digite parte do nome...", key="filtro_cliente_acoes"
        )

        col_periodo_inicio, col_periodo_fim = st.columns(2)
        filtro_periodo_inicio = col_periodo_inicio.date_input(
            "Data início", value=None, key="filtro_periodo_inicio_acoes"
        )
        filtro_periodo_fim = col_periodo_fim.date_input(
            "Data fim", value=None, key="filtro_periodo_fim_acoes"
        )

        hoje = date.today()
        filtro_status_acoes = filtros_col4.selectbox(
            "Status", options=["Todos", "VENCIDA", "HOJE", "FUTURO"],
            key="filtro_status_acoes",
        )

        params_resp = filtro_resp_acoes if filtro_resp_acoes != "Todos" else None
        params_cliente = filtro_cliente_acoes if filtro_cliente_acoes else None
        params_inicio = filtro_periodo_inicio.strftime("%Y-%m-%d") if filtro_periodo_inicio else None
        params_fim = filtro_periodo_fim.strftime("%Y-%m-%d") if filtro_periodo_fim else None
        params_status = filtro_status_acoes if filtro_status_acoes != "Todos" else None

        df_acoes_consolidadas = get_proximas_acoes_consolidadas(
            filtro_responsavel=params_resp,
            filtro_cliente=params_cliente,
            filtro_periodo_inicio=params_inicio,
            filtro_periodo_fim=params_fim,
            filtro_status=params_status,
        )

        if df_acoes_consolidadas.empty:
            st.success("Nenhuma ação encontrada com os filtros atuais.")
        else:
            df_exib_acoes = df_acoes_consolidadas.copy()
            df_exib_acoes["data"] = pd.to_datetime(df_exib_acoes["data"], errors="coerce")
            df_exib_acoes["data"] = df_exib_acoes["data"].dt.strftime("%d/%m/%Y")

            def cor_origem(row):
                if row.get("origem") == "Pendência":
                    return ["background-color: #fff3cd; color: #856404"] * len(row)
                return [""] * len(row)

            st.dataframe(
                df_exib_acoes[["data", "cliente", "contato", "responsavel", "tipo_acao", "observacao", "origem"]]
                .rename(columns={
                    "data": "Data",
                    "cliente": "Cliente",
                    "contato": "Contato",
                    "responsavel": "Responsável",
                    "tipo_acao": "Tipo",
                    "observacao": "Observação",
                    "origem": "Origem",
                })
                .style.apply(cor_origem, axis=1),
                width="stretch",
                height=500,
            )