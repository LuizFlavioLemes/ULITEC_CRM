"""
Módulo de Inteligência Comercial — ULITEC CRM v1.5.2

Regras de negócio para análise de carteira de clientes:
- Clientes esfriando
- Clientes esquentando
- Clientes sem visita
- Clientes sem faturamento
- Clientes com muitas OS
- Clientes com parque Mitsubishi relevante
- Score comercial (0-100)
- Classificação ABCD correta (faturamento_12m > 0 obrigatório)
- Priorização inteligente com integração ao Relacionamento Comercial
"""

from datetime import datetime, date, timedelta
from typing import Optional
import sqlite3

import pandas as pd

from config import DB_PATH


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

# Pesos do score v1.5.2 — priorização inteligente
PESO_MAQUINAS_MITSUBISHI = 30  # Muito Alto
PESO_FATURAMENTO = 30          # Muito Alto (era 25)
PESO_CLASSE_ABC = 15           # Alto
PESO_DIAS_SEM_CONTATO = 10     # Médio
PESO_DIAS_SEM_VISITA = 10      # Médio
PESO_QUEDA_FATURAMENTO = 3     # Complementar
PESO_PREVENTIVAS_VENCIDAS = 1  # Complementar
PESO_OPORTUNIDADES = 1         # Complementar

# Penalização por relacionamento ativo
PENALIDADE_RELACIONAMENTO_ATIVO = 40

# Pesos antigos (mantidos para compatibilidade com funções legadas)
PESO_OS = 20
PESO_VISITA = 10


# ──────────────────────────────────────────────
# AUXILIARES
# ──────────────────────────────────────────────

