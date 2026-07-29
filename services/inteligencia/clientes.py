"""
Módulo de Análise de Clientes — Inteligência Comercial.

Funções para identificar clientes esfriando, esquentando,
sem visita, sem faturamento, com muitas OS e com parque Mitsubishi relevante.
"""

from datetime import datetime, date, timedelta
from typing import Optional

import pandas as pd

from services.inteligencia.utils import (
    _get_conn, _data_limite,
    LIMITE_DIAS_VISITA_ESFRIANDO, LIMITE_DIAS_SEM_VISITA,
    LIMITE_MESES_SEM_FATURAMENTO, PERIODO_ATUAL_DIAS,
    PERIODO_ANTERIOR_DIAS, TOP_N,
)


def get_clientes_esfriando(unidade: Optional[str] = None) -> pd.DataFrame:
    """Clientes com queda de faturamento > 30%, queda de OS > 30% ou sem visita > 120d."""
    conn = _get_conn()
    hoje = date.today().strftime("%Y-%m-%d")
    data_limite_atual = _data_limite(PERIODO_ATUAL_DIAS)
    data_limite_anterior = _data_limite(PERIODO_ATUAL_DIAS + PERIODO_ANTERIOR_DIAS)
    data_limite_visita = _data_limite(LIMITE_DIAS_VISITA_ESFRIANDO)

    query_fat_atual = """SELECT cliente_id, SUM(CAST(valor AS REAL)) AS fat_atual
    FROM faturamento WHERE data_faturamento >= ? AND data_faturamento <= ?"""
    params_fat_atual = [data_limite_atual, hoje]
    if unidade:
        query_fat_atual += " AND unidade = ?"
        params_fat_atual.append(unidade)
    query_fat_atual += " GROUP BY cliente_id"
    df_fat_atual = pd.read_sql_query(query_fat_atual, conn, params=params_fat_atual)

    query_fat_ant = """SELECT cliente_id, SUM(CAST(valor AS REAL)) AS fat_anterior
    FROM faturamento WHERE data_faturamento >= ? AND data_faturamento < ?"""
    params_fat_ant = [data_limite_anterior, data_limite_atual]
    if unidade:
        query_fat_ant += " AND unidade = ?"
        params_fat_ant.append(unidade)
    query_fat_ant += " GROUP BY cliente_id"
    df_fat_ant = pd.read_sql_query(query_fat_ant, conn, params=params_fat_ant)

    query_os_atual = """SELECT cliente_id, COUNT(*) AS os_atual
    FROM ordens_servico WHERE data_recebimento >= ? AND data_recebimento <= ?"""
    params_os_atual = [data_limite_atual, hoje]
    if unidade:
        query_os_atual += " AND unidade = ?"
        params_os_atual.append(unidade)
    query_os_atual += " GROUP BY cliente_id"
    df_os_atual = pd.read_sql_query(query_os_atual, conn, params=params_os_atual)

    query_os_ant = """SELECT cliente_id, COUNT(*) AS os_anterior
    FROM ordens_servico WHERE data_recebimento >= ? AND data_recebimento < ?"""
    params_os_ant = [data_limite_anterior, data_limite_atual]
    if unidade:
        query_os_ant += " AND unidade = ?"
        params_os_ant.append(unidade)
    query_os_ant += " GROUP BY cliente_id"
    df_os_ant = pd.read_sql_query(query_os_ant, conn, params=params_os_ant)

    query_clientes = """SELECT c.id, c.razao_social, c.cidade, c.estado, c.ultima_visita
    FROM clientes c WHERE c.status = 'ATIVO'"""
    params_clientes = []
    if unidade:
        query_clientes += """ AND (EXISTS (SELECT 1 FROM faturamento f WHERE f.cliente_id = c.id AND f.unidade = ?)
           OR EXISTS (SELECT 1 FROM ordens_servico os WHERE os.cliente_id = c.id AND os.unidade = ?))"""
        params_clientes.append(unidade)
        params_clientes.append(unidade)
    df_clientes = pd.read_sql_query(query_clientes, conn, params=params_clientes)
    conn.close()

    df = df_clientes.merge(df_fat_atual, left_on="id", right_on="cliente_id", how="left")
    df = df.merge(df_fat_ant, left_on="id", right_on="cliente_id", how="left", suffixes=("_atual", "_ant"))
    df = df.merge(df_os_atual, left_on="id", right_on="cliente_id", how="left")
    df = df.merge(df_os_ant, left_on="id", right_on="cliente_id", how="left", suffixes=("_atual_os", "_ant_os"))

    for col in ["fat_atual", "fat_anterior", "os_atual", "os_anterior"]:
        df[col] = df[col].fillna(0)

    df["variacao_fat"] = df.apply(
        lambda r: ((r["fat_atual"] - r["fat_anterior"]) / r["fat_anterior"] * 100) if r["fat_anterior"] > 0 else 0, axis=1)
    df["variacao_os"] = df.apply(
        lambda r: ((r["os_atual"] - r["os_anterior"]) / r["os_anterior"] * 100) if r["os_anterior"] > 0 else 0, axis=1)
    df["dias_sem_visita"] = df["ultima_visita"].apply(
        lambda v: (date.today() - datetime.strptime(v, "%Y-%m-%d").date()).days if pd.notna(v) and v else 9999)

    cond_queda_fat = df["variacao_fat"] < -30
    cond_queda_os = df["variacao_os"] < -30
    cond_sem_visita = df["dias_sem_visita"] > LIMITE_DIAS_VISITA_ESFRIANDO
    df_result = df[cond_queda_fat | cond_queda_os | cond_sem_visita].copy()
    df_result["variacao"] = df_result.apply(lambda r: min(r["variacao_fat"], r["variacao_os"]), axis=1)
    df_result = df_result.rename(columns={"razao_social": "cliente", "fat_atual": "faturamento_periodo_atual", "fat_anterior": "faturamento_periodo_anterior"})
    return df_result[["cliente", "cidade", "estado", "faturamento_periodo_atual", "faturamento_periodo_anterior", "variacao", "dias_sem_visita"]].sort_values("variacao", ascending=True).reset_index(drop=True)


