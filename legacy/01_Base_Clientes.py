import streamlit as st
import sqlite3
import pandas as pd

from auth import verificar_acesso, sidebar_usuario

# ── Proteção: autenticado (todos os perfis) ──
verificar_acesso()
sidebar_usuario()

# ── Acesso restrito: apenas MASTER, SOCIO e GESTOR ──
perfil = st.session_state.get("perfil", "OPERADOR")
if perfil == "OPERADOR":
    st.warning("🔒 Acesso restrito. Esta funcionalidade não está disponível para seu perfil.")
    st.info("Consulte o administrador do sistema para mais informações.")
    st.stop()

st.title("👥 Base Mestre de Clientes")

busca = st.text_input("🔍 Pesquisar por Razão Social, Nome Fantasia ou CNPJ:")

try:
    conn = sqlite3.connect("crm.db")

    if "unidade_ativa" in st.session_state and st.session_state["unidade_ativa"] != "GRUPO":
        df = pd.read_sql_query(
            """
            SELECT id, codigo_erp, razao_social, nome_fantasia, cnpj,
                   cidade, estado, telefone, email, segmento,
                   parque_maquinas, maquinas_mitsubishi, classe_abc,
                   tipo_conta, faturamento_12m, ultima_visita, ultimo_faturamento
            FROM clientes
            WHERE origem_erp = ?
            ORDER BY razao_social
            """,
            conn,
            params=(st.session_state["unidade_ativa"],),
        )
    else:
        df = pd.read_sql_query(
            """
            SELECT id, codigo_erp, razao_social, nome_fantasia, cnpj,
                   cidade, estado, telefone, email, segmento,
                   parque_maquinas, maquinas_mitsubishi, classe_abc,
                   tipo_conta, faturamento_12m, ultima_visita, ultimo_faturamento
            FROM clientes
            ORDER BY razao_social
            """,
            conn,
        )

    conn.close()

    if busca:
        df_filtrado = df[
            df["razao_social"].str.contains(busca, case=False, na=False)
            | df["nome_fantasia"].str.contains(busca, case=False, na=False)
            | df["cnpj"].str.contains(busca, case=False, na=False)
        ]
    else:
        df_filtrado = df

    st.dataframe(df_filtrado, width="stretch", hide_index=True)

except Exception as e:
    st.error(f"Erro ao carregar clientes: {e}")