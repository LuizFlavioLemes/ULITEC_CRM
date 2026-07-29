"""
Componente de Indicadores/KPIs da Central de Oportunidades.
Consome exclusivamente services/inteligencia_comercial e services/relacionamento.
Nenhum SQL é executado aqui.
"""

import streamlit as st

from services.inteligencia_comercial import (
    get_preventivas_vencidas,
    get_prospeccao_mitsubishi,
    calcular_score_comercial,
    get_resumo_executivo,
)


def exibir_indicadores(unidade_param=None):
    """
    Renderiza os 6 KPIs da Central de Oportunidades.

    Parâmetros:
        unidade_param: str or None — filtro de unidade
    """
    df_preventivas = get_preventivas_vencidas(unidade=unidade_param)
    df_novos_clientes = get_prospeccao_mitsubishi(unidade=unidade_param)
    df_score = calcular_score_comercial(unidade=unidade_param)
    resumo = get_resumo_executivo(unidade=unidade_param)

    kpi_cols = st.columns(6)

    kpi_cols[0].metric(
        "Preventivas Vencidas",
        len(df_preventivas),
        help="Clientes com mais de 730 dias sem manutenção"
    )

    kpi_cols[1].metric(
        "Prospecção Mitsubishi",
        len(df_novos_clientes),
        help="Empresas com máquinas Mitsubishi que nunca compraram da ULITEC"
    )

    kpi_cols[2].metric(
        "Clientes Esfriando",
        resumo["clientes_esfriando"],
        help="Clientes com queda de faturamento ou sem visita há mais de 120 dias"
    )

    kpi_cols[3].metric(
        "Clientes Esquentando",
        resumo["clientes_esquentando"],
        help="Clientes com crescimento de faturamento acima de 20%"
    )

    kpi_cols[4].metric(
        "Sem Visita",
        resumo["clientes_sem_visita"],
        help="Clientes sem visita há mais de 90 dias ou nunca visitados"
    )

    kpi_cols[5].metric(
        "Score Comercial",
        len(df_score),
        help="Clientes priorizados por potencial comercial"
    )