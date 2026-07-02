import streamlit as st
import pandas as pd
import sqlite3
import re
from datetime import datetime, date

from auth import verificar_acesso, sidebar_usuario

# ── Proteção: MASTER ou GESTOR ──
verificar_acesso(perfis=["MASTER", "GESTOR"])
sidebar_usuario()

st.title("💰 Importar Faturamento")

MESES = {
    "jan": 1, "fev": 2, "mar": 3, "abr": 4, "mai": 5, "jun": 6,
    "jul": 7, "ago": 8, "set": 9, "out": 10, "nov": 11, "dez": 12
}

# Padrão para detectar colunas mensais: Mês/Ano (ex: Jan/25, Jun/25, Dez/25)
PADRAO_MENSAL = re.compile(
    r"^(jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)\s*/\s*(\d{2,4})$",
    re.IGNORECASE
)


def parse_coluna_mensal(nome_coluna: str):
    """Converte 'Jun/25' -> date(2025, 6, 1). Retorna None se não for mês."""
    nome_limpo = str(nome_coluna).strip()
    m = PADRAO_MENSAL.match(nome_limpo)
    if not m:
        return None

    mes = MESES[m.group(1).lower()]
    ano_str = m.group(2)

    if len(ano_str) == 2:
        ano = 2000 + int(ano_str)
    else:
        ano = int(ano_str)

    return date(ano, mes, 1)


arquivo = st.file_uploader(
    "Selecione o relatório do Painel de Vendas",
    type=["xlsx"]
)

unidade = st.selectbox("Unidade", ["ULITEC SP", "ULITEC RS"])

