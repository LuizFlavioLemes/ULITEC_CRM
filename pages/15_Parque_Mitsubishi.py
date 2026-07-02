import streamlit as st
import pandas as pd

from auth import sidebar_usuario
from permissions import verificar_acesso_pagina
from services.mitsubishi import (
    get_indicadores,
    get_nc_series_agrupado,
    get_maquinas_por_estado,
    get_todos_clientes_mitsubishi,
    get_maquinas_por_nc_series,
    importar_arquivo,
    executar_conciliacao,
    get_conciliacao_pendencias,
    get_clientes_para_vinculo,
    get_maquinas_por_filtro,
    get_duplicidades,
    aprovar_sugestao,
    vincular_manual,
    rejeitar_sugestao,
    excluir_vinculo,
)

# ── Proteção: acesso geral (autenticado) ──
verificar_acesso_pagina()
sidebar_usuario()

st.title("🏭 Parque Mitsubishi")

# ============================================================
# ABAS
# ============================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Visão Geral",
    "📥 Importação",
    "🔗 Conciliação",
    "🛠 Revisão",
])

# ============================================================
# ABA 1 — VISÃO GERAL
# ============================================================
with tab1:
    indicadores = get_indicadores()

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Máquinas", indicadores["total_maquinas"])
    c2.metric("Clientes com Mitsubishi", indicadores["total_clientes"])
    c3.metric("Conciliadas", indicadores["conciliadas"])
    c4.metric("Pendentes", indicadores["pendentes"])
    c5.metric("% Conciliado", f"{indicadores['percentual_conciliado']}%")

    st.divider()

    grafico_col1, grafico_col2 = st.columns(2)

    with grafico_col1:
        st.subheader("Máquinas por Série CNC")
        nc_series = get_nc_series_agrupado()
        if not nc_series.empty:
            st.bar_chart(nc_series.set_index("nc_series"), height=300)
        else:
            st.info("Nenhum dado de série CNC disponível.")

    with grafico_col2:
        st.subheader("Máquinas por Estado")
        por_estado = get_maquinas_por_estado()
        if not por_estado.empty:
            st.bar_chart(por_estado.set_index("uf"), height=300)
        else:
            st.info("Nenhum dado de estado disponível.")

    st.divider()

    st.subheader("Clientes com Máquinas Mitsubishi")
    clientes_mitsu = get_todos_clientes_mitsubishi()
    if not clientes_mitsu.empty:
        st.dataframe(clientes_mitsu, width="stretch", height=400)
        st.caption(f"Total de {len(clientes_mitsu)} clientes com máquinas Mitsubishi.")
    else:
        st.info("Nenhum cliente vinculado ainda.")

    st.divider()

    st.subheader("Filtrar Máquinas por Série CNC")
    series_disponiveis = get_maquinas_por_nc_series()
    if not series_disponiveis.empty:
        lista_series = ["Todas"] + list(series_disponiveis["nc_series"])
        serie_selecionada = st.selectbox(
            "Selecione a série CNC",
            lista_series,
            key="filtro_serie_cnc",
        )
        if serie_selecionada != "Todas":
            maquinas_serie = get_maquinas_por_nc_series(serie_selecionada)
            st.dataframe(maquinas_serie, width="stretch", height=400)
            st.caption(f"{len(maquinas_serie)} máquinas encontradas para série {serie_selecionada}.")
        else:
            st.info("Selecione uma série CNC para visualizar as máquinas correspondentes.")
    else:
        st.info("Nenhuma série CNC disponível.")

