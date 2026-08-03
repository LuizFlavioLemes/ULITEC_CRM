
from datetime import date, timedelta

import pandas as pd
import streamlit as st

from auth import sidebar_usuario
from permissions import verificar_acesso_pagina, pode_selecionar_unidade
from services.relacionamento import get_config

from database import get_connection

# ── Proteção: autenticado (todos os perfis) ──
verificar_acesso_pagina()
sidebar_usuario()

st.set_page_config(
    page_title="Pipeline OS",
    layout="wide"
)

st.title("📦 Pipeline de Ordens de Serviço")
st.markdown(
    "Gerencie propostas, ordens de serviço, follow-ups e andamento operacional. "
    "Acompanhe o ciclo completo desde o recebimento até a expedição."
)
st.divider()

# ── Inicialização da segregação por filial ──
if "perfil" not in st.session_state:
    st.session_state["perfil"] = "SOCIO"
if "unidade_ativa" not in st.session_state:
    st.session_state["unidade_ativa"] = "GRUPO"
if "unidade_usuario" not in st.session_state:
    st.session_state["unidade_usuario"] = "ULITEC SP"

if pode_selecionar_unidade():
    escolha = st.sidebar.selectbox(
        "Filtrar Unidade (Visão Gestor)",
        options=["Grupo (Consolidado)", "ULITEC SP", "ULITEC RS"],
        index=0 if st.session_state["unidade_ativa"] == "GRUPO"
               else (1 if st.session_state["unidade_ativa"] == "ULITEC SP" else 2)
    )
    st.session_state["unidade_ativa"] = "GRUPO" if escolha == "Grupo (Consolidado)" else escolha
else:
    st.session_state["unidade_ativa"] = st.session_state["unidade_usuario"]

DB = "crm.db"

STATUS_OS = [
    "RECEBIDA",
    "EM ANALISE",
    "PROPOSTA ENVIADA",
    "FOLLOW-UP",
    "APROVADA",
    "PERDIDA",
    "FATURADA",
    "EXPEDIDA",
    "CANCELADA"
]

conn = get_connection()

query_base = """
    SELECT
        os.id,
        os.numero_os,
        os.status,
        os.unidade,
        os.responsavel,
        os.tecnico,
        os.equipamento,
        os.marca,
        os.modelo,
        os.serial_number,
        os.valor_estimado,
        os.valor_proposta,
        os.valor_faturado,
        os.data_recebimento,
        os.data_envio_proposta,
        os.data_aprovacao,
        os.data_faturamento,
        os.data_expedicao,
        os.proximo_followup,
        os.motivo_perda,
        os.observacoes,
        c.razao_social cliente
    FROM ordens_servico os
    LEFT JOIN clientes c
        ON c.id = os.cliente_id
"""

if st.session_state["unidade_ativa"] == "GRUPO":
    query_final = query_base + " ORDER BY os.id DESC"
    params = ()
else:
    query_final = query_base + " WHERE os.unidade = ? ORDER BY os.id DESC"
    params = (st.session_state["unidade_ativa"],)

df = pd.read_sql_query(query_final, conn, params=params)

if df.empty:
    st.warning("Nenhuma OS encontrada.")
    st.stop()

for campo in [
    "data_recebimento",
    "data_envio_proposta",
    "data_aprovacao",
    "data_faturamento",
    "data_expedicao",
    "proximo_followup"
]:
    df[campo] = pd.to_datetime(
        df[campo],
        errors="coerce"
    )

abertas = df[
    ~df["status"].isin(
        [
            "FATURADA",
            "EXPEDIDA",
            "PERDIDA",
            "CANCELADA"
        ]
    )
]

valor_parado = abertas["valor_proposta"].fillna(0).sum()

valor_faturado = (
    df["valor_faturado"]
    .fillna(0)
    .sum()
)

followups_vencidos = len(
    abertas[
        abertas["proximo_followup"]
        < pd.Timestamp.today()
    ]
)

aprovadas = len(
    df[df["status"] == "APROVADA"]
)

enviadas = len(
    df[
        df["status"].isin(
            [
                "PROPOSTA ENVIADA",
                "APROVADA",
                "FATURADA",
                "EXPEDIDA"
            ]
        )
    ]
)

taxa_aprovacao = 0

if enviadas > 0:
    taxa_aprovacao = round(
        aprovadas / enviadas * 100,
        1
    )

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric(
    "OS abertas",
    len(abertas)
)

c2.metric(
    "Valor parado",
    f"R$ {valor_parado:,.0f}"
)

c3.metric(
    "Valor faturado",
    f"R$ {valor_faturado:,.0f}"
)

c4.metric(
    "Follow-up vencido",
    followups_vencidos
)

