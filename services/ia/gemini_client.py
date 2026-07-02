"""
Integração com API Google Gemini.
Modelos suportados: gemini-2.0-flash, gemini-1.5-flash (gratuitos),
                    gemini-2.0-pro, gemini-1.5-pro (pagos)

PLANO GRATUITO (2026):
  - Modelos: gemini-2.0-flash, gemini-1.5-flash
  - Limite: ~1500 requisições/dia, 30 requisições/minuto
  - Se bater o limite, aguarde ~24h para reset automático
  - Crie um novo projeto no AI Studio para obter nova cota
"""

import time
import random
import google.generativeai as genai

# Estimativa de custo por caractere (USD, aproximado)
# Gemini 2.0 Flash: $0.10/1M caracteres input, $0.40/1M output
# Gemini 1.5 Flash: $0.075/1M caracteres input, $0.30/1M output
PRECOS = {
    "gemini-2.0-flash": {"input": 0.10 / 1_000_000, "output": 0.40 / 1_000_000},
    "gemini-2.0-pro": {"input": 2.00 / 1_000_000, "output": 8.00 / 1_000_000},
    "gemini-1.5-flash": {"input": 0.075 / 1_000_000, "output": 0.30 / 1_000_000},
    "gemini-1.5-pro": {"input": 1.25 / 1_000_000, "output": 5.00 / 1_000_000},
}

# Mapeamento para nomes da API Gemini
MODELOS_API = {
    "gemini-2.0-flash": "gemini-2.0-flash",
    "gemini-2.0-pro": "gemini-2.0-pro-exp-02-05",
    "gemini-1.5-flash": "gemini-1.5-flash",
    "gemini-1.5-pro": "gemini-1.5-pro",
}

# Modelos gratuitos disponíveis (para fallback automático)
MODELOS_GRATUITOS = ["gemini-2.0-flash", "gemini-1.5-flash"]


def _extrair_tempo_espera(erro: str) -> float:
    """
    Tenta extrair o tempo de espera recomendado do erro 429.
    Ex: 'retry_delay { seconds: 33 }' -> 33.0
    """
    import re
    match = re.search(r'seconds:\s*([\d.]+)', str(erro))
    if match:
        return float(match.group(1))
    return 0.0


def _eh_erro_quota(erro: str) -> bool:
    """Verifica se o erro é relacionado a cota/limite (429)."""
    erro_lower = str(erro).lower()
    return any(
        termo in erro_lower
        for termo in [
            "429",
            "quota exceeded",
            "quota",
            "rate limit",
            "resource exhausted",
            "depleted",
            "free_tier_requests",
            "limit: 0",
        ]
    )


def testar_conexao(api_key: str) -> tuple:
    """
    Testa se a chave de API é válida listando modelos.

    Returns:
        (sucesso: bool, mensagem: str)
    """
    try:
        genai.configure(api_key=api_key)
        modelos = list(genai.list_models())
        # Filtra apenas modelos de geração disponíveis
        modelos_gratis = [
            m.name for m in modelos
            if "flash" in m.name.lower() and "generateContent" in str(m.supported_generation_methods)
        ]
        msg = f"✅ Conexão Gemini OK. {len(modelos)} modelos encontrados."
        if modelos_gratis:
            msg += f"\n   Modelos Flash disponíveis: {', '.join(sorted(set(modelos_gratis))[:3])}"
        return True, msg
    except Exception as e:
        erro = str(e)
        if _eh_erro_quota(erro):
            return False, (
                "❌ Cota do Gemini esgotada (429).\n\n"
                "Soluções:\n"
                "1. Crie um NOVO PROJETO gratuito no Google AI Studio:\n"
                "   https://aistudio.google.com/app/apikey\n"
                "2. Gere uma nova API Key e atualize no .env\n"
                "3. Ou configure IA_PROVIDER=openai com uma chave da OpenAI\n\n"
                "⚠️ O modelo gemini-2.0-flash no plano gratuito tem "
                "~1500 req/dia. Se excedeu, aguarde 24h."
            )
        return False, f"❌ Falha na conexão Gemini: {erro}"


