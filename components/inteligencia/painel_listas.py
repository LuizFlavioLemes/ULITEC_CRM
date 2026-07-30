"""
Componente de Painel de Listas — Inteligência Comercial.

Blocos 2-9: Listas especializadas de clientes.

Consome exclusivamente services do módulo inteligencia.
Zero SQL. Zero regra de negócio.

Reutiliza:
- components/common/ → section, panel, empty_state, loading_wrapper
- services/inteligencia_comercial/ → todos os get_*
- services/inteligencia/prioridade.py → get_clientes_prioritarios
"""

from typing import Optional, List
import streamlit as st
import pandas as pd

from components.common import section, panel, empty_state, loading_wrapper
from services.inteligencia_comercial import (
    get_clientes_esfriando,
    get_clientes_esquentando,
    get_clientes_sem_visita,
    get_clientes_sem_faturamento,
    get_clientes_parque_relevante,
    get_preventivas_vencidas,
    get_prospeccao_mitsubishi,
    get_top_faturamento_12m,
)
from services.inteligencia.prioridade import (
    get_clientes_prioritarios,
)


def _format_moeda(valor) -> str:
    """Formata valor monetário."""
    try:
        v = float(valor)
        if v >= 1_000_000:
            return f"R$ {v/1_000_000:.2f}M"
        elif v >= 1_000:
            return f"R$ {v:,.0f}"
        return f"R$ {v:,.2f}"
    except (ValueError, TypeError):
        return "R$ 0"


def _format_dias(valor) -> str:
    """Formata dias."""
    try:
        d = int(valor)
        if d >= 9999:
            return "Nunca"
        return f"{d}d"
    except (ValueError, TypeError):
        return "-"


def _render_estrelas(estrelas: int) -> str:
    """Renderiza estrelas como texto."""
    return "★" * estrelas + "☆" * (5 - estrelas)


def _exibir_lista_generica(
    df: pd.DataFrame,
    titulo: str,
    icone: str,
    colunas: dict,
    empty_msg: str,
    ajuda: str = "",
):
    """
    Exibe uma lista genérica de clientes com formato padronizado.
    """
    section(titulo, icone)

    if df.empty:
        empty_state(empty_msg)
        return

    if ajuda:
        st.caption(ajuda)

    colunas_exibir = list(colunas.keys())
    df_display = df[colunas_exibir].copy()
    df_display = df_display.rename(columns=colunas)

    st.dataframe(
        df_display,
        use_container_width=True,
        height=min(400, 35 * len(df_display) + 40),
    )


