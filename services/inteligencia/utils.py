"""
Utilitários compartilhados entre os módulos de Inteligência Comercial.
"""

from datetime import datetime, date, timedelta
from typing import Optional, Tuple

import pandas as pd
import numpy as np

from database import db

# ──────────────────────────────────────────────
# CONSTANTES
# ──────────────────────────────────────────────

LIMITE_DIAS_VISITA_ESFRIANDO = 120
LIMITE_DIAS_SEM_VISITA = 90
LIMITE_MESES_SEM_FATURAMENTO = 12
TOP_N = 20
TOP_SCORE = 50
PERIODO_ATUAL_DIAS = 90
PERIODO_ANTERIOR_DIAS = 90

# Pesos do score v1.5.2
PESO_MAQUINAS_MITSUBISHI = 30
PESO_FATURAMENTO = 30
PESO_CLASSE_ABC = 15
PESO_DIAS_SEM_CONTATO = 10
PESO_DIAS_SEM_VISITA = 10
PESO_QUEDA_FATURAMENTO = 3
PESO_PREVENTIVAS_VENCIDAS = 1
PESO_OPORTUNIDADES = 1

# Penalização
PENALIDADE_RELACIONAMENTO_ATIVO = 40

# Pesos antigos (compatibilidade)
PESO_OS = 20
PESO_VISITA = 10

# ──────────────────────────────────────────────
# UFS VÁLIDAS
# ──────────────────────────────────────────────

UFS_VALIDAS = frozenset({
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO",
    "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI",
    "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO",
})

# ──────────────────────────────────────────────
# NORMALIZAÇÃO CIDADE / ESTADO
# ──────────────────────────────────────────────

def normalizar_cidade_estado(cidade: str, estado: Optional[str] = None) -> Tuple[str, Optional[str]]:
    """
    Normaliza cidade e estado extraindo a UF do final do nome da cidade.

    Regras:
    - Se cidade termina com ' - XX' onde XX é UF válida, extrai.
    - Se estado já está preenchido corretamente (não vazio, não '-'), mantém.
    - Se estado está vazio, '-' ou None, usa o extraído.
    - Se não reconhece padrão, retorna original.

    Args:
        cidade: Nome da cidade (ex: "CAMPINAS - SP")
        estado: UF atual (pode ser "", "-", None)

    Returns:
        Tupla (cidade_normalizada, estado_normalizado)
    """
    cidade_str = str(cidade).strip() if cidade else ""
    estado_str = str(estado).strip().upper() if estado else ""
    estado_str = estado_str if estado_str not in ("", "-", "NONE") else ""

    # Se estado já está preenchido corretamente, não altera
    if estado_str and estado_str in UFS_VALIDAS:
        return cidade_str, estado_str

    # Tentar extrair UF do final da cidade: "CIDADE - XX"
    if not cidade_str:
        return cidade_str, estado_str if estado_str else None

    partes = cidade_str.rsplit(" - ", 1)
    if len(partes) != 2:
        # Sem " - " no final, mantém original
        return cidade_str, estado_str if estado_str else None

    cidade_limpa = partes[0].strip()
    uf_candidata = partes[1].strip().upper()

    # Verificar se a UF extraída é válida
    if uf_candidata in UFS_VALIDAS:
        return cidade_limpa, uf_candidata

    # UF extraída inválida, mantém original
    return cidade_str, estado_str if estado_str else None


# ──────────────────────────────────────────────
# FALLBACK DE ESTADO NA INTELIGÊNCIA COMERCIAL
# ──────────────────────────────────────────────

def obter_estado_fallback(cidade: str, estado: Optional[str] = None) -> Optional[str]:
    """
    Retorna o estado, usando fallback da UF extraída da cidade se necessário.

    Usado na camada de Service para garantir que filtros por UF funcionem
    mesmo com dados inconsistentes no banco.

    Args:
        cidade: Nome da cidade
        estado: UF atual (pode ser vazio, "-", None)

    Returns:
        UF normalizada ou None se não foi possível determinar
    """
    _, estado_normalizado = normalizar_cidade_estado(cidade, estado)
    return estado_normalizado


# ──────────────────────────────────────────────
# SANEAMENTO DE DADOS EXISTENTES
# ──────────────────────────────────────────────

