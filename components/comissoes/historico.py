"""Componente de UI do historico de fechamentos."""

from datetime import date

import pandas as pd
import streamlit as st

from components import tabela_padrao
from services.comissoes_consultas import listar_fechamentos_para_historico

def render():
    """Renderiza a aba de Historico."""
    hoje = date.today()

    st.markdown("### Historico de Fechamentos")

    col1, col2 = st.columns(2)
    with col1:
        anos = list(range(2020, 2031))
        ano = st.selectbox("Filtrar ano", options=["Todos"] + anos,
                           index=anos.index(hoje.year) + 1, key="historico_ano")
    with col2:
        parceiros_lista = []
        try:
            from services.comissoes_consultas import listar_parceiros_com_carteira
            parceiros_lista = [""] + [p["nome"] for p in listar_parceiros_com_carteira()]
        except Exception:
            pass
        parceiro_filtro = st.selectbox("Filtrar parceiro", options=parceiros_lista,
                                        key="historico_parceiro")

    ano_int = None if ano == "Todos" else int(ano)
    fechamentos = listar_fechamentos_para_historico(ano=ano_int)

    if parceiro_filtro:
        fechamentos = [f for f in fechamentos
                       if f["parceiro_nome"].lower() == parceiro_filtro.lower()]

    if not fechamentos:
        st.info("Nenhum fechamento encontrado para os filtros selecionados.")
        return

    dados = []
    for f in fechamentos:
        dados.append({
            "Competencia": f["competencia"],
            "Parceiro": f["parceiro_nome"],
            "Clientes": f["quantidade_clientes"],
            "Base": f["base_calculo"],
            "Valor Bruto": f"R$ {f['valor_bruto']:,.2f}",
            "Valor Liquido": f"R$ {f['valor_liquido']:,.2f}",
            "Comissao": f"R$ {f['valor_comissao']:,.2f}",
            "Status": f["status"],
            "Fechado em": f["fechado_em"] or "-",
            "Pago em": f["data_pagamento"] or "-",
        })

    tabela_padrao(pd.DataFrame(dados), height=450)

    # Totais
    st.divider()
    total_comissao = sum(f["valor_comissao"] for f in fechamentos)
    total_pago = sum(f["valor_comissao"] for f in fechamentos if f["status"] == "PAGO")
    total_pendente = sum(f["valor_comissao"] for f in fechamentos if f["status"] == "FECHADO")

    col_t1, col_t2, col_t3 = st.columns(3)
    with col_t1:
        st.metric("Total Fechado", f"R$ {total_comissao:,.2f}")
    with col_t2:
        st.metric("Total Pago", f"R$ {total_pago:,.2f}")
    with col_t3:
        st.metric("Total Pendente", f"R$ {total_pendente:,.2f}")