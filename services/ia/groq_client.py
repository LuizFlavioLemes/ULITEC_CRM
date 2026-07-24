"""
Integração com API Groq.
Modelos suportados: llama-3.3-70b-versatile, llama-3.1-8b-instant, mixtral-8x7b-32768

PLANO GRATUITO:
  - Sem limites restritivos de cota
  - Respostas rápidas (LPU)
  - API compatível com OpenAI
"""

import time
from groq import Groq

PRECOS = {
    "llama-3.3-70b-versatile": {"input": 0.59 / 1_000_000, "output": 0.79 / 1_000_000},
    "llama-3.1-8b-instant": {"input": 0.05 / 1_000_000, "output": 0.08 / 1_000_000},
    "llama3-70b-8192": {"input": 0.59 / 1_000_000, "output": 0.79 / 1_000_000},
    "mixtral-8x7b-32768": {"input": 0.24 / 1_000_000, "output": 0.24 / 1_000_000},
    "gemma2-9b-it": {"input": 0.20 / 1_000_000, "output": 0.20 / 1_000_000},
}

def testar_conexao(api_key: str) -> tuple:
    """
    Testa se a chave de API é válida.

    Returns:
        (sucesso: bool, mensagem: str)
    """
    try:
        client = Groq(api_key=api_key)
        # Tenta listar modelos para validar a chave
        modelos = client.models.list()
        return True, f"✅ Conexão Groq OK. {len(modelos.data)} modelos disponíveis."
    except Exception as e:
        return False, f"❌ Falha na conexão Groq: {str(e)}"

def gerar_relatorio(
    api_key: str,
    modelo: str,
    prompt_sistema: str,
    prompt_usuario: str,
    timeout: int = 120,
) -> dict:
    """
    Chama a API Groq para gerar um relatório.

    Args:
        api_key: Chave da API Groq
        modelo: Nome do modelo (ex: llama-3.1-8b-instant)
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
    if not modelo:
        modelo = "llama-3.1-8b-instant"

    precos = PRECOS.get(modelo, {"input": 0.0, "output": 0.0})

    try:
        client = Groq(api_key=api_key, timeout=timeout)

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

        prompt_tokens = resposta.usage.prompt_tokens if resposta.usage else 0
        completion_tokens = resposta.usage.completion_tokens if resposta.usage else 0
        custo = (
            prompt_tokens * precos["input"]
            + completion_tokens * precos["output"]
        )

        conteudo = resposta.choices[0].message.content if resposta.choices else ""

        return {
            "conteudo": conteudo,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "tempo_execucao": round(tempo_total, 2),
            "custo": round(custo, 6),
            "sucesso": True,
            "erro": None,
            "modelo_utilizado": modelo,
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
            "modelo_utilizado": modelo,
        }