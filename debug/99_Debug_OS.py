import streamlit as st
import sqlite3
import pandas as pd

from auth import verificar_acesso, sidebar_usuario

# ── Proteção: autenticado (todos os perfis) ──
verificar_acesso()
sidebar_usuario()

conn = sqlite3.connect("crm.db")

df = pd.read_sql_query("""
SELECT
    numero_os,
    status,
    unidade,
    responsavel,
    data_recebimento,
    valor_proposta,
    origem
FROM ordens_servico
ORDER BY numero_os
""", conn)

conn.close()

st.title("DEBUG OS")

st.write("Quantidade:", len(df))

st.dataframe(
    df,
    width="stretch",
    height=700
)
