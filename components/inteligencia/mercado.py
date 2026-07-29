"""
Componente de Painéis de Mercado.
Consome exclusivamente services/inteligencia_comercial.
Nenhum SQL é executado aqui.
"""

import streamlit as st
import pandas as pd

from services.inteligencia_comercial import (
    classificar_abcd,
    get_top_faturamento_12m,
    get_preventivas_vencidas,
    get_prospeccao_mitsubishi,
    get_ultima_interacao_clientes,
)


def exibir_mercado(unidade_param=None):
    """
    Renderiza os painéis de mercado (ABCD, Top Faturamento, Preventivas, Mitsubishi).

    Parâmetros:
        unidade_param: str or None — filtro de unidade
    """
    st.subheader("📊 Painéis de Mercado")

    tab_abcd, tab_top_fat, tab_preventivas, tab_mitsubishi = st.tabs([
        "Classificação ABCD",
        "Top Faturamento",
        "Preventivas Vencidas",
        "Prospecção Mitsubishi",
    ])

    # ── Classificação ABCD ──
    with tab_abcd:
        st.subheader("Classificação ABCD")
        st.caption("A = top 10% faturamento | B = próximos 30% | C = próximos 60% | D = sem faturamento")

        filtro_classe = st.radio(
            "Filtrar por classe",
            options=["Todas", "A", "B", "C", "D"],
            horizontal=True,
            key="filtro_classe_abcd",
        )

        df_clientes_abc = classificar_abcd(unidade=unidade_param)
        df_clientes_abc["classe_abc"] = df_clientes_abc["classe_abc"].astype(str)

        # Complementar com última interação
        df_ult_interacao = get_ultima_interacao_clientes()
        if not df_ult_interacao.empty:
            df_clientes_abc = df_clientes_abc.merge(
                df_ult_interacao, left_on="id", right_on="cliente_id", how="left"
            )
        df_clientes_abc["ultima_interacao"] = df_clientes_abc.get("ultima_interacao", pd.Series(dtype=str)).fillna("Nunca")

        df_abcd = df_clientes_abc.copy()
        if filtro_classe != "Todas":
            df_abcd = df_abcd[df_abcd["classe_abc"] == filtro_classe]

        if df_abcd.empty:
            st.info("Nenhum cliente encontrado com o filtro selecionado.")
        else:
            df_exib = df_abcd.rename(columns={
                "razao_social": "Cliente", "classe_abc": "Classe",
                "cidade": "Cidade", "estado": "Estado",
                "ultima_visita": "Última Visita",
                "ultima_interacao": "Última Interação",
                "faturamento_12m": "Faturamento 12m",
            })
            df_exib["Faturamento 12m"] = df_exib["Faturamento 12m"].apply(
                lambda x: f"R$ {x:,.2f}" if pd.notna(x) and x > 0 else "R$ 0,00"
            )
            df_exib["Última Visita"] = df_exib["Última Visita"].fillna("Nunca")
            df_exib["Última Interação"] = df_exib["Última Interação"].fillna("Nunca")

            st.dataframe(
                df_exib[["Cliente", "Classe", "Cidade", "Estado",
                         "Faturamento 12m", "Última Interação", "Última Visita"]],
                width="stretch", height=500,
            )
            st.caption(f"Total: {len(df_abcd)} clientes.")

    # ── Top Faturamento ──
    with tab_top_fat:
        st.subheader("Top 20 Clientes por Faturamento (12 meses)")
        df_top_fat = get_top_faturamento_12m(unidade=unidade_param)
        if df_top_fat.empty:
            st.success("Nenhum dado disponível.")
        else:
            df_exib = df_top_fat.rename(columns={
                "cliente": "Cliente", "faturamento_12m": "Faturamento 12m",
                "participacao": "%",
            })
            df_exib["Faturamento 12m"] = df_exib["Faturamento 12m"].apply(lambda x: f"R$ {x:,.2f}")
            df_exib["%"] = df_exib["%"].apply(lambda x: f"{x:.1f}%")
            st.dataframe(df_exib, width="stretch", height=400)

    # ── Preventivas Vencidas ──
    with tab_preventivas:
        st.subheader("Clientes com Preventiva Vencida")
        df_prev = get_preventivas_vencidas(unidade=unidade_param)
        if df_prev.empty:
            st.success("Nenhum cliente com preventiva vencida.")
        else:
            df_exib = df_prev.rename(columns={
                "razao_social": "Cliente", "cidade": "Cidade",
                "estado": "Estado", "data_ultima_os": "Última OS",
                "dias_sem_manutencao": "Dias sem Manutenção",
            })
            df_exib["Última OS"] = pd.to_datetime(df_exib["Última OS"], errors="coerce")
            df_exib = df_exib.dropna(subset=["Última OS"])
            df_exib["Última OS"] = df_exib["Última OS"].dt.strftime("%d/%m/%Y")
            st.dataframe(
                df_exib[["Cliente", "Cidade", "Estado", "Última OS", "Dias sem Manutenção"]],
                width="stretch", height=400,
            )

    # ── Prospecção Mitsubishi ──
    with tab_mitsubishi:
        st.subheader("Empresas com Máquinas Mitsubishi — Nunca Compraram")
        st.caption("Potencial para prospecção ativa (outbound)")
        df_novos = get_prospeccao_mitsubishi(unidade=unidade_param)
        if df_novos.empty:
            st.success("Nenhum cliente em prospecção encontrado.")
        else:
            df_exib = df_novos.rename(columns={
                "razao_social": "Cliente", "cidade": "Cidade",
                "estado": "Estado", "qtd_mitsubishi": "Máquinas",
                "potencial": "Potencial",
            })

            def cor_potencial(val):
                if val == "ALTO":
                    return "background-color: #28a745; color: white"
                elif val == "MÉDIO":
                    return "background-color: #ffc107; color: black"
                return ""

            st.dataframe(
                df_exib.style.map(cor_potencial, subset=["Potencial"]),
                width="stretch", height=400,
            )