from datetime import datetime, date, timedelta

import streamlit as st
import pandas as pd
import sqlite3

from auth import sidebar_usuario
from permissions import verificar_acesso_pagina, pode_selecionar_unidade
from services import formatar_clientes_para_select
from services.inteligencia_comercial import (
    get_clientes_esfriando,
    get_clientes_esquentando,
    get_clientes_sem_visita,
    get_clientes_sem_faturamento,
    get_clientes_muitas_os,
    get_clientes_parque_relevante,
    calcular_score_comercial,
    classificar_abcd,
    get_resumo_executivo,
    PENALIDADE_RELACIONAMENTO_ATIVO,
)
from services.relacionamento import (
    get_alertas_relacionamento,
    get_pendencias,
    carregar_configs_relacionamento,
    get_proximas_acoes_consolidadas,
    get_contagem_proximas_acoes,
)

# ── Proteção: autenticado (todos os perfis) ──
verificar_acesso_pagina()
sidebar_usuario()

st.set_page_config(
    page_title="Central de Oportunidades",
    layout="wide"
)

st.title("Central de Oportunidades")

# ── Inicialização da segregação por filial ──
if "unidade_ativa" not in st.session_state:
    st.session_state["unidade_ativa"] = "GRUPO"
if "unidade_usuario" not in st.session_state:
    st.session_state["unidade_usuario"] = "ULITEC SP"

if pode_selecionar_unidade():
    escolha = st.sidebar.selectbox(
        "Filtrar Unidade",
        options=["Grupo (Consolidado)", "ULITEC SP", "ULITEC RS"],
        index=0 if st.session_state["unidade_ativa"] == "GRUPO"
               else (1 if st.session_state["unidade_ativa"] == "ULITEC SP" else 2)
    )
    st.session_state["unidade_ativa"] = "GRUPO" if escolha == "Grupo (Consolidado)" else escolha
else:
    st.session_state["unidade_ativa"] = st.session_state["unidade_usuario"]

# ── Determinar filtro de unidade ──
unidade_param = None if st.session_state["unidade_ativa"] == "GRUPO" else st.session_state["unidade_ativa"]

conn = sqlite3.connect("crm.db")

# =====================================================
# FILTROS GLOBAIS
# =====================================================

st.sidebar.markdown("## Filtros")

df_estados = pd.read_sql_query(
    "SELECT DISTINCT estado FROM clientes WHERE status = 'ATIVO' ORDER BY estado", conn
)
estados_lista = ["Todos"] + df_estados["estado"].tolist()
filtro_estado = st.sidebar.selectbox("Estado", options=estados_lista)

if filtro_estado != "Todos":
    df_cidades = pd.read_sql_query(
        "SELECT DISTINCT cidade FROM clientes WHERE estado = ? AND status = 'ATIVO' ORDER BY cidade",
        conn, params=[filtro_estado]
    )
else:
    df_cidades = pd.read_sql_query(
        "SELECT DISTINCT cidade FROM clientes WHERE status = 'ATIVO' ORDER BY cidade", conn
    )
cidades_lista = ["Todos"] + df_cidades["cidade"].tolist()
filtro_cidade = st.sidebar.selectbox("Cidade", options=cidades_lista)

df_clientes_filtro = pd.read_sql_query(
    "SELECT id, razao_social, cidade, estado FROM clientes WHERE status = 'ATIVO' ORDER BY razao_social", conn
)
clientes_formatados, _, _ = formatar_clientes_para_select(df_clientes_filtro)
clientes_lista = ["Todos"] + clientes_formatados
filtro_cliente = st.sidebar.selectbox("Cliente", options=clientes_lista)

conn.close()


def aplicar_filtros(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica filtros globais de estado/cidade/cliente a um DataFrame."""
    if df.empty:
        return df
    if "cliente" in df.columns and filtro_cliente != "Todos":
        df = df[df["cliente"] == filtro_cliente]
    if "estado" in df.columns and filtro_estado != "Todos":
        df = df[df["estado"] == filtro_estado]
    if "cidade" in df.columns and filtro_cidade != "Todos":
        df = df[df["cidade"] == filtro_cidade]
    return df


# =====================================================
# CARREGAR DADOS
# =====================================================

conn = sqlite3.connect("crm.db")

dias_alerta = conn.execute(
    "SELECT valor FROM configuracoes WHERE chave = 'dias_alerta_preventiva'"
).fetchone()
dias_alerta = int(dias_alerta[0]) if dias_alerta else 730

dias_followup = conn.execute(
    "SELECT valor FROM configuracoes WHERE chave = 'dias_followup_proposta'"
).fetchone()
dias_followup = int(dias_followup[0]) if dias_followup else 7

# ── Preventivas Vencidas ──
query_preventivas_base = """
WITH ultima_os AS (
    SELECT
        os.cliente_id,
        MAX(
            CASE
                WHEN os.status IN ('FATURADA', 'EXPEDIDA')
                THEN COALESCE(os.data_faturamento, os.data_expedicao)
                ELSE NULL
            END
        ) AS data_ultima_os
    FROM ordens_servico os
    WHERE os.status IN ('FATURADA', 'EXPEDIDA')
      AND COALESCE(os.data_faturamento, os.data_expedicao) IS NOT NULL
"""

if st.session_state["unidade_ativa"] == "GRUPO":
    query_preventivas = query_preventivas_base + """
    GROUP BY os.cliente_id
)
SELECT
    c.id AS cliente_id,
    c.razao_social,
    c.cidade,
    c.estado,
    uo.data_ultima_os,
    CAST(julianday('now') - julianday(uo.data_ultima_os) AS INTEGER) AS dias_sem_manutencao
FROM clientes c
INNER JOIN ultima_os uo ON c.id = uo.cliente_id
WHERE uo.data_ultima_os IS NOT NULL
  AND CAST(julianday('now') - julianday(uo.data_ultima_os) AS INTEGER) > ?
ORDER BY dias_sem_manutencao DESC
"""
    params_preventivas = (dias_alerta,)
else:
    query_preventivas = query_preventivas_base + f"""
      AND os.unidade = ?
    GROUP BY os.cliente_id
)
SELECT
    c.id AS cliente_id,
    c.razao_social,
    c.cidade,
    c.estado,
    uo.data_ultima_os,
    CAST(julianday('now') - julianday(uo.data_ultima_os) AS INTEGER) AS dias_sem_manutencao