def get_clientes_esquentando(unidade: Optional[str] = None) -> pd.DataFrame:
    """Clientes com crescimento de faturamento > 20% ou OS > 20%."""
    conn = _get_conn()
    hoje = date.today().strftime("%Y-%m-%d")
    data_limite_atual = _data_limite(PERIODO_ATUAL_DIAS)
    data_limite_anterior = _data_limite(PERIODO_ATUAL_DIAS + PERIODO_ANTERIOR_DIAS)

    query_fat_atual = """SELECT cliente_id, SUM(CAST(valor AS REAL)) AS fat_atual
    FROM faturamento WHERE data_faturamento >= ? AND data_faturamento <= ?"""
    params_fat_atual = [data_limite_atual, hoje]
    if unidade:
        query_fat_atual += " AND unidade = ?"
        params_fat_atual.append(unidade)
    query_fat_atual += " GROUP BY cliente_id"
    df_fat_atual = pd.read_sql_query(query_fat_atual, conn, params=params_fat_atual)

    query_fat_ant = """SELECT cliente_id, SUM(CAST(valor AS REAL)) AS fat_anterior
    FROM faturamento WHERE data_faturamento >= ? AND data_faturamento < ?"""
    params_fat_ant = [data_limite_anterior, data_limite_atual]
    if unidade:
        query_fat_ant += " AND unidade = ?"
        params_fat_ant.append(unidade)
    query_fat_ant += " GROUP BY cliente_id"
    df_fat_ant = pd.read_sql_query(query_fat_ant, conn, params=params_fat_ant)

    query_os_atual = """SELECT cliente_id, COUNT(*) AS os_atual
    FROM ordens_servico WHERE data_recebimento >= ? AND data_recebimento <= ?"""
    params_os_atual = [data_limite_atual, hoje]
    if unidade:
        query_os_atual += " AND unidade = ?"
        params_os_atual.append(unidade)
    query_os_atual += " GROUP BY cliente_id"
    df_os_atual = pd.read_sql_query(query_os_atual, conn, params=params_os_atual)

    query_os_ant = """SELECT cliente_id, COUNT(*) AS os_anterior
    FROM ordens_servico WHERE data_recebimento >= ? AND data_recebimento < ?"""
    params_os_ant = [data_limite_anterior, data_limite_atual]
    if unidade:
        query_os_ant += " AND unidade = ?"
        params_os_ant.append(unidade)
    query_os_ant += " GROUP BY cliente_id"
    df_os_ant = pd.read_sql_query(query_os_ant, conn, params=params_os_ant)

    df_clientes = pd.read_sql_query("SELECT id, razao_social, cidade, estado FROM clientes WHERE status = 'ATIVO'", conn)
    conn.close()

    df = df_clientes.merge(df_fat_atual, left_on="id", right_on="cliente_id", how="left")
    df = df.merge(df_fat_ant, left_on="id", right_on="cliente_id", how="left", suffixes=("_atual", "_ant"))
    df = df.merge(df_os_atual, left_on="id", right_on="cliente_id", how="left")
    df = df.merge(df_os_ant, left_on="id", right_on="cliente_id", how="left", suffixes=("_atual_os", "_ant_os"))

    for col in ["fat_atual", "fat_anterior", "os_atual", "os_anterior"]:
        df[col] = df[col].fillna(0)

    df["variacao_fat"] = df.apply(
        lambda r: ((r["fat_atual"] - r["fat_anterior"]) / r["fat_anterior"] * 100) if r["fat_anterior"] > 0 else (100 if r["fat_atual"] > 0 else 0), axis=1)
    df["variacao_os"] = df.apply(
        lambda r: ((r["os_atual"] - r["os_anterior"]) / r["os_anterior"] * 100) if r["os_anterior"] > 0 else (100 if r["os_atual"] > 0 else 0), axis=1)

    df_result = df[(df["variacao_fat"] > 20) | (df["variacao_os"] > 20)].copy()
    df_result["variacao"] = df_result.apply(lambda r: max(r["variacao_fat"], r["variacao_os"]), axis=1)
    df_result["faturamento"] = df_result["fat_atual"]
    df_result = df_result.rename(columns={"razao_social": "cliente"})
    return df_result[["cliente", "cidade", "estado", "variacao", "faturamento"]].sort_values("variacao", ascending=False).reset_index(drop=True)