c5.metric(
    "Taxa aprovação",
    f"{taxa_aprovacao}%"
)

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "Pipeline",
        "Atualizar OS",
        "Indicadores",
        "📞 Follow-up de Propostas",
        "⚡ Ações em Massa"
    ]
)

with tab1:

    st.subheader("Pipeline de OS")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        opcoes_status = sorted(
            set(df["status"].dropna().unique()) | set(STATUS_OS)
        )
        filtro_status = st.multiselect(
            "Status",
            opcoes_status,
            default=sorted(df["status"].dropna().unique())
        )

    with col2:
        filtro_unidade = st.multiselect(
            "Unidade",
            sorted(df["unidade"].dropna().unique()),
            default=sorted(df["unidade"].dropna().unique())
        )

    with col3:
        filtro_resp = st.multiselect(
            "Responsável",
            sorted(df["responsavel"].dropna().unique()),
            default=sorted(df["responsavel"].dropna().unique())
        )

    with col4:
        filtro_tecnico = st.multiselect(
            "Técnico",
            sorted(df["tecnico"].dropna().unique()),
            default=sorted(df["tecnico"].dropna().unique())
        )

    pipeline = df.copy()

    if filtro_status:
        pipeline = pipeline[
            pipeline["status"].isin(filtro_status)
        ]

    if filtro_unidade:
        pipeline = pipeline[
            pipeline["unidade"].isin(filtro_unidade)
        ]

    if filtro_resp:
        pipeline = pipeline[
            pipeline["responsavel"].isin(filtro_resp)
        ]

    if filtro_tecnico:
        pipeline = pipeline[
            pipeline["tecnico"].isin(filtro_tecnico)
        ]

    st.dataframe(
        pipeline[
            [
                "numero_os",
                "cliente",
                "status",
                "unidade",
                "responsavel",
                "tecnico",
                "valor_proposta",
                "valor_faturado",
                "data_recebimento",
                "data_aprovacao"
            ]
        ],
        width="stretch",
        height=600
    )

