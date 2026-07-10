import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import numpy as np
from datetime import datetime

from auth import sidebar_usuario
from permissions import verificar_acesso_pagina

# ── Proteção: acesso geral (autenticado) ──
verificar_acesso_pagina()
sidebar_usuario()

# =====================================================
# CONFIG
# =====================================================

st.set_page_config(
    page_title="Dashboard Comercial ULITEC",
    layout="wide"
)

st.title("📊 Dashboard Comercial ULITEC")

# =====================================================
# CORES ABC
# =====================================================

CORES_ABC = {
    "A": "#16a34a",
    "B": "#2563eb",
    "C": "#f59e0b",
    "D": "#dc2626"
}

# =====================================================
# LEITURA BANCO
# =====================================================

conn = sqlite3.connect("crm.db")

clientes = pd.read_sql_query(
    "SELECT * FROM clientes",
    conn
)

faturamento = pd.read_sql_query(
    "SELECT * FROM faturamento",
    conn
)

conn.close()

# ── Guarda contra banco vazio (sem dados para exibir) ──
if len(clientes) == 0:
    st.warning("📭 Nenhum dado encontrado. Importe clientes e faturamento para visualizar o Dashboard.")
    st.info("Acesse **Centro de Importações** no menu lateral para começar.")
    st.stop()

# =====================================================
# FILTROS
# =====================================================

st.sidebar.header("🎯 Filtros")

unidade = st.sidebar.selectbox(
    "Unidade",
    [
        "GRUPO",
        "ULITEC SP",
        "ULITEC RS"
    ]
)

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Classificação Comercial")

perc_a = st.sidebar.slider(
    "Clientes Classe A (%)",
    5,
    30,
    10
)

perc_b = st.sidebar.slider(
    "Clientes Classe B (%)",
    10,
    50,
    30
)

perc_c = st.sidebar.slider(
    "Clientes Classe C (%)",
    20,
    80,
    60
)
# =====================================================
# FILTRO UNIDADE
# =====================================================

if unidade != "GRUPO":

    faturamento = faturamento[
        faturamento["unidade"] == unidade
    ]

# =====================================================
# FATURAMENTO REAL
# =====================================================

fat_cliente = (
    faturamento
    .groupby("cliente_id")["valor"]
    .sum()
    .reset_index()
)

fat_cliente.columns = [
    "id",
    "faturamento_real"
]

clientes = clientes.merge(
    fat_cliente,
    how="left",
    on="id"
)

clientes["faturamento_real"] = (
    clientes["faturamento_real"]
    .fillna(0)
)

# =====================================================
# NUMERICOS
# =====================================================

for coluna in [
    "parque_maquinas",
    "maquinas_mitsubishi",
    "frequencia_visita"
]:

    clientes[coluna] = pd.to_numeric(
        clientes[coluna],
        errors="coerce"
    ).fillna(0)

# =====================================================
# =====================================================
# CLASSIFICACAO COMERCIAL
# =====================================================

clientes = clientes.sort_values(
    "faturamento_real",
    ascending=False
).copy()

clientes["ranking"] = range(
    1,
    len(clientes) + 1
)

clientes_ativos = len(
    clientes[
        clientes["faturamento_real"] > 0
    ]
)

def classificar_rank(r):

    if r <= clientes_ativos * (perc_a / 100):
        return "A"

    elif r <= clientes_ativos * (perc_b / 100):
        return "B"

    elif r <= clientes_ativos * (perc_c / 100):
        return "C"

    return "D"
    
clientes["classe_abc"] = (
    clientes["ranking"]
    .apply(classificar_rank)
)

faturamento_total = clientes[
    "faturamento_real"
].sum()
# =====================================================
# SCORE POTENCIAL
# =====================================================

clientes["score"] = (
    clientes["faturamento_real"] * 0.50
    +
    clientes["parque_maquinas"] * 500
    +
    clientes["maquinas_mitsubishi"] * 1000
    +
    clientes["frequencia_visita"] * 200
)

# =====================================================
# KPIS
# =====================================================

ticket_medio = 0

if clientes_ativos > 0:

    ticket_medio = (
        faturamento_total
        /
        clientes_ativos
    )

classe_a = len(
    clientes[
        clientes["classe_abc"] == "A"
    ]
)

sem_faturamento = len(
    clientes[
        clientes["faturamento_real"] <= 0
    ]
)

# =====================================================
# CARDS
# =====================================================

c1, c2, c3, c4, c5, c6 = st.columns(6)

c1.metric(
    "🏢 Clientes",
    f"{len(clientes):,.0f}"
)

c2.metric(
    "💰 Ativos",
    f"{clientes_ativos:,.0f}"
)

