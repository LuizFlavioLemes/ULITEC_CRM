"""
Página principal do Módulo de Relacionamento Comercial — ULITEC CRM v1.0.6

Fluxo de negócio:
  Planejar visitas → Executar visitas → Registrar interação
  → Gerar pendências → Gerar oportunidades → Receber alertas

v1.0.5 — Adições:
  - Campos de contato nas interações (nome, cargo, telefone, e-mail)
  - Próxima ação estruturada (tipo + observação)
  - Gestão completa de pendências (editar, reabrir, alterar responsável)
  - Blindagem de duplicidade (flag de salvamento + reset)
  - Botão "Nova Pendência" independente

Abas:
  1. Agenda — Hoje, próximos 7 dias, próximos 30 dias
  2. Registrar Interação — Formulário principal com contato e próx. ação estruturada
  3. Histórico — Filtros e consulta com colunas de contato
  4. Pendências Comerciais — Gestão completa (editar, concluir, reabrir)
  5. Nova Pendência — Criação independente (sem interação)
  6. Alertas — Automáticos baseados em regras
"""

from datetime import datetime, date, timedelta

import streamlit as st
import pandas as pd
import sqlite3

from auth import sidebar_usuario
from permissions import verificar_acesso_pagina, tem_acesso
from services import formatar_clientes_para_select
from services.relacionamento import (
    TIPOS_INTERACAO,
    ASSUNTOS_PADRAO,
    RESULTADOS,
    PRIORIDADES,
    TIPOS_PROXIMA_ACAO,
    registrar_interacao,
    get_historico_interacoes,
    get_agenda,
    criar_pendencia,
    get_pendencias,
    concluir_pendencia,
    atualizar_pendencia,
    reabrir_pendencia,
    criar_oportunidade,
    get_alertas_relacionamento,
    get_indicadores_relacionamento,
    carregar_configs_relacionamento,
    salvar_configs_relacionamento,
    get_config,
    criar_evolucao_pendencia,
    get_evolucoes_pendencia,
    concluir_pendencia_com_evolucao,
    reabrir_pendencia_com_evolucao,
)

# ── Proteção: autenticado (todos os perfis) ──
verificar_acesso_pagina()
sidebar_usuario()

st.set_page_config(
    page_title="Relacionamento Comercial",
    layout="wide",
)

st.title("📞 Relacionamento Comercial")
st.markdown(
    "Registre interações, gerencie pendências, acompanhe visitas e "
    "receba alertas automáticos — o pilar principal do CRM ULITEC."
)

# ── Inicialização da sessão ──
if "unidade_ativa" not in st.session_state:
    st.session_state["unidade_ativa"] = "ULITEC SP"
if "unidade_sugerida" not in st.session_state:
    st.session_state["unidade_sugerida"] = st.session_state.get(
        "unidade_usuario", "ULITEC SP"
    )
if "nome_usuario" not in st.session_state:
    st.session_state["nome_usuario"] = ""
if "usuario_id" not in st.session_state:
    st.session_state["usuario_id"] = None

# ── Conexão para dados auxiliares ──
conn = sqlite3.connect("crm.db")

# Carregar lista de clientes para selects
df_clientes = pd.read_sql_query(
    "SELECT id, razao_social, cidade, estado FROM clientes WHERE status = 'ATIVO' ORDER BY razao_social",
    conn,
)
clientes_lista, clientes_dict, clientes_reverso = formatar_clientes_para_select(df_clientes)

conn.close()

# =====================================================
# ABAS
# =====================================================

aba1, aba2, aba3, aba4, aba5, aba6 = st.tabs([
    "📅 Agenda",
    "✏️ Registrar Interação",
    "📋 Histórico",
    "📌 Pendências",
    "➕ Nova Pendência",
    "🔔 Alertas",
])

# =====================================================
# ABA 1 — AGENDA
# =====================================================