with tab2:

    st.subheader("Atualizar OS")

    opcoes_os = {
        f"{row.numero_os} | {row.cliente}": row.id
        for row in df.itertuples()
    }

    os_selecionada = st.selectbox(
        "Selecione a OS",
        list(opcoes_os.keys())
    )

    os_id = opcoes_os[os_selecionada]

    registro = df[
        df["id"] == os_id
    ].iloc[0]

    with st.form("form_os"):

        st.markdown("### Comercial")

        c1, c2, c3 = st.columns(3)

        with c1:
            status = st.selectbox(
                "Status",
                STATUS_OS,
                index=STATUS_OS.index(registro["status"])
                if registro["status"] in STATUS_OS
                else 0
            )

        with c2:
            responsavel = st.text_input(
                "Responsável",
                value=registro["responsavel"]
                if pd.notna(registro["responsavel"])
                else ""
            )

        with c3:
            valor_estimado = st.number_input(
                "Valor Estimado",
                value=float(
                    registro["valor_estimado"]
                    if pd.notna(registro["valor_estimado"])
                    else 0
                )
            )

        c1, c2 = st.columns(2)

        with c1:
            valor_proposta = st.number_input(
                "Valor Proposta",
                value=float(
                    registro["valor_proposta"]
                    if pd.notna(registro["valor_proposta"])
                    else 0
                )
            )

        st.markdown("### Técnico")

        c1, c2, c3 = st.columns(3)

        with c1:
            tecnico = st.text_input(
                "Técnico",
                value=registro["tecnico"]
                if pd.notna(registro["tecnico"])
                else ""
            )

        with c2:
            equipamento = st.text_input(
                "Equipamento",
                value=registro["equipamento"]
                if pd.notna(registro["equipamento"])
                else ""
            )

        with c3:
            marca = st.text_input(
                "Marca",
                value=registro["marca"]
                if pd.notna(registro["marca"])
                else ""
            )

        c1, c2 = st.columns(2)

        with c1:
            modelo = st.text_input(
                "Modelo",
                value=registro["modelo"]
                if pd.notna(registro["modelo"])
                else ""
            )

        with c2:
            serial = st.text_input(
                "Serial",
                value=registro["serial_number"]
                if pd.notna(registro["serial_number"])
                else ""
            )

        st.markdown("### Financeiro")
      
        valor_faturado = st.number_input(
            "Valor Faturado",
            value=float(
                registro["valor_faturado"]
                if pd.notna(registro["valor_faturado"])
                else 0
            )
        )

        st.markdown("### Datas")

        c1, c2, c3 = st.columns(3)

        with c1:
            data_envio = st.date_input(
                "Data envio proposta",
                value=pd.to_datetime(
                    registro["data_envio_proposta"]
                ).date()
                if pd.notna(registro["data_envio_proposta"])
                else None
            )

        with c2:
            data_aprovacao = st.date_input(
                "Data aprovação",
                value=pd.to_datetime(
                    registro["data_aprovacao"]
                ).date()
                if pd.notna(registro["data_aprovacao"])
                else None
            )

        with c3:
            data_faturamento = st.date_input(
                "Data faturamento",
                value=pd.to_datetime(
                    registro["data_faturamento"]
                ).date()
                if pd.notna(registro["data_faturamento"])
                else None
            )

        c1, c2 = st.columns(2)

        with c1:
            data_expedicao = st.date_input(
                "Data expedição",
                value=pd.to_datetime(
                    registro["data_expedicao"]
                ).date()
                if pd.notna(registro["data_expedicao"])
                else None
            )

        with c2:
            data_perda = st.date_input(
                "Data perda",
                value=pd.to_datetime(
                    registro.get("data_perda")
                ).date()
                if pd.notna(registro.get("data_perda"))
                else None
            )

        st.markdown("### Observações")

        motivo_perda = st.text_input(
            "Motivo perda",
            value=registro["motivo_perda"]
            if pd.notna(registro["motivo_perda"])
            else ""
        )

        observacoes = st.text_area(
            "Observações",
            value=registro["observacoes"]
            if pd.notna(registro["observacoes"])
            else ""
        )

        salvar = st.form_submit_button(
            "Salvar Alterações"
        )

    if salvar:

        # ── Lê followup atual do banco para casos de transição não-terminal ──
        row_atual = conn.execute(
            "SELECT proximo_followup FROM ordens_servico WHERE id = ?",
            (int(os_id),)
        ).fetchone()

        followup_atual = row_atual[0] if row_atual else None

        # ── Calcula followup automaticamente ──
        # v1.5.2: Quando volta para PROPOSTA ENVIADA, reseta o ciclo de follow-up
        resetar_ciclo = False
        if status in ("APROVADA", "FATURADA", "EXPEDIDA", "PERDIDA", "CANCELADA"):
            followup_calc = None
        elif status == "PROPOSTA ENVIADA":
            dias = int(get_config("followup_1", "2"))
            followup_calc = date.today() + timedelta(days=dias)
            # Reseta o ciclo se a OS estava em status terminal ou follow-up
            if registro["status"] in (
                "APROVADA", "FATURADA", "EXPEDIDA", "PERDIDA", "CANCELADA"
            ):
                resetar_ciclo = True
        else:
            followup_calc = followup_atual

        # ── Monta dicionário com apenas campos que mudam ──
        campos = {
            "status": status,
            "responsavel": responsavel,
            "tecnico": tecnico,
            "equipamento": equipamento,
            "marca": marca,
            "modelo": modelo,
            "serial_number": serial,
            "valor_estimado": valor_estimado,
            "valor_proposta": valor_proposta,
            "valor_faturado": valor_faturado,
            "data_aprovacao": str(data_aprovacao) if data_aprovacao else None,
            "data_faturamento": str(data_faturamento) if data_faturamento else None,
            "data_expedicao": str(data_expedicao) if data_expedicao else None,
            "data_perda": str(data_perda) if data_perda else None,
            "motivo_perda": motivo_perda,
            "observacoes": observacoes,
            "data_atualizacao": str(date.today()),
            "proximo_followup": str(followup_calc) if followup_calc else None,
            "data_envio_proposta": str(data_envio) if data_envio else (
                "date('now')" if status == "PROPOSTA ENVIADA" else None
            )
        }

        sets = []
        vals = []
        for col, val in campos.items():
            if val == "date('now')":
                sets.append(f"{col} = date('now')")
            else:
                sets.append(f"{col} = ?")
                vals.append(val)

        # v1.5.2: Reseta ciclo de follow-up quando OS volta para PROPOSTA ENVIADA
        if resetar_ciclo:
            sets.append("followup_count = 0")

        vals.append(int(os_id))

        conn.execute(
            f"UPDATE ordens_servico SET {', '.join(sets)} WHERE id = ?",
            vals
        )

        conn.commit()

        st.success(
            "OS atualizada com sucesso."
        )

        st.rerun()

