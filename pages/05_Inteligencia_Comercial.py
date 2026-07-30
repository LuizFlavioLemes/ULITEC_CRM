"""
Página: Inteligência Comercial — ULITEC CRM
============================================

Módulo principal de inteligência de negócio.
Responde: "Qual cliente visitar hoje?", "Quem está esfriando?",
"Quem voltou a comprar?", "Onde existe dinheiro parado?"

Arquitetura:
    Pages → Components → Services → Database

NENHUM SQL nesta página.
Toda informação vem de Services.

Reutiliza:
    - components/common/ (page_header, section, metric_grid, etc.)
    - components/inteligencia/ (resumo, painel_listas)
    - services/inteligencia_comercial/ (todos os services existentes)
"""

import streamlit as st
from typing import Optional

from components.common import page_header, section
from components.inteligencia import (
    exibir_resumo_executivo,
    exibir_prioritarios,
    exibir_esfriando,
    exibir_esquentando,
    exibir_sem_faturamento,
    exibir_sem_visita,
    exibir_preventivas,
    exibir_parque_mitsubishi,
    exibir_top_faturamento,
)
from services.inteligencia.prioridade import get_estados_disponiveis, get_cidades_disponiveis


# ── Funções auxiliares ──

def _init_session_state():
    """Inicializa variáveis de sessão."""
    if "secao_ativa" not in st.session_state:
        st.session_state.secao_ativa = "resumo"
    if "filtro_estado" not in st.session_state:
        st.session_state.filtro_estado = "Todos"
    if "filtro_cidade" not in st.session_state:
        st.session_state.filtro_cidade = "Todas"
    if "filtro_classe" not in st.session_state:
        st.session_state.filtro_classe = "Todas"
    if "filtro_responsavel" not in st.session_state:
        st.session_state.filtro_responsavel = "Todos"
    if "filtro_segmento" not in st.session_state:
        st.session_state.filtro_segmento = "Todos"


def _on_card_click(secao: str):
    """Callback para clique nos cards do resumo."""
    st.session_state.secao_ativa = secao


def _render_filtros_globais():
    """
    Bloco 10: Filtros Globais.
    Estado, Cidade, Classe ABC, Responsável, Segmento.
    Aplicam em TODOS os blocos da página.
    """
    with st.container():
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            estados = ["Todos"] + get_estados_disponiveis()
            st.selectbox(
                "Estado",
                options=estados,
                key="filtro_estado",
                index=0,
            )

        with col2:
            cidades = ["Todas"] + get_cidades_disponiveis()
            st.selectbox(
                "Cidade",
                options=cidades,
                key="filtro_cidade",
                index=0,
            )

        with col3:
            classes = ["Todas", "A", "B", "C", "D"]
            st.selectbox(
                "Classe ABC",
                options=classes,
                key="filtro_classe",
                index=0,
            )

        with col4:
            responsaveis = ["Todos"]
            st.selectbox(
                "Responsável",
                options=responsaveis,
                key="filtro_responsavel",
                index=0,
            )

        with col5:
            segmentos = ["Todos"]
            st.selectbox(
                "Segmento",
                options=segmentos,
                key="filtro_segmento",
                index=0,
            )

    def _limpar_filtros():
        for key in ["filtro_estado", "filtro_cidade", "filtro_classe", "filtro_responsavel", "filtro_segmento"]:
            if key in st.session_state:
                del st.session_state[key]

    if st.button("🔄 Limpar Filtros", use_container_width=False):
        _limpar_filtros()
        st.rerun()

    st.divider()


def _get_filtros() -> dict:
    """Retorna dict com filtros atuais."""
    estado = st.session_state.get("filtro_estado", "Todos")
    cidade = st.session_state.get("filtro_cidade", "Todas")
    classe = st.session_state.get("filtro_classe", "Todas")
    return {
        "estado": estado if estado != "Todos" else None,
        "cidade": cidade if cidade != "Todas" else None,
        "classe_abc": classe if classe != "Todas" else None,
    }


# ── Página principal ──

def main():
    _init_session_state()

    page_header(
        icone="🧠",
        titulo="Inteligência Comercial",
        descricao="Descubra onde investir seu tempo: clientes prioritários, esfriando, esquentando e muito mais.",
    )

    section("🔍 Filtros", "Aplicados em toda a página")
    _render_filtros_globais()

    unidade = st.session_state.get("unidade_ativa")
    if unidade == "GRUPO":
        unidade = None

    indicadores = exibir_resumo_executivo(
        unidade=unidade,
        on_card_click=_on_card_click,
    )

    filtros = _get_filtros()

    # ── Seletor de seção ativa ──
    secao_ativa = st.session_state.get("secao_ativa", "resumo")

    # ── Renderizar bloco ativo ──
    if secao_ativa == "resumo" or secao_ativa == "prioritarios":
        exibir_prioritarios(
            unidade=unidade,
            estado=filtros["estado"],
            cidade=filtros["cidade"],
            classe_abc=filtros["classe_abc"],
        )
        st.markdown("---")

    if secao_ativa == "esfriando":
        exibir_esfriando(
            unidade=unidade,
            estado=filtros["estado"],
            cidade=filtros["cidade"],
        )
        st.markdown("---")

    if secao_ativa == "esquentando":
        exibir_esquentando(
            unidade=unidade,
            estado=filtros["estado"],
            cidade=filtros["cidade"],
        )
        st.markdown("---")

    if secao_ativa == "sem_faturamento":
        exibir_sem_faturamento(
            unidade=unidade,
            estado=filtros["estado"],
            cidade=filtros["cidade"],
        )
        st.markdown("---")

    if secao_ativa == "sem_visita":
        exibir_sem_visita(
            unidade=unidade,
            estado=filtros["estado"],
            cidade=filtros["cidade"],
        )
        st.markdown("---")

    if secao_ativa == "preventivas":
        exibir_preventivas(
            unidade=unidade,
            estado=filtros["estado"],
            cidade=filtros["cidade"],
        )
        st.markdown("---")

    # ── Blocos adicionais (sempre renderizados) ──
    with st.expander("🏭 Parque Mitsubishi", expanded=False):
        exibir_parque_mitsubishi(
            unidade=unidade,
            estado=filtros["estado"],
            cidade=filtros["cidade"],
        )

    with st.expander("💰 Top Faturamento", expanded=False):
        exibir_top_faturamento(
            unidade=unidade,
            estado=filtros["estado"],
            cidade=filtros["cidade"],
        )

    # ── Footer ──
    st.divider()
    st.caption(
        "🧠 Inteligência Comercial v1.7 | "
        "Dados atualizados em tempo real | "
        "Os scores e prioridades são calculados com base em múltiplos fatores "
        "(faturamento, máquinas, classe ABC, visitas, interações, preventivas, oportunidades)"
    )


if __name__ == "__main__":
    main()