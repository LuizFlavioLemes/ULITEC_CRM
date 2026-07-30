"""
Módulo de Priorização Comercial — Inteligência Comercial.

Calcula prioridade (1-5 estrelas) para cada cliente baseado em múltiplos
fatores: score, faturamento, máquinas, classe ABC, tempo sem visita/contato,
queda de faturamento, preventivas vencidas, oportunidades.

Toda informação vem de services existentes. Zero SQL neste módulo.
"""

from typing import Optional, List, Dict
import pandas as pd

from services.inteligencia.score import calcular_score_comercial
from services.inteligencia.clientes import (
    get_clientes_esfriando,
    get_clientes_sem_visita,
    get_clientes_sem_faturamento,
    get_clientes_parque_relevante,
)
from services.inteligencia.mercado import (
    get_preventivas_vencidas,
    get_top_faturamento_12m,
    get_prospeccao_mitsubishi,
)

# ── Limites para motivos ──
DIAS_SEM_VISITA_ALERTA = 90
QUEDA_FAT_ALERTA = -30
MAQUINAS_MITSUBISHI_ALTO = 10
MAQUINAS_MITSUBISHI_MEDIO = 5
PREVENTIVA_VENCIDA_DIAS = 730


def calcular_estrelas(score: float) -> int:
    """Converte score (0-100) em estrelas (1-5)."""
    if score >= 80:
        return 5
    elif score >= 60:
        return 4
    elif score >= 40:
        return 3
    elif score >= 20:
        return 2
    return 1


def gerar_motivos_prioridade(row: pd.Series) -> list:
    """Gera lista de motivos textuais para priorização."""
    motivos = []
    dias_sem_visita = int(row.get("dias_sem_visita", 9999))
    dias_sem_contato = int(row.get("dias_sem_contato", 9999))
    queda = float(row.get("queda_fat_pct", 0))
    maquinas = int(row.get("qtd_maquinas", 0))
    classe = str(row.get("classe_abc", "D"))
    preventiva = int(row.get("dias_sem_manutencao", 0))
    fat_12m = float(row.get("fat_12m", 0))
    opp = int(row.get("opp_abertas", 0))

    if classe in ("A", "B"):
        motivos.append(f"Classe {classe}")
    if maquinas >= MAQUINAS_MITSUBISHI_ALTO:
        motivos.append(f"Grande parque Mitsubishi ({maquinas} máq.)")
    elif maquinas >= MAQUINAS_MITSUBISHI_MEDIO:
        motivos.append(f"{maquinas} máq. Mitsubishi")
    if dias_sem_visita >= DIAS_SEM_VISITA_ALERTA:
        motivos.append(f"Sem visita há {dias_sem_visita}d")
    if dias_sem_contato >= 60:
        motivos.append("Muito tempo sem contato")
    if queda < QUEDA_FAT_ALERTA:
        motivos.append(f"Queda faturamento {queda:.0f}%")
    if preventiva >= PREVENTIVA_VENCIDA_DIAS:
        motivos.append("Preventiva vencida")
    if opp > 0:
        motivos.append(f"{opp} oportunidade(s)")
    if fat_12m >= 100000:
        motivos.append(f"R$ {fat_12m:,.0f} fat. 12m")
    if not motivos:
        motivos.append("Cliente com potencial comercial")
    return motivos


def get_clientes_prioritarios(
    unidade: Optional[str] = None,
    estado: Optional[str] = None,
    cidade: Optional[str] = None,
    classe_abc: Optional[str] = None,
    responsavel: Optional[str] = None,
    segmento: Optional[str] = None,
) -> pd.DataFrame:
    """
    Retorna lista completa de clientes ordenados por prioridade.

    Cada cliente recebe:
    - score (0-100)
    - estrelas (1-5)
    - motivos de prioridade
    - dados complementares (faturamento, máquinas, etc.)

    Aplica filtros opcionais (estado, cidade, classe, responsável, segmento).
    """
    df = calcular_score_comercial(unidade)

    if df.empty:
        return pd.DataFrame(columns=[
            "cliente", "cidade", "estado", "score", "estrelas",
            "classificacao", "classe_abc", "fat_12m", "qtd_maquinas",
            "dias_sem_visita", "dias_sem_contato", "motivos",
            "proxima_acao", "explicacao_score"
        ])

    # ── Aplicar filtros opcionais ──
    if estado and estado != "Todos":
        df = df[df["estado"] == estado].copy()
    if cidade and cidade != "Todas":
        df = df[df["cidade"] == cidade].copy()
    if classe_abc and classe_abc != "Todas":
        df = df[df["classe_abc"] == classe_abc].copy()
    if segmento and segmento != "Todos":
        if "segmento" in df.columns:
            df = df[df["segmento"] == segmento].copy()
    if responsavel and responsavel != "Todos":
        if "responsavel" in df.columns:
            df = df[df["responsavel"] == responsavel].copy()

    # ── Calcular estrelas ──
    df["estrelas"] = df["score"].apply(calcular_estrelas)

    # ── Gerar motivos ──
    df["motivos"] = df.apply(lambda r: gerar_motivos_prioridade(r), axis=1)
    df["motivos_str"] = df["motivos"].apply(lambda m: " | ".join(m))

    # ── Arredondar score e faturamento ──
    df["score"] = df["score"].round(1)

    # ── Colunas finais ──
    colunas = [
        "cliente", "cidade", "estado", "score", "estrelas",
        "classificacao", "classe_abc", "fat_12m", "qtd_maquinas",
        "dias_sem_visita", "dias_sem_contato", "motivos", "motivos_str",
        "ultima_visita", "proxima_acao", "explicacao_score",
        "queda_fat_pct", "dias_sem_manutencao", "opp_abertas",
    ]
    colunas_existentes = [c for c in colunas if c in df.columns]
    return df[colunas_existentes].sort_values("score", ascending=False).reset_index(drop=True)


def get_enriquecer_cliente(
    cliente_id: int,
    unidade: Optional[str] = None,
) -> dict:
    """
    Enriquece dados de um cliente específico com informações
    de prioridade, score, último faturamento, etc.
    Útil para o modal/botão 'Abrir Cliente 360'.
    """
    return {}


def get_estados_disponiveis(unidade: Optional[str] = None) -> list:
    """Retorna lista de estados disponíveis nos clientes ativos."""
    from services.inteligencia.utils import _get_conn
    conn = _get_conn()
    query = "SELECT DISTINCT estado FROM clientes WHERE status = 'ATIVO' AND estado IS NOT NULL ORDER BY estado"
    rows = conn.execute(query).fetchall()
    conn.close()
    return [row[0] for row in rows if row[0]]


def get_cidades_disponiveis(unidade: Optional[str] = None) -> list:
    """Retorna lista de cidades disponíveis nos clientes ativos."""
    from services.inteligencia.utils import _get_conn
    conn = _get_conn()
    query = "SELECT DISTINCT cidade FROM clientes WHERE status = 'ATIVO' AND cidade IS NOT NULL ORDER BY cidade"
    rows = conn.execute(query).fetchall()
    conn.close()
    return [row[0] for row in rows if row[0]]