with aba1:

    st.subheader("📅 Agenda Comercial")

    col_filtro, _ = st.columns([1, 3])
    with col_filtro:
        dias_agenda = st.selectbox(
            "Período",
            options=["Hoje", "Próximos 7 dias", "Próximos 30 dias"],
            key="agenda_periodo",
        )

    dias_map = {"Hoje": 0, "Próximos 7 dias": 7, "Próximos 30 dias": 30}
    dias_frente = dias_map[dias_agenda]

    with st.spinner("Carregando agenda..."):
        df_agenda = get_agenda(
            dias_frente=dias_frente,
            responsavel=None,
        )

    if df_agenda.empty:
        st.success("🎉 Nenhum item pendente para o período selecionado.")
    else:
        hoje = date.today().strftime("%Y-%m-%d")

        df_hoje = df_agenda[df_agenda["data_prevista"] == hoje].copy()
        df_pendente = df_agenda[
            (df_agenda["status"] == "PENDENTE") & (df_agenda["data_prevista"] != hoje)
        ].copy()
        df_vencida = df_agenda[df_agenda["status"] == "VENCIDA"].copy()

        c1, c2, c3 = st.columns(3)
        c1.metric("🔴 Vencidas", len(df_vencida))
        c2.metric("🟡 Hoje", len(df_hoje))
        c3.metric("🟢 Pendentes", len(df_pendente))

        st.divider()

        def cor_status(row):
            if row["status"] == "VENCIDA":
                return ["background-color: #f8d7da; color: #721c24"] * len(row)
            elif row["status"] == "HOJE":
                return ["background-color: #fff3cd; color: #856404"] * len(row)
            return [""] * len(row)

        st.dataframe(
            df_agenda.style.apply(cor_status, axis=1),
            width="stretch",
            height=500,
            column_config={
                "data_prevista": st.column_config.DateColumn("Data Prevista"),
                "tipo_interacao": "Tipo",
                "assunto": "Assunto",
                "cliente": "Cliente",
                "responsavel": "Responsável",
                "descricao": "Descrição",
                "tipo_agenda": "Categoria",
                "status": "Status",
            },
        )

# =====================================================
# ABA 2 — REGISTRAR INTERAÇÃO (v1.0.5: contato + próx. ação estruturada + blindagem)
# =====================================================

