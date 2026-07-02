"""
Abstração de cliente de IA.
Seleciona o provider (Groq, Gemini, OpenAI) baseado na variável de ambiente IA_PROVIDER.

Uso:
    IA_PROVIDER=groq    (default) — usa Groq (llama-3.3-70b-versatile", "llama-3.1-8b-instant, gratuito e rápido)
    IA_PROVIDER=gemini  (fallback)
    IA_PROVIDER=openai  (fallback)
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ── Localiza .env na raiz do projeto de forma absoluta ──
base_dir = Path(__file__).resolve().parent  # services/ia/
env_path = base_dir.parent.parent / '.env'  # sobe até raiz do projeto

# Se não achar, tenta diretório atual (fallback)
if not env_path.exists():
    env_path = base_dir.parent / '.env'

load_dotenv(dotenv_path=env_path, override=True)

def _obter_config() -> dict:
    """Retorna config do provider baseado em .env e defaults."""
    provider = os.getenv("IA_PROVIDER", "groq").strip().lower()

    config = {
        "provider": provider,
    }

    if provider == "groq":
        config["api_key"] = os.getenv("GROQ_API_KEY", "")
        config["modelo"] = os.getenv("GROQ_MODEL", "")
    elif provider == "gemini":
        config["api_key"] = os.getenv("GEMINI_API_KEY", "")
        config["modelo"] = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    elif provider == "openai":
        config["api_key"] = os.getenv("OPENAI_API_KEY", "")
        config["modelo"] = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    else:
        raise ValueError(f"IA_PROVIDER inválido: '{provider}'. Use 'groq', 'gemini' ou 'openai'.")

    return config


def gerar_relatorio(
    api_key: str = "",
    modelo: str = "",
    prompt_sistema: str = "",
    prompt_usuario: str = "",
    timeout: int = 120,
) -> dict:
    """
    Gera relatório usando o provider configurado em IA_PROVIDER.

    Se api_key ou modelo forem fornecidos como string vazia,
    usa os valores de .env ou defaults.

    Args:
        api_key: Chave da API (opcional, usa .env se vazio)
        modelo: Nome do modelo (opcional, usa .env se vazio)
        prompt_sistema: Instruções de sistema
        prompt_usuario: Contexto/dados
        timeout: Timeout em segundos

    Returns:
        dict com: conteudo, prompt_tokens, completion_tokens,
                  custo, sucesso, erro
    """
    config = _obter_config()
    provider = config["provider"]

    api_key = api_key or config["api_key"]
    modelo = modelo or config["modelo"]

    # ── Validação de isolamento: garante que o modelo seja compatível com o provider ──
    # Se IA_PROVIDER=groq e o modelo parece ser do Gemini, retorna erro imediato
    MODELOS_GEMINI = {"gemini-2.0-flash", "gemini-2.0-pro", "gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.5-flash-lite"}
    MODELOS_OPENAI = {"gpt-4o", "gpt-4o-mini"}

    if provider == "gemini" and modelo not in MODELOS_GEMINI:
        return {
            "conteudo": "",
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "custo": 0.0,
            "sucesso": False,
            "erro": (
                f"Modelo '{modelo}' incompatível com o provider GEMINI. "
                f"Verifique GEMINI_MODEL no .env.\n"
                f"Modelos GEMINI disponíveis: {', '.join(sorted(MODELOS_GEMINI))}"
            ),
        }
    if provider == "openai" and modelo not in MODELOS_OPENAI:
        return {
            "conteudo": "",
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "custo": 0.0,
            "sucesso": False,
            "erro": (
                f"Modelo '{modelo}' incompatível com o provider OPENAI. "
                f"Verifique OPENAI_MODEL no .env.\n"
                f"Modelos OPENAI disponíveis: {', '.join(sorted(MODELOS_OPENAI))}"
            ),
        }

    if provider == "groq":
        from services.ia.groq_client import gerar_relatorio as _groq_gerar
        return _groq_gerar(
            api_key=api_key,
            modelo=modelo,
            prompt_sistema=prompt_sistema,
            prompt_usuario=prompt_usuario,
            timeout=timeout,
        )
    elif provider == "gemini":
        from services.ia.gemini_client import gerar_relatorio as _gemini_gerar
        return _gemini_gerar(
            api_key=api_key,
            modelo=modelo,
            prompt_sistema=prompt_sistema,
            prompt_usuario=prompt_usuario,
            timeout=timeout,
        )
    elif provider == "openai":
        from services.ia.openai_client import gerar_relatorio as _openai_gerar
        return _openai_gerar(
            api_key=api_key,
            modelo=modelo,
            prompt_sistema=prompt_sistema,
            prompt_usuario=prompt_usuario,
            timeout=timeout,
        )

    return {
        "conteudo": "",
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "custo": 0.0,
        "sucesso": False,
        "erro": f"Provider '{provider}' não implementado.",
    }
