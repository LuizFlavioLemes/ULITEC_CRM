"""
Componente: loading
===================

Wrappers de loading/spinner padronizados.

Nenhuma regra de negócio — apenas interface.

Funções:
    loading_wrapper(func, *args, mensagem="Carregando...", **kwargs)
        Executa uma função com indicador de carregamento.
        Exemplo: dados = loading_wrapper(buscar_dados, cliente_id=123)

    spinner_context(mensagem="Carregando...")
        Context manager para blocos de código com spinner.
        Exemplo:
            with spinner_context("Calculando scores..."):
                df = calcular_score()
                df = enriquecer(df)
"""

import streamlit as st


def loading_wrapper(func, *args, mensagem: str = "Carregando...", **kwargs):
    """
    Executa uma função com indicador de carregamento (spinner).

    Útil para operações demoradas como consultas ao banco,
    processamento de dados ou chamadas de API.

    Parâmetros:
        func: Função a ser executada
        *args: Argumentos posicionais para a função
        mensagem: Texto exibido durante o carregamento
        **kwargs: Argumentos nomeados para a função

    Retorna:
        O retorno da função executada

    Exemplo:
        df = loading_wrapper(
            pd.read_sql_query,
            "SELECT * FROM clientes",
            conn,
            mensagem="Buscando clientes..."
        )

    Limitações:
        - Não captura exceções — erros da função propagam normalmente
        - A função é executada de forma síncrona (bloqueante)
    """
    with st.spinner(mensagem):
        return func(*args, **kwargs)


class spinner_context:
    """
    Context manager para blocos de código com indicador de carregamento.

    Use com 'with' para envolver múltiplas operações em um único spinner.

    Parâmetros:
        mensagem: Texto exibido durante o carregamento

    Exemplo:
        with spinner_context("Processando relatório..."):
            df_vendas = carregar_vendas()
            df_clientes = carregar_clientes()
            relatorio = gerar_relatorio(df_vendas, df_clientes)
    """

    def __init__(self, mensagem: str = "Carregando..."):
        self.mensagem = mensagem

    def __enter__(self):
        self.spinner = st.spinner(self.mensagem)
        self.spinner.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.spinner.__exit__(exc_type, exc_val, exc_tb)