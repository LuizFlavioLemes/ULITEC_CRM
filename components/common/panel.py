"""
Componente: panel
=================

Painéis com borda, título e ícone para agrupar conteúdo.

Nenhuma regra de negócio — apenas interface.

Funções:
    panel(content, titulo="", icone="")
        Painel genérico com borda e conteúdo.
        Exemplo: panel("Texto aqui", titulo="Detalhes", icone="📋")

    info_panel(mensagem, titulo="")
        Painel informativo (st.info dentro de container com borda).
        Exemplo: info_panel("Dados atualizados em tempo real")

    warning_panel(mensagem, titulo="")
        Painel de alerta/atenção.
        Exemplo: warning_panel("Preencha todos os campos obrigatórios")
"""

import streamlit as st


def panel(content, titulo: str = "", icone: str = ""):
    """
    Painel genérico com borda. Aceita qualquer conteúdo (string ou callable).

    Parâmetros:
        content: Conteúdo a exibir. Pode ser:
            - str: renderiza com st.markdown
            - callable: executa a função dentro do container
        titulo: Título opcional do painel
        icone: Emoji opcional para o título

    Exemplo:
        panel("Conteúdo simples", titulo="Informações", icone="ℹ️")

        with panel("", titulo="Relatório", icone="📊"):
            st.write("Conteúdo complexo aqui")
    """
    titulo_exib = f"{icone} {titulo}" if icone else titulo

    with st.container(border=True):
        if titulo_exib:
            st.markdown(f"**{titulo_exib}**")
        if callable(content):
            content()
        elif content:
            st.markdown(content)


def info_panel(mensagem: str, titulo: str = ""):
    """
    Painel informativo.

    Parâmetros:
        mensagem: Texto informativo
        titulo: Título opcional do painel

    Exemplo:
        info_panel("Módulo em desenvolvimento", titulo="Aviso")
    """
    titulo_exib = f"**{titulo}**  \n" if titulo else ""
    with st.container(border=True):
        st.info(f"{titulo_exib}{mensagem}")


def warning_panel(mensagem: str, titulo: str = ""):
    """
    Painel de alerta/atenção.

    Parâmetros:
        mensagem: Texto de alerta
        titulo: Título opcional

    Exemplo:
        warning_panel("Campos com * são obrigatórios", titulo="Atenção")
    """
    titulo_exib = f"**{titulo}**  \n" if titulo else ""
    with st.container(border=True):
        st.warning(f"{titulo_exib}{mensagem}")