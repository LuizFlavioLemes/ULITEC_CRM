"""
Componente de Listas Acionáveis (Clientes).
Consome exclusivamente services/inteligencia_comercial.
Nenhum SQL é executado aqui.
"""

import streamlit as st
import pandas as pd

from services.inteligencia_comercial import (
    get_clientes_esfriando,
    get_clientes_esquentando,
    get_clientes_sem_visita,
    get_clientes_sem_faturamento,
)


def exibir_listas(unidade_param=None, aplicar_filtros=None):
    """
    Renderiza as listas acionáveis (Esfriando, Esquentando, Sem Visita, Sem Faturamento).

    Parâmetros:
        unidade_param: str or None — filtro de unidade
        aplicar_filtros: callable or None — função para aplicar filtros extras (estado/cidade/cliente)
    """
    df_esfriando = get_clientes_esfriando(unidade=unidade_param)
    df_esquentando = get_clientes_esquentando(unidade=unidade_param)
    df_sem_visita = get_clientes_sem_visita(unidade=unidade_param)
    df_sem_faturamento = get_clientes_sem_faturamento(unidade=unidade_param)

    tab_esfriando, tab_esquentando, tab_sem_visita_tab, tab_sem_faturamento_tab = st.tabs([
        "Clientes Esfriando",
        "Clientes Esquentando",
        "Sem Visita",
        "Sem Faturamento",
    ])

    # ── Esfriando ──
    with tab_esfriando:
        st.subheader("Clientes Esfriando")
        st.caption("Clientes com queda de faturamento > 30% ou sem visita > 120 dias")
        df_aba = aplicar_filtros(df_esfriando) if aplicar_filtros and not df_esfriando.empty else df_esfriando
        if df_aba.empty:
            st.success("Nenhum cliente esfriando no período.")
        else:
            df_exib = df_aba.rename(columns={
                "cliente": "Cliente", "cidade": "Cidade",
                "variacao": "Queda (%)", "dias_sem_visita": "Dias sem Visita",
            })
            df_exib["Queda (%)"] = df_exib["Queda (%)"].apply(lambda x: f"{x:.0f}%")
            df_exib["Dias sem Visita"] = df_exib["Dias sem Visita"].apply(
                lambda x: f"{int(x)}" if pd.notna(x) else "-"
            )

            def destaque_vermelho(row):
                return ["background-color: #ffcccc; color: #8b0000"] * len(row)

            st.dataframe(
                df_exib[["Cliente", "Cidade", "Queda (%)", "Dias sem Visita"]].style.apply(destaque_vermelho, axis=1),
                width="stretch", height=400,
            )

    # ── Esquentando ──
    with tab_esquentando:
        st.subheader("Clientes Esquentando")
        st.caption("Clientes com crescimento de faturamento > 20%")
        df_aba = aplicar_filtros(df_esquentando) if aplicar_filtros and not df_esquentando.empty else df_esquentando
        if df_aba.empty:
            st.success("Nenhum cliente esquentando no período.")
        else:
            df_exib = df_aba.rename(columns={
                "cliente": "Cliente", "cidade": "Cidade",
                "variacao": "Crescimento (%)", "faturamento": "Faturamento",
            })
            df_exib["Crescimento (%)"] = df_exib["Crescimento (%)"].apply(lambda x: f"{x:.0f}%")
            df_exib["Faturamento"] = df_exib["Faturamento"].apply(
                lambda x: f"R$ {x:,.2f}" if pd.notna(x) and x > 0 else "R$ 0,00"
            )

            def destaque_verde(row):
                return ["background-color: #ccffcc; color: #006400"] * len(row)

            st.dataframe(
                df_exib[["Cliente", "Cidade", "Crescimento (%)", "Faturamento"]].style.apply(destaque_verde, axis=1),
                width="stretch", height=400,
            )

    # ── Sem Visita ──
    with tab_sem_visita_tab:
        st.subheader("Clientes Sem Visita")
        df_aba = aplicar_filtros(df_sem_visita) if aplicar_filtros and not df_sem_visita.empty else df_sem_visita
        qtd_nunca = len(df_aba[df_aba["tipo"] == "NUNCA_VISITADO"]) if not df_aba.empty else 0
        qtd_atrasadas = len(df_aba[df_aba["tipo"] == "VISITA_ATRASADA"]) if not df_aba.empty else 0

        cv1, cv2 = st.columns(2)
        cv1.metric("Nunca Visitados", qtd_nunca)
        cv2.metric("Visitas Atrasadas (>90 dias)", qtd_atrasadas)

        if df_aba.empty:
            st.success("Nenhum cliente sem visita encontrado.")
        else:
            df_exib = df_aba.rename(columns={
                "cliente": "Cliente", "cidade": "Cidade",
                "dias_sem_visita": "Dias sem Visita", "tipo": "Tipo",
            })
            df_exib["Dias sem Visita"] = df_exib["Dias sem Visita"].apply(
                lambda x: "Nunca" if pd.isna(x) else str(int(x))
            )

            def destaque_nunca(row):
                if row["Tipo"] == "NUNCA_VISITADO":
                    return ["background-color: #ffeeba; color: #856404"] * len(row)
                return [""] * len(row)

            st.dataframe(
                df_exib.style.apply(destaque_nunca, axis=1),
                width="stretch", height=400,
            )

    # ── Sem Faturamento ──
    with tab_sem_faturamento_tab:
        st.subheader("Clientes Sem Faturamento (12 meses)")
        st.caption("Possuem máquinas Mitsubishi ou histórico de OS, mas não faturam há 12 meses")
        df_aba = aplicar_filtros(df_sem_faturamento) if aplicar_filtros and not df_sem_faturamento.empty else df_sem_faturamento
        if df_aba.empty:
            st.success("Nenhum cliente sem faturamento encontrado.")
        else:
            df_exib = df_aba.rename(columns={
                "cliente": "Cliente", "máquinas": "Máquinas",
                "última OS": "Última OS", "último faturamento": "Último Faturamento",
            })
            st.dataframe(df_exib, width="stretch", height=400)