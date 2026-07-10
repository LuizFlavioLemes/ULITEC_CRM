from datetime import datetime, date

import streamlit as st
import pandas as pd
import sqlite3

from auth import sidebar_usuario
from permissions import verificar_acesso_pagina
from services import formatar_clientes_para_select
from services.ia.engine import gerar_analise_cliente
from services.ia.data_collector import (
    coletar_cliente,
    coletar_faturamento,
    coletar_os,
    coletar_oportunidades,
    coletar_mitsubishi,
    coletar_interacoes,
)
from services.ia.ia_client import _obter_config
from services.ia.prompt_builder import (
    PROMPT_SISTEMA,
    montar_contexto_cliente,
    montar_prompt_completo,
)
from services.relacionamento import (
    get_indicadores_relacionamento,
    get_historico_interacoes,
    get_pendencias,
    get_agenda,
    get_ultimo_contato,
    get_pendencias_abertas_cliente,
    get_proximas_acoes_cliente,
    get_ultimos_eventos_cliente,
    get_contatos_conhecidos,
    get_timeline_unificada,
    get_evolucoes_pendencia,
    TIPOS_EVOLUCAO,
    criar_evolucao_pendencia,
)

# ── Proteção: autenticado (todos os perfis) ──
verificar_acesso_pagina()
sidebar_usuario()

st.title("🎯 Cliente 360°")

conn = sqlite3.connect("crm.db")

clientes = pd.read_sql_query(
    """
    SELECT
        id,
        razao_social,
        cidade,
        estado,
        telefone,
        email,
        segmento,
        faturamento_12m,
        ultima_visita
    FROM clientes
    ORDER BY razao_social
    """,
    conn
)

if len(clientes) == 0:

    st.warning("Nenhum cliente encontrado.")
    st.stop()

clientes_lista, clientes_dict, clientes_reverso = formatar_clientes_para_select(clientes)

cliente_nome = st.selectbox(
    "Selecione o cliente",
    clientes_lista
)

cliente = clientes_reverso[cliente_nome]

cliente_id = int(cliente["id"])

st.divider()

# ==================================================
# INDICADORES PRINCIPAIS
# ==================================================

c1, c2, c3, c4 = st.columns(4)

# máquinas
try:
    maquinas = pd.read_sql_query(
        f"""
        SELECT COUNT(*) qtd
        FROM maquinas_mitsubishi
        WHERE cliente_id = {cliente_id}
        """,
        conn
    ).iloc[0]["qtd"]
except:
    maquinas = 0

# visitas
try:
    visitas = pd.read_sql_query(
        f"""
        SELECT COUNT(*) qtd
        FROM interacoes
        WHERE cliente_id = {cliente_id}
        """,
        conn
    ).iloc[0]["qtd"]
except:
    visitas = 0

# propostas
try:
    propostas = pd.read_sql_query(
        f"""
        SELECT COUNT(*) qtd
        FROM propostas
        WHERE cliente_id = {cliente_id}
        """,
        conn
    ).iloc[0]["qtd"]
except:
    propostas = 0

c1.metric(
    "💰 Fat. 12M",
    f"R$ {cliente['faturamento_12m']:,.0f}"
)

c2.metric(
    "🛠 Máquinas",
    maquinas
)

c3.metric(
    "📅 Visitas",
    visitas
)

c4.metric(
    "📄 Propostas",
    propostas
)

# ==================================================
# INDICADORES DE RELACIONAMENTO
# ==================================================

try:
    ind_relac = get_indicadores_relacionamento(cliente_id)
except:
    ind_relac = {
        "ultima_interacao_data": None,
        "ultima_interacao_tipo": None,
        "pendencias_abertas": 0,
        "pendencias_vencidas": 0,
        "total_interacoes": 0,
        "oportunidades_relacionamento": 0,
    }

c_rel1, c_rel2, c_rel3, c_rel4 = st.columns(4)

c_rel1.metric(
    "📞 Última Interação",
    ind_relac["ultima_interacao_data"] or "Nunca",
    help=f"Tipo: {ind_relac['ultima_interacao_tipo'] or '-'}" if ind_relac["ultima_interacao_data"] else None,
)

c_rel2.metric(
    "📌 Pendências Abertas",
    ind_relac["pendencias_abertas"],
    delta=f"{ind_relac['pendencias_vencidas']} vencidas",
    delta_color="inverse",
)

c_rel3.metric(
    "🔄 Total Interações",
    ind_relac["total_interacoes"],
)

c_rel4.metric(
    "💰 Oportunidades (Relac.)",
    ind_relac["oportunidades_relacionamento"],
)