def sancar_cidade_estado() -> dict:
    """
    Rotina de saneamento de dados existentes.

    Percorre todos os clientes e identifica registros onde:
    - estado é vazio, "-" ou NULL
    - cidade termina com " - XX" onde XX é UF válida

    Extrai automaticamente a UF da cidade e salva no banco.

    Returns:
        dict com:
            "corrigidos": int - quantidade de registros corrigidos
            "ignorados": int - quantidade de registros com padrão não reconhecido
    """
    conn = _get_conn()
    cursor = conn.cursor()

    # Buscar clientes com estado inconsistente
    cursor.execute("""
        SELECT id, cidade, estado
        FROM clientes
        WHERE estado IS NULL
           OR estado = ''
           OR estado = '-'
           OR estado = 'NONE'
    """)

    registros = cursor.fetchall()
    corrigidos = 0
    ignorados = 0

    for cliente_id, cidade, estado_atual in registros:
        cidade_normalizada, estado_normalizado = normalizar_cidade_estado(
            cidade, estado_atual
        )

        if estado_normalizado and estado_normalizado != (str(estado_atual).strip().upper() if estado_atual else ""):
            # Houve extração bem-sucedida
            cursor.execute(
                "UPDATE clientes SET cidade = ?, estado = ? WHERE id = ?",
                (cidade_normalizada, estado_normalizado, cliente_id)
            )
            corrigidos += 1
        elif " - " in (str(cidade).strip() if cidade else ""):
            # Tem " - " no nome mas UF não reconhecida
            ignorados += 1

    conn.commit()
    conn.close()

    return {
        "corrigidos": corrigidos,
        "ignorados": ignorados,
    }


# ──────────────────────────────────────────────
# FUNÇÕES AUXILIARES (EXISTENTES)
# ──────────────────────────────────────────────

def _get_conn():
    """Retorna conexão com o banco de dados."""
    return db.get_connection()

def _data_limite(dias: int) -> str:
    """Retorna data no formato YYYY-MM-DD com N dias atrás."""
    return (date.today() - timedelta(days=dias)).strftime("%Y-%m-%d")

def _get_dias(dt_str) -> int:
    """Calcula dias desde uma data string. Retorna 9999 se inválida."""
    if pd.isna(dt_str) or not dt_str:
        return 9999
    try:
        return (date.today() - datetime.strptime(dt_str, "%Y-%m-%d").date()).days
    except (ValueError, TypeError):
        return 9999

def _normalizar_log(valor, max_val: float):
    """
    Normalização logarítmica vetorizada.
    Retorna valor entre 0 e 1.
    """
    if isinstance(valor, (int, float)):
        if max_val <= 0 or valor <= 0:
            return 0.0
        import math
        return math.log1p(valor) / math.log1p(max_val)
    if max_val <= 0:
        return np.zeros(len(valor))
    return np.where(valor <= 0, 0.0, np.log1p(valor) / np.log1p(max_val))

def _verificar_relacionamento_ativo(cliente_ids: list) -> dict:
    """
    Verifica se cada cliente possui pendência ou oportunidade ABERTA.
    Retorna dict {cliente_id: True/False}
    """
    if not cliente_ids:
        return {}

    conn = _get_conn()
    placeholders = ",".join("?" * len(cliente_ids))
    ids_params = list(cliente_ids)

    df_pend = pd.read_sql_query(
        f"""SELECT DISTINCT cliente_id FROM pendencias_comerciais
            WHERE cliente_id IN ({placeholders}) AND status = 'ABERTA'""",
        conn, params=ids_params
    )

    df_opp = pd.read_sql_query(
        f"""SELECT DISTINCT cliente_id FROM oportunidades
            WHERE cliente_id IN ({placeholders})
            AND status IN ('ABERTA', 'EM ANDAMENTO', 'NEGOCIACAO')""",
        conn, params=ids_params
    )

    conn.close()

    ids_com_atividade = set()
    if not df_pend.empty:
        ids_com_atividade.update(df_pend["cliente_id"].tolist())
    if not df_opp.empty:
        ids_com_atividade.update(df_opp["cliente_id"].tolist())

    return {cid: cid in ids_com_atividade for cid in cliente_ids}