def get_clientes_sem_visita(unidade: Optional[str] = None) -> pd.DataFrame:
    """Clientes nunca visitados ou com última visita > 90 dias."""
    conn = _get_conn()
    data_limite = _data_limite(LIMITE_DIAS_SEM_VISITA)
    query = """SELECT c.razao_social AS cliente, c.cidade,
        CASE WHEN c.ultima_visita IS NULL THEN NULL
            ELSE CAST(julianday('now') - julianday(c.ultima_visita) AS INTEGER) END AS dias_sem_visita,
        CASE WHEN c.ultima_visita IS NULL THEN 'NUNCA_VISITADO' ELSE 'VISITA_ATRASADA' END AS tipo
    FROM clientes c WHERE c.status = 'ATIVO' AND (c.ultima_visita IS NULL OR c.ultima_visita <= ?)"""
    params = [data_limite]
    if unidade:
        query += " AND (SELECT COUNT(*) FROM faturamento f WHERE f.cliente_id = c.id AND f.unidade = ?) > 0"
        params.append(unidade)
    query += " ORDER BY tipo ASC, dias_sem_visita DESC"
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def get_clientes_sem_faturamento(unidade: Optional[str] = None) -> pd.DataFrame:
    """Clientes sem faturamento nos últimos 12 meses, mas com máquinas ou histórico de OS."""
    conn = _get_conn()
    data_limite = _data_limite(LIMITE_MESES_SEM_FATURAMENTO * 30)

    query_base = """SELECT DISTINCT c.id, c.razao_social AS cliente FROM clientes c
    WHERE c.status = 'ATIVO' AND (c.ultimo_faturamento IS NULL OR c.ultimo_faturamento < ?)
      AND (EXISTS (SELECT 1 FROM maquinas_mitsubishi m WHERE m.cliente_id = c.id)
           OR EXISTS (SELECT 1 FROM ordens_servico os WHERE os.cliente_id = c.id))"""
    params_base = [data_limite]
    if unidade:
        query_base += " AND EXISTS (SELECT 1 FROM ordens_servico os2 WHERE os2.cliente_id = c.id AND os2.unidade = ?)"
        params_base.append(unidade)

    df_base = pd.read_sql_query(query_base, conn, params=params_base)
    if df_base.empty:
        conn.close()
        return pd.DataFrame(columns=["cliente", "máquinas", "última OS", "último faturamento"])

    ids = tuple(df_base["id"].tolist())
    placeholders = ",".join("?" * len(ids))

    df_maq = pd.read_sql_query(
        f"SELECT cliente_id, COUNT(*) AS qtd_maquinas FROM maquinas_mitsubishi WHERE cliente_id IN ({placeholders}) GROUP BY cliente_id",
        conn, params=ids)

    params_ult_os = list(ids)
    query_ult_os = f"SELECT cliente_id, MAX(data_recebimento) AS ultima_os FROM ordens_servico WHERE cliente_id IN ({placeholders})"
    if unidade:
        query_ult_os += " AND unidade = ?"
        params_ult_os.append(unidade)
    query_ult_os += " GROUP BY cliente_id"
    df_ult_os = pd.read_sql_query(query_ult_os, conn, params=params_ult_os)

    params_ult_fat = list(ids)
    query_ult_fat = f"SELECT cliente_id, MAX(data_faturamento) AS ultimo_faturamento FROM faturamento WHERE cliente_id IN ({placeholders})"
    if unidade:
        query_ult_fat += " AND unidade = ?"
        params_ult_fat.append(unidade)
    query_ult_fat += " GROUP BY cliente_id"
    df_ult_fat = pd.read_sql_query(query_ult_fat, conn, params=params_ult_fat)
    conn.close()

    df = df_base.merge(df_maq, left_on="id", right_on="cliente_id", how="left")
    df = df.merge(df_ult_os, left_on="id", right_on="cliente_id", how="left")
    df = df.merge(df_ult_fat, left_on="id", right_on="cliente_id", how="left")
    df["máquinas"] = df["qtd_maquinas"].fillna(0).astype(int)
    df["última OS"] = df["ultima_os"].fillna("Nunca")
    df["último faturamento"] = df["ultimo_faturamento"].fillna("Nunca")
    return df[["cliente", "máquinas", "última OS", "último faturamento"]]


