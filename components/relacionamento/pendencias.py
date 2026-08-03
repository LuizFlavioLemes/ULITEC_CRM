"""
Componente das Abas 4 (📌 Pendências) e 5 (➕ Nova Pendência).

Gerencia pendências comerciais com:
- Sub-abas: Abertas, Vencidas, Concluídas
- Cards com timeline de evoluções
- Editar, concluir, reabrir
- Criação independente de pendência

Responsabilidades:
- Exibir cards de pendência com timeline
- Gerenciar CRUD completo de pendências
- Gerenciar criação independente de pendência (aba 5)
"""

from datetime import datetime, date, timedelta

import streamlit as st
import pandas as pd

from services.relacionamento import (
    PRIORIDADES,
    TIPOS_PENDENCIA,
    criar_pendencia,
    get_pendencias,
    atualizar_pendencia,
    criar_evolucao_pendencia,
    get_evolucoes_pendencia,
    concluir_pendencia_com_evolucao,
    reabrir_pendencia_com_evolucao,
)


def _exibir_card_pendencia(row, key_prefix="pend"):
    """Exibe um card de pendência com timeline, edição e ações."""
    with st.container(border=True):
        c1, c2, c3 = st.columns([3, 1, 1])
        c1.markdown(f"**{row['cliente']}** — {row['descricao']}")
        c2.markdown(f"🔵 {row['prioridade']}")
        c3.markdown(f"📅 {row['data_limite']}")

        # ── TIMELINE DE EVOLUÇÕES ──
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
                                proximo_contato=proximo_contato.strftime("%Y-%m-%d")
                                if proximo_contato
                                else None,
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
                    data_atual = datetime.strptime(
                        row["data_limite"], "%Y-%m-%d"
                    ).date()
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
            salvar_click = col_a1.button(
                "💾 Salvar alterações",
                key=f"salvar_{key_prefix}_{row['id']}",
            )
            finalizar_click = col_a2.button(
                "✅ Finalizar Pendência",
                key=f"conc_{key_prefix}_{row['id']}",
            )

            if salvar_click:
                try:
                    atualizar_pendencia(
                        pendencia_id=row["id"],
                        descricao=nova_desc if nova_desc != row["descricao"] else None,
                        prioridade=nova_prio if nova_prio != row["prioridade"] else None,
                        data_limite=nova_data.strftime("%Y-%m-%d")
                        if nova_data != data_atual
                        else None,
                        responsavel=novo_resp
                        if novo_resp != row.get("responsavel", "")
                        else None,
                    )
                    st.success("✅ Pendência atualizada!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erro ao atualizar: {e}")

            # ── CONFIRMAÇÃO DE FINALIZAÇÃO ──
            conf_key = f"confirmar_finalizar_{key_prefix}_{row['id']}"

            if finalizar_click:
                st.session_state[conf_key] = True

            if st.session_state.get(conf_key, False):
                with st.container(border=True):
                    st.warning(
                        "❗ Deseja realmente finalizar esta pendência?\n\n"
                        "Após finalizar ela deixará de aparecer na agenda comercial "
                        "e será registrada como concluída."
                    )
                    col_c1, col_c2 = st.columns(2)
                    with col_c1:
                        if st.button(
                            "✅ Finalizar Pendência",
                            type="primary",
                            width="stretch",
                            key=f"confirmar_conc_{key_prefix}_{row['id']}",
                        ):
                            try:
                                concluir_pendencia_com_evolucao(
                                    pendencia_id=row["id"],
                                    usuario_id=st.session_state.get("usuario_id"),
                                    usuario_nome=st.session_state.get("usuario_nome", ""),
                                    observacao=nova_desc if nova_desc != row["descricao"] else "",
                                )
                                st.session_state.pop(conf_key, None)
                                st.success("Pendência finalizada com sucesso.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Erro ao finalizar: {e}")
                    with col_c2:
                        if st.button(
                            "Cancelar",
                            width="stretch",
                            key=f"cancelar_conc_{key_prefix}_{row['id']}",
                        ):
                            st.session_state.pop(conf_key, None)
                            st.rerun()

        if row["status"] == "FECHADA":
            with st.expander("🔄 Reabrir pendência", expanded=False):
                motivo_reabertura = st.text_area(
                    "Motivo da reabertura",
                    key=f"motivo_reab_{key_prefix}_{row['id']}",
                )
                if st.button(
                    "🔄 Confirmar Reabertura",
                    key=f"reabrir_{key_prefix}_{row['id']}",
                ):
                    try:
                        reabrir_pendencia_com_evolucao(
                            pendencia_id=row["id"],
                            usuario_id=st.session_state.get("usuario_id"),
                            usuario_nome=st.session_state.get("usuario_nome", ""),
                            motivo=motivo_reabertura.strip()
                            if motivo_reabertura.strip()
                            else "",
                        )
                        st.success("🔄 Pendência reaberta!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro ao reabrir: {e}")


def exibir_pendencias():
    """Renderiza a aba Pendências com suas 3 sub-abas."""
    st.subheader("📌 Pendências Comerciais")

    tab_p1, tab_p2, tab_p3 = st.tabs([
        "🔴 Abertas",
        "⚠️ Vencidas",
        "✅ Concluídas",
    ])

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
                _exibir_card_pendencia(row, key_prefix="aberta")

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
                _exibir_card_pendencia(row, key_prefix="vencida")

    with tab_p3:
        df_pend_concluidas = get_pendencias(status="FECHADA")
        if df_pend_concluidas.empty:
            st.info("Nenhuma pendência concluída ainda.")
        else:
            for _, row in df_pend_concluidas.iterrows():
                _exibir_card_pendencia(row, key_prefix="concluida")


def exibir_nova_pendencia(clientes_lista, clientes_dict):
    """
    Renderiza o formulário de criação independente de pendência
    (atualmente aba 5 no Relacionamento Comercial).
    """
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
            pend_tipo = st.selectbox(
                "🏷️ Tipo da Pendência",
                options=TIPOS_PENDENCIA,
                key="nova_pend_tipo",
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
                        tipo_pendencia=pend_tipo,
                    )
                    st.success("✅ Pendência criada com sucesso!")
                    for key in list(st.session_state.keys()):
                        if key.startswith("nova_pend_"):
                            del st.session_state[key]
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erro ao criar pendência: {e}")