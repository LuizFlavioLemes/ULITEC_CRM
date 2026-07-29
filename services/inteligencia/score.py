"""
Módulo de Score Comercial — Inteligência Comercial v1.5.2.

Calcula o score comercial (0-100) para priorização inteligente de clientes.
"""

from datetime import date, timedelta
from typing import Optional

import pandas as pd
import numpy as np

from services.inteligencia.utils import (
    _get_conn, _data_limite, _get_dias, _normalizar_log,
    _verificar_relacionamento_ativo,
    PESO_MAQUINAS_MITSUBISHI, PESO_FATURAMENTO, PESO_CLASSE_ABC,
    PESO_DIAS_SEM_CONTATO, PESO_DIAS_SEM_VISITA,
    PESO_QUEDA_FATURAMENTO, PESO_PREVENTIVAS_VENCIDAS,
    PESO_OPORTUNIDADES, PENALIDADE_RELACIONAMENTO_ATIVO, TOP_SCORE,
)
from services.inteligencia.indicadores import classificar_abcd


def calcular_score_comercial(unidade: Optional[str] = None) -> pd.DataFrame:
    """
    Calcula score comercial real de 0 a 100 para cada cliente ativo.
    Retorna DataFrame com score, classificação, motivo e ação sugerida.
    """
    conn = _get_conn()
    hoje = date.today().strftime("%Y-%m-%d")
    data_12m = _data_limite(365)

    # 1. Clientes base
    query_clientes = """SELECT id, razao_social, cidade, estado, ultima_visita,
        COALESCE(faturamento_12m, 0) AS faturamento_12m
    FROM clientes WHERE status = 'ATIVO'"""
    params_clientes = []
    if unidade:
        query_clientes += " AND EXISTS (SELECT 1 FROM faturamento f WHERE f.cliente_id = clientes.id AND f.unidade = ?)"
        params_clientes.append(unidade)

    df = pd.read_sql_query(query_clientes, conn, params=params_clientes)
    if df.empty:
        conn.close()
        return pd.DataFrame(columns=["cliente", "cidade", "score", "classificacao"])

    ids = df["id"].tolist()
    placeholders_ids = ",".join("?" * len(ids))

    # 2. Faturamento 12 meses
    query_fat = f"""SELECT cliente_id, SUM(CAST(valor AS REAL)) AS fat_12m_calculado
    FROM faturamento WHERE cliente_id IN ({placeholders_ids}) AND data_faturamento >= ?"""
    params_fat = list(ids) + [data_12m]
    if unidade:
        query_fat += " AND unidade = ?"
        params_fat.append(unidade)
    query_fat += " GROUP BY cliente_id"
    df_fat = pd.read_sql_query(query_fat, conn, params=params_fat)

    # 3. Máquinas Mitsubishi
    query_maq = f"SELECT cliente_id, COUNT(*) AS qtd_maquinas FROM maquinas_mitsubishi WHERE cliente_id IN ({placeholders_ids}) GROUP BY cliente_id"
    df_maq = pd.read_sql_query(query_maq, conn, params=ids)

    # 4. Última interação
    query_contato = f"SELECT cliente_id, MAX(data_interacao) AS ultima_interacao FROM interacoes WHERE cliente_id IN ({placeholders_ids}) GROUP BY cliente_id"
    df_contato = pd.read_sql_query(query_contato, conn, params=ids)

    # 5. Oportunidades abertas
    query_opp = f"""SELECT cliente_id, COUNT(*) AS opp_abertas FROM oportunidades
    WHERE cliente_id IN ({placeholders_ids}) AND status IN ('ABERTA', 'EM ANDAMENTO', 'NEGOCIACAO')"""
    params_opp = list(ids)
    if unidade:
        query_opp += " AND unidade = ?"
        params_opp.append(unidade)
    query_opp += " GROUP BY cliente_id"
    df_opp = pd.read_sql_query(query_opp, conn, params=params_opp)

    # 6. Queda de faturamento
    data_90d = _data_limite(90)
    data_180d = _data_limite(180)
    query_queda_fat = f"""SELECT cliente_id,
        SUM(CASE WHEN data_faturamento >= ? THEN CAST(valor AS REAL) ELSE 0 END) AS fat_90d,
        SUM(CASE WHEN data_faturamento >= ? AND data_faturamento < ? THEN CAST(valor AS REAL) ELSE 0 END) AS fat_180d
    FROM faturamento WHERE cliente_id IN ({placeholders_ids})"""
    params_queda = [data_90d, data_180d, data_90d] + list(ids)
    if unidade:
        query_queda_fat += " AND unidade = ?"
        params_queda.append(unidade)
    query_queda_fat += " GROUP BY cliente_id"
    df_queda = pd.read_sql_query(query_queda_fat, conn, params=params_queda)

    # 7. Preventivas vencidas
    query_preventivas = f"""SELECT os.cliente_id,
        CAST(julianday('now') - julianday(MAX(
            CASE WHEN os.status IN ('FATURADA', 'EXPEDIDA')
            THEN COALESCE(os.data_faturamento, os.data_expedicao) ELSE NULL END
        )) AS INTEGER) AS dias_sem_manutencao
    FROM ordens_servico os WHERE os.cliente_id IN ({placeholders_ids})
      AND os.status IN ('FATURADA', 'EXPEDIDA')"""
    params_prev = list(ids)
    if unidade:
        query_preventivas += " AND os.unidade = ?"
        params_prev.append(unidade)
    query_preventivas += " GROUP BY os.cliente_id"
    df_prev = pd.read_sql_query(query_preventivas, conn, params=params_prev)

    conn.close()

    # Merge
    df = df.merge(df_fat, left_on="id", right_on="cliente_id", how="left").drop(columns=["cliente_id"], errors="ignore")
    df = df.merge(df_maq, left_on="id", right_on="cliente_id", how="left").drop(columns=["cliente_id"], errors="ignore")
    df = df.merge(df_contato, left_on="id", right_on="cliente_id", how="left").drop(columns=["cliente_id"], errors="ignore")
    df = df.merge(df_opp, left_on="id", right_on="cliente_id", how="left").drop(columns=["cliente_id"], errors="ignore")
    df = df.merge(df_queda, left_on="id", right_on="cliente_id", how="left").drop(columns=["cliente_id"], errors="ignore")
    df = df.merge(df_prev, left_on="id", right_on="cliente_id", how="left").drop(columns=["cliente_id"], errors="ignore")

    # Preencher NaN
    df["fat_12m"] = df["faturamento_12m"].fillna(0)
    mask_fat_zero = df["fat_12m"] == 0
    df.loc[mask_fat_zero, "fat_12m"] = df.loc[mask_fat_zero, "fat_12m_calculado"].fillna(0)
    df["qtd_maquinas"] = df["qtd_maquinas"].fillna(0)
    df["opp_abertas"] = df["opp_abertas"].fillna(0)
    df["fat_90d"] = df["fat_90d"].fillna(0)
    df["fat_180d"] = df["fat_180d"].fillna(0)
    df["dias_sem_manutencao"] = df["dias_sem_manutencao"].fillna(0)

    df["dias_sem_contato"] = df["ultima_interacao"].apply(_get_dias)
    df["dias_sem_visita"] = df["ultima_visita"].apply(_get_dias)

    df["queda_fat_pct"] = df.apply(
        lambda r: ((r["fat_90d"] - r["fat_180d"]) / r["fat_180d"] * 100) if r["fat_180d"] > 0 else 0, axis=1)

    df_classificacao = classificar_abcd(unidade)
    df = df.merge(df_classificacao[["id", "classe_abc"]], on="id", how="left")
    df["classe_abc"] = df["classe_abc"].fillna("D")

    rel_ativo_map = _verificar_relacionamento_ativo(ids)
    df["relacionamento_ativo"] = df["id"].map(rel_ativo_map).fillna(False)

    # Score
    df["score"] = 0.0
    max_maq = df["qtd_maquinas"].max()
    if max_maq > 0:
        df["score"] += _normalizar_log(df["qtd_maquinas"], max_maq) * PESO_MAQUINAS_MITSUBISHI

    max_fat = df["fat_12m"].max()
    if max_fat > 0:
        df["score"] += _normalizar_log(df["fat_12m"], max_fat) * PESO_FATURAMENTO

    peso_classe = {"A": 15, "B": 10, "C": 5, "D": 0}
    df["score"] += df["classe_abc"].map(peso_classe).fillna(0)
    df["score"] += df["dias_sem_contato"].apply(lambda d: min(PESO_DIAS_SEM_CONTATO, PESO_DIAS_SEM_CONTATO * (min(d, 365) / 365)))
    df["score"] += df["dias_sem_visita"].apply(lambda d: min(PESO_DIAS_SEM_VISITA, PESO_DIAS_SEM_VISITA * (min(d, 365) / 365)))
    df["score"] += df["queda_fat_pct"].apply(lambda q: min(PESO_QUEDA_FATURAMENTO, PESO_QUEDA_FATURAMENTO * (abs(min(q, 0)) / 100)))
    df["score"] += df["dias_sem_manutencao"].apply(lambda d: min(PESO_PREVENTIVAS_VENCIDAS, PESO_PREVENTIVAS_VENCIDAS * (min(d, 730) / 730)))

    max_opp = df["opp_abertas"].max()
    if max_opp > 0:
        df["score"] += (df["opp_abertas"] / max_opp) * PESO_OPORTUNIDADES

    df.loc[df["relacionamento_ativo"], "score"] -= PENALIDADE_RELACIONAMENTO_ATIVO
    df["score"] = df["score"].clip(0, 100).round(1)

    def classificar_score(score_val):
        if score_val >= 80: return "AAA"
        elif score_val >= 60: return "AA"
        elif score_val >= 40: return "A"
        elif score_val >= 20: return "B"
        else: return "C"

    df["classificacao"] = df["score"].apply(classificar_score)

    def gerar_motivo(row):
        partes = []
        if row["classe_abc"] in ("A", "B"):
            partes.append(f"Classe {row['classe_abc']}")
        maq = int(row["qtd_maquinas"])
        if maq > 0: partes.append(f"{maq} máq. Mitsubishi")
        dias_ct = int(row["dias_sem_contato"])
        if dias_ct >= 30: partes.append(f"{dias_ct}d sem contato")
        dias_vs = int(row["dias_sem_visita"])
        if dias_vs >= 90: partes.append(f"sem visita há {dias_vs}d")
        elif dias_vs >= 30: partes.append(f"{dias_vs}d sem visita")
        queda = row["queda_fat_pct"]
        if queda < -30: partes.append(f"queda fat. {queda:.0f}%")
        elif queda < -15: partes.append(f"queda fat. {queda:.0f}%")
        if int(row["dias_sem_manutencao"]) >= 730: partes.append("preventiva vencida")
        opp = int(row["opp_abertas"])
        if opp > 0: partes.append(f"{opp} oportunidade(s)")
        fat = row["fat_12m"]
        if fat > 0 and fat >= 100000: partes.append(f"R$ {fat:,.0f} fat. 12m")
        return " | ".join(partes) if partes else "Cliente com potencial comercial"

    df["motivo_prioridade"] = df.apply(gerar_motivo, axis=1)

    def sugerir_acao(row):
        dias_ct = int(row["dias_sem_contato"])
        dias_vs = int(row["dias_sem_visita"])
        queda = row["queda_fat_pct"]
        maq = int(row["qtd_maquinas"])
        classe = row["classe_abc"]
        prev_vencida = int(row["dias_sem_manutencao"]) >= 730
        opp = int(row["opp_abertas"])
        if classe in ("A", "B") and (dias_ct >= 90 or dias_vs >= 120): return "Visita prioritária"
        if queda < -30: return "Investigar perda de demanda"
        if dias_ct >= 60: return "Agendar ligação comercial"
        if dias_vs >= 90: return "Agendar visita presencial"
        if prev_vencida: return "Oferecer preventiva"
        if opp > 0: return "Acompanhar oportunidades em aberto"
        if classe == "A" and dias_ct >= 30: return "Manter relacionamento estratégico"
        if maq >= 10: return "Propor preventivas e manutenção"
        if dias_ct >= 30: return "Agendar contato comercial"
        return "Analisar carteira e planejar ação"

    df["proxima_acao"] = df.apply(sugerir_acao, axis=1)

    def gerar_explicacao_score(row):
        partes_expl = []
        maq_local = int(row["qtd_maquinas"])
        max_maq_global = df["qtd_maquinas"].max() if "qtd_maquinas" in df.columns else 1
        if max_maq_global > 0:
            pts_maq = round(_normalizar_log(maq_local, max_maq_global) * PESO_MAQUINAS_MITSUBISHI, 1)
        else:
            pts_maq = 0
        if pts_maq > 0: partes_expl.append(f"Máq.Mitsubishi: +{pts_maq}pts ({maq_local} máq.)")
        fat_local = row["fat_12m"]
        max_fat_global = df["fat_12m"].max() if "fat_12m" in df.columns else 1
        if max_fat_global > 0:
            pts_fat = round(_normalizar_log(fat_local, max_fat_global) * PESO_FATURAMENTO, 1)
        else:
            pts_fat = 0
        if pts_fat > 0: partes_expl.append(f"Faturamento: +{pts_fat}pts")
        pts_classe = peso_classe.get(row["classe_abc"], 0)
        if pts_classe > 0: partes_expl.append(f"Classe {row['classe_abc']}: +{pts_classe}pts")
        dias_ct_local = int(row["dias_sem_contato"])
        pts_ct = min(PESO_DIAS_SEM_CONTATO, PESO_DIAS_SEM_CONTATO * (min(dias_ct_local, 365) / 365))
        if pts_ct > 0: partes_expl.append(f"Dias s/contato: +{pts_ct:.1f}pts ({dias_ct_local}d)")
        dias_vs_local = int(row["dias_sem_visita"])
        pts_vs = min(PESO_DIAS_SEM_VISITA, PESO_DIAS_SEM_VISITA * (min(dias_vs_local, 365) / 365))
        if pts_vs > 0: partes_expl.append(f"Dias s/visita: +{pts_vs:.1f}pts ({dias_vs_local}d)")
        queda_local = row["queda_fat_pct"]
        pts_queda = min(PESO_QUEDA_FATURAMENTO, PESO_QUEDA_FATURAMENTO * (abs(min(queda_local, 0)) / 100))
        if pts_queda > 0: partes_expl.append(f"Queda fat.: +{pts_queda:.1f}pts ({queda_local:.0f}%)")
        if row["relacionamento_ativo"]: partes_expl.append(f"Penalidade relacionamento ativo: -{PENALIDADE_RELACIONAMENTO_ATIVO}pts")
        partes_expl.append(f"= Score final: {row['score']:.1f}")
        return "\n".join(partes_expl)

    df["explicacao_score"] = df.apply(gerar_explicacao_score, axis=1)
    df = df.rename(columns={"razao_social": "cliente"})

    return df[[
        "cliente", "cidade", "score", "classificacao", "classe_abc",
        "fat_12m", "qtd_maquinas", "dias_sem_contato", "dias_sem_visita",
        "motivo_prioridade", "proxima_acao", "explicacao_score",
        "relacionamento_ativo", "queda_fat_pct", "dias_sem_manutencao"
    ]].sort_values("score", ascending=False).head(TOP_SCORE).reset_index(drop=True)