def exibir_prioritarios(
    unidade: Optional[str] = None,
    estado: Optional[str] = None,
    cidade: Optional[str] = None,
    classe_abc: Optional[str] = None,
):
    """
    Bloco 2: Clientes Prioritários ordenados por score.
    """
    df = get_clientes_prioritarios(
        unidade=unidade,
        estado=estado,
        cidade=cidade,
        classe_abc=classe_abc,
    )

    section("🎯 Clientes Prioritários", "Ordenado por prioridade comercial")

    if df.empty:
        empty_state("Nenhum cliente prioritário encontrado com os filtros atuais.")
        return

    # Top 50
    df = df.head(50).copy()

    # Formatar colunas
    df["Estrelas"] = df["estrelas"].apply(_render_estrelas)
    df["Faturamento 12m"] = df["fat_12m"].apply(_format_moeda)
    df["Máquinas"] = df["qtd_maquinas"].apply(lambda x: f"{int(x)}" if pd.notna(x) else "0")
    df["Sem Visita"] = df["dias_sem_visita"].apply(_format_dias)
    df["Score"] = df["score"].apply(lambda x: f"{x:.1f}")

    colunas = ["cliente", "cidade", "Score", "Estrelas", "Faturamento 12m", "Máquinas", "Sem Visita", "motivos_str"]
    colunas_rename = {
        "cliente": "Cliente",
        "cidade": "Cidade",
        "Score": "Score",
        "Estrelas": "Prioridade",
        "Faturamento 12m": "Faturamento 12m",
        "Máquinas": "Máq.",
        "Sem Visita": "Sem Visita",
        "motivos_str": "Motivos",
    }

    df_display = df[colunas].copy()
    df_display = df_display.rename(columns=colunas_rename)

    st.dataframe(
        df_display,
        use_container_width=True,
        height=500,
        column_config={
            "Score": st.column_config.NumberColumn("Score", help="Score comercial 0-100", format="%.1f"),
            "Faturamento 12m": st.column_config.TextColumn("Faturamento 12m", help="Faturamento últimos 12 meses"),
            "Motivos": st.column_config.TextColumn("Motivos", help="Razões da prioridade", width="large"),
        }
    )

    st.caption(f"Exibindo {len(df)} clientes prioritários. Clique nos cards do Resumo Executivo para filtrar.")

    # Expandir detalhes
    with st.expander("📋 Ver detalhes por cliente", expanded=False):
        for _, row in df.iterrows():
            estrelas = _render_estrelas(row.get("estrelas", 1))
            with st.container():
                st.markdown(f"**{row['cliente']}** — {estrelas} (Score: {row['score']:.1f})")
                st.markdown(f"📍 {row.get('cidade', '-')} | 🏷️ {row.get('classe_abc', '-')} | 💰 {_format_moeda(row.get('fat_12m', 0))}")
                st.markdown(f"🔧 {int(row.get('qtd_maquinas', 0))} máq. Mitsubishi | 👁️ {_format_dias(row.get('dias_sem_visita', 9999))} sem visita")
                st.markdown(f"📋 Motivos: {row.get('motivos_str', '-')}")
                st.markdown(f"**Próxima ação:** {row.get('proxima_acao', '-')}")
                st.markdown("---")


def exibir_esfriando(unidade: Optional[str] = None, estado: Optional[str] = None, cidade: Optional[str] = None):
    """
    Bloco 3: Clientes Esfriando.
    """
    df = get_clientes_esfriando(unidade)

    if estado and estado != "Todos":
        df = df[df["estado"] == estado].copy()
    if cidade and cidade != "Todas":
        df = df[df["cidade"] == cidade].copy()

    section("🥶 Clientes Esfriando", "Queda de desempenho")

    if df.empty:
        empty_state("Nenhum cliente esfriando no momento.")
        return

    # Formatação
    df["variação"] = df["variacao"].apply(lambda x: f"{x:.1f}%")
    df["fat_atual_fmt"] = df["faturamento_periodo_atual"].apply(_format_moeda)
    df["fat_anterior_fmt"] = df["faturamento_periodo_anterior"].apply(_format_moeda)
    df["dias"] = df["dias_sem_visita"].apply(_format_dias)

    colunas = ["cliente", "cidade", "fat_anterior_fmt", "fat_atual_fmt", "variação", "dias"]
    colunas_rename = {
        "cliente": "Cliente",
        "cidade": "Cidade",
        "fat_anterior_fmt": "Faturamento Anterior",
        "fat_atual_fmt": "Faturamento Atual",
        "variação": "Variação",
        "dias": "Sem Visita",
    }

    df_display = df[colunas].copy().rename(columns=colunas_rename)

    st.dataframe(
        df_display,
        use_container_width=True,
        height=400,
    )

    st.caption("Critério: queda de faturamento >30%, queda de OS >30% ou sem visita >120 dias")


def exibir_esquentando(unidade: Optional[str] = None, estado: Optional[str] = None, cidade: Optional[str] = None):
    """
    Bloco 4: Clientes Esquentando.
    """
    df = get_clientes_esquentando(unidade)

    if estado and estado != "Todos":
        df = df[df["estado"] == estado].copy()
    if cidade and cidade != "Todas":
        df = df[df["cidade"] == cidade].copy()

    section("🔥 Clientes Esquentando", "Crescimento de desempenho")

    if df.empty:
        empty_state("Nenhum cliente esquentando no momento.")
        return

    df["variação"] = df["variacao"].apply(lambda x: f"+{x:.1f}%")
    df["faturamento_fmt"] = df["faturamento"].apply(_format_moeda)

    colunas = ["cliente", "cidade", "variação", "faturamento_fmt"]
    colunas_rename = {
        "cliente": "Cliente",
        "cidade": "Cidade",
        "variação": "Crescimento",
        "faturamento_fmt": "Faturamento",
    }

    df_display = df[colunas].copy().rename(columns=colunas_rename)

    st.dataframe(
        df_display,
        use_container_width=True,
        height=400,
    )

    st.caption("Critério: crescimento de faturamento >20% ou OS >20% no período")


