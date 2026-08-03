"""Componente de UI das comissoes avulsas."""

from datetime import date

import pandas as pd
import streamlit as st

from components import mensagem_sucesso, mensagem_erro, tabela_padrao
from services.comissoes_fechamento import (
    criar_comissao_avulsa, alterar_status_avulsa, excluir_comissao_avulsa,
)
from services.comissoes_consultas import (
    listar_comissoes_avulsas, listar_parceiros_com_carteira,
    listar_clientes_para_select,
)

STATUS_AVULSA = ["AGUARDANDO_FATURAMENTO", "AGUARDANDO_COMPENSACAO", "PAGO"]
TRANSICOES = {
    "AGUARDANDO_FATURAMENTO": "AGUARDANDO_COMPENSACAO",
    "AGUARDANDO_COMPENSACAO": "PAGO",
}

def render():
    """Renderiza a aba de Comissoes Avulsas."""
    hoje = date.today()

    st.markdown("### Comissoes Avulsas")

    col_acoes = st.columns([3, 1])
    with col_acoes[0]:
        parceiros = listar_parceiros_com_carteira()
        opcoes_parceiro = [""] + [p["nome"] for p in parceiros]
        filtro_parceiro = st.selectbox("Filtrar por parceiro", options=opcoes_parceiro,
                                        key="filtro_avulsa")
    with col_acoes[1]:
        if st.button("+ Nova Comissao", type="primary", width="stretch"):
            st.session_state["mostrar_form_avulsa"] = True
            st.rerun()

    # Formulario de nova comissao avulsa
    if st.session_state.get("mostrar_form_avulsa", False):
        with st.container(border=True):
            st.markdown("### Nova Comissao Avulsa")

            opcoes_cli, mapa_cli = listar_clientes_para_select()

            col1, col2 = st.columns(2)
            with col1:
                parceiro_nomes = [p["nome"] for p in parceiros]
                p_sel = st.selectbox("Parceiro *", options=parceiro_nomes,
                                     key="avulsa_parceiro")
                p_id = next((p["id"] for p in parceiros if p["nome"] == p_sel), None)
                cliente_sel = st.selectbox("Cliente (opcional)",
                                           options=[""] + opcoes_cli,
                                           key="avulsa_cliente")
                c_id = mapa_cli.get(cliente_sel) if cliente_sel else None
                descricao = st.text_input("Descricao *", key="avulsa_desc")
                os_id = st.text_input("OS (opcional)", placeholder="Ex: 12345",
                                      key="avulsa_os")

                # ── Modo de cálculo (v2.3) ──
                modo_calculo = st.radio(
                    "Modo de cálculo",
                    options=["Automático", "Valor Fixo"],
                    horizontal=True,
                    key="avulsa_modo",
                    help="Automático: Valor Faturado × Percentual. "
                         "Valor Fixo: informe diretamente o valor da comissão.",
                )

            with col2:
                valor_fat = st.number_input("Valor faturado", min_value=0.0,
                                            step=100.0, format="%.2f",
                                            key="avulsa_valor_fat")
                percentual = st.number_input("Percentual (%)", min_value=0.0,
                                             max_value=100.0, step=0.5,
                                             format="%.2f",
                                             key="avulsa_pct")
                data_prev = st.date_input("Data prevista pagamento",
                                          value=hoje, key="avulsa_data")
                obs = st.text_area("Observacoes", height=70, key="avulsa_obs")

                # ── Valor da Comissão ──
                modo_automatico = modo_calculo == "Automático"
                if modo_automatico:
                    # Cálculo em tempo real (sem salvar)
                    valor_com = round(valor_fat * (percentual / 100), 2)
                    st.metric("Valor Comissão", f"R$ {valor_com:,.2f}",
                              help="Recalculado automaticamente ao alterar Valor Faturado ou Percentual.")
                else:
                    valor_com = st.number_input(
                        "Valor Comissão (fixo)",
                        min_value=0.0,
                        step=100.0,
                        format="%.2f",
                        key="avulsa_valor_fixo",
                        help="Valor fixo informado manualmente. O cálculo automático é ignorado.",
                    )

            col_s, col_c = st.columns(2)
            with col_s:
                salvar = st.button("Salvar", type="primary", width="stretch",
                                   key="avulsa_salvar")
            with col_c:
                cancelar = st.button("Cancelar", width="stretch",
                                     key="avulsa_cancelar")

            if salvar:
                if not p_sel or not descricao:
                    st.error("Parceiro e descricao sao obrigatorios.")
                else:
                    modo_salvar = "AUTOMATICO" if modo_automatico else "FIXO"
                    dados = {
                        "parceiro_id": p_id,
                        "cliente_id": c_id,
                        "os_id": int(os_id) if os_id.strip() else None,
                        "descricao": descricao,
                        "valor_faturado": valor_fat,
                        "percentual": percentual,
                        "valor_comissao": valor_com,
                        "data_prevista": data_prev.isoformat(),
                        "observacoes": obs,
                        "modo_calculo": modo_salvar,
                    }
                    criar_comissao_avulsa(dados)
                    mensagem_sucesso("Comissao avulsa criada!")
                    st.session_state["mostrar_form_avulsa"] = False
                    st.rerun()

            if cancelar:
                st.session_state["mostrar_form_avulsa"] = False
                st.rerun()

    # Listagem de comissoes avulsas
    p_filtro_id = None
    if filtro_parceiro:
        p_filtro = next((p for p in parceiros if p["nome"] == filtro_parceiro), None)
        if p_filtro:
            p_filtro_id = p_filtro["id"]

    avulsas = listar_comissoes_avulsas(parceiro_id=p_filtro_id)

    if not avulsas:
        st.info("Nenhuma comissao avulsa encontrada.")
        return

    dados = []
    for a in avulsas:
        modo_exib = "Automática" if a.get("modo_calculo", "AUTOMATICO") == "AUTOMATICO" else "Manual"
        dados.append({
            "ID": a["id"],
            "Parceiro": a["parceiro_nome"],
            "Descricao": a["descricao"][:50] + "..." if a["descricao"] and len(a["descricao"]) > 50 else (a["descricao"] or ""),
            "OS": a["os_id"] if a["os_id"] else "-",
            "Valor Fat.": f"R$ {a['valor_faturado']:,.2f}",
            "%": f"{a['percentual']:.1f}%",
            "Comissao": f"R$ {a['valor_comissao']:,.2f}",
            "Modo": modo_exib,
            "Data Prev.": a["data_prevista"] or "-",
            "Status": a["status"],
        })

    tabela_padrao(pd.DataFrame(dados), height=350)

    st.divider()
    st.markdown("### Acoes")

    if len(avulsas) > 0:
        opcoes_acao = [f"#{a['id']} - {a['parceiro_nome']}: {a['descricao'][:40]}"
                       for a in avulsas]
        sel_acao = st.selectbox("Selecionar comissao", options=opcoes_acao,
                                 key="sel_acao_avulsa")
        idx = opcoes_acao.index(sel_acao)
        avulsa_sel = avulsas[idx]

        col_av, col_ex = st.columns(2)
        with col_av:
            status_atual = avulsa_sel["status"]
            if status_atual in TRANSICOES:
                prox_status = TRANSICOES[status_atual]
                label = f"Avancar para {prox_status}"
                if st.button(label, width="stretch", key=f"avancar_avulsa_{avulsa_sel['id']}"):
                    alterar_status_avulsa(avulsa_sel["id"], prox_status)
                    mensagem_sucesso(f"Status alterado para {prox_status}")
                    st.rerun()
            else:
                st.info("Comissao ja esta paga ou finalizada.")

        with col_ex:
            if st.button("Excluir", width="stretch", key=f"excluir_avulsa_{avulsa_sel['id']}"):
                excluir_comissao_avulsa(avulsa_sel["id"])
                mensagem_sucesso("Comissao avulsa excluida.")
                st.rerun()
