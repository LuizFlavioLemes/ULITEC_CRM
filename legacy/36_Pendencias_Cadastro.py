import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

from auth import verificar_acesso, sidebar_usuario
from services import formatar_clientes_para_select

# ── Proteção: MASTER ou ADMIN ──
verificar_acesso(perfis=["MASTER", "GESTOR"])
sidebar_usuario()

st.title("📋 Pendências de Cadastro")
st.markdown("Clientes criados automaticamente durante importações que precisam ter o cadastro completado.")

# ── Conexão BD ──
conn = sqlite3.connect("crm.db")

# ── Filtros ──
col1, col2 = st.columns(2)
with col1:
    filtro_status = st.selectbox(
        "Status",
        ["PROVISORIO", "ATIVO", "TODOS"],
        index=0
    )
with col2:
    filtro_origem = st.selectbox(
        "Origem do Cadastro",
        ["IMPORTACAO_FATURAMENTO", "TODOS"],
        index=0
    )

# ── Montar query ──
where_clauses = []
params = []

if filtro_status != "TODOS":
    where_clauses.append("c.status = ?")
    params.append(filtro_status)

if filtro_origem != "TODOS":
    where_clauses.append("c.origem_cadastro = ?")
    params.append(filtro_origem)

where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

# ── Buscar dados ──
query = f"""
    SELECT
        c.id,
        c.codigo_erp,
        c.razao_social,
        c.cnpj,
        c.cidade,
        c.estado,
        c.status,
        c.origem_cadastro,
        c.data_cadastro,
        c.ultima_importacao,
        COALESCE(f.qtd_faturamentos, 0) AS qtd_faturamentos,
        COALESCE(f.total_faturamento, 0) AS total_faturamento
    FROM clientes c
    LEFT JOIN (
        SELECT
            cliente_id,
            COUNT(*) AS qtd_faturamentos,
            ROUND(SUM(valor), 2) AS total_faturamento
        FROM faturamento
        GROUP BY cliente_id
    ) f ON f.cliente_id = c.id
    WHERE {where_sql}
    ORDER BY c.data_cadastro DESC
"""

df = pd.read_sql_query(query, conn, params=params)

# ── Exibir ──
st.metric("Total de clientes pendentes", len(df))

if len(df) > 0:
    # Formatando colunas
    df_display = df.copy()
    df_display["total_faturamento"] = df_display["total_faturamento"].apply(
        lambda x: f"R$ {x:,.2f}"
    )
    df_display["data_cadastro"] = pd.to_datetime(df_display["data_cadastro"]).dt.date

    colunas_exibir = [
        "codigo_erp", "razao_social", "status", "origem_cadastro",
        "data_cadastro", "qtd_faturamentos", "total_faturamento"
    ]

    st.dataframe(
        df_display[colunas_exibir],
        width="stretch",
        column_config={
            "codigo_erp": "Código ERP",
            "razao_social": "Razão Social",
            "status": "Status",
            "origem_cadastro": "Origem",
            "data_cadastro": "Data Cadastro",
            "qtd_faturamentos": "Qtd. Faturamentos",
            "total_faturamento": "Faturamento Total",
        }
    )

    st.divider()

    # ── Ação: Completar cadastro ──
    st.subheader("✏️ Completar Cadastro")

    cliente_ids = df["id"].tolist()
    clientes_formatados, clientes_dict_map, _ = formatar_clientes_para_select(df)

    if clientes_formatados:
        cliente_selecionado = st.selectbox(
            "Selecione um cliente para editar",
            options=clientes_formatados
        )

        if cliente_selecionado:
            cliente_id = clientes_dict_map[cliente_selecionado]
            row = df[df["id"] == cliente_id].iloc[0]

            with st.form(key="form_completar_cadastro"):
                col1, col2 = st.columns(2)

                with col1:
                    novo_codigo = st.text_input(
                        "Código ERP",
                        value=str(row["codigo_erp"]) if row["codigo_erp"] else ""
                    )
                    nova_razao = st.text_input(
                        "Razão Social",
                        value=row["razao_social"] if row["razao_social"] else ""
                    )
                    novo_fantasia = st.text_input(
                        "Nome Fantasia",
                        value=""
                    )
                    novo_cnpj = st.text_input(
                        "CNPJ",
                        value=row["cnpj"] if row["cnpj"] else ""
                    )

                with col2:
                    novo_cidade = st.text_input(
                        "Cidade",
                        value=row["cidade"] if row["cidade"] else ""
                    )
                    novo_estado = st.text_input(
                        "Estado",
                        value=row["estado"] if row["estado"] else ""
                    )
                    novo_telefone = st.text_input(
                        "Telefone",
                        value=""
                    )
                    novo_email = st.text_input(
                        "E-mail",
                        value=""
                    )

                novo_segmento = st.selectbox(
                    "Segmento",
                    ["METALURGICO", "AUTOMOTIVO", "PLASTICO", "FERRAMENTARIA",
                     "ALIMENTICIO", "MEDICO", "OUTROS", ""],
                    index=0
                )

                col1, col2 = st.columns(2)
                with col1:
                    novo_tipo_conta = st.selectbox(
                        "Tipo de Conta",
                        ["LEAD FRIO", "LEAD QUENTE", "CLIENTE ATIVO",
                         "CLIENTE INATIVO", "EX- CLIENTE", "PROSPECCAO"],
                        index=2
                    )
                with col2:
                    novo_classe_abc = st.selectbox(
                        "Classe ABC",
                        ["A", "B", "C", "D"],
                        index=3
                    )

                submitted = st.form_submit_button("💾 Salvar Cadastro", type="primary")

                if submitted:
                    cursor = conn.cursor()
                    cursor.execute(
                        """
                        UPDATE clientes
                        SET
                            codigo_erp = ?,
                            razao_social = ?,
                            nome_fantasia = ?,
                            cnpj = ?,
                            cidade = ?,
                            estado = ?,
                            telefone = ?,
                            email = ?,
                            segmento = ?,
                            tipo_conta = ?,
                            classe_abc = ?,
                            status = 'ATIVO'
                        WHERE id = ?
                        """,
                        (
                            novo_codigo,
                            nova_razao,
                            novo_fantasia,
                            novo_cnpj,
                            novo_cidade,
                            novo_estado,
                            novo_telefone,
                            novo_email,
                            novo_segmento,
                            novo_tipo_conta,
                            novo_classe_abc,
                            cliente_id
                        )
                    )
                    conn.commit()
                    st.success(f"✅ Cliente {novo_codigo} atualizado com sucesso!")
                    st.rerun()

    st.divider()

    # ── Ação em massa ──
    st.subheader("⚡ Ações em Massa")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Ativar Todos os Pendentes", type="secondary", width="stretch"):
            cursor = conn.cursor()
            if filtro_origem != "TODOS":
                cursor.execute(
                    "UPDATE clientes SET status = 'ATIVO' WHERE status = 'PROVISORIO' AND origem_cadastro = ?",
                    (filtro_origem,)
                )
            else:
                cursor.execute(
                    "UPDATE clientes SET status = 'ATIVO' WHERE status = 'PROVISORIO'"
                )
            conn.commit()
            st.success(f"{cursor.rowcount} cliente(s) ativados!")
            st.rerun()

    with col2:
        if st.button("Excluir Selecionados", type="secondary", width="stretch"):
            st.warning("Selecione clientes individualmente para exclusão segura.")

else:
    st.info("✅ Nenhum cliente pendente encontrado. Todos os cadastros estão completos!")

conn.close()