c3.metric(
    "📈 Receita",
    f"R$ {faturamento_total:,.0f}"
)

c4.metric(
    "🎯 Ticket Médio",
    f"R$ {ticket_medio:,.0f}"
)

c5.metric(
    "⭐ Classe A",
    f"{classe_a:,.0f}"
)

c6.metric(
    "⚠️ Sem Fat.",
    f"{sem_faturamento:,.0f}"
)

st.divider()

# =====================================================
# TOP CLIENTES
# =====================================================

top = clientes.head(15)

col1, col2 = st.columns(2)

with col1:

    fig = px.bar(
        top,
        x="faturamento_real",
        y="razao_social",
        orientation="h",
        color="classe_abc",
        color_discrete_map=CORES_ABC,
        title="🏆 Top Clientes"
    )

    fig.update_layout(
        height=600,
        yaxis=dict(
            categoryorder="total ascending"
        )
    )

    st.plotly_chart(
        fig,
        width="stretch"
    )

with col2:

    treemap = px.treemap(
        top,
        path=["classe_abc", "razao_social"],
        values="faturamento_real",
        color="classe_abc",
        color_discrete_map=CORES_ABC,
        title="📊 Receita por Cliente"
    )

    treemap.update_layout(
        height=600
    )

    st.plotly_chart(
        treemap,
        width="stretch"
    )

# =====================================================
# DISTRIBUIÇÃO ABC
# =====================================================

st.divider()

abc = (
    clientes
    .groupby("classe_abc")
    .agg({
        "id":"count",
        "faturamento_real":"sum"
    })
    .reset_index()
)

abc.columns = [
    "Classe",
    "Clientes",
    "Receita"
]

fig2 = px.bar(
    abc,
    x="Classe",
    y="Receita",
    color="Classe",
    color_discrete_map=CORES_ABC,
    title="🏅 Distribuição Receita por Classe"
)

st.plotly_chart(
    fig2,
    width="stretch"
)

# =====================================================
# POTENCIAL
# =====================================================

st.divider()

ranking = (
    clientes
    .sort_values(
        "score",
        ascending=False
    )
    .head(20)
)

fig3 = px.bar(
    ranking,
    x="razao_social",
    y="score",
    color="classe_abc",
    color_discrete_map=CORES_ABC,
    title="🚀 Ranking Potencial Comercial"
)

fig3.update_layout(
    height=500
)

st.plotly_chart(
    fig3,
    width="stretch"
)

# =====================================================
# ESTILO TABELA
# =====================================================

def colorir(row):

    cor = row["classe_abc"]

    if cor == "A":
        return ["background-color:#dcfce7"] * len(row)

    if cor == "B":
        return ["background-color:#dbeafe"] * len(row)

    if cor == "C":
        return ["background-color:#fef3c7"] * len(row)

    return ["background-color:#fee2e2"] * len(row)

# =====================================================
# TABELAS
# =====================================================

st.divider()

col3, col4 = st.columns(2)

with col3:

    st.subheader(
        "🚀 Top Oportunidades Comerciais"
    )

    oportunidades = (
        clientes
        .sort_values(
            "score",
            ascending=False
        )
        .head(20)
    )

    st.dataframe(
        oportunidades[
            [
                "classe_abc",
                "codigo_erp",
                "razao_social",
                "cidade",
                "score"
            ]
        ].style.apply(
            colorir,
            axis=1
        ),
        width="stretch",
        height=400
    )

with col4:

    st.subheader(
        "🏅 Ranking ABC"
    )

    ranking_abc = clientes[
        [
            "classe_abc",
            "codigo_erp",
            "razao_social",
            "faturamento_real"
        ]
    ].head(50)

    st.dataframe(
        ranking_abc.style.apply(
            colorir,
            axis=1
        ),
        width="stretch",
        height=400
    )

# =====================================================
# MAIORES CLIENTES
# =====================================================

st.divider()

st.subheader(
    "💼 Maiores Clientes"
)

st.dataframe(
    top[
        [
            "classe_abc",
            "codigo_erp",
            "razao_social",
            "cidade",
            "segmento",
            "parque_maquinas",
            "faturamento_real"
        ]
    ].style.apply(
        colorir,
        axis=1
    ),
    width="stretch",
    height=600
)

# =====================================================
# ═══════════════════════════════════════════════════
# V1.2.1 — ABAS: 📈 TENDÊNCIA  |  📅 SAZONALIDADE
# ═══════════════════════════════════════════════════
# Totalmente isolada — não altera nada acima.
# =====================================================

st.divider()

aba_tendencia, aba_sazonalidade = st.tabs(["📈 Tendência", "📅 Sazonalidade"])

# ── CONSTANTES ──
NOMES_MESES = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]