def exibir_sem_faturamento(unidade: Optional[str] = None, estado: Optional[str] = None, cidade: Optional[str] = None):
    """
    Bloco 5: Sem Faturamento.
    """
    df = get_clientes_sem_faturamento(unidade)

    section("🚫 Sem Faturamento", "Clientes que não faturam há 12+ meses")

    if df.empty:
        empty_state("Nenhum cliente sem faturamento.")
        return

    st.dataframe(
        df,
        use_container_width=True,
        height=400,
    )

    st.caption("Clientes ativos sem faturamento nos últimos 12 meses, mas com máquinas Mitsubishi ou histórico de OS")


def exibir_sem_visita(unidade: Optional[str] = None, estado: Optional[str] = None, cidade: Optional[str] = None):
    """
    Bloco 6: Sem Visita.
    """
    df = get_clientes_sem_visita(unidade)

    section("👁️ Sem Visita", "Clientes com visita atrasada")

    if df.empty:
        empty_state("Nenhum cliente sem visita.")
        return

    if estado and estado != "Todos":
        df = df[df["estado"] == estado].copy()
    if cidade and cidade != "Todas":
        df = df[df["cidade"] == cidade].copy()

    df["tipo_icone"] = df["tipo"].apply(
        lambda t: "🆕" if t == "NUNCA_VISITADO" else "⚠️"
    )
    df["dias_fmt"] = df["dias_sem_visita"].apply(
        lambda x: f"{int(x)}d" if pd.notna(x) else "Nunca"
    )

    colunas = ["cliente", "cidade", "dias_fmt", "tipo_icone"]
    colunas_rename = {
        "cliente": "Cliente",
        "cidade": "Cidade",
        "dias_fmt": "Dias sem Visita",
        "tipo_icone": "Tipo",
    }

    df_display = df[colunas].copy().rename(columns=colunas_rename)

    st.dataframe(
        df_display,
        use_container_width=True,
        height=400,
    )

    st.caption("Clientes nunca visitados ou com última visita há mais de 90 dias.")


def exibir_preventivas(unidade: Optional[str] = None, estado: Optional[str] = None, cidade: Optional[str] = None):
    """
    Bloco 7: Oportunidades de Preventiva.
    """
    df = get_preventivas_vencidas(unidade)

    section("🛡️ Oportunidades de Preventiva", "Clientes com preventiva vencida")

    if df.empty:
        empty_state("Nenhum cliente com preventiva vencida.")
        return

    if estado and estado != "Todos":
        df = df[df["estado"] == estado].copy()
    if cidade and cidade != "Todas":
        df = df[df["cidade"] == cidade].copy()

    df["dias_sem_manutencao_fmt"] = df["dias_sem_manutencao"].apply(
        lambda x: f"{int(x)}d ({(int(x)/30):.0f} meses)" if pd.notna(x) else "-"
    )

    colunas = ["razao_social", "cidade", "dias_sem_manutencao_fmt"]
    colunas_rename = {
        "razao_social": "Cliente",
        "cidade": "Cidade",
        "dias_sem_manutencao_fmt": "Sem Preventiva",
    }

    df_display = df[colunas].copy().rename(columns=colunas_rename)

    st.dataframe(
        df_display,
        use_container_width=True,
        height=400,
    )

    st.caption("Critério: última OS faturada/expedida há mais de 2 anos. Oportunidade de venda de preventiva.")