# ==================================================
# ABAS
# ==================================================

tabs = st.tabs(
    [
        "Resumo",
        "Visitas",
        "Máquinas",
        "Faturamento",
        "Oportunidades",
        "🤖 Análise IA",
        "📞 Relacionamento",
        "📋 OS Aguardando Aprovação",
    ]
)

# ==================================================
# RESUMO
# ==================================================

with tabs[0]:

    st.subheader("Dados Gerais")

    st.write(
        f"**Cliente:** {cliente['razao_social']}"
    )

    st.write(
        f"**Cidade:** {cliente['cidade']}"
    )

    st.write(
        f"**Estado:** {cliente['estado']}"
    )

    st.write(
        f"**Telefone:** {cliente['telefone']}"
    )

    st.write(
        f"**E-mail:** {cliente['email']}"
    )

    st.write(
        f"**Segmento:** {cliente['segmento']}"
    )

# ==================================================
# VISITAS (v1.3: visualização detalhada de interações)
# ==================================================

with tabs[1]:

    st.subheader("📞 Interações Registradas")

    try:
        df_interacoes = get_historico_interacoes(
            cliente_id=cliente_id,
            limite=200,
        )

        if df_interacoes.empty:
            st.info("Nenhuma interação registrada para este cliente.")
        else:
            st.caption(f"{len(df_interacoes)} interação(ões) encontrada(s).")

            for _, interacao in df_interacoes.iterrows():
                with st.expander(
                    f"📅 {interacao['data_interacao']} — "
                    f"{interacao['tipo_interacao']} | "
                    f"{interacao['assunto']} | "
                    f"{interacao['resultado']}"
                ):
                    # Colunas principais
                    col_d1, col_d2 = st.columns(2)

                    with col_d1:
                        st.markdown(f"**📞 Tipo:** {interacao['tipo_interacao']}")
                        st.markdown(f"**📂 Assunto:** {interacao['assunto']}")
                        st.markdown(f"**✅ Resultado:** {interacao['resultado']}")
                        st.markdown(f"**👤 Responsável:** {interacao['responsavel']}")

                    with col_d2:
                        st.markdown(f"**📅 Data:** {interacao['data_interacao']}")
                        st.markdown(f"**📌 Status:** {interacao['status_exibicao']}")

                    # Descrição / Observações
                    if interacao.get('descricao'):
                        st.markdown("**📝 Observações:**")
                        st.markdown(f"> {interacao['descricao']}")

                    st.divider()

                    # Contato
                    st.markdown("**👤 Contato**")
                    col_ct1, col_ct2 = st.columns(2)
                    with col_ct1:
                        st.markdown(f"Nome: {interacao.get('contato_nome') or '-'}")
                        st.markdown(f"Cargo: {interacao.get('contato_cargo') or '-'}")
                    with col_ct2:
                        st.markdown(f"Telefone: {interacao.get('contato_telefone') or '-'}")
                        st.markdown(f"E-mail: {interacao.get('contato_email') or '-'}")

                    st.divider()

                    # Pendências relacionadas
                    st.markdown("**📌 Pendências Relacionadas**")
                    conn_local = sqlite3.connect("crm.db")
                    try:
                        df_pend_rel = pd.read_sql_query(
                            """
                            SELECT descricao, prioridade, data_limite, status
                            FROM pendencias_comerciais
                            WHERE interacao_id = ?
                            ORDER BY criado_em DESC
                            """,
                            conn_local,
                            params=(interacao["id"],),
                        )
                        if df_pend_rel.empty:
                            st.caption("Nenhuma pendência vinculada a esta interação.")
                        else:
                            st.dataframe(
                                df_pend_rel.rename(columns={
                                    "descricao": "Descrição",
                                    "prioridade": "Prioridade",
                                    "data_limite": "Vencimento",
                                    "status": "Status",
                                }),
                                width="stretch",
                                height=100,
                            )
                    except Exception:
                        st.caption("Nenhuma pendência.")
                    finally:
                        conn_local.close()

                    # Próxima ação
                    if interacao.get('tipo_prox_acao') or interacao.get('data_proxima_acao'):
                        st.divider()
                        st.markdown("**📅 Próxima Ação**")
                        col_pa1, col_pa2 = st.columns(2)
                        with col_pa1:
                            st.markdown(f"Tipo: {interacao.get('tipo_prox_acao') or interacao.get('proxima_acao') or '-'}")
                        with col_pa2:
                            st.markdown(f"Data: {interacao.get('data_proxima_acao') or '-'}")
                        if interacao.get('obs_prox_acao'):
                            st.markdown(f"> {interacao['obs_prox_acao']}")

    except Exception as e:
        st.info(f"Sem visitas: {e}")

