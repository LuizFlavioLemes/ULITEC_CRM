"""
Componente da Aba 1 — 📅 Agenda Comercial

Exibe a agenda de pendências comerciais com filtro por período,
indicadores de vencidas/hoje/pendentes e tabela com coloração por status.

Responsabilidades:
- Exibir card informativo sobre alteração de fluxo (Sprint 1.5)
- Filtrar follow-ups de OS (responsabilidade do Pipeline OS)
- Renderizar tabela de agenda com cores
"""

from datetime import date, datetime, timedelta

import streamlit as st
import pandas as pd

from services.relacionamento import get_agenda


def _proximo_dia_util(d: date) -> date:
    """Retorna o próximo dia útil (segunda a sexta) após a data informada."""
    proximo = d + timedelta(days=1)
    while proximo.weekday() >= 5:  # 5 = sábado, 6 = domingo
        proximo += timedelta(days=1)
    return proximo


def obter_cor_pendencia(data_limite):
    """
    Determina a cor de exibição de uma pendência na agenda com base na urgência.

    Padrão de cores:
        - Vermelho: pendências vencidas
        - Azul:     pendências que vencem HOJE
        - Amarelo:  pendências que vencem no PRÓXIMO DIA ÚTIL
        - Padrão:   demais pendências (sem coloração)

    Regras:
        - Considera apenas dias úteis (segunda a sexta).
        - Ignora sábado e domingo.
        - Não considera feriados nacionais nesta versão.

    Parâmetros:
        data_limite: Data limite da pendência (date ou str "YYYY-MM-DD").

    Retorna:
        Tupla (cor_fundo, cor_texto) ou None se não houver coloração especial.
    """
    if data_limite is None:
        return None

    if isinstance(data_limite, str):
        data_limite = datetime.strptime(data_limite[:10], "%Y-%m-%d").date()
    elif isinstance(data_limite, datetime):
        # Cobre datetime.datetime e pd.Timestamp (subclasse de datetime)
        data_limite = data_limite.date()

    hoje = date.today()

    if data_limite < hoje:
        return ("#f8d7da", "#721c24")  # Vermelho — vencida
    if data_limite == hoje:
        return ("#cce5ff", "#004085")  # Azul — vence hoje
    if data_limite == _proximo_dia_util(hoje):
        return ("#fff3cd", "#856404")  # Amarelo — próximo dia útil
    return None


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
            cor = obter_cor_pendencia(row["data_prevista"])
            if cor is None:
                return [""] * len(row)
            fundo, texto = cor
            return [f"background-color: {fundo}; color: {texto}"] * len(row)

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