def get_clientes_muitas_os(unidade: Optional[str] = None) -> pd.DataFrame:
    """Top 20 clientes por quantidade de OS nos últimos 12 meses."""
    conn = _get_conn()
    data_limite = _data_limite(LIMITE_MESES_SEM_FATURAMENTO * 30)
    query = """SELECT c.razao_social AS cliente, COUNT(os.id) AS qtd_os,
        SUM(COALESCE(CAST(os.valor_estimado AS REAL), 0) + COALESCE(CAST(os.valor_proposta AS REAL), 0)) AS valor_total
    FROM ordens_servico os INNER JOIN clientes c ON os.cliente_id = c.id
    WHERE os.data_recebimento >= ?"""
    params = [data_limite]
    if unidade:
        query += " AND os.unidade = ?"
        params.append(unidade)
    query += " GROUP BY os.cliente_id ORDER BY qtd_os DESC LIMIT ?"
    params.append(TOP_N)
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def get_clientes_parque_relevante(unidade: Optional[str] = None) -> pd.DataFrame:
    """Top 20 clientes por quantidade de máquinas Mitsubishi."""
    conn = _get_conn()
    query = """SELECT c.razao_social AS cliente, COUNT(m.id) AS quantidade_maquinas
    FROM maquinas_mitsubishi m INNER JOIN clientes c ON m.cliente_id = c.id WHERE c.status = 'ATIVO'"""
    params = []
    if unidade:
        query += " AND EXISTS (SELECT 1 FROM ordens_servico os WHERE os.cliente_id = c.id AND os.unidade = ?)"
        params.append(unidade)
    query += " GROUP BY c.id ORDER BY quantidade_maquinas DESC LIMIT ?"
    params.append(TOP_N)
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df