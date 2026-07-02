import sqlite3

import pandas as pd
import streamlit as st

from auth import verificar_acesso, sidebar_usuario

# ── Proteção: autenticado (todos os perfis) ──
verificar_acesso()
sidebar_usuario()

st.set_page_config(
    page_title="Ações em Massa",
    layout="wide"
)

st.title("📦 Ações em Massa - Atualização em Lote")

# ── Segregação por filial ──
if "perfil" not in st.session_state:
    st.session_state["perfil"] = "SOCIO"
if "unidade_ativa" not in st.session_state:
    st.session_state["unidade_ativa"] = "GRUPO"
if "unidade_usuario" not in st.session_state:
    st.session_state["unidade_usuario"] = "ULITEC SP"

# ── Seletor de unidade no corpo da página (visível para todos os perfis) ──
unidade_options = ["Grupo (Consolidado)", "ULITEC SP", "ULITEC RS"]
idx_map = {"GRUPO": 0, "ULITEC SP": 1, "ULITEC RS": 2}
default_idx = idx_map.get(st.session_state["unidade_ativa"], 0)

escolha = st.selectbox(
    "🏢 Filtrar por Unidade",
    options=unidade_options,
    index=default_idx
)
st.session_state["unidade_ativa"] = "GRUPO" if escolha == "Grupo (Consolidado)" else escolha

conn = sqlite3.connect("crm.db")

# ── Query base ──
query_base = """
    SELECT
        os.id,
        os.numero_os,
        c.razao_social AS cliente,
        os.valor_proposta,
        os.status
    FROM ordens_servico os
    LEFT JOIN clientes c ON c.id = os.cliente_id
"""

if st.session_state["unidade_ativa"] == "GRUPO":
    query = query_base + " ORDER BY os.id DESC"
    params = ()
else:
    query = query_base + " WHERE os.unidade = ? ORDER BY os.id DESC"
    params = (st.session_state["unidade_ativa"],)

df = pd.read_sql_query(query, conn, params=params)

st.info(f"OS retornadas pela consulta: {len(df)}")

if df.empty:
    st.warning("Nenhuma OS encontrada para a unidade selecionada.")
    st.stop()

# ── Coluna de seleção ──
df["Selecionar"] = False

# Reordenar: Selecionar na primeira posição
cols = ["Selecionar"] + [c for c in df.columns if c != "Selecionar"]
df = df[cols]

# ── Checkbox "Selecionar / Desmarcar Todos" ──
col_check_all, col_info = st.columns([1, 5])
with col_check_all:
    selecionar_todos = st.checkbox("✅ Selecionar Todos")
with col_info:
    if selecionar_todos:
        st.caption(f"✔️ Todas as **{len(df)}** OS serão marcadas para atualização em lote.")
    else:
        st.caption("Marque individualmente ou use o checkbox ao lado para selecionar todas.")

if selecionar_todos:
    df["Selecionar"] = True

# ── Tabela editável ──
st.subheader("Selecione as OS que deseja atualizar")
df_editado = st.data_editor(df, hide_index=True, width="stretch", height=500)

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

col_status, col_btn_parcial, col_btn_total = st.columns([3, 2, 2])

with col_status:
    novo_status = st.selectbox("Novo status para as OS selecionadas", STATUS_DISPONIVEIS)

with col_btn_parcial:
    executar = st.button("▶️ Atualizar Selecionadas", type="primary", width="stretch")

with col_btn_total:
    atualizar_tudo = st.button("⚡ Atualizar Todas da Unidade", width="stretch")

if executar:
    selecionadas = df_editado[df_editado["Selecionar"] == True]

    if selecionadas.empty:
        st.warning("Nenhuma OS foi selecionada.")
    else:
        ids = selecionadas["id"].tolist()
        placeholders = ",".join("?" for _ in ids)

        conn.execute(
            f"""UPDATE ordens_servico
                SET status = ?,
                    data_atualizacao = date('now')
                WHERE id IN ({placeholders})""",
            (novo_status, *ids)
        )
        conn.commit()

        st.success(f"{len(ids)} OS(s) alterada(s) para o status '{novo_status}' com sucesso!")
        st.rerun()

if atualizar_tudo:
    conn.execute(
        """UPDATE ordens_servico
           SET status = ?,
               data_atualizacao = date('now')
           WHERE 1=1""" + ("" if st.session_state["unidade_ativa"] == "GRUPO" else " AND unidade = ?"),
        (novo_status,) if st.session_state["unidade_ativa"] == "GRUPO" else (novo_status, st.session_state["unidade_ativa"])
    )
    conn.commit()
    st.success(f"✅ Todas as OS da unidade foram alteradas para o status '{novo_status}' com sucesso!")
    st.rerun()

conn.close()
