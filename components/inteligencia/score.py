"""
Componente de Score Comercial.
Consome exclusivamente services/inteligencia_comercial.calcular_score_comercial.
Nenhum SQL é executado aqui.
"""

import streamlit as st
import pandas as pd

from services.inteligencia_comercial import calcular_score_comercial, PENALIDADE_RELACIONAMENTO_ATIVO


def exibir_score(unidade_param=None):
    """
    Renderiza o Top 20 Score Comercial com Grid + Detalhes.
    """
    st.subheader("🏆 Score Comercial — Top 20")
    st.caption("Fila de trabalho — prioriza potencial de negócio, não apenas queda.")

    df_score = calcular_score_comercial(unidade=unidade_param)

    if df_score.empty:
        st.success("Nenhuma prioridade comercial no momento.")
        return

    df_ranking = df_score.head(20).copy()
    df_ranking["#"] = range(1, len(df_ranking) + 1)
    df_ranking["Cliente"] = df_ranking["cliente"]
    df_ranking["Classe"] = df_ranking["classe_abc"]
    df_ranking["Score"] = df_ranking["score"].apply(lambda x: f"{x:.0f}")
    df_ranking["Máquinas"] = df_ranking["qtd_maquinas"].apply(
        lambda x: f"{int(x)}" if pd.notna(x) else "0"
    )
    df_ranking["Faturamento 12m"] = df_ranking["fat_12m"].apply(
        lambda x: f"R$ {x:,.0f}" if pd.notna(x) and x > 0 else "R$ 0"
    )
    df_ranking["Sem Contato"] = df_ranking["dias_sem_contato"].apply(
        lambda x: f"{int(x)}d" if pd.notna(x) and x < 9999 else "-"
    )
    df_ranking["Sem Visita"] = df_ranking["dias_sem_visita"].apply(
        lambda x: f"{int(x)}d" if pd.notna(x) and x < 9999 else "-"
    )
    df_ranking["Motivo"] = df_ranking["motivo_prioridade"]
    df_ranking["Ação"] = df_ranking["proxima_acao"]

    tab_grid, tab_detalhado = st.tabs(["Grid", "Detalhes"])

    with tab_grid:
        colunas_grid = [
            "#", "Cliente", "Classe", "Score", "Máquinas",
            "Faturamento 12m", "Sem Contato", "Sem Visita",
            "Motivo", "Ação"
        ]
        df_grid = df_ranking[colunas_grid].copy()

        def colorir_ranking(row):
            cores = []
            for col in row.index:
                if col == "Score":
                    val = float(row[col])
                    if val >= 80:
                        cores.append("background-color: #16a34a; color: white; font-weight: bold")
                    elif val >= 60:
                        cores.append("background-color: #2563eb; color: white; font-weight: bold")
                    elif val >= 40:
                        cores.append("background-color: #f59e0b; color: black; font-weight: bold")
                    elif val >= 20:
                        cores.append("background-color: #dc2626; color: white; font-weight: bold")
                    else:
                        cores.append("background-color: #e5e7eb; color: #666; font-weight: bold")
                elif col == "Classe":
                    cl = row[col]
                    if cl == "A":
                        cores.append("background-color: #16a34a; color: white; font-weight: bold")
                    elif cl == "B":
                        cores.append("background-color: #2563eb; color: white; font-weight: bold")
                    elif cl == "C":
                        cores.append("background-color: #f59e0b; color: black; font-weight: bold")
                    elif cl == "D":
                        cores.append("background-color: #dc2626; color: white; font-weight: bold")
                    else:
                        cores.append("")
                else:
                    cores.append("")
            return cores

        st.dataframe(
            df_grid.style.apply(colorir_ranking, axis=1),
            width="stretch",
            height=600,
            column_config={
                "Score": st.column_config.NumberColumn("Score", help="0-100. Quanto maior, mais prioritário.", format="%d"),
                "Motivo": st.column_config.TextColumn("Motivo", help="Por que o cliente está na lista", width="large"),
                "Ação": st.column_config.TextColumn("Ação", help="Próxima ação recomendada", width="medium"),
            }
        )
        st.caption(
            "Ordenado por Score (maior primeiro). "
            f"Clientes com relacionamento ativo recebem -{PENALIDADE_RELACIONAMENTO_ATIVO}pts."
        )

    with tab_detalhado:
        st.markdown("### Detalhes por Cliente — Top 20")
        for _, row in df_ranking.iterrows():
            classe = row["Classe"]
            maq = int(row["qtd_maquinas"]) if pd.notna(row["qtd_maquinas"]) else 0
            fat = row["fat_12m"] if pd.notna(row["fat_12m"]) else 0
            dias_contato = int(row["dias_sem_contato"]) if pd.notna(row["dias_sem_contato"]) else 0
            dias_visita = int(row["dias_sem_visita"]) if pd.notna(row["dias_sem_visita"]) else 0
            score = row["score"]
            motivo = row["motivo_prioridade"]
            acao = row["proxima_acao"]
            explicacao = row.get("explicacao_score", "")
            ranking_pos = int(row["#"])

            icone_score = "🏆" if score >= 80 else "⭐" if score >= 60 else "🔹" if score >= 40 else "📌" if score >= 20 else "📋"

            with st.expander(
                f"#{ranking_pos} {icone_score} {row['cliente']}  \n"
                f"Classe {classe} | Score: {score:.0f} | {maq} máquinas | R$ {fat:,.0f}",
                expanded=False
            ):
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.markdown(f"**Cliente:** {row['cliente']}")
                    st.markdown(f"**Classe ABCD:** {classe}")
                    st.markdown(f"**Máquinas Mitsubishi:** {maq}")
                    st.markdown(f"**Faturamento 12m:** R$ {fat:,.0f}")
                    st.markdown(f"**Sem contato:** {dias_contato}d")
                    st.markdown(f"**Sem visita:** {dias_visita}d")
                    st.markdown(f"**Queda faturamento:** {row['queda_fat_pct']:.0f}%")
                    st.markdown(f"**Preventiva:** {'Vencida' if row['dias_sem_manutencao'] >= 730 else 'Em dia'}")
                with col2:
                    st.markdown(f"### Score: **{score:.0f}**")
                    st.markdown("#### Cálculo do Score")
                    explicacao_limpa = explicacao.replace("\n", "  \n")
                    st.markdown(f"```\n{explicacao_limpa}\n```")
                st.markdown("---")
                st.markdown(f"**Motivo:** {motivo}")
                st.markdown(f"**Ação sugerida:** {acao}")

        st.caption("Expanda cada card para ver detalhes completos.")