# ==================================================
# MÁQUINAS
# ==================================================

with tabs[2]:

    try:

        maquinas_df = pd.read_sql_query(
            f"""
            SELECT
                machine,
                serial_number,
                ano,
                warranty_end
            FROM maquinas_mitsubishi
            WHERE cliente_id = {cliente_id}
            """,
            conn
        )

        st.dataframe(
            maquinas_df,
            width="stretch"
        )

    except:
        st.info("Sem máquinas.")

# ==================================================
# FATURAMENTO
# ==================================================

with tabs[3]:

    try:

        fat_df = pd.read_sql_query(
            f"""
            SELECT *
            FROM faturamento
            WHERE cliente_id = {cliente_id}
            ORDER BY data_faturamento DESC
            """,
            conn
        )

        st.dataframe(
            fat_df,
            width="stretch"
        )

    except:
        st.info("Sem faturamento.")

# ==================================================
# OPORTUNIDADES
# ==================================================

with tabs[4]:

    try:

        op_df = pd.read_sql_query(
            f"""
            SELECT *
            FROM oportunidades
            WHERE cliente_id = {cliente_id}
            """,
            conn
        )

        st.dataframe(
            op_df,
            width="stretch"
        )

    except:
        st.info("Sem oportunidades.")

# ==================================================
# ANÁLISE IA
# ==================================================

