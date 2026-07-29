"""
Página principal do Módulo de Relacionamento Comercial — ULITEC CRM

Orquestradora: cada aba é delegada a um componente especializado.

Fluxo de negócio:
  Planejar visitas → Executar visitas → Registrar interação
  → Gerar pendências → Receber alertas
"""

from datetime import date

import streamlit as st
import pandas as pd

from auth import sidebar_usuario
from permissions import verificar_acesso_pagina
from services import formatar_clientes_para_select
from database import get_connection

from components.relacionamento import (
    exibir_agenda,
    exibir_registro,
    exibir_historico,
    exibir_pendencias,
    exibir_nova_pendencia,
    exibir_alertas,
)

# ── Proteção: autenticado (todos os perfis) ──
verificar_acesso_pagina()
sidebar_usuario()

st.set_page_config(page_title="Relacionamento Comercial", layout="wide")

st.title("📞 Relacionamento Comercial")
st.markdown(
    "Gerencie visitas, interações, agenda comercial "
    "e pendências de clientes."
)

# ── Inicialização da sessão ──
if "unidade_ativa" not in st.session_state:
    st.session_state["unidade_ativa"] = "ULITEC SP"
if "unidade_sugerida" not in st.session_state:
    st.session_state["unidade_sugerida"] = st.session_state.get(
        "unidade_usuario", "ULITEC SP"
    )
if "nome_usuario" not in st.session_state:
    st.session_state["nome_usuario"] = ""
if "usuario_id" not in st.session_state:
    st.session_state["usuario_id"] = None

# ── Conexão para dados auxiliares ──
conn = get_connection()

df_clientes = pd.read_sql_query(
    "SELECT id, razao_social, cidade, estado FROM clientes WHERE status = 'ATIVO' ORDER BY razao_social",
    conn,
)
clientes_lista, clientes_dict, clientes_reverso = formatar_clientes_para_select(df_clientes)

BANCO_VAZIO = len(clientes_lista) == 0
if BANCO_VAZIO:
    clientes_lista = ["Nenhum cliente cadastrado"]
    clientes_dict = {}
    clientes_reverso = {}

conn.close()

# =====================================================
# ABAS
# =====================================================

aba1, aba2, aba3, aba4, aba5, aba6 = st.tabs([
    "📅 Agenda",
    "✏️ Registrar Interação",
    "📋 Histórico",
    "📌 Pendências",
    "➕ Nova Pendência",
    "🔔 Alertas",
])

with aba1:
    exibir_agenda()

with aba2:
    exibir_registro(clientes_lista, clientes_dict, clientes_reverso)

with aba3:
    exibir_historico(clientes_lista, clientes_dict)

with aba4:
    exibir_pendencias()

with aba5:
    exibir_nova_pendencia(clientes_lista, clientes_dict)

with aba6:
    exibir_alertas()