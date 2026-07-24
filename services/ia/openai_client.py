"""
Integração com API OpenAI.
Modelos suportados: gpt-4o, gpt-4o-mini
"""

import time
from openai import OpenAI

PRECOS = {
    "gpt-4o": {"input": 2.50 / 1_000_000, "output": 10.00 / 1_000_000},
    "gpt-4o-mini": {"input": 0.15 / 1_000_000, "output": 0.60 / 1_000_000},
}

def testar_conexao(api_key: str) -> tuple:
    """
    Testa se a chave de API é válida listando modelos.

    Returns:
        (sucesso: bool, mensagem: str)
    """
    try:
        client = OpenAI(api_key=api_key, timeout=10)
        client.models.list()
        return True, "✅ Conexão OK"
    except Exception as e:
        return False, f"❌ Falha na conexão: {str(e)}"

def gerar_relatorio(
    api_key: str,
    modelo: str,
    prompt_sistema: str,
    prompt_usuario: str,
    timeout: int = 120,
) -> dict:
    """
    Chama a API OpenAI para gerar um relatório.

    Args:
        api_key: Chave da API OpenAI
        modelo: gpt-4o ou gpt-4o-mini
        prompt_sistema: Instruções de sistema
        prompt_usuario: Contexto/dados do cliente
        timeout: Timeout em segundos

    Returns:
        dict com:
            - conteudo (str): texto gerado
            - prompt_tokens (int)
            - completion_tokens (int)
            - custo (float)
            - sucesso (bool)
            - erro (str ou None)
    """
    if modelo not in PRECOS:
        return {
            "conteudo": "",
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "custo": 0.0,
            "sucesso": False,
            "erro": f"Modelo '{modelo}' não suportado.",
        }

    try:
        client = OpenAI(api_key=api_key, timeout=timeout)

        inicio = time.time()

        resposta = client.chat.completions.create(
            model=modelo,
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": prompt_usuario},
            ],
            temperature=0.3,
            max_tokens=4000,
        )

        tempo_total = time.time() - inicio

        prompt_tokens = resposta.usage.prompt_tokens
        completion_tokens = resposta.usage.completion_tokens
        custo = (
            prompt_tokens * PRECOS[modelo]["input"]
            + completion_tokens * PRECOS[modelo]["output"]
        )

        return {
            "conteudo": resposta.choices[0].message.content,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "tempo_execucao": round(tempo_total, 2),
            "custo": round(custo, 6),
            "sucesso": True,
            "erro": None,
        }

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