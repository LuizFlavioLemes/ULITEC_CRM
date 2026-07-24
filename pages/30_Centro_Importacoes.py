import streamlit as st
import pandas as pd

import re
from datetime import datetime, date

from auth import sidebar_usuario
from permissions import verificar_acesso_pagina, pode_importar
from services import formatar_clientes_para_select

from database import get_connection

# ── Proteção: MASTER, SÓCIO ou GERENTE ──
verificar_acesso_pagina("MASTER", "SÓCIO", "GERENTE")
sidebar_usuario()

st.set_page_config(
    page_title="Centro de Importações",
    layout="wide"
)

st.title("📥 Centro de Importações")
st.markdown("Centralize todas as importações de dados do sistema.")

# ── Conexão BD ──
conn = get_connection()

# ═══════════════════════════════════════════════════════════
# CONSTANTES COMPARTILHADAS
# ═══════════════════════════════════════════════════════════

MESES = {
    "jan": 1, "fev": 2, "mar": 3, "abr": 4, "mai": 5, "jun": 6,
    "jul": 7, "ago": 8, "set": 9, "out": 10, "nov": 11, "dez": 12
}

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

# ═══════════════════════════════════════════════════════════
# ABAS
# ═══════════════════════════════════════════════════════════

tab1, tab2, tab3, tab4 = st.tabs([
    "📋 Importação Clientes",
    "💰 Importação Faturamento",
    "🔧 Importação OS",
    "📋 Pendências de Cadastro"
])

# =====================================================
# ABA 1 — IMPORTAÇÃO CLIENTES
# =====================================================

with tab1:

    st.subheader("📥 Importação de Clientes ERP")

    arquivo_cli = st.file_uploader(
        "Selecione o relatório Relação Clientes",
        type=["xlsx"],
        key="upload_clientes"
    )

    if arquivo_cli:

        try:

            df_cli = pd.read_excel(
                arquivo_cli,
                sheet_name=0,
                header=None
            )

            st.subheader("Prévia")
            st.dataframe(
                df_cli.head(20),
                width="stretch"
            )

            if st.button("IMPORTAR CLIENTES", key="btn_importar_clientes"):

                cursor = conn.cursor()

                importados = 0
                atualizados = 0

                # dados começam após a linha do cabeçalho
                for i in range(8, len(df_cli)):

                    try:
                        codigo = df_cli.iloc[i, 0]

                        # ignora linhas vazias
                        if pd.isna(codigo):
                            continue

                        # ignora linhas IE Principal
                        if not str(codigo).replace(".0", "").isdigit():
                            continue

                        codigo = str(int(float(codigo)))

                        razao_social = str(df_cli.iloc[i, 2]).strip()
                        nome_fantasia = str(df_cli.iloc[i, 4]).strip()
                        cidade = str(df_cli.iloc[i, 6]).strip()
                        telefone = str(df_cli.iloc[i, 7]).strip()
                        email = str(df_cli.iloc[i, 10]).strip()

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
                                VALUES (?, ?, ?, ?, ?, ?)
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

                st.success(f"{importados} clientes importados.")
                st.success(f"{atualizados} clientes atualizados.")

        except Exception as erro:
            st.error(f"Erro: {erro}")

# =====================================================
# ABA 2 — IMPORTAÇÃO FATURAMENTO
# =====================================================