UNIDADE_MAP = {
    "ULITEC SP": "SP",
    "ULITEC RS": "RS",
    "GRUPO": "GRUPO"
}
UNIDADE_ABREV = UNIDADE_MAP.get(unidade, unidade)
UNIDADES_LISTA = ["GRUPO", "ULITEC SP", "ULITEC RS"]
UNIDADES_DISPLAY = ["GRUPO", "SP", "RS"]
CORES_UNIDADES = {"GRUPO": "#1e293b", "SP": "#2563eb", "RS": "#16a34a"}

# ── FUNÇÕES AUXILIARES ──

def calcular_regressao(y):
    """Retorna (coef, r2, tendencia, projecao, y_proj) para um array de valores."""
    x = np.arange(len(y)).astype(float)
    coef = np.polyfit(x, y, 1)
    tendencia = np.polyval(coef, x)
    # R²
    y_medio = np.mean(y)
    ss_total = np.sum((y - y_medio) ** 2)
    ss_residual = np.sum((y - tendencia) ** 2)
    r2 = 1 - (ss_residual / ss_total) if ss_total > 0 else 0
    # Projeção 3 meses
    x_proj = np.arange(len(y), len(y) + 3).astype(float)
    y_proj = np.polyval(coef, x_proj)
    return coef, r2, tendencia, y_proj


def formatar_delta(v):
    """Formata valor de variação percentual com cor."""
    if v is None:
        return "—"
    s = f"{v:+.1f}%"
    if v > 0:
        return f'<span style="color:#16a34a;font-weight:600;">{s}</span>'
    elif v < 0:
        return f'<span style="color:#dc2626;font-weight:600;">{s}</span>'
    else:
        return f'<span style="color:#6b7280;">{s}</span>'


def calcular_variacoes(arr):
    """Retorna lista de variações percentuais (None para o primeiro)."""
    var = [None]
    for i in range(1, len(arr)):
        if arr[i - 1] > 0:
            var.append((arr[i] - arr[i - 1]) / arr[i - 1] * 100)
        else:
            var.append(None)
    return var


# ══════════════════════════════════════════════════
# DADOS COMPARTILHADOS (uma única preparação)
# ══════════════════════════════════════════════════

faturamento["data_faturamento"] = pd.to_datetime(
    faturamento["data_faturamento"], errors="coerce"
)
faturamento["ano"] = faturamento["data_faturamento"].dt.year
faturamento["mes"] = faturamento["data_faturamento"].dt.month
faturamento["ano_mes"] = (
    faturamento["ano"].astype(str) + "-" +
    faturamento["mes"].astype(str).str.zfill(2)
)

# ══════════════════════════════════════════════════
# ABA 1: 📈 TENDÊNCIA
# ══════════════════════════════════════════════════