with tab3:

    st.subheader("📊 Indicadores de Performance")

    # ── Filtro de Período Temporal ──
    periodo = st.radio(
        "Período",
        options=[
            "Últimos 15 dias",
            "Últimos 30 dias",
            "Últimos 60 dias",
            "Mês Atual",
            "Ano Atual",
            "Todo o Período"
        ],
        index=5,
        horizontal=True,
        label_visibility="collapsed"
    )

    hoje = pd.Timestamp.today()

    if periodo == "Últimos 15 dias":
        df_filtrado = df[df["data_recebimento"] >= hoje - pd.Timedelta(days=15)].copy()
    elif periodo == "Últimos 30 dias":
        df_filtrado = df[df["data_recebimento"] >= hoje - pd.Timedelta(days=30)].copy()
    elif periodo == "Últimos 60 dias":
        df_filtrado = df[df["data_recebimento"] >= hoje - pd.Timedelta(days=60)].copy()
    elif periodo == "Mês Atual":
        df_filtrado = df[
            (df["data_recebimento"].dt.year == hoje.year) &
            (df["data_recebimento"].dt.month == hoje.month)
        ].copy()
    elif periodo == "Ano Atual":
        df_filtrado = df[
            df["data_recebimento"].dt.year == hoje.year
        ].copy()
    else:
        df_filtrado = df.copy()

    # ── KPIs ──
    qtd_abertas = len(df_filtrado[~df_filtrado["status"].isin(["FATURADA", "EXPEDIDA", "PERDIDA", "CANCELADA"])])
    qtd_aprovadas = len(df_filtrado[df_filtrado["status"] == "APROVADA"])
    qtd_faturadas = len(df_filtrado[df_filtrado["status"] == "FATURADA"])
    qtd_perdidas = len(df_filtrado[df_filtrado["status"] == "PERDIDA"])

    valor_propostas = df_filtrado["valor_proposta"].fillna(0).sum()
    valor_faturado_total = df_filtrado["valor_faturado"].fillna(0).sum()
    aguardando_aprovacao = df_filtrado.loc[df_filtrado["status"] == "PROPOSTA ENVIADA", "valor_proposta"].fillna(0).sum()

    total_periodo = len(df_filtrado)
    aprovadas_faturadas_expedidas = len(df_filtrado[df_filtrado["status"].isin(["APROVADA", "FATURADA", "EXPEDIDA"])])
    taxa_aprovacao = round(aprovadas_faturadas_expedidas / total_periodo * 100, 1) if total_periodo > 0 else 0.0

    # Tempo médio de envio de proposta
    df_tempo = df_filtrado.dropna(subset=["data_recebimento", "data_envio_proposta"]).copy()
    df_tempo["dias_envio"] = (df_tempo["data_envio_proposta"] - df_tempo["data_recebimento"]).dt.days
    tempo_medio_envio = round(df_tempo["dias_envio"].mean(), 1) if len(df_tempo) > 0 else 0

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("🟡 OS Abertas", qtd_abertas)
    k2.metric("✅ OS Aprovadas", qtd_aprovadas)
    k3.metric("💰 OS Faturadas", qtd_faturadas)
    k4.metric("❌ OS Perdidas", qtd_perdidas)

    k5, k6, k7, k8 = st.columns(4)
    k5.metric("📋 Valor em Propostas", f"R$ {valor_propostas:,.0f}")
    k6.metric("💵 Valor Faturado", f"R$ {valor_faturado_total:,.0f}")
    k7.metric("⏳ Aguardando Aprovação", f"R$ {aguardando_aprovacao:,.0f}")
    k8.metric("📈 Taxa de Aprovação", f"{taxa_aprovacao}%")

    # ── Métrica de Eficiência Comercial ──
    st.markdown("---")
    ce1, ce2, ce3 = st.columns([1, 2, 1])
    with ce2:
        st.metric(
            "⏱️ Tempo Médio de Envio de Proposta",
            f"{tempo_medio_envio} dias",
            help="Média de dias entre o recebimento da OS e o envio da proposta"
        )

    # ── Visão por Unidade ──
    st.markdown("---")
    st.subheader("🏢 Performance por Unidade")

    grupo_unidade = df_filtrado.groupby("unidade").agg(
        Quantidade=("id", "count"),
        Valor_Total_Propostas=("valor_proposta", "sum"),
        Valor_Total_Faturado=("valor_faturado", "sum")
    ).reset_index()
    grupo_unidade.columns = ["Unidade", "Qtd OS", "Valor Total Propostas", "Valor Total Faturado"]
    grupo_unidade["Valor Total Propostas"] = grupo_unidade["Valor Total Propostas"].apply(
        lambda x: f"R$ {x:,.0f}" if pd.notna(x) else "R$ 0"
    )
    grupo_unidade["Valor Total Faturado"] = grupo_unidade["Valor Total Faturado"].apply(
        lambda x: f"R$ {x:,.0f}" if pd.notna(x) else "R$ 0"
    )

    st.dataframe(grupo_unidade, width="stretch", hide_index=True)

    # ── Visão por Técnico ──
    st.markdown("---")
    st.subheader("🔧 Ranking por Técnico")

    grupo_tecnico = df_filtrado.groupby("tecnico").agg(
        Quantidade=("id", "count"),
        Valor_Total_Faturado=("valor_faturado", "sum")
    ).reset_index()
    grupo_tecnico.columns = ["Técnico", "Qtd OS", "Valor Total Faturado"]
    grupo_tecnico["Valor Total Faturado"] = grupo_tecnico["Valor Total Faturado"].apply(
        lambda x: f"R$ {x:,.0f}" if pd.notna(x) else "R$ 0"
    )
    grupo_tecnico = grupo_tecnico.sort_values("Qtd OS", ascending=False)

    st.dataframe(grupo_tecnico, width="stretch", hide_index=True)