# ============================================================
# ABA 2 — IMPORTAÇÃO
# ============================================================
with tab2:
    st.subheader("📥 Importar Base Mitsubishi")

    arquivo = st.file_uploader(
        "Selecione a planilha Mitsubishi (aba: Base)",
        type=["xlsx"],
        key="upload_mitsubishi",
    )

    if arquivo:
        try:
            df_previa = pd.read_excel(arquivo, sheet_name="Base", dtype=str)
            df_previa = df_previa.fillna("")
            df_previa.columns = df_previa.columns.astype(str).str.strip()

            st.success(f"{len(df_previa)} registros encontrados na planilha.")

            st.subheader("Colunas encontradas")
            st.write(list(df_previa.columns))

            st.subheader("Prévia (20 primeiras linhas)")
            st.dataframe(df_previa.head(20), width="stretch")

            if st.button("📥 Importar Base Mitsubishi", key="btn_importar"):
                # Volta ao início do arquivo para re-ler
                arquivo.seek(0)
                resultado = importar_arquivo(arquivo)

                if resultado["sucesso"]:
                    st.success(
                        f"{resultado['importados']} máquinas importadas com sucesso."
                    )
                    st.info(
                        f"Total gravado na tabela: {resultado['total_gravado']}"
                    )
                else:
                    st.error(f"Erro ao importar: {resultado['erro']}")

        except Exception as e:
            st.error(f"Erro ao processar arquivo: {e}")

# ============================================================
# ABA 3 — CONCILIAÇÃO
# ============================================================
with tab3:
    st.subheader("🔗 Conciliação Mitsubishi x Clientes ERP")

    indicadores_conc = get_indicadores()

    c1, c2, c3 = st.columns(3)
    c1.metric("🔴 Pendentes", indicadores_conc["pendentes"])
    c2.metric("✅ Conciliadas", indicadores_conc["conciliadas"])
    c3.metric(
        "% Conciliado",
        f"{indicadores_conc['percentual_conciliado']}%",
    )

    st.divider()

    filtro = st.radio(
        "Filtrar máquinas",
        ["TODOS", "CONCILIADOS", "PENDENTES"],
        horizontal=True,
        key="filtro_conciliacao",
    )

    maquinas_filtradas = get_maquinas_por_filtro(filtro)
    st.dataframe(maquinas_filtradas, width="stretch", height=300)

    st.divider()

    if st.button("🚀 Executar Conciliação Automática", key="btn_conciliar"):
        with st.spinner("Conciliando máquinas..."):
            resultado = executar_conciliacao()

        if not resultado["sucesso"]:
            st.error(f"Erro: {resultado.get('erro', 'desconhecido')}")
        else:
            st.success(f"Conciliação concluída! {resultado['total']} máquinas processadas.")

            col1, col2, col3 = st.columns(3)
            col1.metric("✅ Vinculados", len(resultado["automaticos"]))
            col2.metric("🟡 Revisar", len(resultado["revisar"]))
            col3.metric("🔴 Não Encontrados", len(resultado["nao_encontrados"]))

            if resultado["automaticos"]:
                st.subheader("✅ Vinculados Automaticamente")
                st.dataframe(pd.DataFrame(resultado["automaticos"]), width="stretch")

            if resultado["revisar"]:
                st.subheader("🟡 Revisão Manual")
                df_revisar = pd.DataFrame(resultado["revisar"]).sort_values("score", ascending=False)
                st.dataframe(df_revisar, width="stretch")

            if resultado["nao_encontrados"]:
                st.subheader("🔴 Não Encontrados na Base ERP")
                st.dataframe(pd.DataFrame(resultado["nao_encontrados"]), width="stretch")

