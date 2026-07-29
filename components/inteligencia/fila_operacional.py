"""
Componente da Fila Operacional — "O QUE FAZER HOJE".
Consome services/inteligencia_comercial e database.get_connection.
Nenhum service novo é criado. SQL apenas onde não há service correspondente.
"""

from datetime import date
import pandas as pd
import streamlit as st

from database import get_connection
from services.inteligencia_comercial import (
    get_clientes_esfriando,
    get_clientes_sem_visita,
)


def exibir_fila_operacional(unidade_param=None):
    """
    Renderiza a fila operacional priorizada da Central de Oportunidades.
    Ordem: pendências vencidas > pendências hoje > follow-ups vencidos >
           follow-ups hoje > OS aguardando > clientes esfriando > clientes sem visita.

    Parâmetros:
        unidade_param: str or None — filtro de unidade
    """
    st.markdown("## 📋 O QUE FAZER HOJE")
    st.caption(
        "Fila operacional priorizada: pendências vencidas > pendências hoje > "
        "follow-ups vencidos > follow-ups hoje > OS aguardando > "
        "clientes esfriando > clientes sem visita."
    )

    hoje_str = date.today().strftime("%Y-%m-%d")
    conn_fila = get_connection()
    lista_prioridades = []
    prox_acao_sugerida = {
        "PENDENCIA_VENCIDA": "Atender pendência vencida imediatamente",
        "PENDENCIA_HOJE": "Atender pendência com vencimento hoje",
        "FOLLOWUP_VENCIDO": "Realizar follow-up imediato com cliente",
        "FOLLOWUP_HOJE": "Realizar follow-up agendado para hoje",
        "OS_APROVACAO": "Contatar cliente para aprovação da proposta",
        "ESFRIANDO": "Agendar visita ou contato comercial",
        "SEM_VISITA": "Agendar visita presencial",
    }

    # 1. Pendências Vencidas (data_limite < hoje)
    df_pend_vencidas = pd.read_sql_query(
        """SELECT p.id, c.razao_social AS cliente, p.responsavel,
                  p.descricao, p.data_limite, p.prioridade,
                  CAST(julianday('now') - julianday(p.data_limite) AS INTEGER) AS dias_atraso
           FROM pendencias_comerciais p
           LEFT JOIN clientes c ON p.cliente_id = c.id
           WHERE p.status = 'ABERTA'
             AND p.data_limite < date('now')
           ORDER BY p.data_limite ASC""",
        conn_fila,
    )
    if not df_pend_vencidas.empty:
        for _, row in df_pend_vencidas.iterrows():
            dias = int(row["dias_atraso"]) if pd.notna(row["dias_atraso"]) else 0
            lista_prioridades.append({
                "prioridade": 1,
                "tipo": "🔴 PENDÊNCIA VENCIDA",
                "cliente": row["cliente"],
                "os": "-",
                "motivo": f"{row['descricao']} — {dias} dia(s) atrasada",
                "dias": f"{dias}d",
                "responsavel": row.get("responsavel", "-"),
                "prox_acao": prox_acao_sugerida["PENDENCIA_VENCIDA"],
                "vencimento": str(row["data_limite"])[:10] if pd.notna(row["data_limite"]) else "-",
            })

    # 2. Pendências para Hoje (data_limite == hoje)
    df_pend_hoje = pd.read_sql_query(
        """SELECT p.id, c.razao_social AS cliente, p.responsavel,
                  p.descricao, p.data_limite, p.prioridade
           FROM pendencias_comerciais p
           LEFT JOIN clientes c ON p.cliente_id = c.id
           WHERE p.status = 'ABERTA'
             AND p.data_limite = date('now')
           ORDER BY p.prioridade ASC""",
        conn_fila,
    )
    if not df_pend_hoje.empty:
        for _, row in df_pend_hoje.iterrows():
            lista_prioridades.append({
                "prioridade": 2,
                "tipo": "🟠 PENDÊNCIA HOJE",
                "cliente": row["cliente"],
                "os": "-",
                "motivo": f"{row['descricao']} — vence hoje",
                "dias": "0d",
                "responsavel": row.get("responsavel", "-"),
                "prox_acao": prox_acao_sugerida["PENDENCIA_HOJE"],
                "vencimento": hoje_str,
            })

    # 3. Follow-ups Vencidos (OS com proximo_followup < hoje)
    df_fu_vencidos = pd.read_sql_query(
        """SELECT os.numero_os, c.razao_social AS cliente, os.responsavel,
                  os.proximo_followup, os.valor_proposta,
                  CAST(julianday('now') - julianday(os.proximo_followup) AS INTEGER) AS dias_atraso
           FROM ordens_servico os
           LEFT JOIN clientes c ON os.cliente_id = c.id
           WHERE os.status IN ('PROPOSTA ENVIADA', 'FOLLOW-UP')
             AND os.proximo_followup IS NOT NULL
             AND os.proximo_followup < date('now')
           ORDER BY os.proximo_followup ASC""",
        conn_fila,
    )
    if not df_fu_vencidos.empty:
        for _, row in df_fu_vencidos.iterrows():
            dias = int(row["dias_atraso"]) if pd.notna(row["dias_atraso"]) else 0
            lista_prioridades.append({
                "prioridade": 3,
                "tipo": "🔴 FOLLOW-UP VENCIDO",
                "cliente": row["cliente"],
                "os": str(row["numero_os"]) if pd.notna(row["numero_os"]) else "-",
                "motivo": f"{dias} dia(s) de atraso",
                "dias": f"{dias}d",
                "responsavel": row.get("responsavel", "-"),
                "prox_acao": prox_acao_sugerida["FOLLOWUP_VENCIDO"],
                "vencimento": str(row["proximo_followup"])[:10] if pd.notna(row["proximo_followup"]) else "-",
            })

    # 4. Follow-ups de Hoje
    df_fu_hoje = pd.read_sql_query(
        """SELECT os.numero_os, c.razao_social AS cliente, os.responsavel,
                  os.proximo_followup, os.valor_proposta
           FROM ordens_servico os
           LEFT JOIN clientes c ON os.cliente_id = c.id
           WHERE os.status IN ('PROPOSTA ENVIADA', 'FOLLOW-UP')
             AND os.proximo_followup = date('now')
           ORDER BY os.responsavel""",
        conn_fila,
    )
    if not df_fu_hoje.empty:
        for _, row in df_fu_hoje.iterrows():
            lista_prioridades.append({
                "prioridade": 4,
                "tipo": "🟡 FOLLOW-UP HOJE",
                "cliente": row["cliente"],
                "os": str(row["numero_os"]) if pd.notna(row["numero_os"]) else "-",
                "motivo": "Follow-up agendado para hoje",
                "dias": "0d",
                "responsavel": row.get("responsavel", "-"),
                "prox_acao": prox_acao_sugerida["FOLLOWUP_HOJE"],
                "vencimento": hoje_str,
            })

    # 5. OS Aguardando Aprovação (via SQL inline — sem service correspondente)
    query_os_aprovacao = """
    SELECT
        c.razao_social AS cliente,
        os.valor_proposta AS valor,
        CAST(julianday('now') - julianday(os.data_recebimento) AS INTEGER) AS dias_aguardando,
        os.responsavel,
        os.status
    FROM ordens_servico os
    INNER JOIN clientes c ON os.cliente_id = c.id
    WHERE os.status IN ('AGUARDANDO', 'ORCAMENTO', 'APROVACAO')
    """
    params_os_aprov = []
    if unidade_param:
        query_os_aprovacao += " AND os.unidade = ?"
        params_os_aprov.append(unidade_param)
    query_os_aprovacao += " ORDER BY dias_aguardando DESC"
    df_os_aprovacao = pd.read_sql_query(query_os_aprovacao, conn_fila, params=params_os_aprov)

    for _, row in df_os_aprovacao.iterrows():
        dias = int(row["dias_aguardando"]) if pd.notna(row["dias_aguardando"]) else 0
        if dias >= 7:
            badge = "⏳ OS AGUARDANDO" if dias < 15 else "🔴 OS ATRASADA"
            prioridade = 5 if dias < 15 else 4
            lista_prioridades.append({
                "prioridade": prioridade,
                "tipo": badge,
                "cliente": row["cliente"],
                "os": "-",
                "motivo": f"Aguardando aprovação há {dias} dias",
                "dias": f"{dias}d",
                "responsavel": row.get("responsavel", "-"),
                "prox_acao": prox_acao_sugerida["OS_APROVACAO"],
                "vencimento": f"{dias} dias",
            })

    # 6. Clientes Esfriando
    df_esfriando = get_clientes_esfriando(unidade=unidade_param)
    if not df_esfriando.empty:
        for _, row in df_esfriando.iterrows():
            var = row["variacao"]
            if var < -50:
                lista_prioridades.append({
                    "prioridade": 6,
                    "tipo": "🔴 ESFRIANDO",
                    "cliente": row["cliente"],
                    "os": "-",
                    "motivo": f"Queda de faturamento: {var:.0f}%",
                    "dias": "-",
                    "responsavel": "-",
                    "prox_acao": prox_acao_sugerida["ESFRIANDO"],
                    "vencimento": "-",
                })

    # 7. Clientes Sem Visita
    df_sem_visita = get_clientes_sem_visita(unidade=unidade_param)
    if not df_sem_visita.empty:
        for _, row in df_sem_visita.iterrows():
            dias = row["dias_sem_visita"]
            if pd.notna(dias) and dias > 90:
                lista_prioridades.append({
                    "prioridade": 7,
                    "tipo": "📅 SEM VISITA",
                    "cliente": row["cliente"],
                    "os": "-",
                    "motivo": f"{int(dias)} dias sem visita",
                    "dias": f"{int(dias)}d",
                    "responsavel": "-",
                    "prox_acao": prox_acao_sugerida["SEM_VISITA"],
                    "vencimento": f"{int(dias)}d atrás",
                })

    conn_fila.close()

    # Renderizar tabela
    if lista_prioridades:
        df_hoje = pd.DataFrame(lista_prioridades)
        df_hoje = df_hoje.sort_values("prioridade").reset_index(drop=True)

        def colorir_fila(row):
            if "Prioridade" not in row.index:
                return [""] * len(row)
            val = str(row["Prioridade"])
            if "VENCIDA" in val or "VENCIDO" in val or "ATRASADA" in val:
                return ["background-color: #fce4ec; color: #c62828"] * len(row)
            elif "HOJE" in val:
                return ["background-color: #fff3cd; color: #856404"] * len(row)
            elif "ESFRIANDO" in val:
                return ["background-color: #ffebee; color: #b71c1c"] * len(row)
            elif "AGUARDANDO" in val:
                return ["background-color: #e3f2fd; color: #1565c0"] * len(row)
            elif "SEM VISITA" in val:
                return ["background-color: #f3e5f5; color: #6a1b9a"] * len(row)
            return [""] * len(row)

        colunas_exib = ["tipo", "cliente", "os", "motivo", "dias", "prox_acao"]
        rename_map = {
            "tipo": "Prioridade",
            "cliente": "Cliente",
            "os": "OS",
            "motivo": "Motivo",
            "dias": "Dias",
            "prox_acao": "Próxima Ação Sugerida",
        }
        df_exib_hoje = df_hoje[colunas_exib].rename(columns=rename_map)

        st.dataframe(
            df_exib_hoje.style.apply(colorir_fila, axis=1),
            width="stretch",
            height=min(500, 35 * len(df_exib_hoje) + 40),
        )
        st.caption(
            "Ordem: 🔴 Pendência Vencida > 🟠 Pendência Hoje > 🔴 Follow-up Vencido > "
            "🟡 Follow-up Hoje > 🔴 OS Atrasada > ⏳ OS Aguardando > "
            "🔴 Esfriando > 📅 Sem Visita."
        )
    else:
        st.success("Nenhuma ação urgente no momento.")