if arquivo:

    df = pd.read_excel(arquivo)

    # ── Detectar colunas mensais ──
    colunas_mensais = []
    for col in df.columns:
        if parse_coluna_mensal(col) is not None:
            colunas_mensais.append(col)

    st.subheader("Colunas encontradas")
    st.write(df.columns.tolist())

    st.subheader("Colunas mensais detectadas")
    if colunas_mensais:
        st.success(f"{len(colunas_mensais)} colunas mensais encontradas.")
        st.write(colunas_mensais)
    else:
        st.warning("Nenhuma coluna mensal detectada no formato Mês/Ano (ex: Jun/25, Jul/25).")

    st.subheader("Prévia do arquivo")
    st.dataframe(df.head(20), width="stretch")

    if st.button("Importar faturamento"):

        if not colunas_mensais:
            st.error("Nenhuma coluna mensal encontrada. Verifique o formato do arquivo.")
            st.stop()

        conn = sqlite3.connect("crm.db")
        cursor = conn.cursor()

        clientes_importados = 0
        registros_faturamento = 0
        nao_encontrados = []

        cliente_atual_id = None

        for _, row in df.iterrows():

            codigo = row.get("Unnamed: 1")

            if pd.isna(codigo):
                codigo = row.get("Cod")

            # =====================================================
            # CLIENTE
            # =====================================================

            if pd.notna(codigo):

                try:
                    codigo = str(int(float(codigo)))
                except:
                    continue

                cliente = pd.read_sql_query(
                    """
                    SELECT id
                    FROM clientes
                    WHERE codigo_erp = ?
                    """,
                    conn,
                    params=[codigo]
                )

                if len(cliente) == 0:
                    # ── Cliente nao encontrado: criar provisorio automaticamente ──
                    nome_relatorio = ""
                    for col_nome in ["Descrição", "Descricao", "Cliente", "Razão Social", "Razao Social"]:
                        val_nome = row.get(col_nome, "")
                        if pd.notna(val_nome) and str(val_nome).strip() != "":
                            nome_relatorio = str(val_nome).strip()
                            break
                    if nome_relatorio == "" or nome_relatorio.lower() == "nan":
                        nome_relatorio = f"CLIENTE ERP {codigo}"

                    cursor.execute(
                        """
                        INSERT INTO clientes (
                            codigo_erp,
                            razao_social,
                            tipo_conta,
                            classe_abc,
                            parque_maquinas,
                            maquinas_mitsubishi,
                            frequencia_visita,
                            faturamento_12m,
                            status,
                            origem_cadastro,
                            data_cadastro
                        )
                        VALUES (?, ?, 'LEAD FRIO', 'D', 0, 0, 90, 0, 'PROVISORIO', 'IMPORTACAO_FATURAMENTO', date('now'))
                        """,
                        (codigo, nome_relatorio[:200]),
                    )
                    conn.commit()
                    cliente_atual_id = cursor.lastrowid
                    clientes_importados += 1
                    if codigo not in nao_encontrados:
                        nao_encontrados.append(codigo)
                    # Continua para processar faturamento do cliente criado
                else:
                    cliente_atual_id = int(cliente.iloc[0]["id"])

                # ── Remove registros anteriores SOMENTE da unidade sendo importada ──
                cursor.execute(
                    """
                    DELETE FROM faturamento
                    WHERE cliente_id = ? AND origem = 'PAINEL_VENDAS' AND unidade = ?
                    """,
                    (cliente_atual_id, unidade)
                )

                # ── Percorre colunas mensais e insere faturamento ──
                for col_mes in colunas_mensais:
                    data_ref = parse_coluna_mensal(col_mes)
                    if data_ref is None:
                        continue

                    valor = row.get(col_mes, 0)
                    try:
                        valor = float(valor)
                    except:
                        valor = 0.0

                    if valor <= 0:
                        continue

                    cursor.execute(
                        """
                        INSERT INTO faturamento (
                            cliente_id,
                            unidade,
                            data_faturamento,
                            valor,
                            tipo,
                            origem
                        )
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            cliente_atual_id,
                            unidade,
                            data_ref.isoformat(),
                            valor,
                            "CONSOLIDADO",
                            "PAINEL_VENDAS"
                        )
                    )
                    registros_faturamento += 1

                # ── Recalcula faturamento_12m a partir de TODOS os registros (SP + RS) ──
                cursor.execute(
                    """
                    SELECT COALESCE(SUM(valor), 0),
                           MAX(data_faturamento)
                    FROM faturamento
                    WHERE cliente_id = ?
                    """,
                    (cliente_atual_id,)
                )
                row_fin = cursor.fetchone()
                soma_12m = row_fin[0]
                ultima_data = row_fin[1]

                cursor.execute(
                    """
                    UPDATE clientes
                    SET
                        ultimo_faturamento = ?,
                        faturamento_12m = ?
                    WHERE id = ?
                    """,
                    (
                        ultima_data,
                        soma_12m,
                        cliente_atual_id
                    )
                )

                clientes_importados += 1
                continue

            # =====================================================
            # ITENS (vinculados ao cliente_atual_id)
            # =====================================================

            if cliente_atual_id is None:
                continue

            descricao = str(
                row.get("Descrição", "")
            ).strip()

            if descricao == "" or descricao.lower() == "nan":
                continue

            valor_item = row.get("Total", 0)
            try:
                valor_item = float(valor_item)
            except:
                valor_item = 0

            if valor_item <= 0:
                continue

            # ── Determinar mês do item ──
            # Tenta pegar o mês pelo nome do mês na descrição ou usa a data da primeira coluna mensal não-nula da linha
            data_item = None
            for col_mes in colunas_mensais:
                val_col = row.get(col_mes, 0)
                try:
                    val_col = float(val_col)
                except:
                    val_col = 0
                if val_col > 0:
                    data_item = parse_coluna_mensal(col_mes)
                    break

            if data_item is None:
                data_item = date.today()

            # =====================================================
            # CLASSIFICAÇÃO
            # =====================================================

            if "SERVIÇO" in descricao.upper():
                tipo_item = "SERVICO"
            else:
                tipo_item = "PRODUTO"

            cursor.execute(
                """
                INSERT INTO faturamento_itens (
                    cliente_id,
                    unidade,
                    descricao_item,
                    tipo_item,
                    data_venda,
                    valor_total,
                    origem,
                    data_importacao
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cliente_atual_id,
                    unidade,
                    descricao,
                    tipo_item,
                    data_item.isoformat(),
                    valor_item,
                    "PAINEL_VENDAS",
                    datetime.now().date()
                )
            )

        conn.commit()

        st.success(
            f"{clientes_importados} clientes processados."
        )

        st.success(
            f"{registros_faturamento} registros de faturamento inseridos "
            f"(distribuídos nas {len(colunas_mensais)} colunas mensais)."
        )

        # =====================================================
        # CLIENTES CRIADOS AUTOMATICAMENTE
        # =====================================================

        if len(nao_encontrados) > 0:

            st.warning(
                f"⚠ {len(nao_encontrados)} cliente(s) criado(s) automaticamente como PROVISORIO"
            )

            # Buscar dados dos clientes criados
            placeholders = ",".join("?" for _ in nao_encontrados)
            df_criados = pd.read_sql_query(
                f"""
                SELECT
                    codigo_erp,
                    razao_social,
                    data_cadastro,
                    origem_cadastro,
                    status
                FROM clientes
                WHERE codigo_erp IN ({placeholders})
                """,
                conn,
                params=nao_encontrados
            )

            st.dataframe(df_criados, width="stretch")

            st.info(
                "💡 Clientes criados como **PROVISORIO** precisam ter o cadastro "
                "completado na página **Pendências de Cadastro** (menu Admin)."
            )

        else:

            st.success(
                "Todos os códigos ERP foram encontrados."
            )

        conn.close()