# ============================================================
# ABA 4 — REVISÃO
# ============================================================
with tab4:
    st.subheader("🛠 Revisão de Pendências e Conflitos")

    total_pendente = get_indicadores()["pendentes"]

    # Carrega pendências de conciliação
    pendencias_conciliacao = get_conciliacao_pendencias(200)
    duplicidades = get_duplicidades()

    c1, c2, c3 = st.columns(3)
    c1.metric("🔴 Máquinas sem Cliente", total_pendente)
    c2.metric("🟡 Revisão de Conciliação", len(pendencias_conciliacao))
    c3.metric("🔄 Serial Duplicado", len(duplicidades))

    st.divider()

    # ── DUPLICIDADES ──
    if not duplicidades.empty:
        st.subheader("🔄 Serial Number Duplicado")
        st.warning("Estas máquinas possuem o mesmo serial number. Verifique e corrija.")
        st.dataframe(duplicidades, width="stretch")

        maquina_id_excluir = st.number_input(
            "ID da máquina para excluir vínculo (duplicidade)",
            min_value=1,
            step=1,
            key="input_excluir_duplicidade",
        )
        if st.button("🗑 Excluir Vínculo da Máquina", key="btn_excluir_duplicidade"):
            resultado = excluir_vinculo(maquina_id_excluir)
            if resultado["sucesso"]:
                st.success(f"Vínculo da máquina {maquina_id_excluir} removido.")
                st.rerun()
            else:
                st.error(f"Erro: {resultado['erro']}")

        st.divider()

    # ── REVISÃO MANUAL ──
    if pendencias_conciliacao.empty:
        st.success("Nenhuma pendência de conciliação para revisar.")
    else:
        st.subheader("🟡 Pendências de Conciliação")

        limite_revisao = st.slider(
            "Quantidade para revisar",
            10, 200, 50,
            step=10,
            key="slider_revisao",
        )

        pendencias = get_conciliacao_pendencias(limite_revisao)

        st.dataframe(
            pendencias[
                [
                    "conciliacao_id",
                    "customer",
                    "cliente_sugerido",
                    "score",
                    "city",
                    "uf",
                    "machine",
                    "serial_number",
                ]
            ],
            width="stretch",
            height=320,
        )

        opcoes = {
            f"#{row.conciliacao_id} | {row.customer} -> {row.cliente_sugerido} ({row.score:.1f})": row.conciliacao_id
            for row in pendencias.itertuples()
        }

        if opcoes:
            selecionado_label = st.selectbox(
                "Selecione uma pendência",
                list(opcoes.keys()),
                key="select_pendencia",
            )

            conciliacao_id = int(opcoes[selecionado_label])
            registro = pendencias[
                pendencias["conciliacao_id"] == conciliacao_id
            ].iloc[0]

            st.divider()

            col_dados, col_acao = st.columns([2, 1])

            with col_dados:
                st.subheader("Dados da Máquina")
                st.write(f"**Cliente na base Mitsubishi:** {registro['customer']}")
                st.write(f"**Cidade/UF:** {registro['city']} / {registro['uf']}")
                st.write(f"**Máquina:** {registro['machine']}")
                st.write(f"**Série:** {registro['serial_number']}")
                st.write(f"**NC:** {registro['nc_series']}")
                st.write(f"**Ano:** {registro['ano']}")
                st.write(f"**Sugestão ERP:** {registro['cliente_sugerido']}")
                st.write(f"**Score:** {registro['score']:.2f}")

            with col_acao:
                st.subheader("Decisão")

                clientes_df = get_clientes_para_vinculo()
                clientes_opcoes = {
                    f"{row.razao_social} | {row.cidade or ''}/{row.estado or ''} | ERP {row.codigo_erp or '-'}": row.id
                    for row in clientes_df.itertuples()
                }

                cliente_manual_label = st.selectbox(
                    "Vincular a outro cliente",
                    list(clientes_opcoes.keys()),
                    key="select_cliente_revisao",
                )

                col_btn1, col_btn2 = st.columns(2)

                with col_btn1:
                    if st.button("✅ Aprovar Sugestão", key="btn_aprovar"):
                        resultado = aprovar_sugestao(
                            int(conciliacao_id),
                            int(registro["maquina_id"]),
                            int(registro["cliente_sugerido_id"]),
                            float(registro["score"]),
                        )
                        if resultado["sucesso"]:
                            st.success("Sugestão aprovada!")
                            st.rerun()
                        else:
                            st.error(f"Erro: {resultado['erro']}")

                with col_btn2:
                    if st.button("🔗 Vincular Manualmente", key="btn_vincular"):
                        cliente_id = int(clientes_opcoes[cliente_manual_label])
                        cliente_nome = cliente_manual_label.split(" | ")[0]
                        resultado = vincular_manual(
                            int(conciliacao_id),
                            int(registro["maquina_id"]),
                            cliente_id,
                            float(registro["score"]),
                            cliente_nome,
                        )
                        if resultado["sucesso"]:
                            st.success("Máquina vinculada manualmente.")
                            st.rerun()
                        else:
                            st.error(f"Erro: {resultado['erro']}")

                if st.button("❌ Rejeitar Sugestão", key="btn_rejeitar"):
                    resultado = rejeitar_sugestao(int(conciliacao_id))
                    if resultado["sucesso"]:
                        st.warning("Sugestão rejeitada.")
                        st.rerun()
                    else:
                        st.error(f"Erro: {resultado['erro']}")