"""
Componente da Aba 1 — 📅 Agenda Comercial

Exibe a agenda de pendências comerciais com filtro por período,
indicadores de vencidas/hoje/pendentes e tabela com coloração por status.

Responsabilidades:
- Exibir card informativo sobre alteração de fluxo (Sprint 1.5)
- Filtrar follow-ups de OS (responsabilidade do Pipeline OS)
- Renderizar tabela de agenda com cores
"""

from datetime import date

import streamlit as st
import pandas as pd

from services.relacionamento import get_agenda


def exibir_agenda():
    """Renderiza a aba de Agenda Comercial completa."""
    st.subheader("📅 Agenda Comercial")

    # ── Sprint 1.5: Card informativo sobre alteração de fluxo ──
    with st.container(border=True):
        cols = st.columns([5, 1])
        cols[0].markdown(
            "**ℹ️ Alteração de fluxo operacional**  \n"
            "Os follow-ups de propostas e orçamentos agora são realizados "
            "exclusivamente no módulo **Pipeline OS**. Esta página permanece "
            "dedicada ao relacionamento comercial com clientes."
        )
        if cols[1].button(
            "📦 Abrir Pipeline OS",
            key="btn_pipeline_agenda",
            use_container_width=True,
        ):
            st.switch_page("pages/11_Pipeline_OS.py")

    col_filtro, _ = st.columns([1, 3])
    with col_filtro:
        dias_agenda = st.selectbox(
            "Período",
            options=["Hoje", "Próximos 7 dias", "Próximos 30 dias"],
            index=1,
            key="agenda_periodo",
        )

    dias_map = {"Hoje": 0, "Próximos 7 dias": 7, "Próximos 30 dias": 30}
    dias_frente = dias_map[dias_agenda]

    with st.spinner("Carregando agenda..."):
        df_agenda = get_agenda(
            dias_frente=dias_frente,
            responsavel=None,
        )

    # ── Sprint 1: Remover follow-ups de OS da agenda comercial ──
    if not df_agenda.empty and "tipo_agenda" in df_agenda.columns:
        df_agenda = df_agenda[df_agenda["tipo_agenda"] != "FOLLOW-UP"].copy()

    if df_agenda.empty:
        st.success("🎉 Nenhum item pendente para o período selecionado.")
    else:
        hoje = date.today().strftime("%Y-%m-%d")

        df_hoje = df_agenda[df_agenda["data_prevista"] == hoje].copy()
        df_pendente = df_agenda[
            (df_agenda["status"] == "PENDENTE")
            & (df_agenda["data_prevista"] != hoje)
        ].copy()
        df_vencida = df_agenda[df_agenda["status"] == "VENCIDA"].copy()

        c1, c2, c3 = st.columns(3)
        c1.metric("🔴 Vencidas", len(df_vencida))
        c2.metric("🟡 Hoje", len(df_hoje))
        c3.metric("🟢 A vencer", len(df_pendente))

        st.divider()

        def cor_status(row):
            if row["status"] == "VENCIDA":
                return ["background-color: #f8d7da; color: #721c24"] * len(row)
            elif row["status"] == "HOJE":
                return ["background-color: #fff3cd; color: #856404"] * len(row)
            return [""] * len(row)

        st.dataframe(
            df_agenda.style.apply(cor_status, axis=1),
            width="stretch",
            height=500,
            column_config={
                "data_prevista": st.column_config.DateColumn("Data Prevista"),
                "tipo_interacao": "Tipo",
                "assunto": "Assunto",
                "cliente": "Cliente",
                "responsavel": "Responsável",
                "descricao": "Descrição",
                "tipo_agenda": "Categoria",
                "status": "Status",
            },
        )