with aba2:

    st.subheader("✏️ Registrar Nova Interação")

    # ── BLINDAGEM v1.0.5: flag de salvamento ──
    if st.session_state.get("interacao_salva_flag", False):
        st.success("✅ Interação registrada com sucesso! Preencha novamente para registrar outra.")
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

            # Perfil MASTER e SÓCIO: selectbox editável | Demais perfis: bloqueado
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
                brinde_entregue = st.selectbox(
                    "Brinde entregue",
                    options=["", "Não", "Sim"],
                    key="reg_brinde",
                )

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

        st.divider()
        st.markdown("### 🏷️ Opções Extras")

        criar_pend = st.checkbox(
            "☐ Criar pendência comercial",
            key="reg_criar_pendencia",
        )

        with st.container():
            if criar_pend:
                st.warning("⚠️ Preencha todos os campos obrigatórios de pendência abaixo antes de salvar.")
                col_p1, col_p2, col_p3 = st.columns(3)
                with col_p1:
                    pend_descricao = st.text_input(
                        "Descrição da pendência *",
                        key="reg_pend_desc",
                    )
                with col_p2:
                    pend_prioridade = st.selectbox(
                        "Prioridade",
                        options=PRIORIDADES,
                        key="reg_pend_prioridade",
                    )
                with col_p3:
                    pend_data_limite = st.date_input(
                        "Data limite",
                        value=date.today() + timedelta(days=7),
                        key="reg_pend_data",
                    )
            else:
                pend_descricao = ""
                pend_prioridade = "MEDIA"
                pend_data_limite = date.today() + timedelta(days=7)

        criar_opp = st.checkbox(
            "☐ Criar oportunidade",
            key="reg_criar_oportunidade",
        )

        with st.container():
            if criar_opp:
                st.warning("⚠️ Preencha todos os campos obrigatórios de oportunidade abaixo antes de salvar.")
                col_o1, col_o2, col_o3 = st.columns(3)
                with col_o1:
                    opp_titulo = st.text_input(
                        "Título da oportunidade *",
                        key="reg_opp_titulo",
                    )
                with col_o2:
                    opp_valor = st.number_input(
                        "Valor estimado (R$)",
                        min_value=0.0,
                        value=0.0,
                        step=100.0,
                        key="reg_opp_valor",
                    )
                with col_o3:
                    opp_prob = st.selectbox(
                        "Probabilidade",
                        options=["BAIXA", "MEDIA", "ALTA"],
                        key="reg_opp_prob",
                    )
                opp_obs = st.text_area(
                    "Observação",
                    height=80,
                    key="reg_opp_obs",
                )
            else:
                opp_titulo = ""
                opp_valor = 0.0
                opp_prob = "MEDIA"
                opp_obs = ""

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
            if criar_opp and not opp_titulo.strip():
                erros.append("Informe o título da oportunidade.")

            if erros:
                for erro in erros:
                    st.error(erro)
            else:
                cliente_id = clientes_dict[cliente_selecionado]
                data_str = data_interacao.strftime("%Y-%m-%d")

                # Capturar campos de contato
                contato_nome = st.session_state.get("reg_contato_nome", "") or None
                contato_cargo = st.session_state.get("reg_contato_cargo", "") or None
                contato_telefone = st.session_state.get("reg_contato_telefone", "") or None
                contato_email = st.session_state.get("reg_contato_email", "") or None

                try:
                    # 1. Registrar interação (sem próxima ação)
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
                        # v1.0.5 — contato
                        contato_nome=contato_nome,
                        contato_cargo=contato_cargo,
                        contato_telefone=contato_telefone,
                        contato_email=contato_email,
                    )

                    # 2. Criar pendência se marcado
                    if criar_pend:
                        criar_pendencia(
                            cliente_id=cliente_id,
                            descricao=pend_descricao,
                            prioridade=pend_prioridade,
                            responsavel=responsavel,
                            data_limite=pend_data_limite.strftime("%Y-%m-%d"),
                            interacao_id=interacao_id,
                        )

                    # 3. Criar oportunidade se marcado
                    if criar_opp:
                        criar_oportunidade(
                            cliente_id=cliente_id,
                            titulo=opp_titulo,
                            valor_estimado=opp_valor,
                            probabilidade=opp_prob,
                            observacao=opp_obs,
                            responsavel=responsavel,
                            unidade=unidade,
                        )

                    # ── BLINDAGEM v1.0.5 ──
                    st.session_state["interacao_salva_flag"] = True
                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Erro ao salvar: {e}")

# =====================================================
# ABA 3 — HISTÓRICO
# =====================================================

with aba3:

    st.subheader("📋 Histórico de Interações")

    with st.expander("🔍 Filtros", expanded=True):
        col_f1, col_f2, col_f3 = st.columns(3)

        with col_f1:
            hist_cliente = st.selectbox(
                "Cliente",
                options=["Todos"] + clientes_lista,
                key="hist_cliente",
            )

        with col_f2:
            hist_tipo = st.selectbox(
                "Tipo de Interação",
                options=["Todos"] + TIPOS_INTERACAO,
                key="hist_tipo",
            )

        with col_f3:
            hist_responsavel = st.text_input(
                "Responsável",
                key="hist_responsavel",
            )

        col_f4, col_f5 = st.columns(2)
        with col_f4:
            hist_data_ini = st.date_input(
                "Data início",
                value=date.today() - timedelta(days=90),
                key="hist_data_ini",
            )
        with col_f5:
            hist_data_fim = st.date_input(
                "Data fim",
                value=date.today(),
                key="hist_data_fim",
            )

    hist_params = {}

    if hist_cliente != "Todos":
        hist_params["cliente_id"] = clientes_dict[hist_cliente]
    if hist_tipo != "Todos":
        hist_params["tipo"] = hist_tipo
    if hist_responsavel:
        hist_params["responsavel"] = hist_responsavel

    hist_params["data_inicio"] = hist_data_ini.strftime("%Y-%m-%d")
    hist_params["data_fim"] = hist_data_fim.strftime("%Y-%m-%d")
    hist_params["limite"] = 500

    with st.spinner("Carregando histórico..."):
        df_historico = get_historico_interacoes(**hist_params)

    if df_historico.empty:
        st.info("Nenhuma interação encontrada com os filtros selecionados.")
    else:
        st.caption(f"📊 {len(df_historico)} interações encontradas.")

        def cor_resultado(row):
            if row["resultado"] == "Positivo":
                return ["background-color: #d4edda; color: #155724"] * len(row)
            elif row["resultado"] == "Negativo":
                return ["background-color: #f8d7da; color: #721c24"] * len(row)
            return [""] * len(row)

        st.dataframe(
            df_historico.style.apply(cor_resultado, axis=1),
            width="stretch",
            height=500,
            column_config={
                "data_interacao": st.column_config.DateColumn("Data"),
                "tipo_interacao": "Tipo",
                "assunto": "Assunto",
                "cliente": "Cliente",
                "contato_nome": "Contato",
                "contato_cargo": "Cargo",
                "responsavel": "Resp.",
                "descricao": "Descrição",
                "resultado": "Resultado",
                "tipo_prox_acao": "Próx. Ação",
                "data_proxima_acao": st.column_config.DateColumn("Data Próx."),
                "status_exibicao": "Status",
            },
        )