with tab2:

    st.subheader("💰 Importar Faturamento")

    arquivo_fat = st.file_uploader(
        "Selecione o relatório do Painel de Vendas",
        type=["xlsx"],
        key="upload_faturamento"
    )

    unidade_fat = st.selectbox(
        "Unidade",
        ["ULITEC SP", "ULITEC RS"],
        key="unidade_faturamento"
    )

    if arquivo_fat:

        df_fat = pd.read_excel(arquivo_fat)

        # ── Detectar colunas mensais ──
        colunas_mensais = []
        for col in df_fat.columns:
            if parse_coluna_mensal(col) is not None:
                colunas_mensais.append(col)

        st.subheader("Colunas encontradas")
        st.write(df_fat.columns.tolist())

        st.subheader("Colunas mensais detectadas")
        if colunas_mensais:
            st.success(f"{len(colunas_mensais)} colunas mensais encontradas.")
            st.write(colunas_mensais)
        else:
            st.warning("Nenhuma coluna mensal detectada no formato Mês/Ano (ex: Jun/25, Jul/25).")

        st.subheader("Prévia do arquivo")
        st.dataframe(df_fat.head(20), width="stretch")

        if st.button("Importar faturamento", key="btn_importar_faturamento"):

            if not colunas_mensais:
                st.error("Nenhuma coluna mensal encontrada. Verifique o formato do arquivo.")
                st.stop()

            cursor = conn.cursor()

            clientes_importados = 0
            registros_faturamento = 0
            nao_encontrados = []

            cliente_atual_id = None

            for _, row in df_fat.iterrows():

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
                    else:
                        cliente_atual_id = int(cliente.iloc[0]["id"])

                    # ── Remove registros anteriores SOMENTE da unidade sendo importada ──
                    cursor.execute(
                        """
                        DELETE FROM faturamento
                        WHERE cliente_id = ? AND origem = 'PAINEL_VENDAS' AND unidade = ?
                        """,
                        (cliente_atual_id, unidade_fat)
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
                                unidade_fat,
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
                        unidade_fat,
                        descricao,
                        tipo_item,
                        data_item.isoformat(),
                        valor_item,
                        "PAINEL_VENDAS",
                        datetime.now().date()
                    )
                )

            conn.commit()

            st.success(f"{clientes_importados} clientes processados.")
            st.success(f"{registros_faturamento} registros de faturamento inseridos (distribuídos nas {len(colunas_mensais)} colunas mensais).")

            # =====================================================
            # CLIENTES CRIADOS AUTOMATICAMENTE
            # =====================================================

            if len(nao_encontrados) > 0:
                st.warning(f"⚠ {len(nao_encontrados)} cliente(s) criado(s) automaticamente como PROVISORIO")

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
                    "completado na aba **Pendências de Cadastro**."
                )
            else:
                st.success("Todos os códigos ERP foram encontrados.")

# =====================================================
# ABA 3 — IMPORTAÇÃO OS
# =====================================================