with tabs[5]:

    # ================================================================
    # 📋 GERAR PROMPT (sem API - para ChatGPT/Gemini/Claude)
    # ================================================================

    st.subheader("📋 Gerar Prompt")

    st.markdown(
        "Gere um prompt completo para utilizar no **ChatGPT, Gemini ou Claude** "
        "sem necessidade de API."
    )

    if st.button("📋 Gerar Prompt", width="stretch"):

        with st.spinner("Coletando dados do cliente..."):
            cliente_dados = coletar_cliente(cliente_id)
            faturamento_dados = coletar_faturamento(cliente_id)
            os_dados = coletar_os(cliente_id)
            op_dados = coletar_oportunidades(cliente_id)
            mit_dados = coletar_mitsubishi(cliente_id)
            inter_dados = coletar_interacoes(cliente_id)

            prompt_completo = montar_prompt_completo(
                cliente_dados,
                faturamento_dados,
                os_dados,
                op_dados,
                mit_dados,
                inter_dados,
            )

        st.text_area(
            "📄 Prompt gerado — copie o conteúdo abaixo",
            value=prompt_completo,
            height=500,
            label_visibility="collapsed",
        )

        if st.button("📄 Copiar Prompt", width="stretch"):
            st.code(prompt_completo, language="markdown")
            st.info("Selecione e copie o conteúdo acima.")

    # ═══════════════════════════════════════════════════════════════
    # PROMPT_COMERCIAL — personalização para análise de negócios
    # ═══════════════════════════════════════════════════════════════
    PROMPT_COMERCIAL = """
Você é um Diretor Comercial e Analista de BI Sênior focado em CRM industrial. 
Sua tarefa é avaliar os dados consolidados do cliente e emitir um parecer estratégico de negócios.

REGRAS CRUCIALMENTE OBRIGATÓRIAS:
1. NUNCA utilize a estrutura "SINTOMA", "CAUSA" e "SOLUÇÃO". Isso é terminologia de laboratório e está proibido aqui.
2. NUNCA use jargões de manutenção eletrônica.
3. Divida o seu parecer comercial estritamente nas seguintes seções em maiúsculas:
   - **DIAGNÓSTICO DA CONTA** (Focar na saúde financeira, tempo sem comprar, segmentação)
   - **HISTÓRICO E ENGAJAMENTO** (Avaliar interações de WhatsApp, visitas e ordens de serviço)
   - **PLANO DE AÇÃO COMERCIAL** (Estratégias práticas para o vendedor reativar ou expandir a conta)
"""

    # ================================================================
    # 🚀 GERAR ANÁLISE COMERCIAL IA
    # ================================================================

    # Mostra qual provider/modelo está configurado
    config_atual = _obter_config()
    provider_ativo = config_atual.get("provider", "desconhecido")
    modelo_ativo = config_atual.get("modelo", "desconhecido")

    st.subheader("🚀 Gerar Análise Comercial IA")
    st.caption(
        f"Provider: **{provider_ativo.upper()}** | "
        f"Modelo: `{modelo_ativo}`"
    )

    if st.button("🤖 Gerar Análise Comercial", type="primary", width="stretch"):

        with st.spinner("Coletando dados do cliente..."):
            cliente_dados = coletar_cliente(cliente_id)
            faturamento_dados = coletar_faturamento(cliente_id)
            os_dados = coletar_os(cliente_id)
            op_dados = coletar_oportunidades(cliente_id)
            mit_dados = coletar_mitsubishi(cliente_id)
            inter_dados = coletar_interacoes(cliente_id)

            contexto = montar_contexto_cliente(
                cliente_dados,
                faturamento_dados,
                os_dados,
                op_dados,
                mit_dados,
                inter_dados,
            )

        with st.expander("📋 Ver dados que serão enviados para IA"):
            st.text(contexto)

        with st.spinner("🔄 Gerando análise comercial com IA..."):
            resultado = gerar_analise_cliente(
                cliente_id=cliente_id,
                prompt_sistema=PROMPT_COMERCIAL,
            )

        if resultado["sucesso"]:
            st.success("✅ Análise gerada com sucesso!")

            # Métricas
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            col_m1.metric("Provider", provider_ativo.upper())
            col_m2.metric("Tokens Input", resultado["prompt_tokens"])
            col_m3.metric("Tokens Output", resultado["completion_tokens"])
            col_m4.metric("Tempo", f"{resultado['tempo_execucao']:.1f}s")

            # Relatório
            st.markdown("---")
            st.markdown(resultado["conteudo"])

            # Botão copiar
            st.markdown("---")
            if st.button("📋 Copiar Relatório", width="stretch"):
                st.code(resultado["conteudo"], language="markdown")
                st.info("Copie o conteúdo acima.")

        else:
            st.error(f"❌ Erro ao gerar análise ({provider_ativo.upper()})")
            erro = resultado.get("erro", "Erro desconhecido.")
            erro_str = str(erro)

            with st.expander("📋 Detalhes do erro", expanded=True):
                st.code(erro_str, language="text")

            if provider_ativo == "groq":
                if "401" in erro_str or "unauthorized" in erro_str.lower() or "invalid" in erro_str.lower():
                    st.warning(
                        "🔑 **Chave da API Groq inválida!**\n\n"
                        "**Solução:**\n"
                        "1. Obtenha uma chave gratuita em: https://console.groq.com/keys\n"
                        "2. Configure `GROQ_API_KEY` no arquivo `.env`\n"
                        "3. O modelo `llama-3.3-70b-versatile\", \"llama-3.1-8b-instant` é gratuito."
                    )
                elif "429" in erro_str or "quota" in erro_str.lower() or "rate limit" in erro_str.lower():
                    st.warning("🚫 **Limite de taxa Groq excedido.** Aguarde e tente novamente.")
                elif "timeout" in erro_str.lower():
                    st.warning("⏱️ **Tempo limite excedido.** Tente novamente.")
                else:
                    st.warning(
                        f"🔧 **Erro inesperado no Groq.**\n\n"
                        f"Erro original: {erro_str}\n\n"
                        "Verificações:\n"
                        "1. O pacote `groq` está instalado? (pip install groq)\n"
                        "2. A GROQ_API_KEY é válida?\n"
                        "3. O GROQ_MODEL é válido?"
                    )
            elif provider_ativo == "gemini":
                st.warning(
                    "ℹ️ O provider atual é **Gemini**.\n\n"
                    "Se deseja usar Groq, altere `IA_PROVIDER=groq` no `.env`."
                )
            elif provider_ativo == "openai":
                st.warning(
                    "ℹ️ O provider atual é **OpenAI**.\n\n"
                    "Se deseja usar Groq, altere `IA_PROVIDER=groq` no `.env`."
                )
            else:
                st.warning(f"🔧 **Erro no provider '{provider_ativo}'.**\n\n{erro_str}")

# ==================================================
# RELACIONAMENTO (aba 6 - v1.1: Resumo Executivo)
# ==================================================

