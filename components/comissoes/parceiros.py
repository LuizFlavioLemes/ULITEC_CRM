"""Componente de UI do cadastro de parceiros."""

import streamlit as st

from components import mensagem_sucesso
from services.parceiros import (
    criar_parceiro, atualizar_parceiro,
    ativar_parceiro, desativar_parceiro, excluir_parceiro,
    obter_ids_carteira, substituir_carteira,
)
from services.comissoes_db import query_parceiro_por_id
from services.comissoes_calculo import projetar_comissao_mes
from services.comissoes_consultas import (
    listar_parceiros_com_carteira, listar_clientes_para_select,
)

ESCOPOS = ["GRUPO", "ULITEC SP", "ULITEC RS"]
BASES = ["BRUTO", "LIQUIDO"]

def _render_form(editando_id=None):
    """Renderiza formulario integrado de parceiro + contrato + carteira."""
    editando = None
    if editando_id:
        editando = query_parceiro_por_id(editando_id)

    modo = "Editar" if editando else "Novo"

    with st.form("form_parceiro"):
        st.markdown(f"### {modo} Parceiro")

        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome do Parceiro *",
                                 value=editando["nome"] if editando else "")
            telefone = st.text_input("Telefone",
                                     value=editando["telefone"] if editando else "")
            email = st.text_input("Email",
                                  value=editando["email"] if editando else "")
        with col2:
            pix = st.text_input("PIX",
                                value=editando["pix"] if editando else "")
            dias_pag = st.number_input("Dias para pagamento",
                                       min_value=0, max_value=90, step=5,
                                       value=editando["dias_pagamento"] if editando else 10)
            observacoes = st.text_area("Observacoes",
                                       value=editando["observacoes"] if editando else "",
                                       height=80)

        st.markdown("---")
        st.markdown("**Contrato**")

        col3, col4 = st.columns(2)
        with col3:
            percentual = st.number_input("Percentual (%)", min_value=0.0,
                                          max_value=100.0, step=0.5, format="%.2f",
                                          value=editando["percentual"] if editando else 0.0)
            base_calculo = st.selectbox("Base de calculo", BASES,
                                         index=BASES.index(editando["base_calculo"])
                                         if editando and editando["base_calculo"] in BASES else 0)
        with col4:
            aliquota = st.number_input("Aliquota de impostos (%)", min_value=0.0,
                                        max_value=100.0, step=0.5, format="%.2f",
                                        value=editando["aliquota_impostos"] if editando else 0.0)
            escopo = st.selectbox("Faturamento considerado", ESCOPOS,
                                   index=ESCOPOS.index(editando["faturamento_considerado"])
                                   if editando and editando["faturamento_considerado"] in ESCOPOS else 0)

        st.markdown("---")
        st.markdown("**Carteira de Clientes**")

        opcoes, mapa = listar_clientes_para_select()
        selecionados = []
        if editando:
            ids = obter_ids_carteira(editando_id)
            for label, cid in mapa.items():
                if cid in ids:
                    selecionados.append(label)

        escolhidos = st.multiselect("Selecionar clientes da carteira",
                                     options=opcoes, default=selecionados)

        st.markdown("---")
        col_s, col_c = st.columns(2)
        with col_s:
            salvar = st.form_submit_button("Salvar", type="primary")
        with col_c:
            cancelar = st.form_submit_button("Cancelar")

    if salvar:
        if not nome.strip():
            st.error("Nome do parceiro e obrigatorio.")
            return True

        dados = {
            "nome": nome.strip(), "telefone": telefone, "email": email,
            "pix": pix, "observacoes": observacoes,
            "percentual": percentual, "base_calculo": base_calculo,
            "aliquota_impostos": aliquota,
            "faturamento_considerado": escopo, "dias_pagamento": dias_pag,
        }
        cliente_ids = [mapa[l] for l in escolhidos]

        if editando:
            atualizar_parceiro(editando_id, dados)
            substituir_carteira(editando_id, cliente_ids)
        else:
            pid = criar_parceiro(dados)
            substituir_carteira(pid, cliente_ids)

        mensagem_sucesso("Parceiro salvo com sucesso!")
        st.session_state["mostrar_form_parceiro"] = False
        st.rerun()

    if cancelar:
        st.session_state["mostrar_form_parceiro"] = False
        st.rerun()

    return True

def render():
    """Renderiza a aba de Parceiros."""
    st.subheader("Parceiros")

    col_acoes = st.columns([3, 1])
    with col_acoes[0]:
        termo = st.text_input("Buscar parceiro", placeholder="Digite o nome...",
                              label_visibility="collapsed")
    with col_acoes[1]:
        if st.button("+ Novo Parceiro", type="primary", width="stretch"):
            st.session_state["editando_parceiro"] = None
            st.session_state["mostrar_form_parceiro"] = True
            st.rerun()

    parceiros = listar_parceiros_com_carteira()
    if termo:
        parceiros = [p for p in parceiros if termo.lower() in p["nome"].lower()]

    if st.session_state.get("mostrar_form_parceiro", False):
        editando_id = st.session_state.get("editando_parceiro")
        with st.container(border=True):
            if _render_form(editando_id):
                return

    if not parceiros:
        st.info("Nenhum parceiro cadastrado.")
        return

    proj_dict = {}
    try:
        from datetime import date
        hoje = date.today()
        for p in projetar_comissao_mes(hoje.year, hoje.month):
            proj_dict[p["parceiro_id"]] = p
    except Exception:
        pass

    import pandas as pd
    dados = []
    for p in parceiros:
        pr = proj_dict.get(p["id"], {})
        dados.append({
            "Nome": p["nome"], "Status": p["status"],
            "Clientes": p["qtd_clientes"],
            "%": f"{p['percentual']:.1f}%",
            "Base": p["base_calculo"],
            "Faturamento Considerado": p["faturamento_considerado"],
            "Receita Mes": f"R$ {pr.get('valor_bruto',0):,.0f}",
            "Base Comissao": f"R$ {pr.get('valor_liquido',0):,.0f}",
            "Comissao Projetada": f"R$ {pr.get('valor_comissao',0):,.0f}",
        })

    from components import tabela_padrao
    tabela_padrao(pd.DataFrame(dados), height=400)

    st.divider()
    st.markdown("### Acoes")
    col_s, col_e, col_t, col_d = st.columns([3, 1, 1, 1])
    with col_s:
        nomes = [p["nome"] for p in parceiros]
        sel = st.selectbox("Selecionar parceiro", options=nomes, key="sel_parceiro")
        parceiro = next((p for p in parceiros if p["nome"] == sel), None)

    if parceiro:
        with col_e:
            if st.button("Editar", width="stretch", key=f"editar_parceiro_{parceiro['id']}"):
                st.session_state["editando_parceiro"] = parceiro["id"]
                st.session_state["mostrar_form_parceiro"] = True
                st.rerun()
        with col_t:
            if parceiro["status"] == "ATIVO":
                if st.button("Desativar", width="stretch", key=f"desativar_parceiro_{parceiro['id']}"):
                    desativar_parceiro(parceiro["id"])
                    st.rerun()
            else:
                if st.button("Ativar", width="stretch", key=f"ativar_parceiro_{parceiro['id']}"):
                    ativar_parceiro(parceiro["id"])
                    st.rerun()
        with col_d:
            if st.button("Excluir", width="stretch", key=f"excluir_parceiro_{parceiro['id']}"):
                excluir_parceiro(parceiro["id"])
                st.rerun()