def _get_conn() -> sqlite3.Connection:
    """Retorna conexão com o banco SQLite."""
    return sqlite3.connect(str(DB_PATH))


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
    Normalização logarítmica vetorizada para evitar que outliers dominem o score.
    Aceita scalar ou pandas Series.
    Retorna valor entre 0 e 1.
    """
    import numpy as np
    if isinstance(valor, (int, float)):
        if max_val <= 0 or valor <= 0:
            return 0.0
        import math
        return math.log1p(valor) / math.log1p(max_val)
    # pandas Series — operação vetorizada
    if max_val <= 0:
        return np.zeros(len(valor))
    return np.where(valor <= 0, 0.0, np.log1p(valor) / np.log1p(max_val))


def _verificar_relacionamento_ativo(cliente_ids: list) -> dict:
    """
    Verifica se cada cliente possui pendência comercial ABERTA
    ou oportunidade ABERTA.
    Retorna dict {cliente_id: True/False}
    """
    if not cliente_ids:
        return {}

    conn = _get_conn()
    placeholders = ",".join("?" * len(cliente_ids))
    ids_params = list(cliente_ids)

    # Pendências comerciais ABERTA
    query_pendencias = f"""
    SELECT DISTINCT cliente_id FROM pendencias_comerciais
    WHERE cliente_id IN ({placeholders})
      AND status = 'ABERTA'
    """
    df_pend = pd.read_sql_query(query_pendencias, conn, params=ids_params)

    # Oportunidades ABERTA
    query_opp = f"""
    SELECT DISTINCT cliente_id FROM oportunidades
    WHERE cliente_id IN ({placeholders})
      AND status IN ('ABERTA', 'EM ANDAMENTO', 'NEGOCIACAO')
    """
    df_opp = pd.read_sql_query(query_opp, conn, params=ids_params)

    conn.close()

    # Montar set de IDs com relacionamento ativo
    ids_com_atividade = set()
    if not df_pend.empty:
        ids_com_atividade.update(df_pend["cliente_id"].tolist())
    if not df_opp.empty:
        ids_com_atividade.update(df_opp["cliente_id"].tolist())

    return {cid: cid in ids_com_atividade for cid in cliente_ids}


# ──────────────────────────────────────────────
# CLASSIFICAÇÃO ABCD (v1.5.1)
# ──────────────────────────────────────────────

def classificar_abcd(unidade: Optional[str] = None) -> pd.DataFrame:
    """
    Classificação ABCD correta:
    - Filtra APENAS clientes com faturamento_12m > 0 para classes A, B, C
    - Clientes com faturamento_12m = 0 ou sem relevância → Classe D
    
    Retorna DataFrame com id, razao_social, classe_abc, faturamento_12m
    """
    conn = _get_conn()
    
    query = """
    SELECT c.id, c.razao_social, c.cidade, c.estado, 
           COALESCE(f. faturamento_12m, 0) AS faturamento_12m,
           c.ultima_visita
    FROM clientes c
    LEFT JOIN (
        SELECT cliente_id, SUM(CAST(valor AS REAL)) AS faturamento_12m
        FROM faturamento
    """
    params = []
    if unidade:
        query += " WHERE unidade = ?"
        params.append(unidade)
    query += """
        GROUP BY cliente_id
    ) f ON f.cliente_id = c.id
    WHERE c.status = 'ATIVO'
    """
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    if df.empty:
        df["classe_abc"] = "D"
        return df
    
    # Separar clientes com faturamento > 0
    mask_com_faturamento = df["faturamento_12m"] > 0
    df_classificar = df[mask_com_faturamento].copy()
    df_sem_faturamento = df[~mask_com_faturamento].copy()
    
    # Classificar apenas quem tem faturamento
    if len(df_classificar) > 0:
        df_classificar = df_classificar.sort_values("faturamento_12m", ascending=False)
        qtd = len(df_classificar)
        # Percentuais fixos: A=10%, B=30%, C=60%
        limite_a = max(1, int(qtd * 0.10))
        limite_b = max(1, int(qtd * (0.10 + 0.30)))
        
        df_classificar["classe_abc"] = "D"
        df_classificar.iloc[:limite_a, df_classificar.columns.get_loc("classe_abc")] = "A"
        df_classificar.iloc[limite_a:limite_b, df_classificar.columns.get_loc("classe_abc")] = "B"
        df_classificar.iloc[limite_b:, df_classificar.columns.get_loc("classe_abc")] = "C"
    else:
        df_classificar["classe_abc"] = "D"
    
    # Todos sem faturamento são D
    df_sem_faturamento["classe_abc"] = "D"
    
    # Combinar resultados
    df_result = pd.concat([df_classificar, df_sem_faturamento], ignore_index=True)
    
    return df_result


# ──────────────────────────────────────────────
# CLIENTES ESFRIANDO
# ──────────────────────────────────────────────

def get_clientes_esfriando(unidade: Optional[str] = None) -> pd.DataFrame:
    """
    Clientes com queda de faturamento > 30% ou queda de OS > 30%
    nos últimos 90 dias vs 90 dias anteriores, OU sem visita há mais de 120 dias.
    """
    conn = _get_conn()
    hoje = date.today().strftime("%Y-%m-%d")
    data_limite_atual = _data_limite(PERIODO_ATUAL_DIAS)
    data_limite_anterior = _data_limite(PERIODO_ATUAL_DIAS + PERIODO_ANTERIOR_DIAS)
    data_limite_visita = _data_limite(LIMITE_DIAS_VISITA_ESFRIANDO)

    # Faturamento período atual
    query_fat_atual = """
    SELECT cliente_id, SUM(CAST(valor AS REAL)) AS fat_atual
    FROM faturamento
    WHERE data_faturamento >= ? AND data_faturamento <= ?
    """
    params_fat_atual = [data_limite_atual, hoje]
    if unidade:
        query_fat_atual += " AND unidade = ?"
        params_fat_atual.append(unidade)
    query_fat_atual += " GROUP BY cliente_id"
    df_fat_atual = pd.read_sql_query(query_fat_atual, conn, params=params_fat_atual)

    # Faturamento período anterior
    query_fat_ant = """
    SELECT cliente_id, SUM(CAST(valor AS REAL)) AS fat_anterior
    FROM faturamento
    WHERE data_faturamento >= ? AND data_faturamento < ?
    """
    params_fat_ant = [data_limite_anterior, data_limite_atual]
    if unidade:
        query_fat_ant += " AND unidade = ?"
        params_fat_ant.append(unidade)
    query_fat_ant += " GROUP BY cliente_id"
    df_fat_ant = pd.read_sql_query(query_fat_ant, conn, params=params_fat_ant)

    # OS período atual
    query_os_atual = """
    SELECT cliente_id, COUNT(*) AS os_atual
    FROM ordens_servico
    WHERE data_recebimento >= ? AND data_recebimento <= ?
    """
    params_os_atual = [data_limite_atual, hoje]
    if unidade:
        query_os_atual += " AND unidade = ?"
        params_os_atual.append(unidade)
    query_os_atual += " GROUP BY cliente_id"
    df_os_atual = pd.read_sql_query(query_os_atual, conn, params=params_os_atual)

    # OS período anterior
    query_os_ant = """
    SELECT cliente_id, COUNT(*) AS os_anterior
    FROM ordens_servico
    WHERE data_recebimento >= ? AND data_recebimento < ?
    """
    params_os_ant = [data_limite_anterior, data_limite_atual]
    if unidade:
        query_os_ant += " AND unidade = ?"
        params_os_ant.append(unidade)
    query_os_ant += " GROUP BY cliente_id"
    df_os_ant = pd.read_sql_query(query_os_ant, conn, params=params_os_ant)

    # Clientes base — filtrar por unidade se necessário
    query_clientes = """
    SELECT c.id, c.razao_social, c.cidade, c.estado, c.ultima_visita
    FROM clientes c
    WHERE c.status = 'ATIVO'
    """
    params_clientes = []
    if unidade:
        query_clientes += """
      AND (EXISTS (SELECT 1 FROM faturamento f WHERE f.cliente_id = c.id AND f.unidade = ?)
           OR
           EXISTS (SELECT 1 FROM ordens_servico os WHERE os.cliente_id = c.id AND os.unidade = ?))
        """
        params_clientes.append(unidade)
        params_clientes.append(unidade)
    df_clientes = pd.read_sql_query(query_clientes, conn, params=params_clientes)

    conn.close()

    # Merge faturamento
    df = df_clientes.merge(df_fat_atual, left_on="id", right_on="cliente_id", how="left")
    df = df.merge(df_fat_ant, left_on="id", right_on="cliente_id", how="left", suffixes=("_atual", "_ant"))
    df = df.merge(df_os_atual, left_on="id", right_on="cliente_id", how="left")
    df = df.merge(df_os_ant, left_on="id", right_on="cliente_id", how="left", suffixes=("_atual_os", "_ant_os"))

    # Preencher NaN com 0
    for col in ["fat_atual", "fat_anterior", "os_atual", "os_anterior"]:
        df[col] = df[col].fillna(0)

    # Calcular variações
    df["variacao_fat"] = df.apply(
        lambda r: ((r["fat_atual"] - r["fat_anterior"]) / r["fat_anterior"] * 100)
        if r["fat_anterior"] > 0 else 0, axis=1
    )
    df["variacao_os"] = df.apply(
        lambda r: ((r["os_atual"] - r["os_anterior"]) / r["os_anterior"] * 100)
        if r["os_anterior"] > 0 else 0, axis=1
    )

    # Dias sem visita
    df["dias_sem_visita"] = df["ultima_visita"].apply(
        lambda v: (date.today() - datetime.strptime(v, "%Y-%m-%d").date()).days
        if pd.notna(v) and v else 9999
    )

    # Critérios: queda fat > 30% OU queda OS > 30% OU sem visita > 120 dias
    cond_queda_fat = df["variacao_fat"] < -30
    cond_queda_os = df["variacao_os"] < -30
    cond_sem_visita = df["dias_sem_visita"] > LIMITE_DIAS_VISITA_ESFRIANDO

    df_result = df[cond_queda_fat | cond_queda_os | cond_sem_visita].copy()

    # Definir variação principal (a maior queda)
    df_result["variacao"] = df_result.apply(
        lambda r: min(r["variacao_fat"], r["variacao_os"]), axis=1
    )

    df_result = df_result.rename(columns={
        "razao_social": "cliente",
        "fat_atual": "faturamento_periodo_atual",
        "fat_anterior": "faturamento_periodo_anterior",
    })

    return df_result[[
        "cliente", "cidade", "estado",
        "faturamento_periodo_atual", "faturamento_periodo_anterior",
        "variacao", "dias_sem_visita"
    ]].sort_values("variacao", ascending=True).reset_index(drop=True)


# ──────────────────────────────────────────────
# CLIENTES ESQUENTANDO
# ──────────────────────────────────────────────

def get_clientes_esquentando(unidade: Optional[str] = None) -> pd.DataFrame:
    """
    Clientes com crescimento de faturamento > 20% ou crescimento de OS > 20%
    nos últimos 90 dias vs 90 dias anteriores.
    """
    conn = _get_conn()
    hoje = date.today().strftime("%Y-%m-%d")
    data_limite_atual = _data_limite(PERIODO_ATUAL_DIAS)
    data_limite_anterior = _data_limite(PERIODO_ATUAL_DIAS + PERIODO_ANTERIOR_DIAS)

    # Faturamento período atual
    query_fat_atual = """
    SELECT cliente_id, SUM(CAST(valor AS REAL)) AS fat_atual
    FROM faturamento
    WHERE data_faturamento >= ? AND data_faturamento <= ?
    """
    params_fat_atual = [data_limite_atual, hoje]
    if unidade:
        query_fat_atual += " AND unidade = ?"
        params_fat_atual.append(unidade)
    query_fat_atual += " GROUP BY cliente_id"
    df_fat_atual = pd.read_sql_query(query_fat_atual, conn, params=params_fat_atual)

    # Faturamento período anterior
    query_fat_ant = """
    SELECT cliente_id, SUM(CAST(valor AS REAL)) AS fat_anterior
    FROM faturamento
    WHERE data_faturamento >= ? AND data_faturamento < ?
    """
    params_fat_ant = [data_limite_anterior, data_limite_atual]
    if unidade:
        query_fat_ant += " AND unidade = ?"
        params_fat_ant.append(unidade)
    query_fat_ant += " GROUP BY cliente_id"
    df_fat_ant = pd.read_sql_query(query_fat_ant, conn, params=params_fat_ant)

    # OS período atual
    query_os_atual = """
    SELECT cliente_id, COUNT(*) AS os_atual
    FROM ordens_servico
    WHERE data_recebimento >= ? AND data_recebimento <= ?
    """
    params_os_atual = [data_limite_atual, hoje]
    if unidade:
        query_os_atual += " AND unidade = ?"
        params_os_atual.append(unidade)
    query_os_atual += " GROUP BY cliente_id"
    df_os_atual = pd.read_sql_query(query_os_atual, conn, params=params_os_atual)

    # OS período anterior
    query_os_ant = """
    SELECT cliente_id, COUNT(*) AS os_anterior
    FROM ordens_servico
    WHERE data_recebimento >= ? AND data_recebimento < ?
    """
    params_os_ant = [data_limite_anterior, data_limite_atual]
    if unidade:
        query_os_ant += " AND unidade = ?"
        params_os_ant.append(unidade)
    query_os_ant += " GROUP BY cliente_id"
    df_os_ant = pd.read_sql_query(query_os_ant, conn, params=params_os_ant)

    # Clientes base
    df_clientes = pd.read_sql_query(
        "SELECT id, razao_social, cidade, estado FROM clientes WHERE status = 'ATIVO'", conn
    )

    conn.close()

    # Merge
    df = df_clientes.merge(df_fat_atual, left_on="id", right_on="cliente_id", how="left")
    df = df.merge(df_fat_ant, left_on="id", right_on="cliente_id", how="left", suffixes=("_atual", "_ant"))
    df = df.merge(df_os_atual, left_on="id", right_on="cliente_id", how="left")
    df = df.merge(df_os_ant, left_on="id", right_on="cliente_id", how="left", suffixes=("_atual_os", "_ant_os"))

    for col in ["fat_atual", "fat_anterior", "os_atual", "os_anterior"]:
        df[col] = df[col].fillna(0)

    df["variacao_fat"] = df.apply(
        lambda r: ((r["fat_atual"] - r["fat_anterior"]) / r["fat_anterior"] * 100)
        if r["fat_anterior"] > 0 else (100 if r["fat_atual"] > 0 else 0), axis=1
    )
    df["variacao_os"] = df.apply(
        lambda r: ((r["os_atual"] - r["os_anterior"]) / r["os_anterior"] * 100)
        if r["os_anterior"] > 0 else (100 if r["os_atual"] > 0 else 0), axis=1
    )

    cond_cresc_fat = df["variacao_fat"] > 20
    cond_cresc_os = df["variacao_os"] > 20

    df_result = df[cond_cresc_fat | cond_cresc_os].copy()

    df_result["variacao"] = df_result.apply(
        lambda r: max(r["variacao_fat"], r["variacao_os"]), axis=1
    )

    df_result["faturamento"] = df_result["fat_atual"]

    df_result = df_result.rename(columns={"razao_social": "cliente"})

    return df_result[[
        "cliente", "cidade", "estado", "variacao", "faturamento"
    ]].sort_values("variacao", ascending=False).reset_index(drop=True)


# ──────────────────────────────────────────────
# CLIENTES SEM VISITA
# ──────────────────────────────────────────────

def get_clientes_sem_visita(unidade: Optional[str] = None) -> pd.DataFrame:
    """
    Clientes nunca visitados (ultima_visita IS NULL) OU com última visita > 90 dias.
    
    Retorna:
    - cliente
    - dias_sem_visita (NULL = 'Nunca' na exibição)
    - cidade
    - tipo: 'NUNCA_VISITADO' | 'VISITA_ATRASADA'
    
    Ordenados: primeiro nunca visitados, depois por maior tempo sem visita.
    """
    conn = _get_conn()
    data_limite = _data_limite(LIMITE_DIAS_SEM_VISITA)

    query = """
    SELECT
        c.razao_social AS cliente,
        c.cidade,
        CASE
            WHEN c.ultima_visita IS NULL THEN NULL
            ELSE CAST(julianday('now') - julianday(c.ultima_visita) AS INTEGER)
        END AS dias_sem_visita,
        CASE
            WHEN c.ultima_visita IS NULL THEN 'NUNCA_VISITADO'
            ELSE 'VISITA_ATRASADA'
        END AS tipo
    FROM clientes c
    WHERE c.status = 'ATIVO'
      AND (
          c.ultima_visita IS NULL
          OR c.ultima_visita <= ?
      )
    """
    params = [data_limite]
    if unidade:
        query += " AND (SELECT COUNT(*) FROM faturamento f WHERE f.cliente_id = c.id AND f.unidade = ?) > 0"
        params.append(unidade)

    query += " ORDER BY tipo ASC, dias_sem_visita DESC"

    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


# ──────────────────────────────────────────────
# CLIENTES SEM FATURAMENTO
# ──────────────────────────────────────────────

def get_clientes_sem_faturamento(unidade: Optional[str] = None) -> pd.DataFrame:
    """
    Clientes sem faturamento nos últimos 12 meses,
    mas que possuem máquinas Mitsubishi OU histórico de OS.
    """
    conn = _get_conn()
    data_limite = _data_limite(LIMITE_MESES_SEM_FATURAMENTO * 30)

    # Clientes sem faturamento nos últimos 12 meses
    query_base = """
    SELECT DISTINCT c.id, c.razao_social AS cliente
    FROM clientes c
    WHERE c.status = 'ATIVO'
      AND (
          c.ultimo_faturamento IS NULL
          OR c.ultimo_faturamento < ?
      )
      AND (
          EXISTS (SELECT 1 FROM maquinas_mitsubishi m WHERE m.cliente_id = c.id)
          OR
          EXISTS (SELECT 1 FROM ordens_servico os WHERE os.cliente_id = c.id)
      )
    """
    params_base = [data_limite]
    if unidade:
        query_base += """
      AND EXISTS (SELECT 1 FROM ordens_servico os2 WHERE os2.cliente_id = c.id AND os2.unidade = ?)
        """
        params_base.append(unidade)

    df_base = pd.read_sql_query(query_base, conn, params=params_base)

    if df_base.empty:
        conn.close()
        return pd.DataFrame(columns=["cliente", "máquinas", "última OS", "último faturamento"])

    ids = tuple(df_base["id"].tolist())
    placeholders = ",".join("?" * len(ids))

    # Máquinas Mitsubishi
    query_maq = f"""
    SELECT cliente_id, COUNT(*) AS qtd_maquinas
    FROM maquinas_mitsubishi
    WHERE cliente_id IN ({placeholders})
    GROUP BY cliente_id
    """
    df_maq = pd.read_sql_query(query_maq, conn, params=ids)

    # Última OS
    query_ult_os = f"""
    SELECT cliente_id, MAX(data_recebimento) AS ultima_os
    FROM ordens_servico
    WHERE cliente_id IN ({placeholders})
    GROUP BY cliente_id
    """
    params_ult_os = list(ids)
    if unidade:
        query_ult_os += " AND unidade = ?"
        params_ult_os.append(unidade)
    df_ult_os = pd.read_sql_query(query_ult_os, conn, params=params_ult_os)

    # Último faturamento
    query_ult_fat = f"""
    SELECT cliente_id, MAX(data_faturamento) AS ultimo_faturamento
    FROM faturamento
    WHERE cliente_id IN ({placeholders})
    GROUP BY cliente_id
    """
    params_ult_fat = list(ids)
    if unidade:
        query_ult_fat += " AND unidade = ?"
        params_ult_fat.append(unidade)
    df_ult_fat = pd.read_sql_query(query_ult_fat, conn, params=params_ult_fat)

    conn.close()

    df = df_base.merge(df_maq, left_on="id", right_on="cliente_id", how="left")
    df = df.merge(df_ult_os, left_on="id", right_on="cliente_id", how="left")
    df = df.merge(df_ult_fat, left_on="id", right_on="cliente_id", how="left")

    df["máquinas"] = df["qtd_maquinas"].fillna(0).astype(int)
    df["última OS"] = df["ultima_os"].fillna("Nunca")
    df["último faturamento"] = df["ultimo_faturamento"].fillna("Nunca")

    return df[["cliente", "máquinas", "última OS", "último faturamento"]]


# ──────────────────────────────────────────────
# CLIENTES COM MUITAS OS
# ──────────────────────────────────────────────

def get_clientes_muitas_os(unidade: Optional[str] = None) -> pd.DataFrame:
    """
    Top 20 clientes por quantidade de OS nos últimos 12 meses.
    """
    conn = _get_conn()
    data_limite = _data_limite(LIMITE_MESES_SEM_FATURAMENTO * 30)

    query = """
    SELECT
        c.razao_social AS cliente,
        COUNT(os.id) AS qtd_os,
        SUM(COALESCE(CAST(os.valor_estimado AS REAL), 0) + COALESCE(CAST(os.valor_proposta AS REAL), 0)) AS valor_total
    FROM ordens_servico os
    INNER JOIN clientes c ON os.cliente_id = c.id
    WHERE os.data_recebimento >= ?
    """
    params = [data_limite]
    if unidade:
        query += " AND os.unidade = ?"
        params.append(unidade)

    query += """
    GROUP BY os.cliente_id
    ORDER BY qtd_os DESC
    LIMIT ?
    """
    params.append(TOP_N)

    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


# ──────────────────────────────────────────────
# CLIENTES COM PARQUE MITSUBISHI RELEVANTE
# ──────────────────────────────────────────────

def get_clientes_parque_relevante(unidade: Optional[str] = None) -> pd.DataFrame:
    """
    Top 20 clientes por quantidade de máquinas Mitsubishi.
    """
    conn = _get_conn()

    query = """
    SELECT
        c.razao_social AS cliente,
        COUNT(m.id) AS quantidade_maquinas
    FROM maquinas_mitsubishi m
    INNER JOIN clientes c ON m.cliente_id = c.id
    WHERE c.status = 'ATIVO'
    """
    params = []
    if unidade:
        query += """
      AND EXISTS (SELECT 1 FROM ordens_servico os WHERE os.cliente_id = c.id AND os.unidade = ?)
        """
        params.append(unidade)

    query += """
    GROUP BY c.id
    ORDER BY quantidade_maquinas DESC
    LIMIT ?
    """
    params.append(TOP_N)

    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


# ──────────────────────────────────────────────
# SCORE COMERCIAL v1.5.2 — PRIORIZAÇÃO INTELIGENTE
# ──────────────────────────────────────────────

def calcular_score_comercial(unidade: Optional[str] = None) -> pd.DataFrame:
    """
    Calcula score comercial real de 0 a 100 para cada cliente ativo.
    
    Pesos v1.5.2:
    - Máquinas Mitsubishi (Muito Alto): 30 pts
    - Faturamento 12m (Muito Alto): 30 pts
    - Classe ABCD (Alto): 15 pts
    - Dias sem contato (Médio): 10 pts
    - Dias sem visita (Médio): 10 pts
    - Queda faturamento (Complementar): 3 pts
    - Preventivas vencidas (Complementar): 1 pt
    - Oportunidades abertas (Complementar): 1 pt
    
    Penalização:
    - Cliente com pendência comercial ABERTA ou oportunidade ABERTA: -40 pts
    
    Integração com Relacionamento Comercial:
    - Clientes já sendo trabalhados são fortemente penalizados ou podem ser excluídos.
    """
    conn = _get_conn()
    hoje = date.today().strftime("%Y-%m-%d")
    data_12m = _data_limite(365)

    # 1. Clientes base
    query_clientes = """
    SELECT id, razao_social, cidade, estado, ultima_visita,
           COALESCE(faturamento_12m, 0) AS faturamento_12m
    FROM clientes
    WHERE status = 'ATIVO'
    """
    params_clientes = []
    if unidade:
        query_clientes += """
      AND EXISTS (SELECT 1 FROM faturamento f WHERE f.cliente_id = clientes.id AND f.unidade = ?)
        """
        params_clientes.append(unidade)

    df = pd.read_sql_query(query_clientes, conn, params=params_clientes)

    if df.empty:
        conn.close()
        return pd.DataFrame(columns=["cliente", "cidade", "score", "classificacao"])

    ids = df["id"].tolist()
    placeholders_ids = ",".join("?" * len(ids))

    # 2. Faturamento 12 meses (para clientes sem faturamento_12m preenchido)
    query_fat = f"""
    SELECT cliente_id, SUM(CAST(valor AS REAL)) AS fat_12m_calculado
    FROM faturamento
    WHERE cliente_id IN ({placeholders_ids})
      AND data_faturamento >= ?
    """
    params_fat = list(ids) + [data_12m]
    if unidade:
        query_fat += " AND unidade = ?"
        params_fat.append(unidade)
    query_fat += " GROUP BY cliente_id"
    df_fat = pd.read_sql_query(query_fat, conn, params=params_fat)

    # 3. Máquinas Mitsubishi
    query_maq = f"""
    SELECT cliente_id, COUNT(*) AS qtd_maquinas
    FROM maquinas_mitsubishi
    WHERE cliente_id IN ({placeholders_ids})
    GROUP BY cliente_id
    """
    df_maq = pd.read_sql_query(query_maq, conn, params=ids)

    # 4. Última interação (dias sem contato)
    query_contato = f"""
    SELECT cliente_id, MAX(data_interacao) AS ultima_interacao
    FROM interacoes
    WHERE cliente_id IN ({placeholders_ids})
    GROUP BY cliente_id
    """
    df_contato = pd.read_sql_query(query_contato, conn, params=ids)

    # 5. Oportunidades abertas (para análise geral)
    query_opp = f"""
    SELECT cliente_id, COUNT(*) AS opp_abertas
    FROM oportunidades
    WHERE cliente_id IN ({placeholders_ids})
      AND status IN ('ABERTA', 'EM ANDAMENTO', 'NEGOCIACAO')
    """
    params_opp = list(ids)
    if unidade:
        query_opp += " AND unidade = ?"
        params_opp.append(unidade)
    query_opp += " GROUP BY cliente_id"
    df_opp = pd.read_sql_query(query_opp, conn, params=params_opp)

    # 6. Queda de faturamento (últimos 90 dias vs 90 dias anteriores)
    data_90d = _data_limite(90)
    data_180d = _data_limite(180)
    
    query_queda_fat = f"""
    SELECT 
        cliente_id,
        SUM(CASE WHEN data_faturamento >= ? THEN CAST(valor AS REAL) ELSE 0 END) AS fat_90d,
        SUM(CASE WHEN data_faturamento >= ? AND data_faturamento < ? THEN CAST(valor AS REAL) ELSE 0 END) AS fat_180d
    FROM faturamento
    WHERE cliente_id IN ({placeholders_ids})
    """
    params_queda = [data_90d, data_180d, data_90d] + list(ids)
    if unidade:
        query_queda_fat += " AND unidade = ?"
        params_queda.append(unidade)
    query_queda_fat += " GROUP BY cliente_id"
    df_queda = pd.read_sql_query(query_queda_fat, conn, params=params_queda)

    # 7. Preventivas vencidas (dias sem manutenção)
    query_preventivas = f"""
    SELECT 
        os.cliente_id,
        CAST(julianday('now') - julianday(MAX(
            CASE WHEN os.status IN ('FATURADA', 'EXPEDIDA')
            THEN COALESCE(os.data_faturamento, os.data_expedicao)
            ELSE NULL END
        )) AS INTEGER) AS dias_sem_manutencao
    FROM ordens_servico os
    WHERE os.cliente_id IN ({placeholders_ids})
      AND os.status IN ('FATURADA', 'EXPEDIDA')
    """
    params_prev = list(ids)
    if unidade:
        query_preventivas += " AND os.unidade = ?"
        params_prev.append(unidade)
    query_preventivas += " GROUP BY os.cliente_id"
    df_prev = pd.read_sql_query(query_preventivas, conn, params=params_prev)

    conn.close()

    # Merge
    df = df.merge(df_fat, left_on="id", right_on="cliente_id", how="left")
    df = df.drop(columns=["cliente_id"], errors="ignore")
    df = df.merge(df_maq, left_on="id", right_on="cliente_id", how="left")
    df = df.drop(columns=["cliente_id"], errors="ignore")
    df = df.merge(df_contato, left_on="id", right_on="cliente_id", how="left")
    df = df.drop(columns=["cliente_id"], errors="ignore")
    df = df.merge(df_opp, left_on="id", right_on="cliente_id", how="left")
    df = df.drop(columns=["cliente_id"], errors="ignore")
    df = df.merge(df_queda, left_on="id", right_on="cliente_id", how="left")
    df = df.drop(columns=["cliente_id"], errors="ignore")
    df = df.merge(df_prev, left_on="id", right_on="cliente_id", how="left")
    df = df.drop(columns=["cliente_id"], errors="ignore")

    # Preencher NaN
    df["fat_12m"] = df["faturamento_12m"].fillna(0)
    mask_fat_zero = df["fat_12m"] == 0
    df.loc[mask_fat_zero, "fat_12m"] = df.loc[mask_fat_zero, "fat_12m_calculado"].fillna(0)
    
    df["qtd_maquinas"] = df["qtd_maquinas"].fillna(0)
    df["opp_abertas"] = df["opp_abertas"].fillna(0)
    df["fat_90d"] = df["fat_90d"].fillna(0)
    df["fat_180d"] = df["fat_180d"].fillna(0)
    df["dias_sem_manutencao"] = df["dias_sem_manutencao"].fillna(0)

    # Calcular dias sem contato e sem visita
    df["dias_sem_contato"] = df["ultima_interacao"].apply(_get_dias)
    df["dias_sem_visita"] = df["ultima_visita"].apply(_get_dias)

    # Calcular queda de faturamento (%)
    df["queda_fat_pct"] = df.apply(
        lambda r: ((r["fat_90d"] - r["fat_180d"]) / r["fat_180d"] * 100)
        if r["fat_180d"] > 0 else 0, axis=1
    )

    # Calcular classificação ABCD
    df_classificacao = classificar_abcd(unidade)
    df = df.merge(
        df_classificacao[["id", "classe_abc"]],
        on="id",
        how="left"
    )
    df["classe_abc"] = df["classe_abc"].fillna("D")

    # ── MELHORIA 1: Verificar relacionamento ativo ──
    rel_ativo_map = _verificar_relacionamento_ativo(ids)
    df["relacionamento_ativo"] = df["id"].map(rel_ativo_map).fillna(False)

    # ── NORMALIZAÇÃO DOS PESOS v1.5.2 ──
    # Score base = somatório de cada componente normalizado (0-100)
    df["score"] = 0.0

    # 1. Máquinas Mitsubishi (30 pts) - peso MUITO ALTO
    max_maq = df["qtd_maquinas"].max()
    if max_maq > 0:
        df["score"] += _normalizar_log(df["qtd_maquinas"], max_maq) * PESO_MAQUINAS_MITSUBISHI

    # 2. Faturamento 12m (30 pts) - peso MUITO ALTO (usando normalização log)
    max_fat = df["fat_12m"].max()
    if max_fat > 0:
        df["score"] += _normalizar_log(df["fat_12m"], max_fat) * PESO_FATURAMENTO

    # 3. Classe ABC (15 pts) - peso ALTO
    peso_classe = {"A": 15, "B": 10, "C": 5, "D": 0}
    df["score"] += df["classe_abc"].map(peso_classe).fillna(0)

    # 4. Dias sem contato (10 pts) - peso MÉDIO
    # Quanto MAIS dias sem contato, MAIOR o score (precisa de ação)
    df["score"] += df["dias_sem_contato"].apply(
        lambda d: min(PESO_DIAS_SEM_CONTATO, PESO_DIAS_SEM_CONTATO * (min(d, 365) / 365))
    )

    # 5. Dias sem visita (10 pts) - peso MÉDIO
    df["score"] += df["dias_sem_visita"].apply(
        lambda d: min(PESO_DIAS_SEM_VISITA, PESO_DIAS_SEM_VISITA * (min(d, 365) / 365))
    )

    # 6. Queda faturamento (3 pts) - complementar
    # Queda negativa = GANHA pontos (precisa de atenção)
    df["score"] += df["queda_fat_pct"].apply(
        lambda q: min(PESO_QUEDA_FATURAMENTO, PESO_QUEDA_FATURAMENTO * (abs(min(q, 0)) / 100))
    )

    # 7. Preventivas vencidas (1 pt) - complementar
    df["score"] += df["dias_sem_manutencao"].apply(
        lambda d: min(PESO_PREVENTIVAS_VENCIDAS, PESO_PREVENTIVAS_VENCIDAS * (min(d, 730) / 730))
    )

    # 8. Oportunidades abertas (1 pt) - complementar
    max_opp = df["opp_abertas"].max()
    if max_opp > 0:
        df["score"] += (df["opp_abertas"] / max_opp) * PESO_OPORTUNIDADES

    # ── MELHORIA 1: Penalização por relacionamento ativo ──
    # Se cliente já possui pendência ABERTA ou oportunidade ABERTA,
    # aplica penalização forte no score
    df.loc[df["relacionamento_ativo"], "score"] -= PENALIDADE_RELACIONAMENTO_ATIVO

    # Arredondar e limitar 0-100
    df["score"] = df["score"].clip(0, 100).round(1)

    # Classificação por score
    def classificar_score(score):
        if score >= 80:
            return "AAA"
        elif score >= 60:
            return "AA"
        elif score >= 40:
            return "A"
        elif score >= 20:
            return "B"
        else:
            return "C"

    df["classificacao"] = df["score"].apply(classificar_score)

    # ── MELHORIA 3: Motivo da Prioridade Explicável ──
    def gerar_motivo(row):
        partes = []
        # Classe
        if row["classe_abc"] in ("A", "B"):
            partes.append(f"Classe {row['classe_abc']}")
        # Máquinas Mitsubishi
        maq = int(row["qtd_maquinas"])
        if maq > 0:
            partes.append(f"{maq} máq. Mitsubishi")
        # Dias sem contato (se relevante)
        dias_ct = int(row["dias_sem_contato"])
        if dias_ct >= 30:
            partes.append(f"{dias_ct}d sem contato")
        # Dias sem visita (se relevante)
        dias_vs = int(row["dias_sem_visita"])
        if dias_vs >= 90:
            partes.append(f"sem visita há {dias_vs}d")
        elif dias_vs >= 30:
            partes.append(f"{dias_vs}d sem visita")
        # Queda faturamento
        queda = row["queda_fat_pct"]
        if queda < -30:
            partes.append(f"queda fat. {queda:.0f}%")
        elif queda < -15:
            partes.append(f"queda fat. {queda:.0f}%")
        # Preventivas vencidas
        if int(row["dias_sem_manutencao"]) >= 730:
            partes.append("preventiva vencida")
        # Oportunidades
        opp = int(row["opp_abertas"])
        if opp > 0:
            partes.append(f"{opp} oportunidade(s)")
        # Faturamento
        fat = row["fat_12m"]
        if fat > 0:
            if fat >= 100000:
                partes.append(f"R$ {fat:,.0f} fat. 12m")
        
        return " | ".join(partes) if partes else "Cliente com potencial comercial"

    df["motivo_prioridade"] = df.apply(gerar_motivo, axis=1)

    # ── MELHORIA 4: Ação Sugerida Contextual ──
    def sugerir_acao(row):
        dias_ct = int(row["dias_sem_contato"])
        dias_vs = int(row["dias_sem_visita"])
        queda = row["queda_fat_pct"]
        maq = int(row["qtd_maquinas"])
        classe = row["classe_abc"]
        prev_vencida = int(row["dias_sem_manutencao"]) >= 730
        opp = int(row["opp_abertas"])

        # Cliente estratégico abandonado
        if classe in ("A", "B") and (dias_ct >= 90 or dias_vs >= 120):
            return "Visita prioritária"
        
        # Cliente com queda de faturamento
        if queda < -30:
            return "Investigar perda de demanda"
        
        # Sem contato há muito tempo
        if dias_ct >= 60:
            return "Agendar ligação comercial"
        
        # Sem visita há muito tempo
        if dias_vs >= 90:
            return "Agendar visita presencial"
        
        # Preventiva vencida
        if prev_vencida:
            return "Oferecer preventiva"
        
        # Oportunidades abertas para acompanhar
        if opp > 0:
            return "Acompanhar oportunidades em aberto"
        
        # Cliente grande sem ação recente
        if classe == "A" and dias_ct >= 30:
            return "Manter relacionamento estratégico"
        
        # Cliente com muitas máquinas
        if maq >= 10:
            return "Propor preventivas e manutenção"
        
        # Cliente médio sem contato
        if dias_ct >= 30:
            return "Agendar contato comercial"
        
        return "Analisar carteira e planejar ação"

    df["proxima_acao"] = df.apply(sugerir_acao, axis=1)

    # ── MELHORIA 6: Explicabilidade do Score ──
    def gerar_explicacao_score(row):
        """Gera explicação legível de como o score foi calculado."""
        partes_expl = []
        
        maq = int(row["qtd_maquinas"])
        max_maq_global = df["qtd_maquinas"].max() if "qtd_maquinas" in df.columns else 1
        if max_maq_global > 0:
            pts_maq = round(_normalizar_log(maq, max_maq_global) * PESO_MAQUINAS_MITSUBISHI, 1)
        else:
            pts_maq = 0
        if pts_maq > 0:
            partes_expl.append(f"Máq.Mitsubishi: +{pts_maq}pts ({maq} máq.)")
        
        fat = row["fat_12m"]
        max_fat_global = df["fat_12m"].max() if "fat_12m" in df.columns else 1
        if max_fat_global > 0:
            pts_fat = round(_normalizar_log(fat, max_fat_global) * PESO_FATURAMENTO, 1)
        else:
            pts_fat = 0
        if pts_fat > 0:
            partes_expl.append(f"Faturamento: +{pts_fat}pts")
        
        pts_classe = peso_classe.get(row["classe_abc"], 0)
        if pts_classe > 0:
            partes_expl.append(f"Classe {row['classe_abc']}: +{pts_classe}pts")
        
        dias_ct = int(row["dias_sem_contato"])
        pts_ct = min(PESO_DIAS_SEM_CONTATO, PESO_DIAS_SEM_CONTATO * (min(dias_ct, 365) / 365))
        if pts_ct > 0:
            partes_expl.append(f"Dias s/contato: +{pts_ct:.1f}pts ({dias_ct}d)")
        
        dias_vs = int(row["dias_sem_visita"])
        pts_vs = min(PESO_DIAS_SEM_VISITA, PESO_DIAS_SEM_VISITA * (min(dias_vs, 365) / 365))
        if pts_vs > 0:
            partes_expl.append(f"Dias s/visita: +{pts_vs:.1f}pts ({dias_vs}d)")
        
        queda = row["queda_fat_pct"]
        pts_queda = min(PESO_QUEDA_FATURAMENTO, PESO_QUEDA_FATURAMENTO * (abs(min(queda, 0)) / 100))
        if pts_queda > 0:
            partes_expl.append(f"Queda fat.: +{pts_queda:.1f}pts ({queda:.0f}%)")
        
        if row["relacionamento_ativo"]:
            partes_expl.append(f"Penalidade relacionamento ativo: -{PENALIDADE_RELACIONAMENTO_ATIVO}pts")
        
        score_total = row["score"]
        partes_expl.append(f"= Score final: {score_total:.1f}")
        
        return "\n".join(partes_expl)

    df["explicacao_score"] = df.apply(gerar_explicacao_score, axis=1)

    df = df.rename(columns={"razao_social": "cliente"})

    # Colunas do resultado
    return df[[
        "cliente", "cidade", "score", "classificacao", "classe_abc",
        "fat_12m", "qtd_maquinas", "dias_sem_contato", "dias_sem_visita",
        "motivo_prioridade", "proxima_acao", "explicacao_score",
        "relacionamento_ativo", "queda_fat_pct", "dias_sem_manutencao"
    ]].sort_values("score", ascending=False).head(TOP_SCORE).reset_index(drop=True)


# ──────────────────────────────────────────────
# RESUMO EXECUTIVO
# ──────────────────────────────────────────────

def get_resumo_executivo(unidade: Optional[str] = None) -> dict:
    """
    Retorna dicionário com indicadores resumidos:
    - total_clientes
    - clientes_esfriando
    - clientes_esquentando
    - clientes_sem_visita
    - clientes_sem_faturamento
    - maquinas_monitoradas
    """
    conn = _get_conn()

    # Total clientes ativos
    query_total = "SELECT COUNT(*) AS total FROM clientes WHERE status = 'ATIVO'"
    params_total = []
    if unidade:
        query_total += " AND EXISTS (SELECT 1 FROM faturamento f WHERE f.cliente_id = clientes.id AND f.unidade = ?)"
        params_total.append(unidade)
    total_clientes = conn.execute(query_total, params_total).fetchone()[0]

    conn.close()

    # Usar funções existentes
    df_esfriando = get_clientes_esfriando(unidade)
    df_esquentando = get_clientes_esquentando(unidade)
    df_sem_visita = get_clientes_sem_visita(unidade)
    df_sem_faturamento = get_clientes_sem_faturamento(unidade)
    df_parque = get_clientes_parque_relevante(unidade)

    return {
        "total_clientes": total_clientes,
        "clientes_esfriando": len(df_esfriando),
        "clientes_esquentando": len(df_esquentando),
        "clientes_sem_visita": len(df_sem_visita),
        "clientes_sem_faturamento": len(df_sem_faturamento),
        "maquinas_monitoradas": int(df_parque["quantidade_maquinas"].sum()) if not df_parque.empty else 0,
    }