import utils.bootstrap  # noqa: F401 — bootstrap único: .env, WAL, schema, monkey-patch .connect

import streamlit as st

from auth import init_auth, mostrar_login, sidebar_usuario
from permissions import pode_selecionar_unidade
from config import DB_PATH

st.set_page_config(
    page_title="CRM Industrial ULITEC",
    page_icon="🏭",
    layout="centered",
)

# ── Inicializar sistema de autenticação (migra colunas, cria MASTER) ──
init_auth()

# ── Se não estiver logado, mostrar tela de login ──
if not st.session_state.get("usuario_logado", False):
    mostrar_login()
    st.stop()

# ── Inicialização da sessão (valores padrão para usuários já autenticados) ──
if "perfil" not in st.session_state:
    st.session_state["perfil"] = "SÓCIO"
if "unidade_ativa" not in st.session_state:
    st.session_state["unidade_ativa"] = "GRUPO"
if "unidade_usuario" not in st.session_state:
    st.session_state["unidade_usuario"] = "ULITEC SP"

# ── Sidebar com informações do usuário ──
sidebar_usuario()

# ── Seletor de unidade na sidebar ──
if pode_selecionar_unidade():
    escolha = st.sidebar.selectbox(
        "Filtrar Unidade (Visão Gestor)",
        options=["Grupo (Consolidado)", "ULITEC SP", "ULITEC RS"],
        index=0
        if st.session_state["unidade_ativa"] == "GRUPO"
        else (1 if st.session_state["unidade_ativa"] == "ULITEC SP" else 2),
    )
    st.session_state["unidade_ativa"] = (
        "GRUPO" if escolha == "Grupo (Consolidado)" else escolha
    )
else:
    st.session_state["unidade_ativa"] = st.session_state["unidade_usuario"]

# ================================================================
# PÁGINA DE BOAS-VINDAS EXECUTIVA
# ================================================================

st.markdown(
    """
    <div style="text-align: center; padding: 3rem 0;">
        <h1 style="font-size: 3rem; margin-bottom: 0.5rem;">🏭 CRM Industrial ULITEC</h1>
        <p style="font-size: 1.2rem; color: #666;">
            Portal ERP — Inteligência Comercial, Operacional e Financeira
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("---")

col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #1e3a5f, #2d6a9f);
                    padding: 2.5rem;
                    border-radius: 1rem;
                    text-align: center;
                    color: white;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.15);">
            <h2 style="color: white; margin-bottom: 1rem;">📊 Painel Executivo</h2>
            <p style="font-size: 1rem; opacity: 0.9; margin-bottom: 1.5rem;">
                Acesse o dashboard completo com indicadores de desempenho,
                sazonalidade, ranking de clientes e muito mais.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button(
        "🚀 Entrar no Painel Executivo",
        type="primary",
        width="stretch",
    ):
        st.switch_page("pages/00_Dashboard.py")

from components import rodape_padrao
rodape_padrao()
