import streamlit as st
import pandas as pd
import sqlite3

from auth import verificar_acesso, sidebar_usuario

# ── Proteção: MASTER ou GESTOR ──
verificar_acesso(perfis=["MASTER", "GESTOR"])
sidebar_usuario()

st.title("📥 Importação de Clientes ERP")

arquivo = st.file_uploader(
    "Selecione o relatório Relação Clientes",
    type=["xlsx"]
)

if arquivo:

    try:

        df = pd.read_excel(
            arquivo,
            sheet_name=0,
            header=None
        )

        st.subheader("Prévia")

        st.dataframe(
            df.head(20),
            width="stretch"
        )

        if st.button("IMPORTAR CLIENTES"):

            conn = sqlite3.connect("crm.db")
            cursor = conn.cursor()

            importados = 0
            atualizados = 0

            # dados começam após a linha do cabeçalho
            for i in range(8, len(df)):

                try:

                    codigo = df.iloc[i, 0]

                    # ignora linhas vazias
                    if pd.isna(codigo):
                        continue

                    # ignora linhas IE Principal
                    if not str(codigo).replace(".0", "").isdigit():
                        continue

                    codigo = str(int(float(codigo)))

                    razao_social = str(df.iloc[i, 2]).strip()

                    nome_fantasia = str(df.iloc[i, 4]).strip()

                    cidade = str(df.iloc[i, 6]).strip()

                    telefone = str(df.iloc[i, 7]).strip()

                    email = str(df.iloc[i, 10]).strip()

                    existe = pd.read_sql_query(
                        """
                        SELECT id
                        FROM clientes
                        WHERE codigo_erp = ?
                        """,
                        conn,
                        params=[codigo]
                    )

                    if len(existe) > 0:

                        cursor.execute(
                            """
                            UPDATE clientes
                            SET
                                razao_social=?,
                                nome_fantasia=?,
                                cidade=?,
                                telefone=?,
                                email=?
                            WHERE codigo_erp=?
                            """,
                            (
                                razao_social,
                                nome_fantasia,
                                cidade,
                                telefone,
                                email,
                                codigo
                            )
                        )

                        atualizados += 1

                    else:

                        cursor.execute(
                            """
                            INSERT INTO clientes
                            (
                                codigo_erp,
                                razao_social,
                                nome_fantasia,
                                cidade,
                                telefone,
                                email
                            )
                            VALUES
                            (?, ?, ?, ?, ?, ?)
                            """,
                            (
                                codigo,
                                razao_social,
                                nome_fantasia,
                                cidade,
                                telefone,
                                email
                            )
                        )

                        importados += 1

                except Exception:
                    continue

            conn.commit()
            conn.close()

            st.success(
                f"{importados} clientes importados."
            )

            st.success(
                f"{atualizados} clientes atualizados."
            )

    except Exception as erro:

        st.error(f"Erro: {erro}")