# =====================================================
# ABA 4 — PENDÊNCIAS (v1.0.5: gestão completa)
# =====================================================

with aba4:

    st.subheader("📌 Pendências Comerciais")

    tab_p1, tab_p2, tab_p3 = st.tabs([
        "🔴 Abertas",
        "⚠️ Vencidas",
        "✅ Concluídas",
    ])

    # ── Função auxiliar para exibir card de pendência com gestão e timeline ──
    def exibir_card_pendencia(row, key_prefix="pend"):
        with st.container(border=True):
            # Cabeçalho
            c1, c2, c3 = st.columns([3, 1, 1])
            c1.markdown(f"**{row['cliente']}** — {row['descricao']}")
            c2.markdown(f"🔵 {row['prioridade']}")
            c3.markdown(f"📅 {row['data_limite']}")

            # ── TIMELINE DE EVOLUÇÕES (v1.3) ──
            evol_exp = st.expander("📜 Timeline da Pendência", expanded=False)
            with evol_exp:
                df_evol = get_evolucoes_pendencia(row["id"])
                if df_evol.empty:
                    st.caption("Nenhuma evolução registrada ainda.")
                else:
                    for _, evol in df_evol.iterrows():
                        icone_tipo = {
                            "COMENTARIO": "💬",
                            "ANDAMENTO": "🔄",
                            "CONCLUSAO": "✅",
                            "REABERTURA": "🔄",
                            "ALTERACAO_PRAZO": "📅",
                            "ALTERACAO_PRIORIDADE": "🔵",
                            "ALTERACAO_RESPONSAVEL": "👤",
                        }.get(evol["tipo_evolucao"], "📌")
                        data_evol = str(evol["criado_em"])[:16] if evol["criado_em"] else ""
                        autor = evol["usuario_nome"] or ""
                        st.markdown(
                            f"{icone_tipo} **{data_evol}** — {evol['descricao']}"
                            f"{' — *' + autor + '*' if autor else ''}"
                        )

                st.divider()

                # Formulário para nova evolução (v1.4: sem Tipo, com Próximo Contato)
                with st.form(key=f"form_evol_{key_prefix}_{row['id']}"):
                    nova_evol_desc = st.text_area(
                        "Comentário / Andamento",
                        key=f"evol_desc_{key_prefix}_{row['id']}",
                    )
                    proximo_contato = st.date_input(
                        "Próximo Contato",
                        value=None,
                        key=f"evol_prox_contato_{key_prefix}_{row['id']}",
                    )
                    submitted_evol = st.form_submit_button(
                        "📝 Registrar Atualização",
                        width="stretch",
                    )
                    if submitted_evol:
                        if nova_evol_desc.strip():
                            try:
                                criar_evolucao_pendencia(
                                    pendencia_id=row["id"],
                                    descricao=nova_evol_desc.strip(),
                                    usuario_id=st.session_state.get("usuario_id"),
                                    usuario_nome=st.session_state.get("usuario_nome", ""),
                                    proximo_contato=proximo_contato.strftime("%Y-%m-%d") if proximo_contato else None,
                                )
                                st.success("✅ Evolução registrada!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Erro ao registrar: {e}")
                        else:
                            st.warning("Informe a descrição da evolução.")

            # Expandir para edição
            with st.expander("✏️ Editar pendência"):
                nova_desc = st.text_area(
                    "Descrição",
                    value=row["descricao"],
                    key=f"edit_desc_{key_prefix}_{row['id']}",
                )
                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    idx_prio = PRIORIDADES.index(row["prioridade"])
                    nova_prio = st.selectbox(
                        "Prioridade",
                        options=PRIORIDADES,
                        index=idx_prio,
                        key=f"edit_prio_{key_prefix}_{row['id']}",
                    )
                with col_e2:
                    try:
                        data_atual = datetime.strptime(row["data_limite"], "%Y-%m-%d").date()
                    except (ValueError, TypeError):
                        data_atual = date.today()
                    nova_data = st.date_input(
                        "Data Limite",
                        value=data_atual,
                        key=f"edit_data_{key_prefix}_{row['id']}",
                    )
                novo_resp = st.text_input(
                    "Responsável",
                    value=row.get("responsavel", ""),
                    key=f"edit_resp_{key_prefix}_{row['id']}",
                )

                col_a1, col_a2 = st.columns(2)
                salvar_click = col_a1.button("💾 Salvar alterações", key=f"salvar_{key_prefix}_{row['id']}")
                concluir_click = col_a2.button("✅ Concluir", key=f"conc_{key_prefix}_{row['id']}")

                if salvar_click:
                    try:
                        atualizar_pendencia(
                            pendencia_id=row["id"],
                            descricao=nova_desc if nova_desc != row["descricao"] else None,
                            prioridade=nova_prio if nova_prio != row["prioridade"] else None,
                            data_limite=nova_data.strftime("%Y-%m-%d") if nova_data != data_atual else None,
                            responsavel=novo_resp if novo_resp != row.get("responsavel", "") else None,
                        )
                        st.success("✅ Pendência atualizada!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro ao atualizar: {e}")

                if concluir_click:
                    try:
                        concluir_pendencia_com_evolucao(
                            pendencia_id=row["id"],
                            usuario_id=st.session_state.get("usuario_id"),
                            usuario_nome=st.session_state.get("usuario_nome", ""),
                            observacao=nova_desc if nova_desc != row["descricao"] else "",
                        )
                        st.success("✅ Pendência concluída!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro ao concluir: {e}")

            # Botão reabrir (só aparece se já concluída)
            if row["status"] == "FECHADA":
                with st.expander("🔄 Reabrir pendência", expanded=False):
                    motivo_reabertura = st.text_area(
                        "Motivo da reabertura",
                        key=f"motivo_reab_{key_prefix}_{row['id']}",
                    )
                    if st.button("🔄 Confirmar Reabertura", key=f"reabrir_{key_prefix}_{row['id']}"):
                        try:
                            reabrir_pendencia_com_evolucao(
                                pendencia_id=row["id"],
                                usuario_id=st.session_state.get("usuario_id"),
                                usuario_nome=st.session_state.get("usuario_nome", ""),
                                motivo=motivo_reabertura.strip() if motivo_reabertura.strip() else "",
                            )
                            st.success("🔄 Pendência reaberta!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Erro ao reabrir: {e}")

    with tab_p1:
        df_pend_abertas = get_pendencias(status="ABERTA")

        if not df_pend_abertas.empty:
            hoje_str = date.today().strftime("%Y-%m-%d")
            df_pend_abertas = df_pend_abertas[
                (df_pend_abertas["data_limite"] >= hoje_str)
                | (df_pend_abertas["data_limite"].isna())
            ]

        if df_pend_abertas.empty:
            st.success("🎉 Nenhuma pendência aberta.")
        else:
            for _, row in df_pend_abertas.iterrows():
                exibir_card_pendencia(row, key_prefix="aberta")

    with tab_p2:
        df_pend_vencidas = get_pendencias(status="ABERTA")

        if not df_pend_vencidas.empty:
            hoje_str = date.today().strftime("%Y-%m-%d")
            df_pend_vencidas = df_pend_vencidas[
                df_pend_vencidas["data_limite"] < hoje_str
            ]

        if df_pend_vencidas.empty:
            st.success("🎉 Nenhuma pendência vencida.")
        else:
            for _, row in df_pend_vencidas.iterrows():
                exibir_card_pendencia(row, key_prefix="vencida")

    with tab_p3:
        df_pend_concluidas = get_pendencias(status="FECHADA")

        if df_pend_concluidas.empty:
            st.info("Nenhuma pendência concluída ainda.")
        else:
            for _, row in df_pend_concluidas.iterrows():
                exibir_card_pendencia(row, key_prefix="concluida")

