"""Componente de UI do Dashboard de Comissoes."""

import pandas as pd
import streamlit as st

from services.comissoes_dashboard import (
    indicadores_gerais, indicadores_por_periodo,
    top_parceiros, top_clientes, _calcular_periodo,
)
from services.comissoes_calculo import projetar_comissao_mes
from services.comissoes_db import query_comissoes_avulsas_vencidas
from components import linha_indicadores, tabela_padrao, mensagem_atencao

PERIODOS = [
    "Mes atual", "Mes anterior", "Ultimos 3 meses",
    "Ultimos 6 meses", "Ultimos 12 meses", "Ano atual",
]

def render():
    """Renderiza a aba de Dashboard."""
    periodo = st.selectbox(
        "Periodo de analise", options=PERIODOS, key="filtro_dashboard"
    )

    # Item 2: Alerta de avulsas vencidas
    avulsas_vencidas = query_comissoes_avulsas_vencidas()
    if avulsas_vencidas:
        qtd = len(avulsas_vencidas)
        mensagem_atencao(
            f"Existem {qtd} comissoes aguardando conferencia de pagamento."
        )

    # Calcular indicadores conforme periodo
    kpis = indicadores_gerais()
    data_ini, data_fim = _calcular_periodo(periodo)

    # Extrair ano/mes para consulta de periodo
    hoje = __import__("datetime", fromlist=["date"]).date.today()
    if periodo == "Mes atual":
        kpis_periodo = indicadores_por_periodo(hoje.year, hoje.month)
    elif periodo == "Mes anterior":
        mes_ant = hoje.month - 1 if hoje.month > 1 else 12
        ano_ant = hoje.year if hoje.month > 1 else hoje.year - 1
        kpis_periodo = indicadores_por_periodo(ano_ant, mes_ant)
    elif periodo == "Ano atual":
        kpis_periodo = indicadores_por_periodo(hoje.year)
    elif periodo == "Todo periodo":
        kpis_periodo = indicadores_por_periodo(2020)
    else:
        # Ultimos 3/6/12 meses: calcula agregado
        meses_map = {"Ultimos 3 meses": 3, "Ultimos 6 meses": 6, "Ultimos 12 meses": 12}
        qtd = meses_map.get(periodo, 3)
        mes_ref = hoje.month - qtd
        ano_ref = hoje.year
        while mes_ref < 1:
            mes_ref += 12
            ano_ref -= 1
        kpis_periodo = indicadores_por_periodo(ano_ref, mes_ref)
        # Soma mes a mes ate hoje
        total_fechado = 0
        total_pago = 0
        total_pendente = 0
        for m in range(qtd):
            m_atual = hoje.month - m
            a_atual = hoje.year
            while m_atual < 1:
                m_atual += 12
                a_atual -= 1
            parcial = indicadores_por_periodo(a_atual, m_atual)
            total_fechado += parcial["total_fechado"]
            total_pago += parcial["total_pago"]
            total_pendente += parcial["total_pendente"]
        kpis_periodo = {
            "total_fechamentos": 0,
            "quantidade_pagos": 0,
            "total_fechado": round(total_fechado, 2),
            "total_pago": round(total_pago, 2),
            "total_pendente": round(total_pendente, 2),
        }

    # Se for mes atual, projecao nos KPIs
    if periodo == "Mes atual":
        proj = projetar_comissao_mes(hoje.year, hoje.month)
        proj_total = sum(p["valor_comissao"] for p in proj) if proj else 0
    else:
        proj_total = 0

    linha_indicadores([
        {"rotulo": "Parceiros Ativos", "valor": kpis["parceiros_ativos"]},
        {"rotulo": "Carteiras", "valor": kpis["total_carteiras"]},
        {"rotulo": "Comissao Fechada",
         "valor": f"R$ {kpis_periodo['total_fechado']:,.2f}"},
        {"rotulo": "Comissao Paga",
         "valor": f"R$ {kpis_periodo['total_pago']:,.2f}"},
    ])

    linha_indicadores([
        {"rotulo": "Comissao Pendente",
         "valor": f"R$ {kpis_periodo['total_pendente']:,.2f}"},
        {"rotulo": "Comissao Projetada (mes)",
         "valor": f"R$ {proj_total:,.2f}" if proj_total > 0 else "-"},
        {"rotulo": "Maior Parceiro", "valor": kpis["maior_parceiro"]},
        {"rotulo": "Maior Cliente", "valor": "-"},
    ])

    st.divider()

    # Projecao do mes atual
    if periodo == "Mes atual":
        st.subheader("Projecao do Mes")
        projecao = projetar_comissao_mes(hoje.year, hoje.month)

        if projecao:
            df_proj = pd.DataFrame([{
                "Parceiro": p["parceiro_nome"],
                "Clientes": p["total_clientes"],
                "Valor Bruto": p["valor_bruto"],
                "Valor Liquido": p["valor_liquido"],
                "Comissao Projetada": p["valor_comissao"],
            } for p in projecao])
            total = df_proj["Comissao Projetada"].sum()
            tabela_padrao(df_proj, height=200)
            st.markdown(f"**Total comissao projetada do mes: R$ {total:,.2f}**")
        else:
            st.info("Nenhum parceiro com carteira ativa para projecao.")

        st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Top Parceiros")
        rp = top_parceiros(5)
        if rp:
            tabela_padrao(pd.DataFrame(rp), height=200)
        else:
            st.info("Nenhum fechamento ainda.")
    with col2:
        st.subheader("Top Clientes")
        rc = top_clientes(5)
        if rc:
            tabela_padrao(pd.DataFrame(rc), height=200)
        else:
            st.info("Nenhum fechamento ainda.")