# =====================================================
# ABA 4 — FOLLOW-UP DE PROPOSTAS (PAINEL OPERACIONAL)
# =====================================================

with tab4:

    st.subheader("📞 Painel Operacional — Follow-up de Propostas")

    # Filtrar OS com proposta enviada e aguardando retorno
    df_propostas = df[
        df["status"].isin(["PROPOSTA ENVIADA", "FOLLOW-UP"])
    ].copy()

    if df_propostas.empty:
        st.success("Nenhuma proposta pendente de follow-up no momento.")
    else:
        hoje = pd.Timestamp.today().normalize()
        amanha = hoje + pd.Timedelta(days=1)
        limite_3dias = hoje + pd.Timedelta(days=3)

        # ── Função auxiliar: extrair último histórico do campo observacoes ──
        def extrair_ultimo_historico(obs):
            """Extrai a primeira linha do campo observacoes (entrada mais recente)."""
            if pd.isna(obs) or not obs:
                return "—"
            primeira_linha = str(obs).split("\n")[0].strip()
            # Limitar tamanho para exibição
            if len(primeira_linha) > 120:
                return primeira_linha[:117] + "..."
            return primeira_linha

        # ── Classificar cada proposta ──
        df_propostas["dias_restantes"] = (
            df_propostas["proximo_followup"] - hoje
        ).dt.days

        df_propostas["categoria"] = "DEMAIS"
        df_propostas.loc[
            df_propostas["proximo_followup"] < hoje, "categoria"
        ] = "ATRASADO"
        df_propostas.loc[
            df_propostas["proximo_followup"] == hoje, "categoria"
        ] = "HOJE"
        df_propostas.loc[
            df_propostas["proximo_followup"] == amanha, "categoria"
        ] = "AMANHA"
        df_propostas.loc[
            (df_propostas["proximo_followup"] > hoje)
            & (df_propostas["proximo_followup"] <= limite_3dias)
            & (df_propostas["categoria"] == "DEMAIS"),
            "categoria"
        ] = "PROXIMOS_3"

        df_propostas["ultimo_historico"] = df_propostas["observacoes"].apply(
            extrair_ultimo_historico
        )

        # ── Contadores ──
        qtd_atrasados = len(df_propostas[df_propostas["categoria"] == "ATRASADO"])
        qtd_hoje = len(df_propostas[df_propostas["categoria"] == "HOJE"])
        qtd_amanha = len(df_propostas[df_propostas["categoria"] == "AMANHA"])
        qtd_prox3 = len(df_propostas[df_propostas["categoria"] == "PROXIMOS_3"])
        qtd_demais = len(df_propostas[
            ~df_propostas["categoria"].isin(
                ["ATRASADO", "HOJE", "AMANHA", "PROXIMOS_3"]
            )
        ])

        # ═══════════════════════════════════════════════════
        # AUTO-SELEÇÃO DA FILA MAIS URGENTE
        # ═══════════════════════════════════════════════════
        if "filtro_followup" not in st.session_state:
            if qtd_atrasados > 0:
                st.session_state["filtro_followup"] = "ATRASADO"
            elif qtd_hoje > 0:
                st.session_state["filtro_followup"] = "HOJE"
            elif qtd_amanha > 0:
                st.session_state["filtro_followup"] = "AMANHA"
            elif qtd_prox3 > 0:
                st.session_state["filtro_followup"] = "PROXIMOS_3"
            else:
                st.session_state["filtro_followup"] = "DEMAIS"

        # ═══════════════════════════════════════════════════
        # CARDS COMO FILTROS CLICÁVEIS
        # ═══════════════════════════════════════════════════
        c1, c2, c3, c4, c5 = st.columns(5)

        with c1:
            if st.button(
                f"🔴 ATRASADOS\n\n**{qtd_atrasados}**",
                key="btn_atrasados",
                width="stretch",
                type="primary" if st.session_state["filtro_followup"] == "ATRASADO" else "secondary",
            ):
                st.session_state["filtro_followup"] = "ATRASADO"
                st.rerun()

        with c2:
            if st.button(
                f"🟡 HOJE\n\n**{qtd_hoje}**",
                key="btn_hoje",
                width="stretch",
                type="primary" if st.session_state["filtro_followup"] == "HOJE" else "secondary",
            ):
                st.session_state["filtro_followup"] = "HOJE"
                st.rerun()

        with c3:
            if st.button(
                f"🔵 AMANHÃ\n\n**{qtd_amanha}**",
                key="btn_amanha",
                width="stretch",
                type="primary" if st.session_state["filtro_followup"] == "AMANHA" else "secondary",
            ):
                st.session_state["filtro_followup"] = "AMANHA"
                st.rerun()

        with c4:
            if st.button(
                f"🟢 PRÓXIMOS\n3 DIAS\n\n**{qtd_prox3}**",
                key="btn_prox3",
                width="stretch",
                type="primary" if st.session_state["filtro_followup"] == "PROXIMOS_3" else "secondary",
            ):
                st.session_state["filtro_followup"] = "PROXIMOS_3"
                st.rerun()

        with c5:
            if st.button(
                f"⚪ DEMAIS\n\n**{qtd_demais}**",
                key="btn_demais",
                width="stretch",
                type="primary" if st.session_state["filtro_followup"] == "DEMAIS" else "secondary",
            ):
                st.session_state["filtro_followup"] = "DEMAIS"
                st.rerun()

        st.markdown("---")

        # ═══════════════════════════════════════════════════
        # TABELA ÚNICA CONFORME FILTRO SELECIONADO
        # ═══════════════════════════════════════════════════

        filtro = st.session_state["filtro_followup"]

        # Mapeamento de categoria para config visual
        CATEGORIAS_CONFIG = {
            "ATRASADO": {
                "titulo": "🔴 Follow-ups Atrasados",
                "descricao": "Esses clientes deveriam ter sido contatados e exigem atenção imediata.",
                "condicao": lambda d: d["categoria"] == "ATRASADO",
            },
            "HOJE": {
                "titulo": "🟡 Follow-ups de Hoje",
                "descricao": "Contatos programados para serem realizados hoje.",
                "condicao": lambda d: d["categoria"] == "HOJE",
            },
            "AMANHA": {
                "titulo": "🔵 Follow-ups de Amanhã",
                "descricao": "Contatos previstos para amanhã. Prepare-se com antecedência.",
                "condicao": lambda d: d["categoria"] == "AMANHA",
            },
            "PROXIMOS_3": {
                "titulo": "🟢 Próximos 3 Dias",
                "descricao": "Follow-ups programados para os próximos 3 dias.",
                "condicao": lambda d: d["categoria"] == "PROXIMOS_3",
            },
            "DEMAIS": {
                "titulo": "⚪ Demais Follow-ups",
                "descricao": "Propostas com follow-up agendado para datas futuras.",
                "condicao": lambda d: ~d["categoria"].isin(
                    ["ATRASADO", "HOJE", "AMANHA", "PROXIMOS_3"]
                ),
            },
        }

        config = CATEGORIAS_CONFIG[filtro]
        df_filtrado = df_propostas[config["condicao"](df_propostas)].sort_values(
            "proximo_followup"
        )
        qtd_filtrado = len(df_filtrado)

        # Título com resumo descritivo
        st.markdown(f"### {config['titulo']} ({qtd_filtrado})")
        st.caption(config["descricao"])

        if df_filtrado.empty:
            st.info("Nenhum registro nesta fila.")
        else:
            # Montar linhas formatadas (mesmo formato da função original)
            linhas = []
            for _, row in df_filtrado.iterrows():
                dias = row["dias_restantes"]
                if pd.isna(dias):
                    dias_str = "—"
                    badge = "⚪"
                elif dias < 0:
                    dias_str = f"{abs(int(dias))}d atraso"
                    badge = "🔴"
                elif dias == 0:
                    dias_str = "Hoje"
                    badge = "🟡"
                elif dias == 1:
                    dias_str = "Amanhã"
                    badge = "🔵"
                else:
                    dias_str = f"{int(dias)}d restantes"
                    badge = "🟢"

                data_followup = (
                    row["proximo_followup"].strftime("%d/%m/%Y")
                    if pd.notna(row["proximo_followup"])
                    else "—"
                )

                linhas.append({
                    " ": badge,
                    "OS": str(row["numero_os"]),
                    "Cliente": row["cliente"] if pd.notna(row["cliente"]) else "—",
                    "Responsável": row["responsavel"] if pd.notna(row["responsavel"]) else "—",
                    "Próximo Follow-up": data_followup,
                    "Prazo": dias_str,
                    "Último Histórico": row["ultimo_historico"],
                })

            df_exibicao = pd.DataFrame(linhas)
            st.dataframe(
                df_exibicao,
                width="stretch",
                height=min(600, 35 * len(linhas) + 38),
                hide_index=True,
                column_config={
                    " ": st.column_config.Column(width="small"),
                    "OS": st.column_config.Column(width="small"),
                    "Cliente": st.column_config.Column(width="medium"),
                    "Responsável": st.column_config.Column(width="small"),
                    "Próximo Follow-up": st.column_config.Column(width="small"),
                    "Prazo": st.column_config.Column(width="small"),
                    "Último Histórico": st.column_config.Column(width="large"),
                },
            )

        st.markdown("---")

        # ═══════════════════════════════════════════════════
        # REGISTRAR FOLLOW-UP (mantido da versão original)
        # ═══════════════════════════════════════════════════

        with st.container(border=True):
            st.subheader("📝 Registrar Follow-up Realizado")

            with st.form(key="form_followup_pipeline"):

                os_selecionada = st.selectbox(
                    "Nº da OS que você acabou de interagir:",
                    options=df_propostas["numero_os"].tolist(),
                    key="select_os_followup_pipeline"
                )

                historico_contato = st.text_area(
                    "Histórico do Contato (O que foi conversado?)",
                    height=150,
                    key="textarea_historico_pipeline"
                )

                submitted = st.form_submit_button("Registrar Follow-up e Agendar Próximo")

                if submitted:
                    if not historico_contato.strip():
                        st.error("Por favor, preencha o histórico do contato antes de registrar.")
                    else:
                        conn2 = get_connection()
                        hoje_str_dmy = date.today().strftime("%d/%m/%Y")

                        row = conn2.execute(
                            "SELECT followup_count, observacoes FROM ordens_servico WHERE numero_os = ?",
                            (os_selecionada,)
                        ).fetchone()
                        followup_count = row[0] if row and row[0] is not None else 0
                        obs_atual = row[1] if row and row[1] else ""

                        dias_followup_1 = int(get_config("followup_1", "2"))
                        dias_followup_2 = int(get_config("followup_2", "7"))
                        dias_followup_3 = int(get_config("followup_3", "15"))

                        # REGRA DE NEGÓCIO — Ciclo de follow-up:
                        #
                        # followup_1: intervalo entre o envio da proposta e o PRIMEIRO follow-up
                        #             (aplicado automaticamente quando a proposta é enviada)
                        # followup_2: intervalo entre o PRIMEIRO e o SEGUNDO follow-up
                        # followup_3: intervalo entre TODOS os follow-ups seguintes (terceiro em diante)
                        #
                        # O followup_count indica quantos follow-ups JÁ foram registrados.
                        # Portanto, a decisão do PRÓXIMO intervalo é baseada no count ATUAL:
                        #   count == 0 → primeiro follow-up sendo registrado agora → próximo usa followup_2
                        #   count == 1 → segundo follow-up sendo registrado agora  → próximo usa followup_3
                        #   count >= 2 → terceiro follow-up em diante              → próximo usa followup_3
                        #
                        # Após o terceiro follow-up, o CRM continua lembrando o operador
                        # indefinidamente, sempre utilizando o intervalo definido em followup_3.
                        if followup_count == 0:
                            nova_data_followup = date.today() + pd.Timedelta(days=dias_followup_2)
                        elif followup_count == 1:
                            nova_data_followup = date.today() + pd.Timedelta(days=dias_followup_3)
                        else:
                            # followup_count >= 2: mantém followup_3 indefinidamente
                            nova_data_followup = date.today() + pd.Timedelta(days=dias_followup_3)

                        nova_data_followup_str = nova_data_followup.strftime("%Y-%m-%d")
                        novo_historico = f"[{hoje_str_dmy}]: {historico_contato.strip()}\n" + obs_atual

                        conn2.execute(
                            """UPDATE ordens_servico 
                               SET followup_count = followup_count + 1, 
                                   proximo_followup = ?, 
                                   observacoes = ?
                               WHERE numero_os = ?""",
                            (nova_data_followup_str, novo_historico, os_selecionada)
                        )
                        conn2.commit()
                        conn2.close()

                        st.success(
                            f"✅ Follow-up da OS {os_selecionada} registrado com sucesso! "
                            f"Próximo agendado para {nova_data_followup.strftime('%d/%m/%Y')}."
                        )
                        st.rerun()

