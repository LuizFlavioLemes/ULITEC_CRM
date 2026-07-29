"""
Componente: metric_grid
=======================

Grid flexível de métricas/KPIs para dashboards.

Nenhuma regra de negócio — apenas interface.

Funções:
    metric_grid(indicadores, cols=4)
        Linha completa de KPIs padronizados.
        indicadores: lista de dicts com "rotulo", "valor", "delta"(opc), "help"(opc), "icone"(opc)
        Exemplo:
            metric_grid([
                {"rotulo": "Clientes", "valor": 150, "icone": "🏢"},
                {"rotulo": "Receita", "valor": "R$ 1.2M", "delta": "+12%"},
            ], cols=2)

    metric_card(rotulo, valor, delta=None, help_text=None, icone="")
        Card de métrica individual (wrapper de st.metric).
        Exemplo: metric_card("Ticket Médio", "R$ 5.400", delta="+8%", icone="🎫")
"""

import streamlit as st


def metric_card(
    rotulo: str,
    valor,
    delta=None,
    help_text=None,
    icone: str = "",
):
    """
    Card de métrica individual padronizado.

    Parâmetros:
        rotulo: Nome do indicador (ex: "Clientes Ativos")
        valor: Valor do indicador (int, float, str formatada)
        delta: Variação opcional (ex: "+15%")
        help_text: Texto de tooltip opcional
        icone: Emoji opcional para prefixar o rótulo

    Exemplo:
        metric_card("Receita", "R$ 1.2M", delta="+12%",
                    help_text="Faturamento total", icone="📈")
    """
    rotulo_exib = f"{icone} {rotulo}" if icone else rotulo
    st.metric(
        label=rotulo_exib,
        value=valor,
        delta=delta,
        help=help_text,
    )


def metric_grid(indicadores: list, cols: int = 4):
    """
    Linha completa de KPIs padronizados em grid.

    Parâmetros:
        indicadores: Lista de dicionários, cada um com:
            - "rotulo": str (obrigatório)
            - "valor": qualquer (obrigatório)
            - "delta": str (opcional)
            - "help": str (opcional)
            - "icone": str (opcional)
        cols: Número de colunas (default=4)

    Exemplo:
        metric_grid([
            {"rotulo": "Clientes", "valor": 150, "icone": "🏢", "help": "Total de clientes ativos"},
            {"rotulo": "Receita", "valor": "R$ 1.2M", "delta": "+12%"},
            {"rotulo": "OS Abertas", "valor": 45, "icone": "🔧"},
        ], cols=3)

    Limitações:
        - Todos os cards têm a mesma largura (1/cols da tela)
        - Não suporta tooltips customizados por card além do parâmetro help
    """
    if not indicadores:
        return

    colunas = st.columns(cols)
    for i, indicador in enumerate(indicadores):
        with colunas[i % cols]:
            metric_card(
                rotulo=indicador.get("rotulo", ""),
                valor=indicador.get("valor", "-"),
                delta=indicador.get("delta"),
                help_text=indicador.get("help"),
                icone=indicador.get("icone", ""),
            )