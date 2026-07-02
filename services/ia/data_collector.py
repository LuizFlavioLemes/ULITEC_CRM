"""
Coleta dados do banco para alimentar o prompt da IA.
Cada fonte de dados tem sua própria função para facilitar manutenção e crescimento futuro.
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta

from config import DB_PATH


def _get_conn():
    return sqlite3.connect(str(DB_PATH))


def coletar_cliente(cliente_id: int) -> dict:
    """Dados cadastrais do cliente."""
    conn = _get_conn()
    try:
        df = pd.read_sql_query(
            """
            SELECT razao_social, cidade, estado, segmento,
                   observacoes, status
            FROM clientes
            WHERE id = ?
            """,
            conn,
            params=(cliente_id,),
        )
        if df.empty:
            return {}
        return df.iloc[0].to_dict()
    finally:
        conn.close()


def coletar_faturamento(cliente_id: int) -> dict:
    """
    Faturamento dos últimos 12 meses.
    Retorna: faturamento_12m, ultimo_faturamento, meses_faturados, media_mensal
    """
    conn = _get_conn()
    try:
        data_limite = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

        df = pd.read_sql_query(
            """
            SELECT data_faturamento, valor
            FROM faturamento
            WHERE cliente_id = ? AND data_faturamento >= ?
            ORDER BY data_faturamento DESC
            """,
            conn,
            params=(cliente_id, data_limite),
        )

        if df.empty:
            return {
                "faturamento_12m": 0.0,
                "ultimo_faturamento": None,
                "meses_faturados": 0,
                "media_mensal": 0.0,
            }

        fat_12m = float(df["valor"].sum())
        ultimo = df.iloc[0]["data_faturamento"]
        meses = df["data_faturamento"].str[:7].nunique()
        media = fat_12m / max(meses, 1)

        return {
            "faturamento_12m": round(fat_12m, 2),
            "ultimo_faturamento": str(ultimo),
            "meses_faturados": int(meses),
            "media_mensal": round(media, 2),
        }
    finally:
        conn.close()


def coletar_os(cliente_id: int) -> dict:
    """
    Ordens de serviço dos últimos 24 meses.
    Retorna: quantidade_total, ultima_os, valor_total
    """
    conn = _get_conn()
    try:
        data_limite = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")

        df = pd.read_sql_query(
            """
            SELECT numero_os, data_recebimento, valor_estimado, status
            FROM ordens_servico
            WHERE cliente_id = ? AND data_recebimento >= ?
            ORDER BY data_recebimento DESC
            """,
            conn,
            params=(cliente_id, data_limite),
        )

        if df.empty:
            return {
                "quantidade_total": 0,
                "ultima_os": None,
                "valor_total": 0.0,
                "por_status": {},
            }

        qtd = len(df)
        ultima = df.iloc[0]["numero_os"]
        valor = float(df["valor_estimado"].sum())
        por_status = df.groupby("status").size().to_dict()

        return {
            "quantidade_total": qtd,
            "ultima_os": str(ultima),
            "valor_total": round(valor, 2),
            "por_status": por_status,
        }
    finally:
        conn.close()


def coletar_oportunidades(cliente_id: int) -> dict:
    """
    Oportunidades do cliente.
    Retorna: abertas, ganhas, perdidas, valor_potencial
    """
    conn = _get_conn()
    try:
        df = pd.read_sql_query(
            """
            SELECT status, valor_estimado
            FROM oportunidades
            WHERE cliente_id = ?
            """,
            conn,
            params=(cliente_id,),
        )

        if df.empty:
            return {
                "abertas": 0,
                "ganhas": 0,
                "perdidas": 0,
                "valor_potencial": 0.0,
            }

        status_upper = df["status"].fillna("").str.upper()
        abertas = len(df[status_upper.isin(["ABERTA", "EM ANDAMENTO"])])
        ganhas = len(df[status_upper == "GANHA"])
        perdidas = len(df[status_upper == "PERDIDA"])
        valor_pot = float(df[status_upper.isin(["ABERTA", "EM ANDAMENTO"])]["valor_estimado"].sum())

        return {
            "abertas": int(abertas),
            "ganhas": int(ganhas),
            "perdidas": int(perdidas),
            "valor_potencial": round(valor_pot, 2),
        }
    finally:
        conn.close()


def coletar_mitsubishi(cliente_id: int) -> dict:
    """
    Máquinas Mitsubishi do cliente.
    Retorna: quantidade, principais_series_cnc
    """
    conn = _get_conn()
    try:
        df = pd.read_sql_query(
            """
            SELECT nc_series, machine
            FROM maquinas_mitsubishi
            WHERE cliente_id = ?
            """,
            conn,
            params=(cliente_id,),
        )

        if df.empty:
            return {
                "quantidade": 0,
                "principais_series_cnc": [],
            }

        qtd = len(df)
        series = df["nc_series"].value_counts().head(5).to_dict()

        return {
            "quantidade": qtd,
            "principais_series_cnc": [f"{k} ({v})" for k, v in series.items()],
        }
    finally:
        conn.close()


def coletar_interacoes(cliente_id: int) -> list:
    """
    Últimas 10 interações com o cliente.
    """
    conn = _get_conn()
    try:
        df = pd.read_sql_query(
            """
            SELECT data_interacao, tipo_interacao, responsavel,
                   resumo, proxima_acao
            FROM interacoes
            WHERE cliente_id = ?
            ORDER BY data_interacao DESC
            LIMIT 10
            """,
            conn,
            params=(cliente_id,),
        )

        if df.empty:
            return []

        return df.to_dict("records")
    finally:
        conn.close()