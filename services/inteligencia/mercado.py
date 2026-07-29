"""
Módulo de Análise de Mercado — Inteligência Comercial.

Funções para preventivas vencidas, prospecção Mitsubishi,
top faturamento e última interação por cliente.
"""

from typing import Optional

import pandas as pd

from services.inteligencia.utils import _get_conn


def get_preventivas_vencidas(unidade: Optional[str] = None, dias_alerta: int = 730) -> pd.DataFrame:
    """Clientes com preventiva vencida (última OS FATURADA/EXPEDIDA > N dias)."""
    conn = _get_conn()
    query = """WITH ultima_os AS (
        SELECT os.cliente_id,
            MAX(CASE WHEN os.status IN ('FATURADA', 'EXPEDIDA')
                THEN COALESCE(os.data_faturamento, os.data_expedicao) ELSE NULL END) AS data_ultima_os
        FROM ordens_servico os
        WHERE os.status IN ('FATURADA', 'EXPEDIDA')
          AND COALESCE(os.data_faturamento, os.data_expedicao) IS NOT NULL"""
    params = []
    if unidade:
        query += " AND os.unidade = ?"
        params.append(unidade)
    query += """ GROUP BY os.cliente_id)
    SELECT c.id AS cliente_id, c.razao_social, c.cidade, c.estado,
           uo.data_ultima_os,
           CAST(julianday('now') - julianday(uo.data_ultima_os) AS INTEGER) AS dias_sem_manutencao
    FROM clientes c INNER JOIN ultima_os uo ON c.id = uo.cliente_id
    WHERE uo.data_ultima_os IS NOT NULL
      AND CAST(julianday('now') - julianday(uo.data_ultima_os) AS INTEGER) > ?
    ORDER BY dias_sem_manutencao DESC"""
    params.append(dias_alerta)
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def get_prospeccao_mitsubishi(unidade: Optional[str] = None) -> pd.DataFrame:
    """Empresas com máquinas Mitsubishi que nunca tiveram OS na unidade."""
    conn = _get_conn()
    if not unidade:
        query = """SELECT c.razao_social, c.cidade, c.estado, COUNT(m.id) AS qtd_mitsubishi
        FROM clientes c INNER JOIN maquinas_mitsubishi m ON m.cliente_id = c.id
        WHERE NOT EXISTS (SELECT 1 FROM ordens_servico os WHERE os.cliente_id = c.id)
        GROUP BY c.id ORDER BY qtd_mitsubishi DESC"""
        params = ()
    else:
        query = """SELECT c.razao_social, c.cidade, c.estado, COUNT(m.id) AS qtd_mitsubishi
        FROM clientes c INNER JOIN maquinas_mitsubishi m ON m.cliente_id = c.id
        WHERE NOT EXISTS (SELECT 1 FROM ordens_servico os WHERE os.cliente_id = c.id AND os.unidade = ?)
        GROUP BY c.id ORDER BY qtd_mitsubishi DESC"""
        params = (unidade,)
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    if not df.empty:
        def classificar_potencial(qtd):
            if qtd >= 15: return "ALTO"
            elif qtd >= 5: return "MÉDIO"
            else: return "BAIXO"
        df["potencial"] = df["qtd_mitsubishi"].apply(classificar_potencial)
    return df


def get_top_faturamento_12m(unidade: Optional[str] = None, limite: int = 20) -> pd.DataFrame:
    """Top N clientes por faturamento nos últimos 12 meses."""
    conn = _get_conn()
    query = """SELECT c.razao_social AS cliente,
        COALESCE(SUM(CAST(f.valor AS REAL)), 0) AS faturamento_12m
    FROM clientes c LEFT JOIN faturamento f ON f.cliente_id = c.id
        AND f.data_faturamento >= date('now', '-12 months')
    WHERE c.status = 'ATIVO'"""
    params = []
    if unidade:
        query += " AND f.unidade = ?"
        params.append(unidade)
    query += " GROUP BY c.id ORDER BY faturamento_12m DESC LIMIT ?"
    params.append(limite)
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    total = df["faturamento_12m"].sum()
    df["participacao"] = df["faturamento_12m"].apply(lambda v: (v / total * 100) if total > 0 else 0)
    return df


def get_ultima_interacao_clientes() -> pd.DataFrame:
    """Retorna DataFrame com cliente_id e ultima_interacao (MAX data_interacao)."""
    conn = _get_conn()
    df = pd.read_sql_query(
        "SELECT cliente_id, MAX(data_interacao) AS ultima_interacao FROM interacoes GROUP BY cliente_id",
        conn,
    )
    conn.close()
    return df