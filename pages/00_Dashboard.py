import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

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

clientes_ativos = len(
    clientes[
        clientes["faturamento_real"] > 0
    ]
)

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