with aba_tendencia:

    # ── Filtro de Período ──
    periodo = st.segmented_control(
        "Período",
        options=["Últimos 3 meses", "Últimos 6 meses", "Últimos 12 meses"],
        default="Últimos 6 meses",
        key="periodo_tendencia_v2"
    )

    # Data de corte
    hoje = datetime.now()
    meses_map = {
        "Últimos 3 meses": 3,
        "Últimos 6 meses": 6,
        "Últimos 12 meses": 12
    }
    n_meses = meses_map[periodo]
    corte = hoje.year * 12 + hoje.month - n_meses
    corte_ano = corte // 12
    corte_mes = corte % 12 + 1
    mask_periodo = (faturamento["ano"] > corte_ano) | (
        (faturamento["ano"] == corte_ano) & (faturamento["mes"] >= corte_mes)
    )

    # ── Checkbox Comparar Unidades ──
    comparar_unidades = st.checkbox(
        "☐ Comparar unidades",
        value=False,
        key="comparar_unidades"
    )

    # ── Dados da unidade principal (filtro lateral) ──
    if unidade != "GRUPO":
        dados_principal = faturamento[mask_periodo & (faturamento["unidade"] == unidade)].copy()
    else:
        dados_principal = faturamento[mask_periodo].copy()

    mensal_principal = (
        dados_principal
        .groupby(["ano", "mes", "ano_mes"], as_index=False)["valor"]
        .sum()
        .sort_values(["ano", "mes"])
        .reset_index(drop=True)
    )
    mensal_principal.rename(columns={"valor": "receita"}, inplace=True)

    if len(mensal_principal) == 0:
        st.info("📭 Nenhum dado de faturamento disponível para o período selecionado.")
        st.stop()

    # Regressão + projeção da principal
    y_principal = mensal_principal["receita"].values.astype(float)
    coef_principal, r2, tendencia_principal, y_proj_principal = calcular_regressao(y_principal)
    mensal_principal["tendencia"] = tendencia_principal

    # Variações
    variacao_principal = calcular_variacoes(y_principal)

    # Dataframe projeção principal
    ultimo_mes = mensal_principal.iloc[-1]
    proj_principal = []
    for i in range(3):
        m = ultimo_mes["mes"] + i + 1
        a = ultimo_mes["ano"]
        if m > 12:
            m -= 12
            a += 1
        proj_principal.append({
            "ano": a, "mes": m,
            "ano_mes": f"{a}-{m:02d}",
            "projecao": y_proj_principal[i]
        })
    proj_principal_df = pd.DataFrame(proj_principal)

    # ── GRÁFICO ──
    import plotly.graph_objects as go

    fig_tend = go.Figure()

    if comparar_unidades:
        # Mostra todas as unidades
        for uni, display in zip(UNIDADES_LISTA, UNIDADES_DISPLAY):
            if uni == "GRUPO":
                dados_uni = faturamento[mask_periodo].copy()
            else:
                dados_uni = faturamento[mask_periodo & (faturamento["unidade"] == uni)].copy()

            mensal_uni = (
                dados_uni
                .groupby(["ano", "mes", "ano_mes"], as_index=False)["valor"]
                .sum()
                .sort_values(["ano", "mes"])
                .reset_index(drop=True)
            )
            if len(mensal_uni) == 0:
                continue

            fig_tend.add_trace(go.Scatter(
                x=mensal_uni["ano_mes"],
                y=mensal_uni["valor"],
                mode="lines+markers",
                name=display,
                line=dict(color=CORES_UNIDADES[display], width=2),
                marker=dict(size=6),
                hovertemplate=(
                    f"<b>{display}</b><br>"
                    "%{x}<br>"
                    "R$ %{y:,.2f}<br>"
                    "<extra></extra>"
                )
            ))

        # Projeção apenas da unidade principal
        fig_tend.add_trace(go.Scatter(
            x=proj_principal_df["ano_mes"],
            y=proj_principal_df["projecao"],
            mode="lines+markers",
            name=f"Projeção ({UNIDADE_ABREV})",
            line=dict(color="#f59e0b", width=2, dash="dash"),
            marker=dict(size=8, color="#f59e0b", symbol="diamond"),
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Projetado: R$ %{y:,.2f}<br>"
                "<extra></extra>"
            )
        ))

    else:
        # Apenas a unidade selecionada (comportamento original)
        # Receita Real
        fig_tend.add_trace(go.Scatter(
            x=mensal_principal["ano_mes"],
            y=mensal_principal["receita"],
            mode="lines+markers",
            name=f"Receita Real ({UNIDADE_ABREV})",
            line=dict(color="#16a34a", width=3),
            marker=dict(size=8, color="#16a34a"),
            customdata=[[v] if v is not None else [None] for v in variacao_principal],
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Receita: R$ %{y:,.2f}<br>"
                "Variação: %{customdata[0]:+.1f}%<br>"
                "<extra></extra>"
            )
        ))
        # Tendência
        fig_tend.add_trace(go.Scatter(
            x=mensal_principal["ano_mes"],
            y=mensal_principal["tendencia"],
            mode="lines",
            name="Tendência",
            line=dict(color="#2563eb", width=2, dash="dot"),
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Tendência: R$ %{y:,.2f}<br>"
                "<extra></extra>"
            )
        ))
        # Projeção
        fig_tend.add_trace(go.Scatter(
            x=proj_principal_df["ano_mes"],
            y=proj_principal_df["projecao"],
            mode="lines+markers",
            name="Projeção",
            line=dict(color="#f59e0b", width=2, dash="dash"),
            marker=dict(size=8, color="#f59e0b", symbol="diamond"),
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Projetado: R$ %{y:,.2f}<br>"
                "<extra></extra>"
            )
        ))

    fig_tend.update_layout(
        title=f"📈 Evolução do Faturamento — {UNIDADE_ABREV}",
        xaxis_title="Mês",
        yaxis_title="Receita (R$)",
        height=500,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig_tend, width="stretch")

    # ── TABELA DE VARIAÇÃO MENSAL ──
    st.markdown("### 📋 Variação Mensal")

    tabela_var = pd.DataFrame({
        "Mês": mensal_principal["ano_mes"],
        "Receita": mensal_principal["receita"].apply(lambda x: f"R$ {x:,.0f}"),
        "Δ Mês anterior": variacao_principal
    })

    # Aplicar cores usando HTML renderizado
    linhas_html = ""
    for _, row in tabela_var.iterrows():
        delta_str = formatar_delta(row["Δ Mês anterior"])
        linhas_html += (
            f"<tr style='border-bottom:1px solid #e2e8f0;'>"
            f"<td style='padding:6px 12px;'>{row['Mês']}</td>"
            f"<td style='padding:6px 12px;text-align:right;'>{row['Receita']}</td>"
            f"<td style='padding:6px 12px;text-align:right;'>{delta_str}</td>"
            f"</tr>"
        )

    st.markdown(
        f"""
        <div style="overflow-x:auto;background:#f8fafc;border-radius:8px;padding:4px;">
            <table style="width:100%;font-size:14px;border-collapse:collapse;">
                <thead>
                    <tr style="border-bottom:2px solid #cbd5e1;">
                        <th style="padding:8px 12px;text-align:left;color:#475569;">Mês</th>
                        <th style="padding:8px 12px;text-align:right;color:#475569;">Receita</th>
                        <th style="padding:8px 12px;text-align:right;color:#475569;">Δ Mês anterior</th>
                    </tr>
                </thead>
                <tbody>
                    {linhas_html}
                </tbody>
            </table>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ── KPI DA TENDÊNCIA ──
    st.markdown("---")

    # CMM
    variacoes_validas_principal = [v for v in variacao_principal if v is not None]
    cmm = sum(variacoes_validas_principal) / len(variacoes_validas_principal) if variacoes_validas_principal else 0.0

    # Sinal tendência
    if coef_principal[0] > 0:
        sinal_tendencia = "📈 Crescimento"
        cor_tendencia = "#16a34a"
    elif coef_principal[0] < 0:
        sinal_tendencia = "📉 Queda"
        cor_tendencia = "#dc2626"
    else:
        sinal_tendencia = "➡ Estável"
        cor_tendencia = "#6b7280"

    # Média mensal
    media_mensal = mensal_principal["receita"].mean()

    # Projeção próximo mês
    proj_prox_mes = y_proj_principal[0]
    if mensal_principal["receita"].iloc[-1] > 0:
        var_proj = (proj_prox_mes - mensal_principal["receita"].iloc[-1]) / mensal_principal["receita"].iloc[-1] * 100
    else:
        var_proj = 0.0

    # Confiabilidade (R²)
    if r2 >= 0.85:
        conf_status = "🟢 Alta"
        conf_cor = "#16a34a"
    elif r2 >= 0.60:
        conf_status = "🟡 Média"
        conf_cor = "#f59e0b"
    else:
        conf_status = "🔴 Baixa"
        conf_cor = "#dc2626"

    k1, k2, k3, k4, k5 = st.columns(5)

    with k1:
        cor_cmm = "#16a34a" if cmm >= 0 else "#dc2626"
        st.markdown(
            f"""
            <div style="background:#f8fafc;border-radius:12px;padding:14px;text-align:center;border-left:4px solid {cor_cmm};">
                <p style="margin:0;font-size:13px;color:#64748b;">📊 Cresc. Médio Mensal</p>
                <p style="margin:4px 0 0;font-size:24px;font-weight:700;color:{cor_cmm};">{cmm:+.1f}%</p>
            </div>
            """, unsafe_allow_html=True
        )

    with k2:
        st.markdown(
            f"""
            <div style="background:#f8fafc;border-radius:12px;padding:14px;text-align:center;border-left:4px solid {cor_tendencia};">
                <p style="margin:0;font-size:13px;color:#64748b;">🎯 Tendência</p>
                <p style="margin:4px 0 0;font-size:24px;font-weight:700;color:{cor_tendencia};">{sinal_tendencia}</p>
            </div>
            """, unsafe_allow_html=True
        )

    with k3:
        st.markdown(
            f"""
            <div style="background:#f8fafc;border-radius:12px;padding:14px;text-align:center;border-left:4px solid #2563eb;">
                <p style="margin:0;font-size:13px;color:#64748b;">📅 Média Mensal</p>
                <p style="margin:4px 0 0;font-size:24px;font-weight:700;color:#1e293b;">R$ {media_mensal:,.0f}</p>
            </div>
            """, unsafe_allow_html=True
        )

    with k4:
        cor_proj = "#16a34a" if var_proj >= 0 else "#dc2626"
        st.markdown(
            f"""
            <div style="background:#f8fafc;border-radius:12px;padding:14px;text-align:center;border-left:4px solid {cor_proj};">
                <p style="margin:0;font-size:13px;color:#64748b;">🔮 Proj. Próx. Mês</p>
                <p style="margin:2px 0 0;font-size:24px;font-weight:700;color:#1e293b;">R$ {proj_prox_mes:,.0f}</p>
                <p style="margin:0;font-size:12px;color:{cor_proj};">{var_proj:+.1f}% vs último mês</p>
            </div>
            """, unsafe_allow_html=True
        )

    with k5:
        st.markdown(
            f"""
            <div style="background:#f8fafc;border-radius:12px;padding:14px;text-align:center;border-left:4px solid {conf_cor};">
                <p style="margin:0;font-size:13px;color:#64748b;">🎯 Confiabilidade</p>
                <p style="margin:2px 0 0;font-size:24px;font-weight:700;color:{conf_cor};">{conf_status}</p>
                <p style="margin:0;font-size:12px;color:#64748b;">R² = {r2:.2f}</p>
            </div>
            """, unsafe_allow_html=True
        )

    # ── INSIGHTS MELHORADOS ──
    st.markdown("---")
    st.markdown("### 🤖 Insights Automáticos")

    # Cálculos avançados para insights
    # 1. CMM já calculado
    # 2. Aceleração: compara CMM dos últimos 3 meses vs CMM total
    ultimos_3_var = variacoes_validas_principal[-3:] if len(variacoes_validas_principal) >= 3 else variacoes_validas_principal
    cmm_ultimos_3 = sum(ultimos_3_var) / len(ultimos_3_var) if ultimos_3_var else 0.0

    # 3. Crescimento últimos 3 meses vs início do período
    ultimos_3_meses = mensal_principal.tail(3)
    if len(ultimos_3_meses) >= 2:
        cresc_3m = (ultimos_3_meses["receita"].iloc[-1] - ultimos_3_meses["receita"].iloc[0]) / ultimos_3_meses["receita"].iloc[0] * 100
    else:
        cresc_3m = 0.0

    # 4. Sazonalidade (dados agregados por mês ignorando ano)
    if unidade != "GRUPO":
        dados_saz = faturamento[faturamento["unidade"] == unidade].copy()
    else:
        dados_saz = faturamento.copy()

    sazonal_insight = (
        dados_saz
        .groupby("mes", as_index=False)["valor"]
        .sum()
    )
    sazonal_insight["mes_nome"] = sazonal_insight["mes"].apply(lambda m: NOMES_MESES[m - 1])
    melhor_mes_insight = sazonal_insight.loc[sazonal_insight["valor"].idxmax()]
    pior_mes_insight = sazonal_insight.loc[sazonal_insight["valor"].idxmin()]
    media_historica = sazonal_insight["valor"].mean()

    # 5. Comparação mês atual com média histórica
    mes_atual_receita = mensal_principal["receita"].iloc[-1] if len(mensal_principal) > 0 else 0
    if media_historica > 0:
        comp_media = (mes_atual_receita - media_historica) / media_historica * 100
    else:
        comp_media = 0.0

    # 6. Projeção do próximo mês em valor absoluto
    proj_prox_mes_valor = y_proj_principal[0]

    # 7. Crescimento projetado
    cresc_proj = (y_proj_principal[-1] - y_principal[-1]) / y_principal[-1] * 100 if y_principal[-1] > 0 else 0.0

    insights = []

    # Insight 1: Tendência com CMM
    if abs(cmm) > 0.5:
        insights.append(
            f"📈 **Crescimento médio de {abs(cmm):.1f}%** ao mês no período analisado."
            if cmm > 0 else
            f"📉 **Queda média de {abs(cmm):.1f}%** ao mês no período analisado."
        )
    else:
        insights.append("➡ O faturamento apresenta-se **estável** no período, sem variação significativa.")

    # Insight 2: Aceleração/redução recente
    if len(variacoes_validas_principal) >= 3:
        if abs(cmm_ultimos_3) > 0.5 and abs(cmm) > 0.5:
            if cmm_ultimos_3 > cmm:
                insights.append(f"📊 Os últimos 3 meses **aceleraram** em relação ao período total ({cmm_ultimos_3:+.1f}% vs {cmm:+.1f}%).")
            elif cmm_ultimos_3 < cmm:
                insights.append(f"📊 Os últimos 3 meses **desaceleraram** em relação ao período total ({cmm_ultimos_3:+.1f}% vs {cmm:+.1f}%).")
        elif abs(cresc_3m) > 1:
            if cresc_3m > 0:
                insights.append(f"📊 Os últimos 3 meses cresceram **{cresc_3m:.1f}%** em relação ao início do período.")
            else:
                insights.append(f"📊 Os últimos 3 meses caíram **{abs(cresc_3m):.1f}%** em relação ao início do período.")

    # Insight 3: Comparação com média histórica
    if abs(comp_media) > 3:
        if comp_media > 0:
            insights.append(f"🏆 O mês atual está **{comp_media:.1f}% acima** da média histórica da unidade.")
        else:
            insights.append(f"⚠️ O mês atual está **{abs(comp_media):.1f}% abaixo** da média histórica da unidade.")

    # Insight 4: Unidade acima ou abaixo da tendência
    ultimo_real = y_principal[-1]
    ultima_tendencia = tendencia_principal[-1]
    if ultima_tendencia > 0:
        desvio_tendencia = (ultimo_real - ultima_tendencia) / ultima_tendencia * 100
        if abs(desvio_tendencia) > 2:
            if desvio_tendencia > 0:
                insights.append(f"📊 O último mês está **{desvio_tendencia:.1f}% acima** da tendência esperada, sugerindo desempenho superior ao padrão.")
            else:
                insights.append(f"📊 O último mês está **{abs(desvio_tendencia):.1f}% abaixo** da tendência esperada, indicando desempenho inferior ao padrão.")
        else:
            insights.append(f"📊 O último mês está **alinhado** com a tendência esperada (desvio de apenas {abs(desvio_tendencia):.1f}%).")

    # Insight 5: Melhor mês histórico (agregado por mês, ignorando ano)
    insights.append(
        f"🏆 **{melhor_mes_insight['mes_nome']}** é historicamente o melhor mês"
        f" (R$ {melhor_mes_insight['valor']:,.0f})."
    )

    # Insight 6: Pior mês histórico (agregado por mês, ignorando ano)
    insights.append(
        f"⚠️ **{pior_mes_insight['mes_nome']}** possui desempenho abaixo da média histórica"
        f" (R$ {pior_mes_insight['valor']:,.0f} vs R$ {media_historica:,.0f})."
    )

    # Insight 7: Projeção do próximo mês
    insights.append(
        f"🔮 A projeção indica faturamento de aproximadamente **R$ {proj_prox_mes_valor:,.0f}** para o próximo mês"
        f" ({cresc_proj:+.1f}% em relação ao último mês real)."
    )

    # Insight 8: Confiabilidade da regressão
    if r2 >= 0.85:
        insights.append(f"✅ A regressão linear apresenta **alta confiabilidade** (R² = {r2:.2f}), indicando que a tendência é consistente.")
    elif r2 >= 0.60:
        insights.append(f"📊 A regressão linear apresenta **confiabilidade média** (R² = {r2:.2f}). A tendência deve ser interpretada com cautela.")
    else:
        insights.append(f"⚠️ A regressão linear apresenta **baixa aderência** (R² = {r2:.2f}). Os dados reais têm muita variabilidade.")

    # Exibir insights
    for frase in insights:
        st.markdown(
            f"""
            <div style="background:#f1f5f9;border-radius:8px;padding:10px 16px;margin-bottom:6px;border-left:4px solid #2563eb;">
                <p style="margin:0;font-size:15px;color:#1e293b;">{frase}</p>
            </div>
            """,
            unsafe_allow_html=True
        )


# ══════════════════════════════════════════════════
# ABA 2: 📅 SAZONALIDADE
# ══════════════════════════════════════════════════

with aba_sazonalidade:

    # Reaproveitar dados de sazonalidade da unidade já filtrada
    if unidade != "GRUPO":
        dados_saz_aba = faturamento[faturamento["unidade"] == unidade].copy()
    else:
        dados_saz_aba = faturamento.copy()

    # Agrega por mês (todos os anos)
    sazonal = (
        dados_saz_aba
        .groupby("mes", as_index=False)["valor"]
        .sum()
    )
    sazonal.columns = ["mes", "receita"]
    sazonal["mes_nome"] = sazonal["mes"].apply(lambda m: NOMES_MESES[m - 1])

    # Agrega por mês+ano para encontrar melhor/pior mês específico
    sazonal_detalhado = (
        dados_saz_aba
        .groupby(["ano", "mes"], as_index=False)["valor"]
        .sum()
    )
    sazonal_detalhado["ano_mes_str"] = (
        sazonal_detalhado["ano"].astype(str) + "-" +
        sazonal_detalhado["mes"].astype(str).str.zfill(2)
    )
    sazonal_detalhado["mes_nome"] = sazonal_detalhado["mes"].apply(lambda m: NOMES_MESES[m - 1])

    total_sazonal = sazonal["receita"].sum()
    sazonal["%"] = (sazonal["receita"] / total_sazonal * 100).round(1)

    # ── CARDS: Melhor mês e Pior mês específicos ──
    melhor_especifico = sazonal_detalhado.loc[sazonal_detalhado["valor"].idxmax()]
    pior_especifico = sazonal_detalhado.loc[sazonal_detalhado["valor"].idxmin()]

    c_saz1, c_saz2 = st.columns(2)

    with c_saz1:
        st.markdown(
            f"""
            <div style="background:#f0fdf4;border-radius:12px;padding:18px;text-align:center;border-left:4px solid #16a34a;">
                <p style="margin:0;font-size:16px;color:#166534;">🏆 Melhor mês</p>
                <p style="margin:6px 0;font-size:20px;font-weight:700;color:#16a34a;">{melhor_especifico['mes_nome']}/{melhor_especifico['ano']}</p>
                <p style="margin:0;font-size:18px;font-weight:600;color:#1e293b;">R$ {melhor_especifico['valor']:,.0f}</p>
            </div>
            """, unsafe_allow_html=True
        )

    with c_saz2:
        st.markdown(
            f"""
            <div style="background:#fef2f2;border-radius:12px;padding:18px;text-align:center;border-left:4px solid #dc2626;">
                <p style="margin:0;font-size:16px;color:#991b1b;">⚠️ Pior mês</p>
                <p style="margin:6px 0;font-size:20px;font-weight:700;color:#dc2626;">{pior_especifico['mes_nome']}/{pior_especifico['ano']}</p>
                <p style="margin:0;font-size:18px;font-weight:600;color:#1e293b;">R$ {pior_especifico['valor']:,.0f}</p>
            </div>
            """, unsafe_allow_html=True
        )

    # ── MÉDIA HISTÓRICA + COMPARAÇÃO ──
    st.markdown("---")

    # Receita média histórica (considerando todos os meses do período disponível)
    receita_media_historica = sazonal["receita"].mean()

    # Mês atual (último mês com dado)
    mes_atual_label = f"{NOMES_MESES[mensal_principal['mes'].iloc[-1] - 1]}/{mensal_principal['ano'].iloc[-1]}"
    mes_atual_valor = mensal_principal["receita"].iloc[-1]

    if receita_media_historica > 0:
        perc_vs_media = (mes_atual_valor - receita_media_historica) / receita_media_historica * 100
    else:
        perc_vs_media = 0.0

    cor_comp = "#16a34a" if perc_vs_media >= 0 else "#dc2626"
    sinal_comp = "acima" if perc_vs_media >= 0 else "abaixo"

    c_media1, c_media2 = st.columns(2)

    with c_media1:
        st.markdown(
            f"""
            <div style="background:#f8fafc;border-radius:12px;padding:18px;text-align:center;border-left:4px solid #2563eb;">
                <p style="margin:0;font-size:15px;color:#64748b;">📊 Receita Média Histórica</p>
                <p style="margin:6px 0 0;font-size:24px;font-weight:700;color:#1e293b;">R$ {receita_media_historica:,.0f}</p>
            </div>
            """, unsafe_allow_html=True
        )

    with c_media2:
        st.markdown(
            f"""
            <div style="background:#f8fafc;border-radius:12px;padding:18px;text-align:center;border-left:4px solid {cor_comp};">
                <p style="margin:0;font-size:15px;color:#64748b;">📈 {mes_atual_label}</p>
                <p style="margin:2px 0 0;font-size:20px;font-weight:700;color:#1e293b;">R$ {mes_atual_valor:,.0f}</p>
                <p style="margin:2px 0 0;font-size:16px;font-weight:600;color:{cor_comp};">{abs(perc_vs_media):.1f}% {sinal_comp} da média</p>
            </div>
            """, unsafe_allow_html=True
        )

    # ── TABELAS LADO A LADO ──
    st.markdown("---")

    # Top 5 melhores
    melhores = sazonal.sort_values("receita", ascending=False).head(5)
    melhores_tabela = melhores[["mes_nome", "receita", "%"]].copy()
    melhores_tabela.columns = ["Mês", "Receita", "%"]
    melhores_tabela["Receita"] = melhores_tabela["Receita"].apply(lambda x: f"R$ {x:,.0f}")
    melhores_tabela["%"] = melhores_tabela["%"].apply(lambda x: f"{x:.1f}%")

    # Top 5 piores
    piores = sazonal.sort_values("receita", ascending=True).head(5)
    piores_tabela = piores[["mes_nome", "receita", "%"]].copy()
    piores_tabela.columns = ["Mês", "Receita", "%"]
    piores_tabela["Receita"] = piores_tabela["Receita"].apply(lambda x: f"R$ {x:,.0f}")
    piores_tabela["%"] = piores_tabela["%"].apply(lambda x: f"{x:.1f}%")

    col_saz1, col_saz2 = st.columns(2)

    with col_saz1:
        st.markdown("**✅ Melhores Meses (Top 5)**")
        st.dataframe(melhores_tabela, hide_index=True, width="stretch")

    with col_saz2:
        st.markdown("**❌ Piores Meses (Top 5)**")
        st.dataframe(piores_tabela, hide_index=True, width="stretch")