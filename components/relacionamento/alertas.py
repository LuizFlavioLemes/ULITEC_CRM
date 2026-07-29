"""
Componente da Aba 6 (atual) — 🔔 Alertas de Relacionamento

Exibe alertas automáticos baseados nas regras configuradas na Administração.

Responsabilidades:
- Gerar e exibir alertas de visita próxima do vencimento
- Gerar e exibir alertas de pendências vencidas
- Exibir observação sobre fluxo operacional (Sprint 1.5)
"""

import streamlit as st

from services.relacionamento import get_alertas_relacionamento


def exibir_alertas():
    """Renderiza a aba de Alertas de Relacionamento."""
    st.subheader("🔔 Alertas de Relacionamento")
    st.markdown(
        "Alertas automáticos baseados nas regras configuradas na "
        "Administração (frequência por classe, alertas de visita/contato). "
        "Alertas operacionais de proposta/orçamento são gerenciados no Pipeline OS."
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