"""
Módulo de Resumo Executivo — Inteligência Comercial.

Fornece indicadores resumidos da carteira de clientes.
"""

from typing import Optional

from services.inteligencia.utils import _get_conn
from services.inteligencia.clientes import (
    get_clientes_esfriando,
    get_clientes_esquentando,
    get_clientes_sem_visita,
    get_clientes_sem_faturamento,
    get_clientes_parque_relevante,
)


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
    query_total = "SELECT COUNT(*) AS total FROM clientes WHERE status = 'ATIVO'"
    params_total = []
    if unidade:
        query_total += " AND EXISTS (SELECT 1 FROM faturamento f WHERE f.cliente_id = clientes.id AND f.unidade = ?)"
        params_total.append(unidade)
    total_clientes = conn.execute(query_total, params_total).fetchone()[0]
    conn.close()

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