FROM clientes c
INNER JOIN ultima_os uo ON c.id = uo.cliente_id
WHERE uo.data_ultima_os IS NOT NULL
  AND CAST(julianday('now') - julianday(uo.data_ultima_os) AS INTEGER) > ?
ORDER BY dias_sem_manutencao DESC
"""
    params_preventivas = (st.session_state["unidade_ativa"], dias_alerta)

df_preventivas = pd.read_sql_query(query_preventivas, conn, params=params_preventivas)

# ── Novos Clientes – Prospecção Mitsubishi ──
if st.session_state["unidade_ativa"] == "GRUPO":
    query_novos_clientes = """
    SELECT
        c.razao_social,
        c.cidade,
        c.estado,
        COUNT(m.id) AS qtd_mitsubishi
    FROM clientes c
    INNER JOIN maquinas_mitsubishi m ON m.cliente_id = c.id
    WHERE NOT EXISTS (
        SELECT 1
        FROM ordens_servico os
        WHERE os.cliente_id = c.id
    )
    GROUP BY c.id
    ORDER BY qtd_mitsubishi DESC
    """
    params_novos = ()
else:
    query_novos_clientes = """
    SELECT
        c.razao_social,
        c.cidade,
        c.estado,
        COUNT(m.id) AS qtd_mitsubishi
    FROM clientes c
    INNER JOIN maquinas_mitsubishi m ON m.cliente_id = c.id
    WHERE NOT EXISTS (
        SELECT 1
        FROM ordens_servico os
        WHERE os.cliente_id = c.id
          AND os.unidade = ?
    )
    GROUP BY c.id
    ORDER BY qtd_mitsubishi DESC
    """
    params_novos = (st.session_state["unidade_ativa"],)

df_novos_clientes = pd.read_sql_query(query_novos_clientes, conn, params=params_novos)


def classificar_potencial(qtd):
    if qtd >= 15:
        return "ALTO"
    elif qtd >= 5:
        return "MÉDIO"
    else:
        return "BAIXO"


df_novos_clientes["potencial"] = df_novos_clientes["qtd_mitsubishi"].apply(classificar_potencial)

# ── Dados de Inteligência Comercial ──
df_esfriando = get_clientes_esfriando(unidade=unidade_param)
df_esquentando = get_clientes_esquentando(unidade=unidade_param)
df_sem_visita = get_clientes_sem_visita(unidade=unidade_param)
df_sem_faturamento = get_clientes_sem_faturamento(unidade=unidade_param)
df_muitas_os = get_clientes_muitas_os(unidade=unidade_param)
df_parque = get_clientes_parque_relevante(unidade=unidade_param)
df_score = calcular_score_comercial(unidade=unidade_param)
resumo = get_resumo_executivo(unidade=unidade_param)

# ── Classificação ABCD ──
df_clientes_abc = classificar_abcd(unidade=unidade_param)

df_ult_interacao = pd.read_sql_query(
    """
    SELECT cliente_id, MAX(data_interacao) AS ultima_interacao
    FROM interacoes
    GROUP BY cliente_id
    """,
    conn,
)
df_clientes_abc = df_clientes_abc.merge(df_ult_interacao, left_on="id", right_on="cliente_id", how="left")
df_clientes_abc["ultima_interacao"] = df_clientes_abc["ultima_interacao"].fillna("Nunca")

# ── OS Aguardando Aprovação ──
query_os_aprovacao = """
SELECT
    c.razao_social AS cliente,
    os.valor_proposta AS valor,
    CAST(julianday('now') - julianday(os.data_recebimento) AS INTEGER) AS dias_aguardando,
    os.responsavel,
    os.status
FROM ordens_servico os
INNER JOIN clientes c ON os.cliente_id = c.id
WHERE os.status IN ('AGUARDANDO', 'ORCAMENTO', 'APROVACAO')
"""
params_os_aprov = []
if unidade_param:
    query_os_aprovacao += " AND os.unidade = ?"
    params_os_aprov.append(unidade_param)
query_os_aprovacao += " ORDER BY dias_aguardando DESC"
df_os_aprovacao = pd.read_sql_query(query_os_aprovacao, conn, params=params_os_aprov)

# ── Top Faturamento 12m ──
query_top_fat = """
SELECT
    c.razao_social AS cliente,
    COALESCE(SUM(CAST(f.valor AS REAL)), 0) AS faturamento_12m
