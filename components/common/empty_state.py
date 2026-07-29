"""
Componente: empty_state
========================

Estados vazios padronizados (sem dados, sem resultados).

Nenhuma regra de negócio — apenas interface.

Funções:
    empty_state(mensagem="Nenhum dado encontrado", icone="📭")
        Estado vazio para áreas sem dados.
        Exemplo: empty_state("Nenhum cliente cadastrado", icone="🏢")

    no_results(mensagem="Nenhum resultado encontrado")
        Estado vazio para busca sem resultados.
        Exemplo: no_results("Nenhum cliente encontrado com este filtro")
"""

import streamlit as st


def empty_state(mensagem: str = "Nenhum dado encontrado", icone: str = "📭"):
    """
    Estado vazio padronizado para quando não há dados.

    Exibe uma mensagem de sucesso (st.success) com o ícone e texto.

    Parâmetros:
        mensagem: Texto da mensagem (ex: "Nenhum cliente cadastrado")
        icone: Emoji representando o contexto (ex: "🏢", "📊", "📞")

    Exemplo:
        empty_state("Nenhuma pendência para hoje", icone="📌")
    """
    st.success(f"{icone} {mensagem}")


def no_results(mensagem: str = "Nenhum resultado encontrado"):
    """
    Estado vazio padronizado para filtros/busca sem resultados.

    Exibe uma mensagem informativa (st.info).

    Parâmetros:
        mensagem: Texto da mensagem

    Exemplo:
        no_results("Nenhum cliente encontrado com os filtros atuais")
    """
    st.info(mensagem)