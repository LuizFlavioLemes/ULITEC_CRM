"""
Componente da Aba 2 — ✏️ Registrar Interação

Formulário principal para registro de interações comerciais com cliente.
Inclui:
- Dados do contato (nome, cargo, telefone, e-mail)
- Campos industriais para visitas presenciais
- Opção para criar pendência vinculada
- Blindagem anti-duplicidade (flag de salvamento)

Responsabilidades:
- Renderizar formulário completo de interação
- Validar campos obrigatórios
- Chamar services.relacionamento.registrar_interacao
- Gerenciar flag de salvamento para evitar duplicidade
"""

from datetime import date, timedelta

import streamlit as st
import pandas as pd

from permissions import tem_acesso
from services.relacionamento import (
    TIPOS_INTERACAO,
    ASSUNTOS_PADRAO,
    RESULTADOS,
    PRIORIDADES,
    TIPOS_PENDENCIA,
    registrar_interacao,
    criar_pendencia,
)


def exibir_registro(clientes_lista, clientes_dict, clientes_reverso):
    """
    Renderiza a aba de Registro de Interação.

    Parâmetros:
        clientes_lista: list[str] — labels para selectbox
        clientes_dict: dict — mapeia label → id
        clientes_reverso: dict — mapeia label → dict com dados do cliente
    """
    st.subheader("✏️ Registrar Nova Interação")

    # ── BLINDAGEM v1.0.5: flag de salvamento ──
    if st.session_state.get("interacao_salva_flag", False):
        st.success(
            "✅ Interação registrada com sucesso! Preencha novamente para registrar outra."
        )
        if st.button("🔄 Nova Interação", width="stretch"):
            for key in list(st.session_state.keys()):
                if key.startswith("reg_"):
                    del st.session_state[key]
            st.session_state["interacao_salva_flag"] = False
            st.rerun()
        st.stop()

    with st.form(key="form_registrar_interacao"):

        col1, col2 = st.columns(2)

        with col1:
            cliente_selecionado = st.selectbox(
                "👤 Cliente *",
                options=clientes_lista,
                key="reg_cliente",
            )

            # ── v1.0.5: DADOS DO CONTATO ──
            with st.expander("👤 Dados do Contato", expanded=False):
                st.caption("Registre com quem foi a interação")
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    st.text_input("Nome do contato", key="reg_contato_nome")
                    st.text_input("Cargo", key="reg_contato_cargo")
                with col_c2:
                    st.text_input("Telefone", key="reg_contato_telefone")
                    st.text_input("E-mail", key="reg_contato_email")

            tipo_interacao = st.selectbox(
                "📞 Tipo de Interação *",
                options=TIPOS_INTERACAO,
                key="reg_tipo",
            )

            assunto = st.selectbox(
                "📂 Assunto",
                options=ASSUNTOS_PADRAO,
                key="reg_assunto",
            )

            data_interacao = st.date_input(
                "📅 Data da Interação",
                value=date.today(),
                key="reg_data",
            )

        with col2:
            resultado = st.selectbox(
                "✅ Resultado",
                options=RESULTADOS,
                key="reg_resultado",
            )

            responsavel = st.text_input(
                "👤 Responsável *",
                value=st.session_state.get("usuario_nome", ""),
                key="reg_responsavel",
                disabled=True,
                help="Preenchido automaticamente com seu usuário",
            )

            # ── Sugerir unidade automaticamente conforme o cliente selecionado ──
            rotulo_cliente = st.session_state.get("reg_cliente", "")
            if rotulo_cliente and rotulo_cliente in clientes_reverso:
                dados_cliente = clientes_reverso[rotulo_cliente]
                estado_cliente = str(dados_cliente.get("estado", "")).upper()
                if "SP" in estado_cliente:
                    unidade_default = "ULITEC SP"
                elif "RS" in estado_cliente:
                    unidade_default = "ULITEC RS"
                else:
                    unidade_default = st.session_state.get(
                        "unidade_usuario", "ULITEC SP"
                    )
            else:
                unidade_default = st.session_state.get(
                    "unidade_usuario", "ULITEC SP"
                )

            unidade_options = ["ULITEC SP", "ULITEC RS"]
            unidade_index = 0 if unidade_default == "ULITEC SP" else 1

            unidade = st.selectbox(
                "🏢 Unidade",
                options=unidade_options,
                index=unidade_index,
                key="reg_unidade",
                disabled=not tem_acesso("MASTER", "SÓCIO"),
                help=(
                    "MASTER e SÓCIO podem alterar a unidade livremente. "
                    "Demais perfis: preenchido automaticamente conforme o cliente."
                ),
            )

            status_interacao = st.selectbox(
                "📌 Status da Interação",
                options=["ABERTA", "CONCLUIDA", "CANCELADA"],
                key="reg_status_interacao",
            )

        descricao = st.text_area(
            "📝 Descrição / Resumo da Interação",
            height=150,
            key="reg_descricao",
        )

        # ==============================================
        # Campos Industriais (Visita Presencial)
        # ==============================================
        if tipo_interacao == "Visita Presencial":
            st.divider()
            st.markdown("### 🏭 Informações da Visita (Campos Industriais)")

            STATUS_CLIENTE_OPTS = [
                "Expandindo",
                "Aquecido",
                "Estável",
                "Reduzindo Produção",
                "Em Risco",
                "Possível Perda",
                "Paralisado",
            ]
            NIVEL_PRODUCAO_OPTS = [
                "100% Capacidade",
                "75% Produção Alta",
                "50% Produção Normal",
                "25% Produção Reduzida",
                "Produção Crítica",
                "Parado",
            ]
            PERSPECTIVA_OPTS = [
                "Forte Crescimento",
                "Crescimento",
                "Estável",
                "Queda Moderada",
                "Forte Queda",
                "Sem Informação",
            ]

            col_i1, col_i2 = st.columns(2)
            with col_i1:
                qtd_maquinas = st.number_input(
                    "Quantidade de máquinas",
                    min_value=0, value=0, step=1,
                    key="reg_qtd_maq",
                )
                qtd_mitsubishi = st.number_input(
                    "Quantidade Mitsubishi",
                    min_value=0, value=0, step=1,
                    key="reg_qtd_mit",
                )
                status_cliente = st.selectbox(
                    "Status do cliente",
                    options=[""] + STATUS_CLIENTE_OPTS,
                    key="reg_status_cliente",
                )
                nivel_producao = st.selectbox(
                    "Nível de produção",
                    options=[""] + NIVEL_PRODUCAO_OPTS,
                    key="reg_nivel_prod",
                )
            with col_i2:
                perspectiva_6m = st.selectbox(
                    "Perspectiva próximos 6 meses",
                    options=[""] + PERSPECTIVA_OPTS,
                    key="reg_perspectiva",
                )
                concorrentes = st.text_input(
                    "Concorrentes encontrados",
                    key="reg_concorrentes",
                )
                st.markdown("##### Brinde entregue?")
                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    entregou_brinde = st.radio(
                        "Brinde entregue?",
                        options=["Não", "Sim"],
                        key="reg_entregou_brinde",
                        horizontal=True,
                        label_visibility="collapsed",
                    )
                with col_b2:
                    pass

                if entregou_brinde == "Sim":
                    descricao_brinde = st.text_input(
                        "Qual brinde foi entregue?",
                        key="reg_descricao_brinde",
                    )
                    data_brinde = st.date_input(
                        "Data da entrega",
                        value=date.today(),
                        key="reg_data_brinde",
                    )
                else:
                    descricao_brinde = ""
                    data_brinde = date.today()

            st.divider()
            st.markdown("### 🎯 Resultado Comercial")

            RESULTADO_COMERCIAL_OPTS = [
                "Sem oportunidade",
                "Oportunidade identificada",
                "Preventiva sugerida",
                "Proposta solicitada",
                "Retorno agendado",
                "Cliente sem interesse",
            ]
            resultado_comercial = st.selectbox(
                "Resultado Comercial",
                options=[""] + RESULTADO_COMERCIAL_OPTS,
                key="reg_resultado_comercial",
            )
        else:
            qtd_maquinas = None
            qtd_mitsubishi = None
            brinde_entregue = None
            status_cliente = None
            nivel_producao = None
            perspectiva_6m = None
            concorrentes = None
            resultado_comercial = None
            entregou_brinde = None
            descricao_brinde = None
            data_brinde = None

        st.divider()
        st.markdown("### 🏷️ Criar Pendência Comercial")

        criar_pend = st.checkbox(
            "☑ Criar Pendência Comercial",
            key="reg_criar_pendencia",
        )

        with st.container():
            if criar_pend:
                st.warning(
                    "⚠️ Preencha todos os campos obrigatórios de pendência abaixo antes de salvar."
                )
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    pend_descricao = st.text_input(
                        "Descrição da pendência *",
                        key="reg_pend_desc",
                    )
                    pend_tipo = st.selectbox(
                        "Tipo da Pendência",
                        options=TIPOS_PENDENCIA,
                        key="reg_pend_tipo",
                    )
                with col_p2:
                    pend_prioridade = st.selectbox(
                        "Prioridade",
                        options=PRIORIDADES,
                        key="reg_pend_prioridade",
                    )
                    pend_data_limite = st.date_input(
                        "Data limite",
                        value=date.today() + timedelta(days=7),
                        key="reg_pend_data",
                    )
            else:
                pend_descricao = ""
                pend_prioridade = "MEDIA"
                pend_tipo = None
                pend_data_limite = date.today() + timedelta(days=7)

        st.divider()

        submitted = st.form_submit_button(
            "💾 Salvar Interação",
            type="primary",
            width="stretch",
        )

        if submitted:
            erros = []
            if not cliente_selecionado:
                erros.append("Selecione um cliente.")
            if not responsavel.strip():
                erros.append("Informe o responsável.")

            if criar_pend and not pend_descricao.strip():
                erros.append("Informe a descrição da pendência.")

            if erros:
                for erro in erros:
                    st.error(erro)
            else:
                cliente_id = clientes_dict[cliente_selecionado]
                data_str = data_interacao.strftime("%Y-%m-%d")

                contato_nome = st.session_state.get("reg_contato_nome", "") or None
                contato_cargo = st.session_state.get("reg_contato_cargo", "") or None
                contato_telefone = (
                    st.session_state.get("reg_contato_telefone", "") or None
                )
                contato_email = st.session_state.get("reg_contato_email", "") or None

                try:
                    # Formatar data_brinde se for date object
                    data_brinde_str = data_brinde.strftime("%Y-%m-%d") if hasattr(data_brinde, "strftime") else data_brinde

                    interacao_id = registrar_interacao(
                        cliente_id=cliente_id,
                        tipo_interacao=tipo_interacao,
                        assunto=assunto,
                        descricao=descricao,
                        resultado=resultado,
                        responsavel=responsavel,
                        usuario_id=st.session_state.get("usuario_id"),
                        unidade=unidade,
                        data_interacao=data_str,
                        status_interacao=status_interacao,
                        qtd_maquinas=qtd_maquinas,
                        qtd_mitsubishi=qtd_mitsubishi,
                        brinde_entregue=brinde_entregue,
                        status_cliente=status_cliente,
                        nivel_producao=nivel_producao,
                        perspectiva_6m=perspectiva_6m,
                        concorrentes=concorrentes,
                        resultado_comercial=resultado_comercial,
                        contato_nome=contato_nome,
                        contato_cargo=contato_cargo,
                        contato_telefone=contato_telefone,
                        contato_email=contato_email,
                        entregou_brinde=entregou_brinde,
                        descricao_brinde=descricao_brinde or None,
                        data_brinde=data_brinde_str,
                    )

                    if criar_pend:
                        criar_pendencia(
                            cliente_id=cliente_id,
                            descricao=pend_descricao,
                            prioridade=pend_prioridade,
                            responsavel=responsavel,
                            data_limite=pend_data_limite.strftime("%Y-%m-%d"),
                            interacao_id=interacao_id,
                            tipo_pendencia=pend_tipo,
                        )

                    st.session_state["interacao_salva_flag"] = True
                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Erro ao salvar: {e}")