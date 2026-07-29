"""
Componente: section
===================

Seções com título, subtítulo e divisor visual para organizar páginas.

Nenhuma regra de negócio — apenas interface.

Funções:
    section(titulo, descricao="")
        Seção completa com título (h3), descrição opcional e divisor.
        Exemplo: section("Indicadores", "KPIs do período selecionado")

    subsection(titulo)
        Subseção com st.subheader.
        Exemplo: subsection("Clientes Prioritários")

    divider()
        Divisor padronizado (st.divider).
        Exemplo: divider()
"""

import streamlit as st


def section(titulo: str, descricao: str = ""):
    """
    Seção completa com título, descrição opcional e divisor.

    Parâmetros:
        titulo: Título da seção (renderizado como h3)
        descricao: Texto descritivo opcional (renderizado como caption)

    Exemplo:
        section("Indicadores de Vendas", "Últimos 30 dias")
    """
    st.markdown(f"### {titulo}")
    if descricao:
        st.caption(descricao)
    st.divider()


def subsection(titulo: str):
    """
    Subseção dentro de uma seção.

    Parâmetros:
        titulo: Texto do subtítulo

    Exemplo:
        subsection("Análise por Região")
    """
    st.subheader(titulo)


def divider():
    """
    Divisor visual padronizado.

    Equivalente a st.divider().

    Exemplo:
        divider()
    """
    st.divider()