def gerar_relatorio(
    api_key: str,
    modelo: str,
    prompt_sistema: str,
    prompt_usuario: str,
    timeout: int = 120,
    max_tentativas: int = 3,
) -> dict:
    """
    Chama a API Google Gemini para gerar um relatório.
    Inclui retry com backoff exponencial para erros de cota (429).

    Args:
        api_key: Chave da API Gemini
        modelo: gemini-2.0-flash (padrão gratuito), gemini-1.5-flash
        prompt_sistema: Instruções de sistema
        prompt_usuario: Contexto/dados do cliente
        timeout: Timeout em segundos
        max_tentativas: Máximo de tentativas em caso de erro 429

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
            "erro": f"Modelo Gemini '{modelo}' não suportado. "
                    f"Use: {', '.join(PRECOS.keys())}",
        }

    modelo_api = MODELOS_API.get(modelo, modelo)

    for tentativa in range(1, max_tentativas + 1):
        try:
            genai.configure(api_key=api_key)

            model = genai.GenerativeModel(
                model_name=modelo_api,
                system_instruction=prompt_sistema,
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": 4000,
                },
            )

            inicio = time.time()

            response = model.generate_content(
                prompt_usuario,
                request_options={"timeout": timeout},
            )

            tempo_total = time.time() - inicio

            # Gemini não retorna contagem de tokens diretamente na resposta
            # Estimamos baseado no tamanho do texto
            texto_gerado = response.text if response.text else ""
            prompt_chars = len(prompt_sistema) + len(prompt_usuario)
            completion_chars = len(texto_gerado)

            # Estimativa aproximada: 1 token ~= 4 caracteres
            prompt_tokens = max(1, prompt_chars // 4)
            completion_tokens = max(1, completion_chars // 4)

            custo = (
                prompt_tokens * PRECOS[modelo]["input"]
                + completion_tokens * PRECOS[modelo]["output"]
            )

            return {
                "conteudo": texto_gerado,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "tempo_execucao": round(tempo_total, 2),
                "custo": round(custo, 6),
                "sucesso": True,
                "erro": None,
                "modelo_utilizado": modelo,
            }

        except Exception as e:
            erro = str(e)
            tempo_espera = _extrair_tempo_espera(erro)

            # Se for erro de cota e ainda temos tentativas
            if _eh_erro_quota(erro) and tentativa < max_tentativas:
                # Usa o tempo sugerido pelo Google ou um backoff progressivo
                if tempo_espera > 0:
                    espera = tempo_espera + random.uniform(1, 3)
                else:
                    espera = (2 ** tentativa) + random.uniform(0, 2)

                # Limita espera máxima em 60s
                espera = min(espera, 60)

                time.sleep(espera)
                continue

            # Se foi a última tentativa ou erro não recuperável
            # Tenta fallback automático para gemini-1.5-flash
            if (
                _eh_erro_quota(erro)
                and modelo == "gemini-2.0-flash"
                and tentativa == max_tentativas
            ):
                return {
                    "conteudo": "",
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "tempo_execucao": 0.0,
                    "custo": 0.0,
                    "sucesso": False,
                    "erro": (
                        f"⚠️ Cota do Gemini esgotada para '{modelo}'.\n\n"
                        "📋 Sugestões:\n"
                        "1. **Troque o modelo** no .env para gemini-1.5-flash "
                        "(pode ter cota diferente)\n"
                        "2. **Crie uma NOVA chave de API** (projeto gratuito novo):\n"
                        "   → https://aistudio.google.com/app/apikey\n"
                        "3. **Aguarde ~24h** para o reset automático da cota diária\n"
                        "4. **Use OpenAI** como fallback: IA_PROVIDER=openai\n\n"
                        f"Detalhe técnico: {erro}"
                    ),
                    "modelo_utilizado": modelo,
                }

            return {
                "conteudo": "",
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "tempo_execucao": 0.0,
                "custo": 0.0,
                "sucesso": False,
                "erro": erro,
                "modelo_utilizado": modelo,
            }

    # Fallback - não deveria chegar aqui
    return {
        "conteudo": "",
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "tempo_execucao": 0.0,
        "custo": 0.0,
        "sucesso": False,
        "erro": "Número máximo de tentativas excedido.",
    }