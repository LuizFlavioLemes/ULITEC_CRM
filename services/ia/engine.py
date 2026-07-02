"""
Orquestrador principal do módulo IA.
Coordena: coleta de dados → montagem de prompt → chamada OpenAI → salvamento de logs.
"""

import sqlite3
from datetime import datetime

from services.ia.data_collector import (
    coletar_cliente,
    coletar_faturamento,
    coletar_os,
    coletar_oportunidades,
    coletar_mitsubishi,
    coletar_interacoes,
)
from services.ia.prompt_builder import PROMPT_SISTEMA, montar_contexto_cliente
from services.ia.ia_client import gerar_relatorio

from config import DB_PATH


def _salvar_log(
    cliente_id: int,
    modelo: str,
    prompt_tokens: int,
    completion_tokens: int,
    tempo_execucao: float,
    custo: float,
):
    """Salva o log da execução na tabela relatorios_ia."""
    conn = sqlite3.connect(str(DB_PATH))
    try:
        conn.execute(
            """
            INSERT INTO relatorios_ia
                (cliente_id, modelo, prompt_tokens, completion_tokens,
                 tempo_execucao, custo_estimado, criado_em)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                cliente_id,
                modelo,
                prompt_tokens,
                completion_tokens,
                tempo_execucao,
                custo,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def gerar_relatorio_tecnico(
    prompt_sistema: str,
    prompt_usuario: str,
    api_key: str = "",
    modelo: str = "",
    timeout: int = 120,
) -> dict:
    """
    Gera relatório técnico usando o provider configurado (via ia_client).

    Args:
        prompt_sistema: Instruções de sistema (ex: PROMPT_SISTEMA_ULITEC)
        prompt_usuario: Contexto/dados para o relatório
        api_key: Chave da API (opcional, usa .env se vazio)
        modelo: Nome do modelo (opcional, usa .env se vazio)
        timeout: Timeout em segundos

    Returns:
        dict com: conteudo, prompt_tokens, completion_tokens, custo, sucesso, erro
    """
    return gerar_relatorio(
        api_key=api_key,
        modelo=modelo,
        prompt_sistema=prompt_sistema,
        prompt_usuario=prompt_usuario,
        timeout=timeout,
    )


def gerar_analise_cliente(
    cliente_id: int,
    prompt_sistema: str = None,
) -> dict:
    """
    Gera uma análise completa de cliente usando IA.
    Usa o provider configurado no .env (Groq por padrão).

    Args:
        cliente_id: ID do cliente no banco

    Returns:
        dict com:
            - sucesso (bool)
            - conteudo (str): relatório em Markdown
            - prompt_tokens (int)
            - completion_tokens (int)
            - tempo_execucao (float)
            - custo (float)
            - erro (str ou None)
    """
    try:
        # 1. Coleta dados
        cliente = coletar_cliente(cliente_id)
        faturamento = coletar_faturamento(cliente_id)
        os_data = coletar_os(cliente_id)
        oportunidades = coletar_oportunidades(cliente_id)
        mitsubishi = coletar_mitsubishi(cliente_id)
        interacoes = coletar_interacoes(cliente_id)

        # 2. Monta contexto
        contexto = montar_contexto_cliente(
            cliente, faturamento, os_data, oportunidades, mitsubishi, interacoes
        )

        # 3. Chama IA (provider configurado no .env)
        prompt_final = prompt_sistema if prompt_sistema else PROMPT_SISTEMA
        resultado = gerar_relatorio(
            prompt_sistema=prompt_final,
            prompt_usuario=contexto,
        )

        # 4. Salva log
        if resultado["sucesso"]:
            from services.ia.ia_client import _obter_config
            config = _obter_config()
            _salvar_log(
                cliente_id=cliente_id,
                modelo=config.get("modelo", "desconhecido"),
                prompt_tokens=resultado["prompt_tokens"],
                completion_tokens=resultado["completion_tokens"],
                tempo_execucao=resultado["tempo_execucao"],
                custo=resultado["custo"],
            )

        return resultado

    except Exception as e:
        return {
            "conteudo": "",
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "tempo_execucao": 0.0,
            "custo": 0.0,
            "sucesso": False,
            "erro": str(e),
        }