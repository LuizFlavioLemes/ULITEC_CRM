"""
Pagina principal do modulo Gestao de Comissoes — ULITEC CRM v1.0

Orquestradora de abas. Cada aba e um componente independente em components/comissoes/.
Nenhuma regra de negocio aqui — apenas UI e navegacao.
"""

import streamlit as st

from auth import verificar_acesso, sidebar_usuario
from components import titulo_pagina

verificar_acesso()
sidebar_usuario()

st.set_page_config(page_title="Gestao de Comissoes", layout="wide")

titulo_pagina("", "Gestao de Comissoes",
              "Controle de parceiros, carteiras, comissoes e fechamento mensal")

st.markdown(
    '<p style="font-size:0.85rem;color:#888;margin-top:-0.5rem;">'
    "Os valores exibidos sao projecoes dinamicas. "
    "O fechamento oficial ocorre apenas apos a confirmacao da competencia."
    "</p>",
    unsafe_allow_html=True,
)

st.divider()

aba1, aba2, aba3, aba4, aba5 = st.tabs([
    "Dashboard", "Parceiros", "Fechamento", "Historico", "Comissoes Avulsas"
])

with aba1:
    from components.comissoes.dashboard import render as render_dashboard
    render_dashboard()

with aba2:
    from components.comissoes.parceiros import render as render_parceiros
    render_parceiros()

with aba3:
    from components.comissoes.fechamento import render as render_fechamento
    render_fechamento()

with aba4:
    from components.comissoes.historico import render as render_historico
    render_historico()

with aba5:
    from components.comissoes.avulsas import render as render_avulsas
    render_avulsas()