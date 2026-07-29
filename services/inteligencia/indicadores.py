"""
Módulo de Indicadores de Segmentação — Inteligência Comercial.

Contém a classificação ABCD de clientes.
"""

from typing import Optional

import pandas as pd

from services.inteligencia.utils import _get_conn


def classificar_abcd(unidade: Optional[str] = None) -> pd.DataFrame:
    """
    Classificação ABCD correta.
    Retorna DataFrame com id, razao_social, classe_abc, faturamento_12m.
    """
    conn = _get_conn()
    query = """SELECT c.id, c.razao_social, c.cidade, c.estado,
               COALESCE(f.faturamento_12m, 0) AS faturamento_12m, c.ultima_visita
    FROM clientes c LEFT JOIN (
        SELECT cliente_id, SUM(CAST(valor AS REAL)) AS faturamento_12m
        FROM faturamento"""
    params = []
    if unidade:
        query += " WHERE unidade = ?"
        params.append(unidade)
    query += " GROUP BY cliente_id) f ON f.cliente_id = c.id WHERE c.status = 'ATIVO'"

    df = pd.read_sql_query(query, conn, params=params)
    conn.close()

    if df.empty:
        df["classe_abc"] = "D"
        return df

    mask_com_faturamento = df["faturamento_12m"] > 0
    df_classificar = df[mask_com_faturamento].copy()
    df_sem_faturamento = df[~mask_com_faturamento].copy()

    if len(df_classificar) > 0:
        df_classificar = df_classificar.sort_values("faturamento_12m", ascending=False)
        qtd = len(df_classificar)
        limite_a = max(1, int(qtd * 0.10))
        limite_b = max(1, int(qtd * (0.10 + 0.30)))
        df_classificar["classe_abc"] = "D"
        df_classificar.iloc[:limite_a, df_classificar.columns.get_loc("classe_abc")] = "A"
        df_classificar.iloc[limite_a:limite_b, df_classificar.columns.get_loc("classe_abc")] = "B"
        df_classificar.iloc[limite_b:, df_classificar.columns.get_loc("classe_abc")] = "C"
    else:
        df_classificar["classe_abc"] = "D"

    df_sem_faturamento["classe_abc"] = "D"
    return pd.concat([df_classificar, df_sem_faturamento], ignore_index=True)