"""
Componente: toolbar
===================

Barra de ações/botões padronizada.

Nenhuma regra de negócio — apenas interface.

Funções:
    toolbar(botoes, cols=None)
        Barra de botões padronizada em linha.
        botoes: lista de dicts com "rotulo", "tipo" (primary/secondary), "key"
        Exemplo:
            clicado = toolbar([
                {"rotulo": "💾 Salvar", "tipo": "primary", "key": "btn_salvar"},
                {"rotulo": "↩️ Cancelar", "key": "btn_cancelar"},
            ])

    action_button(rotulo, tipo="secondary", key=None, largura="stretch")
        Botão de ação individual padronizado.
        Exemplo: action_button("📥 Exportar", key="btn_export")
"""

import streamlit as st


def action_button(rotulo: str, tipo: str = "secondary", key=None, largura="stretch"):
    """
    Botão de ação individual padronizado.

    Parâmetros:
        rotulo: Texto do botão (pode incluir emoji)
        tipo: "primary" | "secondary" (default="secondary")
        key: Chave única para o botão (obrigatório para múltiplos botões)
        largura: Largura do botão (default="stretch")

    Retorna:
        bool — True se clicado

    Exemplo:
        if action_button("📥 Exportar CSV", key="export_csv"):
            st.info("Exportando...")
    """
    type_val = "primary" if tipo == "primary" else "secondary"
    return st.button(
        rotulo,
        type=type_val,
        use_container_width=(largura == "stretch"),
        key=key,
    )


def toolbar(botoes: list, cols: int = None):
    """
    Barra de botões padronizada em linha.

    Parâmetros:
        botoes: Lista de dicionários, cada um com:
            - "rotulo": str (obrigatório)
            - "tipo": "primary" | "secondary" (opcional, default="secondary")
            - "key": str (opcional, mas recomendado para evitar warning do Streamlit)
        cols: Número de colunas (opcional — calculado automaticamente se não informado)

    Retorna:
        str — Rótulo do botão clicado, ou None se nenhum

    Exemplo:
        acao = toolbar([
            {"rotulo": "💾 Salvar", "tipo": "primary", "key": "save"},
            {"rotulo": "🗑 Excluir", "tipo": "secondary", "key": "delete"},
        ])
        if acao == "💾 Salvar":
            salvar_dados()

    Limitações:
        - Botões não podem ter o mesmo rótulo (use keys diferentes)
    """
    if not botoes:
        return None

    if cols is None:
        cols = len(botoes)

    colunas = st.columns(cols)
    resultado = None

    for i, botao in enumerate(botoes):
        with colunas[i % cols]:
            rotulo = botao.get("rotulo", "Botão")
            tipo = botao.get("tipo", "secondary")
            key = botao.get("key", f"tb_{i}_{rotulo[:10]}")

            if st.button(
                rotulo,
                type="primary" if tipo == "primary" else "secondary",
                use_container_width=True,
                key=key,
            ):
                resultado = rotulo

    return resultado