# =====================================================
# FUNÇÃO AUXILIAR — Ações em Massa
# =====================================================

def _aplicar_regras_status_massa(conn, novo_status, ids=None, unidade=None):
    """
    Aplica as mesmas regras da atualização individual para ações em massa.
    Reutilizada por 'Atualizar Selecionadas' e 'Atualizar Todas da Unidade'.
    """
    if novo_status == "PROPOSTA ENVIADA":
        dias = int(get_config("followup_1", "2"))
        sql = """UPDATE ordens_servico
                 SET status = ?,
                     data_envio_proposta = date('now'),
                     proximo_followup = date('now', ?),
                     data_atualizacao = date('now')"""
        params = [novo_status, f'+{dias} days']
    elif novo_status in ("APROVADA", "FATURADA", "EXPEDIDA", "PERDIDA", "CANCELADA"):
        sql = """UPDATE ordens_servico
                 SET status = ?,
                     proximo_followup = NULL,
                     data_atualizacao = date('now')"""
        params = [novo_status]
    else:
        sql = """UPDATE ordens_servico
                 SET status = ?,
                     data_atualizacao = date('now')"""
        params = [novo_status]

    if ids:
        placeholders = ",".join("?" for _ in ids)
        sql += f" WHERE id IN ({placeholders})"
        params.extend(ids)
    elif unidade and unidade != "GRUPO":
        sql += " WHERE unidade = ?"
        params.append(unidade)

    conn.execute(sql, params)
    conn.commit()