FROM clientes c
LEFT JOIN faturamento f ON f.cliente_id = c.id
    AND f.data_faturamento >= date('now', '-12 months')
WHERE c.status = 'ATIVO'
"""
params_top_fat = []
if unidade_param:
    query_top_fat += " AND f.unidade = ?"
    params_top_fat.append(unidade_param)
query_top_fat += " GROUP BY c.id ORDER BY faturamento_12m DESC LIMIT 20"
df_top_fat = pd.read_sql_query(query_top_fat, conn, params=params_top_fat)
total_fat_top = df_top_fat["faturamento_12m"].sum()
df_top_fat["participacao"] = df_top_fat["faturamento_12m"].apply(
    lambda v: (v / total_fat_top * 100) if total_fat_top > 0 else 0
)

conn.close()

# =====================================================
# O QUE FAZER HOJE — Fila Operacional (v1.6.10)
# =====================================================

st.markdown("## 📋 O QUE FAZER HOJE")
st.caption(
    "Fila operacional priorizada: pendências vencidas > pendências hoje > "
    "follow-ups vencidos > follow-ups hoje > OS aguardando > "
    "clientes esfriando > clientes sem visita."
)

hoje_str = date.today().strftime("%Y-%m-%d")
conn_fila = sqlite3.connect("crm.db")
lista_prioridades = []
prox_acao_sugerida = {
    "PENDENCIA_VENCIDA": "Atender pendência vencida imediatamente",
    "PENDENCIA_HOJE": "Atender pendência com vencimento hoje",
    "FOLLOWUP_VENCIDO": "Realizar follow-up imediato com cliente",
    "FOLLOWUP_HOJE": "Realizar follow-up agendado para hoje",
    "OS_APROVACAO": "Contatar cliente para aprovação da proposta",
    "ESFRIANDO": "Agendar visita ou contato comercial",
    "SEM_VISITA": "Agendar visita presencial",
}

# 1. Pendências Vencidas (data_limite < hoje)
df_pend_vencidas = pd.read_sql_query(
    """SELECT p.id, c.razao_social AS cliente, p.responsavel,
              p.descricao, p.data_limite, p.prioridade,
              CAST(julianday('now') - julianday(p.data_limite) AS INTEGER) AS dias_atraso
       FROM pendencias_comerciais p
       LEFT JOIN clientes c ON p.cliente_id = c.id
       WHERE p.status = 'ABERTA'
         AND p.data_limite < date('now')
       ORDER BY p.data_limite ASC""",
    conn_fila,
)
if not df_pend_vencidas.empty:
    for _, row in df_pend_vencidas.iterrows():
        dias = int(row["dias_atraso"]) if pd.notna(row["dias_atraso"]) else 0
        lista_prioridades.append({
            "prioridade": 1,
            "tipo": "🔴 PENDÊNCIA VENCIDA",
            "cliente": row["cliente"],
            "os": "-",
            "motivo": f"{row['descricao']} — {dias} dia(s) atrasada",
            "dias": f"{dias}d",
            "responsavel": row.get("responsavel", "-"),
            "prox_acao": prox_acao_sugerida["PENDENCIA_VENCIDA"],
            "vencimento": str(row["data_limite"])[:10] if pd.notna(row["data_limite"]) else "-",
        })

# 2. Pendências para Hoje (data_limite == hoje)
df_pend_hoje = pd.read_sql_query(
    """SELECT p.id, c.razao_social AS cliente, p.responsavel,
              p.descricao, p.data_limite, p.prioridade
       FROM pendencias_comerciais p
       LEFT JOIN clientes c ON p.cliente_id = c.id
       WHERE p.status = 'ABERTA'
         AND p.data_limite = date('now')
       ORDER BY p.prioridade ASC""",
    conn_fila,
)
if not df_pend_hoje.empty:
    for _, row in df_pend_hoje.iterrows():
        lista_prioridades.append({
            "prioridade": 2,
            "tipo": "🟠 PENDÊNCIA HOJE",
            "cliente": row["cliente"],
            "os": "-",
            "motivo": f"{row['descricao']} — vence hoje",
            "dias": "0d",
            "responsavel": row.get("responsavel", "-"),
            "prox_acao": prox_acao_sugerida["PENDENCIA_HOJE"],
            "vencimento": hoje_str,
        })

# 3. Follow-ups Vencidos (OS com proximo_followup < hoje)
df_fu_vencidos = pd.read_sql_query(
    """SELECT os.numero_os, c.razao_social AS cliente, os.responsavel,
              os.proximo_followup, os.valor_proposta,
              CAST(julianday('now') - julianday(os.proximo_followup) AS INTEGER) AS dias_atraso
       FROM ordens_servico os
       LEFT JOIN clientes c ON os.cliente_id = c.id
       WHERE os.status IN ('PROPOSTA ENVIADA', 'FOLLOW-UP')
         AND os.proximo_followup IS NOT NULL
         AND os.proximo_followup < date('now')
       ORDER BY os.proximo_followup ASC""",
    conn_fila,
)
if not df_fu_vencidos.empty:
    for _, row in df_fu_vencidos.iterrows():
        dias = int(row["dias_atraso"]) if pd.notna(row["dias_atraso"]) else 0
        lista_prioridades.append({
            "prioridade": 3,
            "tipo": "🔴 FOLLOW-UP VENCIDO",
            "cliente": row["cliente"],
            "os": str(row["numero_os"]) if pd.notna(row["numero_os"]) else "-",
            "motivo": f"{dias} dia(s) de atraso",
            "dias": f"{dias}d",
            "responsavel": row.get("responsavel", "-"),
            "prox_acao": prox_acao_sugerida["FOLLOWUP_VENCIDO"],
            "vencimento": str(row["proximo_followup"])[:10] if pd.notna(row["proximo_followup"]) else "-",
        })

# 4. Follow-ups de Hoje
df_fu_hoje = pd.read_sql_query(
    """SELECT os.numero_os, c.razao_social AS cliente, os.responsavel,
              os.proximo_followup, os.valor_proposta
       FROM ordens_servico os
       LEFT JOIN clientes c ON os.cliente_id = c.id
       WHERE os.status IN ('PROPOSTA ENVIADA', 'FOLLOW-UP')
         AND os.proximo_followup = date('now')
       ORDER BY os.responsavel""",
    conn_fila,
)
if not df_fu_hoje.empty:
    for _, row in df_fu_hoje.iterrows():
        lista_prioridades.append({
            "prioridade": 4,
            "tipo": "🟡 FOLLOW-UP HOJE",
            "cliente": row["cliente"],
            "os": str(row["numero_os"]) if pd.notna(row["numero_os"]) else "-",
            "motivo": "Follow-up agendado para hoje",
            "dias": "0d",
            "responsavel": row.get("responsavel", "-"),
            "prox_acao": prox_acao_sugerida["FOLLOWUP_HOJE"],
            "vencimento": hoje_str,
        })

# 5. OS Aguardando Aprovação
for _, row in df_os_aprovacao.iterrows():
    dias = int(row["dias_aguardando"]) if pd.notna(row["dias_aguardando"]) else 0
    if dias >= 7:
        badge = "⏳ OS AGUARDANDO" if dias < 15 else "🔴 OS ATRASADA"
        prioridade = 5 if dias < 15 else 4
        lista_prioridades.append({
            "prioridade": prioridade,
            "tipo": badge,
            "cliente": row["cliente"],
            "os": "-",
            "motivo": f"Aguardando aprovação há {dias} dias",
            "dias": f"{dias}d",
            "responsavel": row.get("responsavel", "-"),
            "prox_acao": prox_acao_sugerida["OS_APROVACAO"],
            "vencimento": f"{dias} dias",
        })

# 6. Clientes Esfriando
if not df_esfriando.empty:
    for _, row in df_esfriando.iterrows():
        var = row["variacao"]
        if var < -50:
            lista_prioridades.append({
                "prioridade": 6,
                "tipo": "🔴 ESFRIANDO",
                "cliente": row["cliente"],
                "os": "-",
                "motivo": f"Queda de faturamento: {var:.0f}%",
                "dias": "-",
                "responsavel": "-",
                "prox_acao": prox_acao_sugerida["ESFRIANDO"],
                "vencimento": "-",
            })

# 7. Clientes Sem Visita
if not df_sem_visita.empty:
    for _, row in df_sem_visita.iterrows():
        dias = row["dias_sem_visita"]
        if pd.notna(dias) and dias > 90:
            lista_prioridades.append({
                "prioridade": 7,
                "tipo": "📅 SEM VISITA",
                "cliente": row["cliente"],
                "os": "-",
                "motivo": f"{int(dias)} dias sem visita",
                "dias": f"{int(dias)}d",
                "responsavel": "-",
                "prox_acao": prox_acao_sugerida["SEM_VISITA"],
                "vencimento": f"{int(dias)}d atrás",
            })

conn_fila.close()

# Ordenar por prioridade
if lista_prioridades:
    df_hoje = pd.DataFrame(lista_prioridades)
    df_hoje = df_hoje.sort_values("prioridade").reset_index(drop=True)

    def colorir_fila(row):
        # Proteção defensiva: se "Prioridade" (coluna renomeada) não existir, retorna vazio
        if "Prioridade" not in row.index:
            return [""] * len(row)
        val = str(row["Prioridade"])
        if "VENCIDA" in val or "VENCIDO" in val or "ATRASADA" in val:
            return ["background-color: #fce4ec; color: #c62828"] * len(row)
        elif "HOJE" in val:
            return ["background-color: #fff3cd; color: #856404"] * len(row)
        elif "ESFRIANDO" in val:
            return ["background-color: #ffebee; color: #b71c1c"] * len(row)
        elif "AGUARDANDO" in val:
            return ["background-color: #e3f2fd; color: #1565c0"] * len(row)
        elif "SEM VISITA" in val:
            return ["background-color: #f3e5f5; color: #6a1b9a"] * len(row)
        return [""] * len(row)

    colunas_exib = ["tipo", "cliente", "os", "motivo", "dias", "prox_acao"]
    rename_map = {
        "tipo": "Prioridade",
        "cliente": "Cliente",
        "os": "OS",
        "motivo": "Motivo",
        "dias": "Dias",
        "prox_acao": "Próxima Ação Sugerida",
    }
    df_exib_hoje = df_hoje[colunas_exib].rename(columns=rename_map)

    st.dataframe(
        df_exib_hoje.style.apply(colorir_fila, axis=1),
        width="stretch",
        height=min(500, 35 * len(df_exib_hoje) + 40),
    )
    st.caption(
        "Ordem: 🔴 Pendência Vencida > 🟠 Pendência Hoje > 🔴 Follow-up Vencido > "
        "🟡 Follow-up Hoje > 🔴 OS Atrasada > ⏳ OS Aguardando > "
        "🔴 Esfriando > 📅 Sem Visita."
    )
else:
    st.success("Nenhuma ação urgente no momento.")

st.divider()

# =====================================================
# INDICADORES (KPIs simplificados)
# =====================================================

kpi_cols = st.columns(6)

kpi_cols[0].metric(
    "Preventivas Vencidas",
    len(df_preventivas),
    help="Clientes com mais de 730 dias sem manutenção"
)

kpi_cols[1].metric(
    "Prospecção Mitsubishi",
    len(df_novos_clientes),
    help="Empresas com máquinas Mitsubishi que nunca compraram da ULITEC"
)

kpi_cols[2].metric(
    "Clientes Esfriando",
    resumo["clientes_esfriando"],
    help="Clientes com queda de faturamento ou sem visita há mais de 120 dias"
)

kpi_cols[3].metric(
    "Clientes Esquentando",
    resumo["clientes_esquentando"],
    help="Clientes com crescimento de faturamento acima de 20%"
)

kpi_cols[4].metric(
    "Sem Visita",
    resumo["clientes_sem_visita"],
    help="Clientes sem visita há mais de 90 dias ou nunca visitados"
)

kpi_cols[5].metric(
    "Score Comercial",
    len(df_score),
    help="Clientes priorizados por potencial comercial"
)

st.divider()

# =====================================================
# PRIORIDADES COMERCIAIS
# =====================================================

st.markdown("## Prioridades Comerciais")
st.caption("Fila de trabalho — prioriza potencial de negócio, não apenas queda.")

df_pend_prioridades = get_pendencias(status="ABERTA")

if df_score.empty:
    st.success("Nenhuma prioridade comercial no momento.")
else:
    df_ranking = df_score.head(20).copy()
    df_ranking["#"] = range(1, len(df_ranking) + 1)

    df_ranking["Cliente"] = df_ranking["cliente"]
    df_ranking["Classe"] = df_ranking["classe_abc"]
    df_ranking["Score"] = df_ranking["score"].apply(lambda x: f"{x:.0f}")
    df_ranking["Máquinas"] = df_ranking["qtd_maquinas"].apply(
        lambda x: f"{int(x)}" if pd.notna(x) else "0"
    )
    df_ranking["Faturamento 12m"] = df_ranking["fat_12m"].apply(
        lambda x: f"R$ {x:,.0f}" if pd.notna(x) and x > 0 else "R$ 0"
    )
    df_ranking["Sem Contato"] = df_ranking["dias_sem_contato"].apply(
        lambda x: f"{int(x)}d" if pd.notna(x) and x < 9999 else "-"
    )
    df_ranking["Sem Visita"] = df_ranking["dias_sem_visita"].apply(
        lambda x: f"{int(x)}d" if pd.notna(x) and x < 9999 else "-"
    )
    df_ranking["Motivo"] = df_ranking["motivo_prioridade"]
    df_ranking["Ação"] = df_ranking["proxima_acao"]

    tab_grid, tab_detalhado = st.tabs(["Grid", "Detalhes"])

    with tab_grid:
        st.markdown("### Top 20 Prioridades")

        colunas_grid = [
            "#", "Cliente", "Classe", "Score", "Máquinas",
            "Faturamento 12m", "Sem Contato", "Sem Visita",
            "Motivo", "Ação"
        ]

        df_grid = df_ranking[colunas_grid].copy()

        def colorir_ranking(row):
            cores = []
            for col in row.index:
                if col == "Score":
                    val = float(row[col])
                    if val >= 80:
                        cores.append("background-color: #16a34a; color: white; font-weight: bold")
                    elif val >= 60:
                        cores.append("background-color: #2563eb; color: white; font-weight: bold")
                    elif val >= 40:
                        cores.append("background-color: #f59e0b; color: black; font-weight: bold")
                    elif val >= 20:
                        cores.append("background-color: #dc2626; color: white; font-weight: bold")
                    else:
                        cores.append("background-color: #e5e7eb; color: #666; font-weight: bold")
                elif col == "Classe":
                    cl = row[col]
                    if cl == "A":
                        cores.append("background-color: #16a34a; color: white; font-weight: bold")
                    elif cl == "B":
                        cores.append("background-color: #2563eb; color: white; font-weight: bold")
                    elif cl == "C":
                        cores.append("background-color: #f59e0b; color: black; font-weight: bold")
                    elif cl == "D":
                        cores.append("background-color: #dc2626; color: white; font-weight: bold")
                    else:
                        cores.append("")
                else:
                    cores.append("")
            return cores

        st.dataframe(
            df_grid.style.apply(colorir_ranking, axis=1),
            width="stretch",
            height=600,
            column_config={
                "Score": st.column_config.NumberColumn("Score", help="0-100. Quanto maior, mais prioritário.", format="%d"),
                "Motivo": st.column_config.TextColumn("Motivo", help="Por que o cliente está na lista", width="large"),
                "Ação": st.column_config.TextColumn("Ação", help="Próxima ação recomendada", width="medium"),
            }
        )

        st.caption(
            "Ordenado por Score (maior primeiro). "
            f"Clientes com relacionamento ativo recebem -{PENALIDADE_RELACIONAMENTO_ATIVO}pts."
        )

    with tab_detalhado:
        st.markdown("### Detalhes por Cliente — Top 20")

        for _, row in df_ranking.iterrows():
            classe = row["Classe"]
            maq = int(row["qtd_maquinas"]) if pd.notna(row["qtd_maquinas"]) else 0
            fat = row["fat_12m"] if pd.notna(row["fat_12m"]) else 0
            dias_contato = int(row["dias_sem_contato"]) if pd.notna(row["dias_sem_contato"]) else 0
            dias_visita = int(row["dias_sem_visita"]) if pd.notna(row["dias_sem_visita"]) else 0
            score = row["score"]
            motivo = row["motivo_prioridade"]
            acao = row["proxima_acao"]
            explicacao = row.get("explicacao_score", "")
            rel_ativo = row["relacionamento_ativo"]

            cor_classe = {"A": "#16a34a", "B": "#2563eb", "C": "#f59e0b", "D": "#dc2626"}
            cor = cor_classe.get(classe, "#666")

            if score >= 80:
                icone_score = "🏆"
            elif score >= 60:
                icone_score = "⭐"
            elif score >= 40:
                icone_score = "🔹"
            elif score >= 20:
                icone_score = "📌"
            else:
                icone_score = "📋"

            ranking_pos = int(row["#"])

            with st.expander(
                f"#{ranking_pos} {icone_score} {row['cliente']}  \n"
                f"Classe {classe} | Score: {score:.0f} | {maq} máquinas | R$ {fat:,.0f}",
                expanded=False
            ):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown(f"**Cliente:** {row['cliente']}")
                    st.markdown(f"**Classe ABCD:** {classe}")
                    st.markdown(f"**Máquinas Mitsubishi:** {maq}")
                    st.markdown(f"**Faturamento 12m:** R$ {fat:,.0f}")
                    st.markdown(f"**Sem contato:** {dias_contato}d")
                    st.markdown(f"**Sem visita:** {dias_visita}d")
                    st.markdown(f"**Queda faturamento:** {row['queda_fat_pct']:.0f}%")
                    st.markdown(f"**Preventiva:** {'Vencida' if row['dias_sem_manutencao'] >= 730 else 'Em dia'}")

                with col2:
                    st.markdown(f"### Score: **{score:.0f}**")
                    st.markdown("#### Cálculo do Score")
                    explicacao_limpa = explicacao.replace("\n", "  \n")
                    st.markdown(f"```\n{explicacao_limpa}\n```")

                st.markdown("---")
                st.markdown(f"**Motivo:** {motivo}")
                st.markdown(f"**Ação sugerida:** {acao}")

        st.caption("Expanda cada card para ver detalhes completos.")

st.divider()

# =====================================================
# LISTAS ACIONÁVEIS
# =====================================================

st.markdown("## Listas Acionáveis")

tab_esfriando, tab_esquentando, tab_sem_visita_tab, tab_sem_faturamento_tab, tab_classificacao = st.tabs([
    "Clientes Esfriando",
    "Clientes Esquentando",
    "Sem Visita",
    "Sem Faturamento",
    "Classificação ABCD",
])

# ── Esfriando ──
with tab_esfriando:
    st.subheader("Clientes Esfriando")
    st.caption("Clientes com queda de faturamento > 30% ou sem visita > 120 dias")
    df_aba = aplicar_filtros(df_esfriando)
    if df_aba.empty:
        st.success("Nenhum cliente esfriando no período.")
    else:
        df_aba_exib = df_aba.rename(columns={
            "cliente": "Cliente",
            "cidade": "Cidade",
            "variacao": "Queda (%)",
            "dias_sem_visita": "Dias sem Visita",
        })
        df_aba_exib["Queda (%)"] = df_aba_exib["Queda (%)"].apply(lambda x: f"{x:.0f}%")
        df_aba_exib["Dias sem Visita"] = df_aba_exib["Dias sem Visita"].apply(
            lambda x: f"{int(x)}" if pd.notna(x) else "-"
        )

        def destaque_vermelho(row):
            return ["background-color: #ffcccc; color: #8b0000"] * len(row)

        st.dataframe(
            df_aba_exib[["Cliente", "Cidade", "Queda (%)", "Dias sem Visita"]].style.apply(destaque_vermelho, axis=1),
            width="stretch",
            height=400,
        )

# ── Esquentando ──
with tab_esquentando:
    st.subheader("Clientes Esquentando")
    st.caption("Clientes com crescimento de faturamento > 20%")
    df_aba = aplicar_filtros(df_esquentando)
    if df_aba.empty:
        st.success("Nenhum cliente esquentando no período.")
    else:
        df_aba_exib = df_aba.rename(columns={
            "cliente": "Cliente",
            "cidade": "Cidade",
            "variacao": "Crescimento (%)",
            "faturamento": "Faturamento",
        })
        df_aba_exib["Crescimento (%)"] = df_aba_exib["Crescimento (%)"].apply(lambda x: f"{x:.0f}%")
        df_aba_exib["Faturamento"] = df_aba_exib["Faturamento"].apply(
            lambda x: f"R$ {x:,.2f}" if pd.notna(x) and x > 0 else "R$ 0,00"
        )

        def destaque_verde(row):
            return ["background-color: #ccffcc; color: #006400"] * len(row)

        st.dataframe(
            df_aba_exib[["Cliente", "Cidade", "Crescimento (%)", "Faturamento"]].style.apply(destaque_verde, axis=1),
            width="stretch",
            height=400,
        )

# ── Sem Visita ──
with tab_sem_visita_tab:
    st.subheader("Clientes Sem Visita")
    df_aba = aplicar_filtros(df_sem_visita)
    qtd_nunca = len(df_aba[df_aba["tipo"] == "NUNCA_VISITADO"]) if not df_aba.empty else 0
    qtd_atrasadas = len(df_aba[df_aba["tipo"] == "VISITA_ATRASADA"]) if not df_aba.empty else 0

    cv1, cv2 = st.columns(2)
    cv1.metric("Nunca Visitados", qtd_nunca)
    cv2.metric("Visitas Atrasadas (>90 dias)", qtd_atrasadas)

    if df_aba.empty:
        st.success("Nenhum cliente sem visita encontrado.")
    else:
        df_exib = df_aba.rename(columns={
            "cliente": "Cliente",
            "cidade": "Cidade",
            "dias_sem_visita": "Dias sem Visita",
            "tipo": "Tipo",
        })
        df_exib["Dias sem Visita"] = df_exib["Dias sem Visita"].apply(
            lambda x: "Nunca" if pd.isna(x) else str(int(x))
        )

        def destaque_nunca(row):
            if row["Tipo"] == "NUNCA_VISITADO":
                return ["background-color: #ffeeba; color: #856404"] * len(row)
            return [""] * len(row)

        st.dataframe(
            df_exib.style.apply(destaque_nunca, axis=1),
            width="stretch",
            height=400,
        )

# ── Sem Faturamento ──
with tab_sem_faturamento_tab:
    st.subheader("Clientes Sem Faturamento (12 meses)")
    st.caption("Possuem máquinas Mitsubishi ou histórico de OS, mas não faturam há 12 meses")
    df_aba = aplicar_filtros(df_sem_faturamento)
    if df_aba.empty:
        st.success("Nenhum cliente sem faturamento encontrado.")
    else:
        df_exib = df_aba.rename(columns={
            "cliente": "Cliente",
            "máquinas": "Máquinas",
            "última OS": "Última OS",
            "último faturamento": "Último Faturamento",
        })
        st.dataframe(df_exib, width="stretch", height=400)

# ── Classificação ABCD ──
with tab_classificacao:
    st.subheader("Classificação ABCD")
    st.caption("A = top 10% faturamento | B = próximos 30% | C = próximos 60% | D = sem faturamento")

    filtro_classe = st.radio(
        "Filtrar por classe",
        options=["Todas", "A", "B", "C", "D"],
        horizontal=True,
        key="filtro_classe_abcd",
    )

    df_clientes_abc["classe_abc"] = df_clientes_abc["classe_abc"].astype(str)

    df_abcd = df_clientes_abc.copy()
    if filtro_classe != "Todas":
        df_abcd = df_abcd[df_abcd["classe_abc"] == filtro_classe]

    if df_abcd.empty:
        st.info("Nenhum cliente encontrado com o filtro selecionado.")
    else:
        df_exib_abcd = df_abcd.rename(columns={
            "razao_social": "Cliente",
            "classe_abc": "Classe",
            "cidade": "Cidade",
            "estado": "Estado",
            "ultima_visita": "Última Visita",
            "ultima_interacao": "Última Interação",
            "faturamento_12m": "Faturamento 12m",
        })
        df_exib_abcd["Faturamento 12m"] = df_exib_abcd["Faturamento 12m"].apply(
            lambda x: f"R$ {x:,.2f}" if pd.notna(x) and x > 0 else "R$ 0,00"
        )
        df_exib_abcd["Última Visita"] = df_exib_abcd["Última Visita"].fillna("Nunca")
        df_exib_abcd["Última Interação"] = df_exib_abcd["Última Interação"].fillna("Nunca")

        st.dataframe(
            df_exib_abcd[["Cliente", "Classe", "Cidade", "Estado",
                          "Faturamento 12m", "Última Interação", "Última Visita"]],
            width="stretch",
            height=500,
        )
        st.caption(f"Total: {len(df_abcd)} clientes.")

st.divider()

# =====================================================
# OPERACIONAL
# =====================================================

st.markdown("## Operacional")
tab_top_fat, tab_os_aprovacao, tab_preventivas_eng, tab_mitsubishi_eng = st.tabs([
    "Top Faturamento 12m",
    "OS Aguardando Aprovação",
    "Preventivas Vencidas",
    "Prospecção Mitsubishi",
])

# ── Top Faturamento 12m ──
with tab_top_fat:
    st.subheader("Top 20 Clientes por Faturamento (12 meses)")
    if df_top_fat.empty:
        st.success("Nenhum dado disponível.")
    else:
        df_exib_top = df_top_fat.rename(columns={
            "cliente": "Cliente",
            "faturamento_12m": "Faturamento 12m",
            "participacao": "%",
        })
        df_exib_top["Faturamento 12m"] = df_exib_top["Faturamento 12m"].apply(lambda x: f"R$ {x:,.2f}")
        df_exib_top["%"] = df_exib_top["%"].apply(lambda x: f"{x:.1f}%")
        st.dataframe(df_exib_top, width="stretch", height=400)

# ── OS Aguardando Aprovação ──
with tab_os_aprovacao:
    st.subheader("OS Aguardando Aprovação")
    st.caption("Aguardando aprovação por mais de 7 dias merecem follow-up")
    if df_os_aprovacao.empty:
        st.success("Nenhuma OS aguardando aprovação.")
    else:
        df_exib_os = df_os_aprovacao.rename(columns={
            "cliente": "Cliente",
            "valor": "Valor",
            "dias_aguardando": "Dias",
            "responsavel": "Responsável",
            "status": "Status",
        })
        df_exib_os["Valor"] = df_exib_os["Valor"].apply(
            lambda x: f"R$ {x:,.2f}" if pd.notna(x) and x > 0 else "R$ 0,00"
        )

        def destaque_os_atrasada(row):
            if row["Dias"] > 15:
                return ["background-color: #f8d7da; color: #721c24"] * len(row)
            elif row["Dias"] > 7:
                return ["background-color: #fff3cd; color: #856404"] * len(row)
            return [""] * len(row)

        st.dataframe(
            df_exib_os.style.apply(destaque_os_atrasada, axis=1),
            width="stretch",
            height=400,
        )

# ── Preventivas Vencidas ──
with tab_preventivas_eng:
    st.subheader(f"Clientes com Preventiva Vencida (> {dias_alerta} dias)")
    if df_preventivas.empty:
        st.success("Nenhum cliente com preventiva vencida.")
    else:
        df_exibicao = df_preventivas.rename(columns={
            "razao_social": "Cliente",
            "cidade": "Cidade",
            "estado": "Estado",
            "data_ultima_os": "Última OS",
            "dias_sem_manutencao": "Dias sem Manutenção"
        })
        df_exibicao["Última OS"] = pd.to_datetime(df_exibicao["Última OS"], errors="coerce")
        df_exibicao = df_exibicao.dropna(subset=["Última OS"])
        df_exibicao["Última OS"] = df_exibicao["Última OS"].dt.strftime("%d/%m/%Y")

        st.dataframe(
            df_exibicao[["Cliente", "Cidade", "Estado", "Última OS", "Dias sem Manutenção"]],
            width="stretch",
            height=400,
        )

# ── Prospecção Mitsubishi ──
with tab_mitsubishi_eng:
    st.subheader("Empresas com Máquinas Mitsubishi — Nunca Compraram")
    st.caption("Potencial para prospecção ativa (outbound)")
    if df_novos_clientes.empty:
        st.success("Nenhum cliente em prospecção encontrado.")
    else:
        df_exib_novos = df_novos_clientes.rename(columns={
            "razao_social": "Cliente",
            "cidade": "Cidade",
            "estado": "Estado",
            "qtd_mitsubishi": "Máquinas",
            "potencial": "Potencial"
        })

        def cor_potencial(val):
            if val == "ALTO":
                return "background-color: #28a745; color: white"
            elif val == "MÉDIO":
                return "background-color: #ffc107; color: black"
            return ""

        st.dataframe(
            df_exib_novos.style.map(cor_potencial, subset=["Potencial"]),
            width="stretch",
            height=400
        )

st.divider()

# =====================================================
# RELACIONAMENTO
# =====================================================

st.markdown("## Relacionamento")
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
        # Adicionar colunas de detalhamento
        df_pend_exib = df_pend_abertas.rename(columns={
            "cliente": "Cliente",
            "descricao": "Descrição",
            "responsavel": "Responsável",
            "prioridade": "Prioridade",
            "data_limite": "Vencimento",
        })
        # Formatar vencimento
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

    # Filtros
    filtros_col1, filtros_col2, filtros_col3, filtros_col4 = st.columns(4)

    df_resp = get_pendencias(status="ABERTA")
    responsables = ["Todos"]
    if not df_resp.empty and "responsavel" in df_resp.columns:
        resp_list = df_resp["responsavel"].dropna().unique().tolist()
        responsables = ["Todos"] + sorted(resp_list)

    filtro_resp_acoes = filtros_col1.selectbox("Responsável", options=responsables, key="filtro_resp_acoes")

    filtro_cliente_acoes = filtros_col2.text_input("Cliente", placeholder="Digite parte do nome...", key="filtro_cliente_acoes")

    col_periodo_inicio, col_periodo_fim = st.columns(2)
    filtro_periodo_inicio = col_periodo_inicio.date_input("Data início", value=None, key="filtro_periodo_inicio_acoes")
    filtro_periodo_fim = col_periodo_fim.date_input("Data fim", value=None, key="filtro_periodo_fim_acoes")

    hoje = date.today()
    filtro_status_acoes = filtros_col4.selectbox("Status", options=["Todos", "VENCIDA", "HOJE", "FUTURO"], key="filtro_status_acoes")

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