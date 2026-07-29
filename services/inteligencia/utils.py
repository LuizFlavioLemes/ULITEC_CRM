"""
Utilitários compartilhados entre os módulos de Inteligência Comercial.
"""

from datetime import datetime, date, timedelta
from typing import Optional

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
# FUNÇÕES AUXILIARES
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