def exibir_parque_mitsubishi(unidade: Optional[str] = None, estado: Optional[str] = None, cidade: Optional[str] = None):
    """
    Bloco 8: Parque Mitsubishi.
    """
    df_prospeccao = get_prospeccao_mitsubishi(unidade)
    df_parque = get_clientes_parque_relevante(unidade)

    section("🏭 Parque Mitsubishi", "Clientes com maior potencial Mitsubishi")

    # Seção 1: Prospecção (tem máquinas mas nunca teve OS)
    if not df_prospeccao.empty:
        if estado and estado != "Todos":
            df_prospeccao = df_prospeccao[df_prospeccao["estado"] == estado].copy()
        if cidade and cidade != "Todas":
            df_prospeccao = df_prospeccao[df_prospeccao["cidade"] == cidade].copy()

        st.markdown("#### 📡 Potencial de Prospecção")
        st.caption("Empresas com máquinas Mitsubishi que NUNCA tiveram OS na unidade")

        df_prospeccao["qtd_mitsubishi"] = df_prospeccao["qtd_mitsubishi"].apply(lambda x: f"{int(x)} máq.")

        colunas = ["razao_social", "cidade", "qtd_mitsubishi", "potencial"]
        colunas_rename = {
            "razao_social": "Empresa",
            "cidade": "Cidade",
            "qtd_mitsubishi": "Máquinas Mitsubishi",
            "potencial": "Potencial",
        }

        df_display = df_prospeccao[colunas].copy().rename(columns=colunas_rename)
        st.dataframe(df_display, use_container_width=True, height=300)
        st.markdown("---")

    # Seção 2: Maior parque
    if not df_parque.empty:
        if estado and estado != "Todos":
            df_parque = df_parque[df_parque["estado"] == estado].copy() if "estado" in df_parque.columns else df_parque
        if cidade and cidade != "Todas":
            df_parque = df_parque[df_parque["cidade"] == cidade].copy() if "cidade" in df_parque.columns else df_parque

        st.markdown("#### 🏆 Top Parque Mitsubishi")
        st.caption("Clientes com mais máquinas Mitsubishi")

        df_parque["quantidade_maquinas_fmt"] = df_parque["quantidade_maquinas"].apply(
            lambda x: f"{int(x)} máq."
        )

        colunas = ["cliente", "quantidade_maquinas_fmt"]
        colunas_rename = {
            "cliente": "Cliente",
            "quantidade_maquinas_fmt": "Máquinas",
        }

        df_display = df_parque[colunas].copy().rename(columns=colunas_rename)
        st.dataframe(df_display, use_container_width=True, height=300)

    if df_prospeccao.empty and df_parque.empty:
        empty_state("Nenhum cliente com parque Mitsubishi encontrado.")


def exibir_top_faturamento(unidade: Optional[str] = None, estado: Optional[str] = None, cidade: Optional[str] = None):
    """
    Bloco 9: Top Faturamento.
    """
    df = get_top_faturamento_12m(unidade, limite=20)

    section("💰 Top Faturamento", "Top 20 clientes por faturamento nos últimos 12 meses")

    if df.empty:
        empty_state("Dados de faturamento não disponíveis.")
        return

    if estado and estado != "Todos" and "estado" in df.columns:
        df = df[df["estado"] == estado].copy()
    if cidade and cidade != "Todas" and "cidade" in df.columns:
        df = df[df["cidade"] == cidade].copy()

    df["faturamento_12m_fmt"] = df["faturamento_12m"].apply(_format_moeda)
    df["participacao_fmt"] = df["participacao"].apply(lambda x: f"{x:.1f}%")
    df["#"] = range(1, len(df) + 1)

    colunas = ["#", "cliente", "faturamento_12m_fmt", "participacao_fmt"]
    colunas_rename = {
        "cliente": "Cliente",
        "faturamento_12m_fmt": "Faturamento 12m",
        "participacao_fmt": "Participação",
    }

    df_display = df[colunas].copy().rename(columns=colunas_rename)

    st.dataframe(
        df_display,
        use_container_width=True,
        height=500,
        column_config={
            "#": st.column_config.NumberColumn("#", help="Posição", width="small"),
        }
    )

    # Total
    total = df["faturamento_12m"].sum()
    st.caption(f"Faturamento total top 20: {_format_moeda(total)}")