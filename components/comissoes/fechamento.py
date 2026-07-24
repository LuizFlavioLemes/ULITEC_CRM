"""Componente de UI do fechamento mensal."""

from datetime import date

import pandas as pd
import streamlit as st

from components import mensagem_sucesso, mensagem_atencao, tabela_padrao
from services.comissoes_calculo import projetar_comissao_mes
from services.comissoes_fechamento import fechar_competencia, registrar_pagamento
from services.comissoes_consultas import listar_fechamentos_para_historico
from services.comissoes_dashboard import resumo_competencia

MESES_NOME = ["Janeiro", "Fevereiro", "Marco", "Abril", "Maio", "Junho",
              "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

def render():
    """Renderiza a aba de Fechamento Mensal."""
    hoje = date.today()

    st.markdown("### Conferir Fechamento")
    st.caption(
        "Os valores exibidos sao projecoes dinamicas com base no faturamento atual. "
        "O fechamento oficial ocorre apenas apos a confirmacao da competencia."
    )

    col1, col2 = st.columns(2)
    with col1:
        ano = st.number_input("Ano", min_value=2020, max_value=2030,
                              value=hoje.year, step=1, key="fechamento_ano")
    with col2:
        mes = st.selectbox("Mes", options=list(range(1, 13)),
                           format_func=lambda m: MESES_NOME[m - 1],
                           index=hoje.month - 1, key="fechamento_mes")

    competencia = f"{ano:04d}-{mes:02d}"

    # Verificar se ja existe fechamento
    existentes = listar_fechamentos_para_historico(ano=ano)
    ja_fechado = any(f["competencia"] == competencia
                     and f["status"] == "FECHADO" for f in existentes)
    ja_pago = any(f["competencia"] == competencia
                  and f["status"] == "PAGO" for f in existentes)

    if ja_pago:
        st.success(f"Competencia {competencia} esta **PAGA**.")
        resumo = resumo_competencia(competencia)
        if resumo:
            st.metric("Total comissao", f"R$ {resumo['total_comissao']:,.2f}")
        return

    if ja_fechado:
        st.success(f"Competencia {competencia} ja esta **FECHADA**.")
        resumo = resumo_competencia(competencia)
        if resumo:
            st.metric("Total comissao", f"R$ {resumo['total_comissao']:,.2f}")

            # Pagamento
            st.divider()
            st.markdown("### Registrar Pagamento")
            fechados = [f for f in existentes
                        if f["competencia"] == competencia and f["status"] == "FECHADO"]
            if fechados:
                nomes = [f["parceiro_nome"] for f in fechados]
                sel_parceiro = st.selectbox("Selecionar parceiro para pagamento",
                                             options=nomes, key="sel_pagamento")
                sel_f = next(f for f in fechados if f["parceiro_nome"] == sel_parceiro)
                obs = st.text_area("Observacao do pagamento", height=60)
                if st.button("Confirmar Pagamento", type="primary"):
                    registrar_pagamento(sel_f["id"], obs)
                    mensagem_sucesso("Pagamento registrado!")
                    st.rerun()
        return

    # Projecao para conferencia
    st.divider()
    st.markdown(f"**Conferencia para {competencia}**")

    projecao = projetar_comissao_mes(ano, mes)

    if not projecao:
        st.info("Nenhum parceiro com carteira ativa para esta competencia.")
        return

    dados = []
    total_bruto = 0
    total_liquido = 0
    total_comissao = 0

    for p in projecao:
        dados.append({
            "Parceiro": p["parceiro_nome"],
            "Clientes": p["total_clientes"],
            "Faturamento Considerado": p["faturamento_considerado"],
            "Valor Bruto": f"R$ {p['valor_bruto']:,.2f}",
            "Valor Liquido": f"R$ {p['valor_liquido']:,.2f}",
            "Comissao": f"R$ {p['valor_comissao']:,.2f}",
        })
        total_bruto += p["valor_bruto"]
        total_liquido += p["valor_liquido"]
        total_comissao += p["valor_comissao"]

    tabela_padrao(pd.DataFrame(dados), height=250)

    st.markdown("---")
    col_totais = st.columns(3)
    with col_totais[0]:
        st.metric("Total Bruto", f"R$ {total_bruto:,.2f}")
    with col_totais[1]:
        st.metric("Total Liquido", f"R$ {total_liquido:,.2f}")
    with col_totais[2]:
        st.metric("Total Comissao", f"R$ {total_comissao:,.2f}")

    st.divider()

    if st.button("Confirmar Fechamento", type="primary", width="stretch"):
        ids = fechar_competencia(competencia)
        if ids:
            mensagem_sucesso(f"Competencia {competencia} fechada com sucesso! "
                             f"{len(ids)} parceiro(s) processado(s).")
            st.rerun()
        else:
            mensagem_atencao("Nenhum registro foi fechado. "
                             "Verifique se ja nao existe fechamento para esta competencia.")