with tab3:

    st.subheader("📥 Importar Ordens de Serviço")

    unidade_os = st.selectbox(
        "Unidade das OS importadas",
        ["ULITEC SP", "ULITEC RS"],
        key="unidade_os"
    )

    arquivo_os = st.file_uploader(
        "Selecione o relatório de OS",
        type=["xlsx", "xls"],
        key="upload_os"
    )

    if arquivo_os:

        try:

            df_os = pd.read_excel(arquivo_os, header=None)

            # ═══════════════════════════════════════════════════════════
            # LOCALIZAR CABEÇALHO
            # ═══════════════════════════════════════════════════════════

            keywords_header = {
                "os":          ["cod", "cod.controle", "controle"],
                "abertura":    ["dt abert", "dt.abert", "abertura", "data abertura"]
            }

            header_row = None
            for i in range(min(30, len(df_os))):
                acertos = 0
                for campo, palavras in keywords_header.items():
                    for j in range(df_os.shape[1]):
                        try:
                            val = str(df_os.iloc[i, j]).strip().lower() if pd.notna(df_os.iloc[i, j]) else ""
                        except:
                            val = ""
                        if any(p in val for p in palavras):
                            acertos += 1
                            break
                if acertos >= 1:
                    header_row = i
                    break

            if header_row is None:
                st.error("❌ Cabeçalho não encontrado no relatório.")
                st.stop()

            # ═══════════════════════════════════════════════════════════
            # MAPEAMENTO DINÂMICO DAS COLUNAS
            # ═══════════════════════════════════════════════════════════

            header_map = {}
            for j in range(df_os.shape[1]):
                try:
                    val = str(df_os.iloc[header_row, j]).strip() if pd.notna(df_os.iloc[header_row, j]) else ""
                except:
                    val = ""
                if val:
                    header_map[val] = j
                    header_map[val.lower()] = j

            def encontrar_coluna(nomes_possiveis):
                for nome in nomes_possiveis:
                    if nome in header_map:
                        return header_map[nome]
                return None

            col_map = {}
            col_map["cod_cliente"] = encontrar_coluna(["cod", "COD"])
            col_map["cliente"] = encontrar_coluna(["Cliente", "cliente", "CLIENTE"])
            col_map["abertura"] = encontrar_coluna(["Dt Abert", "dt abert", "DT ABERT", "Dt.Abert", "dt.abert", "Abertura", "abertura", "Data Abertura", "data abertura"])
            col_map["previsao"] = encontrar_coluna(["Dt Previsão", "Dt Previsao", "dt previsão", "dt previsao", "Dt.Previs", "dt.previs", "Previsão", "Previsao"])
            col_map["fechamento"] = encontrar_coluna(["Dt Fecha", "dt fecha", "DT FECHA", "Dt.Fecha", "dt.fecha", "Fechamento", "fechamento", "Data Fecha", "data fecha"])
            col_map["total"] = encontrar_coluna(["Total", "total", "TOTAL"])
            col_map["tipo"] = encontrar_coluna(["Tipo", "tipo", "TIPO"])

            # ── Detectar coluna da OS (Cod ou Controle) ──
            col_cod = encontrar_coluna(["Cod", "cod", "COD"])
            col_controle = encontrar_coluna(["Controle", "controle", "CONTROLE"])

            col_map["os"] = None
            if col_cod is not None or col_controle is not None:
                candidatos_os = {}
                if col_cod is not None:
                    candidatos_os["Cod"] = col_cod
                if col_controle is not None and col_controle != col_cod:
                    candidatos_os["Controle"] = col_controle

                melhor_nome = None
                melhor_qtd = -1
                melhor_idx = None

                for nome, idx in candidatos_os.items():
                    qtd = 0
                    for i in range(header_row + 1, min(header_row + 100, len(df_os))):
                        v = df_os.iloc[i, idx]
                        if pd.notna(v):
                            try:
                                if int(v) > 0:
                                    qtd += 1
                            except:
                                pass
                    if qtd > melhor_qtd:
                        melhor_qtd = qtd
                        melhor_nome = nome
                        melhor_idx = idx

                if melhor_nome is not None:
                    col_map["os"] = melhor_idx

            # ═══════════════════════════════════════════════════════════
            # VALIDAR COLUNAS OBRIGATÓRIAS
            # ═══════════════════════════════════════════════════════════

            campos_obrigatorios = ["os", "cod_cliente", "cliente", "abertura", "total"]
            campos_faltando = [c for c in campos_obrigatorios if col_map.get(c) is None]
            if campos_faltando:
                st.error(f"❌ Colunas obrigatórias não encontradas no cabeçalho: {', '.join(campos_faltando)}")
                st.stop()

            # ═══════════════════════════════════════════════════════════
            # CONEXÃO BANCO E LEITURA DE CLIENTES
            # ═══════════════════════════════════════════════════════════

            cursor = conn.cursor()

            clientes_df = pd.read_sql_query(
                "SELECT id, codigo_erp FROM clientes", conn
            )
            clientes_df["codigo_erp"] = clientes_df["codigo_erp"].astype(str).str.strip()

            registros = []

            col_os = col_map["os"]
            col_cod_cliente = col_map["cod_cliente"]
            col_nome_cliente = col_map["cliente"]
            col_abertura = col_map["abertura"]
            col_previsao = col_map.get("previsao")
            col_fechamento = col_map.get("fechamento")
            col_total = col_map["total"]

            # ═══════════════════════════════════════════════════════════
            # LEITURA DAS OS
            # ═══════════════════════════════════════════════════════════

            for i in range(header_row + 1, len(df_os)):

                try:
                    linha = df_os.iloc[i]

                    # ── CRITÉRIO 1: OS = número inteiro positivo ──
                    numero_os = linha[col_os]
                    if pd.isna(numero_os):
                        continue
                    try:
                        numero_os = int(numero_os)
                        if numero_os <= 0:
                            continue
                    except:
                        continue

                    # ── CRITÉRIO 2: Código cliente preenchido ──
                    codigo_cliente = str(linha[col_cod_cliente]).strip()
                    if codigo_cliente == "" or codigo_cliente.lower() in ("nan", "none"):
                        continue

                    # ── CRITÉRIO 3: Nome cliente preenchido ──
                    try:
                        nome_cliente = str(linha[col_nome_cliente]).strip()
                        if nome_cliente == "" or nome_cliente.lower() in ("nan", "none"):
                            continue
                    except:
                        continue

                    # ── CRITÉRIO 4: Data abertura válida ──
                    data_abertura = linha[col_abertura]
                    if not pd.notna(data_abertura):
                        continue
                    data_abertura_str = str(data_abertura).strip()
                    if data_abertura_str.lower() in ("nan", "none", "nat", ""):
                        continue

                    # ── Total (opcional, aceita 0) ──
                    valor_total_f = 0
                    valor_total = linha[col_total]
                    if pd.notna(valor_total):
                        try:
                            valor_total_f = float(valor_total)
                        except:
                            pass

                    # ── Match com cliente no banco ──
                    cliente_match = clientes_df[
                        clientes_df["codigo_erp"] == codigo_cliente
                    ]
                    cliente_id = None
                    if len(cliente_match) > 0:
                        cliente_id = int(cliente_match.iloc[0]["id"])

                    # ── Datas ──
                    data_previsao = linha[col_previsao] if col_previsao is not None else None
                    data_fechamento = linha[col_fechamento] if col_fechamento is not None else None

                    # ── Status ──
                    status = "RECEBIDA"
                    if pd.notna(data_previsao):
                        status = "PROPOSTA ENVIADA"
                    if pd.notna(data_fechamento):
                        status = "APROVADA"

                    registros.append({
                        "numero_os": str(numero_os),
                        "cliente_id": cliente_id,
                        "data_recebimento": data_abertura,
                        "data_envio_proposta": data_previsao,
                        "data_aprovacao": data_fechamento,
                        "valor_proposta": valor_total_f,
                        "status": status
                    })

                except:
                    pass

            # ═══════════════════════════════════════════════════════════
            # GRAVAÇÃO
            # ═══════════════════════════════════════════════════════════

            inseridos = 0
            atualizados = 0

            for registro in registros:

                existe = cursor.execute(
                    "SELECT id FROM ordens_servico WHERE numero_os = ?",
                    (registro["numero_os"],)
                ).fetchone()

                if existe:
                    cursor.execute(
                        """
                        UPDATE ordens_servico
                        SET cliente_id=?, unidade=?, responsavel=?, equipamento=?,
                            marca=?, modelo=?, serial_number=?, data_recebimento=?,
                            data_envio_proposta=?, data_aprovacao=?, valor_proposta=?,
                            status=?, data_atualizacao=?
                        WHERE numero_os=?
                        """,
                        (
                            registro["cliente_id"], unidade_os,
                            "", "", "", "", "",
                            str(registro["data_recebimento"]),
                            str(registro["data_envio_proposta"]),
                            str(registro["data_aprovacao"]),
                            float(registro["valor_proposta"]),
                            registro["status"],
                            str(date.today()),
                            registro["numero_os"]
                        )
                    )
                    atualizados += 1
                else:
                    cursor.execute(
                        """
                        INSERT INTO ordens_servico (
                            numero_os, cliente_id, unidade, responsavel, equipamento,
                            marca, modelo, serial_number, data_recebimento,
                            data_envio_proposta, data_aprovacao, valor_proposta,
                            status, origem, data_criacao, data_atualizacao
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            registro["numero_os"], registro["cliente_id"],
                            unidade_os,
                            "", "", "", "", "",
                            str(registro["data_recebimento"]),
                            str(registro["data_envio_proposta"]),
                            str(registro["data_aprovacao"]),
                            float(registro["valor_proposta"]),
                            registro["status"], "ERP",
                            str(date.today()), str(date.today())
                        )
                    )
                    inseridos += 1

            conn.commit()

            # ═══════════════════════════════════════════════════════════
            # RESUMO FINAL
            # ═══════════════════════════════════════════════════════════

            st.success("✅ Relatório processado com sucesso!")

            col1, col2, col3 = st.columns(3)
            col1.metric("OS encontradas", len(registros))
            col2.metric("Inseridas", inseridos)
            col3.metric("Atualizadas", atualizados)

        except Exception as erro:
            st.error(f"❌ Falha na importação: {str(erro)}")

# =====================================================
# ABA 4 — PENDÊNCIAS DE CADASTRO
# =====================================================

with tab4:

    st.subheader("📋 Pendências de Cadastro")
    st.markdown("Clientes criados automaticamente durante importações que precisam ter o cadastro completado.")

    # ── Filtros ──
    colf1, colf2 = st.columns(2)
    with colf1:
        filtro_status = st.selectbox(
            "Status",
            ["PROVISORIO", "ATIVO", "TODOS"],
            index=0,
            key="pend_status"
        )
    with colf2:
        filtro_origem = st.selectbox(
            "Origem do Cadastro",
            ["IMPORTACAO_FATURAMENTO", "TODOS"],
            index=0,
            key="pend_origem"
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
    query_pend = f"""
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

    df_pend = pd.read_sql_query(query_pend, conn, params=params)

    # ── Exibir ──
    st.metric("Total de clientes pendentes", len(df_pend))

    if len(df_pend) > 0:
        # Formatando colunas
        df_display = df_pend.copy()
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

        cliente_ids = df_pend["id"].tolist()
        clientes_formatados, clientes_dict_map, _ = formatar_clientes_para_select(df_pend)

        if clientes_formatados:
            cliente_selecionado = st.selectbox(
                "Selecione um cliente para editar",
                options=clientes_formatados,
                key="pend_select_cliente"
            )

            if cliente_selecionado:
                cliente_id = clientes_dict_map[cliente_selecionado]
                row = df_pend[df_pend["id"] == cliente_id].iloc[0]

                with st.form(key="form_completar_cadastro"):
                    c1, c2 = st.columns(2)

                    with c1:
                        novo_codigo = st.text_input(
                            "Código ERP",
                            value=str(row["codigo_erp"]) if row["codigo_erp"] else ""
                        )
                        nova_razao = st.text_input(
                            "Razão Social",
                            value=row["razao_social"] if row["razao_social"] else ""
                        )
                        novo_fantasia = st.text_input("Nome Fantasia", value="")
                        novo_cnpj = st.text_input(
                            "CNPJ",
                            value=row["cnpj"] if row["cnpj"] else ""
                        )

                    with c2:
                        novo_cidade = st.text_input(
                            "Cidade",
                            value=row["cidade"] if row["cidade"] else ""
                        )
                        novo_estado = st.text_input(
                            "Estado",
                            value=row["estado"] if row["estado"] else ""
                        )
                        novo_telefone = st.text_input("Telefone", value="")
                        novo_email = st.text_input("E-mail", value="")

                    novo_segmento = st.selectbox(
                        "Segmento",
                        ["METALURGICO", "AUTOMOTIVO", "PLASTICO", "FERRAMENTARIA",
                         "ALIMENTICIO", "MEDICO", "OUTROS", ""],
                        index=0
                    )

                    c1, c2 = st.columns(2)
                    with c1:
                        novo_tipo_conta = st.selectbox(
                            "Tipo de Conta",
                            ["LEAD FRIO", "LEAD QUENTE", "CLIENTE ATIVO",
                             "CLIENTE INATIVO", "EX- CLIENTE", "PROSPECCAO"],
                            index=2
                        )
                    with c2:
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

        colb1, colb2, colb3 = st.columns(3)
        with colb1:
            if st.button("Ativar Todos os Pendentes", type="secondary", width="stretch", key="btn_ativar_todos"):
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

        with colb2:
            if st.button("Excluir Selecionados", type="secondary", width="stretch", key="btn_excluir_selecionados"):
                st.warning("Selecione clientes individualmente para exclusão segura.")

    else:
        st.info("✅ Nenhum cliente pendente encontrado. Todos os cadastros estão completos!")

conn.close()