# =====================================================
# ABA 5 — NOVA PENDÊNCIA (v1.0.5: independente de interação)
# =====================================================

with aba5:

    st.subheader("➕ Nova Pendência Comercial")
    st.markdown("Crie uma pendência diretamente, sem precisar registrar uma interação.")

    with st.form(key="form_nova_pendencia"):

        col_pn1, col_pn2 = st.columns(2)

        with col_pn1:
            pend_cliente = st.selectbox(
                "👤 Cliente *",
                options=clientes_lista,
                key="nova_pend_cliente",
            )
            pend_desc = st.text_input(
                "📝 Descrição da pendência *",
                key="nova_pend_desc",
            )

        with col_pn2:
            pend_prio = st.selectbox(
                "🔵 Prioridade",
                options=PRIORIDADES,
                index=1,
                key="nova_pend_prio",
            )
            pend_resp = st.text_input(
                "👤 Responsável",
                value=st.session_state.get("usuario_nome", ""),
                key="nova_pend_resp",
            )
            pend_data = st.date_input(
                "📅 Data limite",
                value=date.today() + timedelta(days=7),
                key="nova_pend_data",
            )

        submitted_pend = st.form_submit_button(
            "💾 Criar Pendência",
            type="primary",
            width="stretch",
        )

        if submitted_pend:
            erros_pend = []
            if not pend_cliente:
                erros_pend.append("Selecione um cliente.")
            if not pend_desc.strip():
                erros_pend.append("Informe a descrição da pendência.")

            if erros_pend:
                for erro in erros_pend:
                    st.error(erro)
            else:
                try:
                    criar_pendencia(
                        cliente_id=clientes_dict[pend_cliente],
                        descricao=pend_desc,
                        prioridade=pend_prio,
                        responsavel=pend_resp,
                        data_limite=pend_data.strftime("%Y-%m-%d"),
                    )
                    st.success("✅ Pendência criada com sucesso!")
                    # Resetar formulário
                    for key in list(st.session_state.keys()):
                        if key.startswith("nova_pend_"):
                            del st.session_state[key]
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erro ao criar pendência: {e}")