# =====================================================
# ABA 5 — AÇÕES EM MASSA
# =====================================================

with tab5:

    st.subheader("⚡ Ações em Massa - Atualização em Lote")

    # ── Coluna de seleção ──
    df_acoes = df.copy()
    df_acoes["Selecionar"] = False

    # Reordenar: Selecionar na primeira posição
    cols_acoes = ["Selecionar"] + [c for c in df_acoes.columns if c != "Selecionar"]
    df_acoes = df_acoes[cols_acoes]

    # ── Checkbox "Selecionar / Desmarcar Todos" ──
    col_check_all, col_info = st.columns([1, 5])
    with col_check_all:
        selecionar_todos = st.checkbox("✅ Selecionar Todos", key="check_all_pipeline")
    with col_info:
        if selecionar_todos:
            st.caption(f"✔️ Todas as **{len(df_acoes)}** OS serão marcadas para atualização em lote.")
        else:
            st.caption("Marque individualmente ou use o checkbox ao lado para selecionar todas.")

    if selecionar_todos:
        df_acoes["Selecionar"] = True

    # ── Tabela editável ──
    st.subheader("Selecione as OS que deseja atualizar")
    df_editado = st.data_editor(
        df_acoes[["Selecionar", "numero_os", "cliente", "status", "unidade", "responsavel", "valor_proposta"]],
        hide_index=True,
        width="stretch",
        height=500,
        key="data_editor_pipeline"
    )

    # ── Painel de comando do lote ──
    st.markdown("---")

    STATUS_DISPONIVEIS = [
        "RECEBIDA",
        "PROPOSTA ENVIADA",
        "APROVADA",
        "FATURADA",
        "EXPEDIDA",
        "PERDIDA",
        "CANCELADA"
    ]

    col_status_massa, col_btn_parcial, col_btn_total = st.columns([3, 2, 2])

    with col_status_massa:
        novo_status_massa = st.selectbox(
            "Novo status para as OS selecionadas",
            STATUS_DISPONIVEIS,
            key="novo_status_pipeline"
        )

    with col_btn_parcial:
        executar_massa = st.button(
            "▶️ Atualizar Selecionadas",
            type="primary",
            width="stretch",
            key="btn_atualizar_selecionadas_pipeline"
        )

    with col_btn_total:
        atualizar_tudo_massa = st.button(
            "⚡ Atualizar Todas da Unidade",
            width="stretch",
            key="btn_atualizar_tudo_pipeline"
        )

    if executar_massa:
        selecionadas = df_editado[df_editado["Selecionar"] == True]

        if selecionadas.empty:
            st.warning("Nenhuma OS foi selecionada.")
        else:
            ids = df_acoes.loc[selecionadas.index, "id"].tolist()
            _aplicar_regras_status_massa(conn, novo_status_massa, ids=ids)
            st.success(f"{len(ids)} OS(s) alterada(s) para o status '{novo_status_massa}' com sucesso!")
            st.rerun()

    if atualizar_tudo_massa:
        unidade_atual = st.session_state["unidade_ativa"]
        _aplicar_regras_status_massa(conn, novo_status_massa, unidade=unidade_atual)
        st.success(f"✅ Todas as OS da unidade foram alteradas para o status '{novo_status_massa}' com sucesso!")
        st.rerun()
