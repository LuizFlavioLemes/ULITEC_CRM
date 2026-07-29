"""
Componente: page_header
=======================

Cabeçalhos padronizados para páginas do CRM.

Nenhuma regra de negócio — apenas interface.

Funções:
    page_header(icone, titulo, descricao="")
        Cabeçalho completo com ícone, título e descrição opcional.
        Exemplo: page_header("📊", "Dashboard", "Visão geral do período")

    section_header(titulo, descricao="")
        Cabeçalho de seção dentro de uma página.
        Exemplo: section_header("Clientes Ativos")

    page_subtitle(texto)
        Subtítulo padronizado (st.subheader).
        Exemplo: page_subtitle("Relatório Gerencial")
"""

import streamlit as st


def page_header(icone: str, titulo: str, descricao: str = ""):
    """
    Cabeçalho completo de página.

    Parâmetros:
        icone: Emoji/ícone da página (ex: "📊", "🎯", "📞")
        titulo: Nome da página
        descricao: Texto opcional exibido abaixo do título

    Exemplo:
        page_header("📊", "Dashboard Comercial", "Indicadores do período")
    """
    st.title(f"{icone} {titulo}")
    if descricao:
        st.markdown(descricao)


def section_header(titulo: str, descricao: str = ""):
    """
    Cabeçalho de seção com st.subheader.

    Parâmetros:
        titulo: Nome da seção
        descricao: Texto opcional exibido como caption

    Exemplo:
        section_header("Clientes Prioritários", "Top 10 por faturamento")
    """
    st.subheader(titulo)
    if descricao:
        st.caption(descricao)


def page_subtitle(texto: str):
    """
    Subtítulo padronizado.

    Parâmetros:
        texto: Texto do subtítulo

    Exemplo:
        page_subtitle("Módulo de Gestão Comercial")
    """
    st.subheader(texto)