# =====================================================
# ABA 6 — ALERTAS
# =====================================================

with aba6:

    st.subheader("🔔 Alertas de Relacionamento")
    st.markdown(
        "Alertas automáticos baseados nas regras configuradas na "
        "Administração (frequência por classe, alertas de visita/contato)."
    )

    with st.spinner("Gerando alertas..."):
        alertas = get_alertas_relacionamento()

    if not alertas:
        st.success("🎉 Nenhum alerta no momento. Tudo em dia!")
    else:
        st.warning(f"{len(alertas)} alerta(s) encontrado(s)")

        tipos_alerta = {}
        for alerta in alertas:
            tipo = alerta["tipo"]
            if tipo not in tipos_alerta:
                tipos_alerta[tipo] = []
            tipos_alerta[tipo].append(alerta)

        for tipo, lista in tipos_alerta.items():
            nome_tipo = {
                "VISITA_PROXIMA_VENCIMENTO": "📅 Visitas Próximas do Vencimento",
                "PENDENCIA_VENCIDA": "📌 Pendências Vencidas",
            }.get(tipo, tipo)

            with st.expander(f"{nome_tipo} ({len(lista)})", expanded=True):
                for alerta in lista:
                    severidade_icone = (
                        "🔴" if alerta["severidade"] == "ALTA" else "🟡"
                    )
                    st.markdown(
                        f"{severidade_icone} **{alerta['cliente']}**: "
                        f"{alerta['descricao']}"
                    )