with tabs[6]:

    st.subheader("📞 Resumo Executivo do Relacionamento")

    # ── Bloco 1: Último Contato ──
    st.markdown("### 📞 Último Contato")
    ultimo = get_ultimo_contato(cliente_id)

    if ultimo:
        col_uc1, col_uc2, col_uc3 = st.columns(3)
        col_uc1.metric("Data", ultimo["data_interacao"] or "-")
        col_uc2.metric("Tipo", ultimo["tipo_interacao"] or "-")
        col_uc3.metric("Resultado", ultimo["resultado"] or "-")

        col_uc4, col_uc5, col_uc6 = st.columns(3)
        col_uc4.metric("Contato", ultimo["contato_nome"] or "-")
        col_uc5.metric("Cargo", ultimo["contato_cargo"] or "-")
        col_uc6.metric("Responsável", ultimo["responsavel"] or "-")

        if ultimo.get("descricao"):
            st.caption(f"**Descrição:** {ultimo['descricao']}")
    else:
        st.info("Nenhum contato registrado para este cliente.")

    st.markdown("---")

    # ── Bloco 2: Pendências Abertas ──
    st.markdown("### 📌 Pendências Abertas")
    try:
        df_pend_abertas = get_pendencias_abertas_cliente(cliente_id)

        if df_pend_abertas.empty:
            st.success("Nenhuma pendência aberta para este cliente.")
        else:
            colunas_pend = [c for c in ["descricao", "responsavel", "data_limite", "status_exibicao"]
                           if c in df_pend_abertas.columns]
            st.dataframe(
                df_pend_abertas[colunas_pend].rename(columns={
                    "descricao": "Descrição",
                    "responsavel": "Responsável",
                    "data_limite": "Vencimento",
                    "status_exibicao": "Status",
                }),
                width="stretch",
                height=200,
            )
    except Exception as e:
        st.info("Nenhuma pendência.")

    st.markdown("---")

    # ── Bloco 3: Oportunidades com Follow-up Pendente ──
    st.markdown("### 📅 Oportunidades com Follow-up Pendente")
    try:
        conn_local = sqlite3.connect("crm.db")
        df_opp_followup = pd.read_sql_query(
            """
            SELECT os.proximo_followup AS data_followup,
                   os.valor_proposta AS valor,
                   os.status,
                   os.responsavel,
                   os.observacoes
            FROM ordens_servico os
            WHERE os.cliente_id = ?
              AND os.proximo_followup IS NOT NULL
              AND os.proximo_followup <= date('now', '+30 days')
            ORDER BY os.proximo_followup ASC
            """,
            conn_local,
            params=(cliente_id,),
        )
        conn_local.close()

        if df_opp_followup.empty:
            st.success("Nenhum follow-up pendente para este cliente.")
        else:
            for _, row in df_opp_followup.iterrows():
                dias = (datetime.strptime(row["data_followup"], "%Y-%m-%d") - datetime.now()).days if row["data_followup"] else 0
                icone = "🔴" if dias < 0 else ("🟡" if dias <= 3 else "🟢")
                st.markdown(
                    f"{icone} **Follow-up**: {row['data_followup']} — "
                    f"R$ {row['valor']:,.2f} — "
                    f"Resp: {row['responsavel']}"
                )
    except Exception as e:
        st.info("Nenhum follow-up pendente.")

    st.markdown("---")

    # ── Bloco 4: Timeline Unificada (v1.3) ──
    st.markdown("### 📋 Timeline Unificada")
    st.caption("Interações, evoluções, pendências e oportunidades em ordem cronológica.")
    try:
        df_timeline = get_timeline_unificada(cliente_id, limite=50)

        if df_timeline.empty:
            st.info("Nenhum evento registrado.")
        else:
            for _, evento in df_timeline.iterrows():
                icone = evento.get("icone", "📌")
                data = str(evento["data"])[:10] if evento["data"] else ""
                desc = evento.get("descricao", "")
                detalhes = evento.get("detalhes", "")
                resp = evento.get("responsavel", "") or ""

                # Criar card visual para cada evento
                with st.container(border=True):
                    cols = st.columns([1, 5, 2])
                    cols[0].markdown(f"**{icone}**")
                    cols[1].markdown(f"**{data}** — {desc}")
                    if resp:
                        cols[2].markdown(f"👤 {resp}")
                    if detalhes:
                        st.caption(f"📎 {detalhes}")

    except Exception as e:
        st.info("Nenhum evento.")

    st.markdown("---")

    # ── Bloco 5: Contatos Conhecidos (v1.1) ──
    st.markdown("### 👤 Contatos Conhecidos")
    try:
        df_contatos = get_contatos_conhecidos(cliente_id)

        if df_contatos.empty:
            st.info("Nenhum contato conhecido extraído das interações.")
        else:
            for _, contato in df_contatos.iterrows():
                cols = st.columns([2, 2, 2, 2, 1])
                cols[0].markdown(f"**{contato['contato_nome']}**")
                cols[1].markdown(f"*{contato['contato_cargo'] or '-'}*")
                cols[2].markdown(f"📞 {contato['contato_telefone'] or '-'}")
                cols[3].markdown(f"✉️ {contato['contato_email'] or '-'}")
                cols[4].markdown(f"*{contato['ultimo_contato'][:10] if contato['ultimo_contato'] else '-'}*")
            st.caption("Contatos extraídos do histórico de interações. Agrupados por nome.")
    except Exception as e:
        st.info("Nenhum contato conhecido.")

