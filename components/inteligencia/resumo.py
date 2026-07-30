"""
Componente de Resumo Executivo — Inteligência Comercial.

Bloco 1: Cards superiores clicáveis com indicadores da carteira.

Consome exclusivamente services sem SQL.

Reutiliza:
- components/common/metric_grid.py → metric_grid
- components/common/section.py → section
- services/inteligencia/resumo.py → get_resumo_executivo
- services/inteligencia/clientes.py → get_clientes_esfriando, etc.
"""

from typing import Optional, Callable
import streamlit as st
import pandas as pd

from components.common import metric_grid, section, empty_state
from services.inteligencia_comercial import (
    get_resumo_executivo,
    get_clientes_esfriando,
    get_clientes_esquentando,
    get_clientes_sem_visita,
    get_clientes_sem_faturamento,
    get_preventivas_vencidas,
)


def _format_num(valor: int) -> str:
    """Formata número inteiro para exibição."""
    return f"{valor:,}".replace(",", ".")


def _card_clicavel(rotulo: str, valor: int, delta: Optional[str], icone: str, help_text: str, key: str) -> bool:
    """
    Renderiza um card de métrica clicável.
    Retorna True se o card foi clicado.
    """
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.metric(
            label=f"{icone} {rotulo}",
            value=_format_num(valor),
            delta=delta,
            help=help_text,
        )
    with col3:
        clicked = st.button("📋", key=key, help="Clique para ver lista")
    return clicked


def exibir_resumo_executivo(
    unidade: Optional[str] = None,
    on_card_click: Optional[Callable] = None,
) -> dict:
    """
    Renderiza cards do Resumo Executivo.

    Cada card mostra um indicador e é clicável.
    Quando clicado, retorna o identificador do card via callback.

    Retorna dict com os indicadores atuais.
    """
    indicadores = get_resumo_executivo(unidade)
    total_clientes = indicadores.get("total_clientes", 0)

    # Cache preventivas para usar aqui
    df_preventivas = get_preventivas_vencidas(unidade)
    total_preventivas = len(df_preventivas)

    st.markdown("### 📊 Resumo Executivo")
    st.caption("Visão geral da sua carteira de clientes")
    st.markdown("")

    # Grid 3x2 de cards
    # Linha 1: 3 cards
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="🥶 Clientes Esfriando",
            value=_format_num(indicadores.get("clientes_esfriando", 0)),
            help="Clientes com queda de faturamento >30%, queda de OS >30% ou sem visita >120 dias",
        )
        if st.button("Ver lista", key="btn_esfriando", use_container_width=True):
            if on_card_click:
                on_card_click("esfriando")

    with col2:
        st.metric(
            label="🔥 Clientes Esquentando",
            value=_format_num(indicadores.get("clientes_esquentando", 0)),
            help="Clientes com crescimento de faturamento >20% ou OS >20%",
        )
        if st.button("Ver lista", key="btn_esquentando", use_container_width=True):
            if on_card_click:
                on_card_click("esquentando")

    with col3:
        st.metric(
            label="🚫 Sem Faturamento",
            value=_format_num(indicadores.get("clientes_sem_faturamento", 0)),
            help="Clientes ativos sem faturamento nos últimos 12 meses",
        )
        if st.button("Ver lista", key="btn_sem_fat", use_container_width=True):
            if on_card_click:
                on_card_click("sem_faturamento")

    # Linha 2: 3 cards
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="👁️ Sem Visita",
            value=_format_num(indicadores.get("clientes_sem_visita", 0)),
            help="Clientes com última visita há >90 dias ou nunca visitados",
        )
        if st.button("Ver lista", key="btn_sem_visita", use_container_width=True):
            if on_card_click:
                on_card_click("sem_visita")

    with col2:
        st.metric(
            label="🛡️ Preventivas Vencidas",
            value=_format_num(total_preventivas),
            help="Clientes com última preventiva (OS faturada/expedida) há mais de 2 anos",
        )
        if st.button("Ver lista", key="btn_preventivas", use_container_width=True):
            if on_card_click:
                on_card_click("preventivas")

    with col3:
        st.metric(
            label="🏆 Clientes Prioridade A",
            value=_format_num(indicadores.get("clientes_esquentando", 0) + indicadores.get("clientes_esfriando", 0)),
            help="Soma de clientes esquentando + esfriando (maior potencial de atenção)",
        )
        if st.button("Ver lista", key="btn_prioridade_a", use_container_width=True):
            if on_card_click:
                on_card_click("prioritarios")

    st.divider()
    return indicadores