# ==================================================
# ABA 7 — 📋 OS AGUARDANDO APROVAÇÃO (PAINEL DE NEGOCIAÇÃO)
# ==================================================

with tabs[7]:

    st.subheader("📋 OS Aguardando Aprovação — Painel de Negociação")

    # ── Query única: TODAS as OS do cliente em negociação ──
    df_os_negociacao = pd.read_sql_query(
        """
        SELECT
            id,
            numero_os,
            status,
            responsavel,
            equipamento,
            marca,
            modelo,
            valor_proposta,
            data_recebimento,
            data_envio_proposta,
            proximo_followup,
            followup_count,
            observacoes
        FROM ordens_servico
        WHERE cliente_id = ?
          AND status IN ('PROPOSTA ENVIADA', 'FOLLOW-UP')
        ORDER BY
            CASE WHEN proximo_followup < date('now') THEN 0
                 WHEN proximo_followup = date('now') THEN 1
                 WHEN proximo_followup = date('now', '+1 day') THEN 2
                 ELSE 3
            END,
            proximo_followup ASC
        """,
        conn,
        params=(cliente_id,),
    )

    hoje = date.today()

    # ── Se não houver propostas, exibir card verde e sair ──
    if df_os_negociacao.empty:

        st.success("✅ Este cliente não possui propostas aguardando aprovação.")
        st.stop()

    # ── Derivar indicadores em memória (apenas 1 query) ──
    qtd_aguardando = len(df_os_negociacao)
    valor_total_aguardando = df_os_negociacao["valor_proposta"].fillna(0).sum()

    # Proposta mais antiga (data_envio_proposta mais distante)
    datas_envio = df_os_negociacao["data_envio_proposta"].dropna()
    if not datas_envio.empty:
        data_mais_antiga = pd.to_datetime(datas_envio.min())
        dias_proposta_mais_antiga = (datetime.now() - data_mais_antiga).days
    else:
        data_mais_antiga = None
        dias_proposta_mais_antiga = 0

    # Follow-ups vencidos, hoje, amanhã
    followups_vencidos = 0
    followups_hoje = 0
    followups_amanha = 0

    for _, row in df_os_negociacao.iterrows():
        prox_fu = row["proximo_followup"]
        if pd.notna(prox_fu):
            prox_fu_date = pd.to_datetime(prox_fu).date()
            if prox_fu_date < hoje:
                followups_vencidos += 1
            elif prox_fu_date == hoje:
                followups_hoje += 1
            elif prox_fu_date == hoje + pd.Timedelta(days=1):
                followups_amanha += 1

    # Maior proposta
    idx_maior = df_os_negociacao["valor_proposta"].fillna(0).idxmax()
    maior_proposta_os = df_os_negociacao.loc[idx_maior, "numero_os"]
    maior_proposta_valor = df_os_negociacao.loc[idx_maior, "valor_proposta"]

    # ═══════════════════════════════════════════════
    # PAINEL "RESUMO DA VISITA"
    # ═══════════════════════════════════════════════

    with st.container(border=True):
        st.markdown("### 📋 Resumo da Visita")
        st.caption("Informações consolidadas para preparação de visitas comerciais.")

        col_r1, col_r2, col_r3, col_r4 = st.columns(4)
        col_r1.metric("Propostas Aguardando", qtd_aguardando)
        col_r2.metric("Valor Total", f"R$ {valor_total_aguardando:,.0f}")
        col_r3.metric(
            "Maior Proposta",
            f"OS {maior_proposta_os} — R$ {maior_proposta_valor:,.0f}" if pd.notna(maior_proposta_valor) else "—"
        )
        col_r4.metric("Mais Antiga", f"{dias_proposta_mais_antiga} dias" if dias_proposta_mais_antiga > 0 else "—")

        col_r5, col_r6, col_r7, col_r8 = st.columns(4)
        col_r5.metric("🔴 Follow-ups Vencidos", followups_vencidos)
        col_r6.metric("🟡 Follow-ups Hoje", followups_hoje)
        col_r7.metric("🔵 Follow-ups Amanhã", followups_amanha)
        col_r8.metric("💰 Valor Parado", f"R$ {valor_total_aguardando:,.0f}")

    # ═══════════════════════════════════════════════
    # INDICADORES EXECUTIVOS (cards no topo)
    # ═══════════════════════════════════════════════

    col_k1, col_k2, col_k3, col_k4 = st.columns(4)
    col_k1.metric("📋 OS Aguardando Aprovação", qtd_aguardando)
    col_k2.metric("💰 Valor Total Aguardando", f"R$ {valor_total_aguardando:,.0f}")
    col_k3.metric("📅 Proposta Mais Antiga", f"{dias_proposta_mais_antiga} dias" if dias_proposta_mais_antiga > 0 else "—")
    col_k4.metric("🔴 Follow-ups Vencidos", followups_vencidos)

    col_k5, col_k6, col_k7, col_k8 = st.columns(4)
    col_k5.metric("🟡 Follow-ups Hoje", followups_hoje)
    col_k6.metric("🔵 Follow-ups Amanhã", followups_amanha)

    st.divider()

    # ═══════════════════════════════════════════════
    # TABELA PRINCIPAL
    # ═══════════════════════════════════════════════

    st.markdown("### Propostas em Negociação")

    # ── Função auxiliar: extrair último contato do histórico ──
    def extrair_ultimo_contato(observacoes):
        """Extrai a última interação registrada do campo observacoes.
        Formato esperado: [dd/mm/aaaa]: texto
        Retorna tupla (data, texto_resumido)"""
        if pd.isna(observacoes) or not observacoes:
            return ("—", "—")
        linhas = str(observacoes).strip().split("\n")
        linhas = [l.strip() for l in linhas if l.strip()]
        if not linhas:
            return ("—", "—")
        primeira = linhas[0]
        # Formato esperado: [dd/mm/aaaa]: texto
        if "]: " in primeira:
            partes = primeira.split("]: ", 1)
            data = partes[0].replace("[", "").strip()
            texto = partes[1].strip()
        else:
            data = ""
            texto = primeira
        # Limitar a ~80 caracteres
        if len(texto) > 80:
            texto = texto[:77] + "..."
        return (data if data else "—", texto if texto else "—")

    # ── Função: extrair histórico completo como timeline ──
    def extrair_timeline(observacoes):
        """Extrai todas as entradas do campo observacoes em ordem cronológica.
        Retorna lista de dicts com data, icone, texto."""
        if pd.isna(observacoes) or not observacoes:
            return []
        linhas = str(observacoes).strip().split("\n")
        linhas = [l.strip() for l in linhas if l.strip()]
        entradas = []
        for linha in linhas:
            if "]: " in linha:
                partes = linha.split("]: ", 1)
                data_raw = partes[0].replace("[", "").strip()
                texto = partes[1].strip()
                icone = "📞"  # Default: contato telefônico
                if "proposta" in texto.lower() or "enviada" in texto.lower():
                    icone = "📄"
                elif "prometeu" in texto.lower() or "retorno" in texto.lower():
                    icone = "📅"
                elif "aprov" in texto.lower():
                    icone = "✅"
                elif "perdeu" in texto.lower() or "perd" in texto.lower():
                    icone = "❌"
                entradas.append({
                    "data": data_raw,
                    "icone": icone,
                    "texto": texto,
                })
            else:
                entradas.append({
                    "data": "—",
                    "icone": "📌",
                    "texto": linha,
                })
        # Inverter para ordem cronológica (mais antigo primeiro)
        entradas.reverse()
        return entradas

    # ── Clasificar status de follow-up para badge ──
    def classificar_followup(data_followup):
        if pd.isna(data_followup):
            return ("⚪", "Sem follow-up")
        data_fu = pd.to_datetime(data_followup).date() if hasattr(pd.to_datetime(data_followup), 'date') else data_followup
        if isinstance(data_fu, str):
            data_fu = pd.to_datetime(data_fu).date()
        if data_fu < hoje:
            return ("🔴", "Follow-up vencido")
        elif data_fu == hoje:
            return ("🟡", "Hoje")
        elif data_fu == hoje + pd.Timedelta(days=1):
            return ("🔵", "Amanhã")
        else:
            return ("🟢", "Dentro do prazo")

    # ── Montar linhas da tabela ──
    linhas_tabela = []
    for _, row in df_os_negociacao.iterrows():
        # Dias aguardando
        if pd.notna(row["data_envio_proposta"]):
            data_envio = pd.to_datetime(row["data_envio_proposta"])
            dias_aguardando = (datetime.now() - data_envio).days
        else:
            dias_aguardando = 0

        # Próximo follow-up
        badge_fu, status_fu_texto = classificar_followup(row["proximo_followup"])
        data_fu_str = pd.to_datetime(row["proximo_followup"]).strftime("%d/%m/%Y") if pd.notna(row["proximo_followup"]) else "—"

        # Último contato
        data_ult_contato, texto_ult_contato = extrair_ultimo_contato(row["observacoes"])

        # Follow-up count
        fup_count = row["followup_count"] if pd.notna(row["followup_count"]) else 0

        # Negociação longa?
        alerta_longa = ""
        if dias_aguardando >= 90 or fup_count >= 10:
            alerta_longa = "⚠ Negociação longa"

        linhas_tabela.append({
            "badge_fu": badge_fu,
            "status_fu": status_fu_texto,
            "OS": str(row["numero_os"]),
            "Equipamento": row["equipamento"] if pd.notna(row["equipamento"]) else "—",
            "Valor": row["valor_proposta"] if pd.notna(row["valor_proposta"]) else 0,
            "Data Envio": pd.to_datetime(row["data_envio_proposta"]).strftime("%d/%m/%Y") if pd.notna(row["data_envio_proposta"]) else "—",
            "Dias Aguardando": dias_aguardando,
            "Próx. Follow-up": data_fu_str,
            "Status Follow-up": status_fu_texto,
            "Responsável": row["responsavel"] if pd.notna(row["responsavel"]) else "—",
            "Qtd Follow-ups": int(fup_count),
            "Último Contato": f"{data_ult_contato} — {texto_ult_contato}" if texto_ult_contato != "—" else "—",
            "alerta_longa": alerta_longa,
            "_id": row["id"],
            "_numero_os": row["numero_os"],
            "_observacoes": row["observacoes"],
            "_followup_count": fup_count,
            "_dias_aguardando": dias_aguardando,
            "_data_envio": row["data_envio_proposta"],
            "_responsavel": row["responsavel"],
            "_equipamento": row["equipamento"],
            "_proximo_followup": row["proximo_followup"],
        })

    df_exibicao = pd.DataFrame(linhas_tabela)

    # ── Ordenação: vencido → hoje → amanhã → próximos → mais recentes ──
    ordem_categoria = {
        "Follow-up vencido": 0,
        "Hoje": 1,
        "Amanhã": 2,
        "Dentro do prazo": 3,
        "Sem follow-up": 4,
    }
    df_exibicao["_ordem"] = df_exibicao["Status Follow-up"].map(ordem_categoria)
    df_exibicao = df_exibicao.sort_values(["_ordem", "Dias Aguardando"], ascending=[True, False]).reset_index(drop=True)

    # ═══════════════════════════════════════════════
    # RENDERIZAÇÃO DA TABELA COM EXPANDERS
    # ═══════════════════════════════════════════════

    for idx, row in df_exibicao.iterrows():

        badge = row["badge_fu"]
        os_numero = row["OS"]
        valor = row["Valor"]
        dias_ag = row["Dias Aguardando"]
        alerta = row["alerta_longa"]
        equip = row["Equipamento"]

        # Título do expander
        titulo_expander = f"{badge} **OS {os_numero}** — {equip} — R$ {valor:,.2f} — {dias_ag}d"
        if alerta:
            titulo_expander += f" | ⚠️ {alerta}"

        with st.expander(titulo_expander, expanded=False):

            # ── Informações principais ──
            col_info1, col_info2, col_info3 = st.columns(3)
            col_info1.markdown(f"**OS:** {os_numero}")
            col_info1.markdown(f"**Equipamento:** {equip}")
            col_info1.markdown(f"**Valor:** R$ {valor:,.2f}")

            col_info2.markdown(f"**Data Envio:** {row['Data Envio']}")
            col_info2.markdown(f"**Dias em Negociação:** {dias_ag}d")
            col_info2.markdown(f"**Responsável:** {row['_responsavel']}")

            col_info3.markdown(f"**Próx. Follow-up:** {row['Próx. Follow-up']}")
            col_info3.markdown(f"**Qtd Follow-ups:** {int(row['_followup_count'])}")
            col_info3.markdown(f"**Status:** {row['Status Follow-up']}")

            # Alerta de negociação longa
            if alerta:
                st.warning(alerta)

            # ── Histórico / Timeline ──
            st.markdown("---")
            st.markdown("### 📋 Histórico de Interações")

            timeline = extrair_timeline(row["_observacoes"])
            if timeline:
                for entrada in timeline:
                    with st.container(border=True):
                        cols = st.columns([1, 5])
                        cols[0].markdown(f"**{entrada['icone']}**")
                        cols[1].markdown(f"**{entrada['data']}** — {entrada['texto']}")
            else:
                st.info("Nenhum histórico registrado para esta OS.")

    # ═══════════════════════════════════════════════
    # NOTA DE RODAPÉ
    # ═══════════════════════════════════════════════

    st.caption(
        f"*Total de {len(df_exibicao)} OS em negociação. "
        f"Valor parado: R$ {valor_total_aguardando:,.2f}. "
        f"Dados atualizados dinamicamente.*"
    )

conn.close()