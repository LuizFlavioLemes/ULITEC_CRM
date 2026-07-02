import streamlit as st
import pandas as pd
import sqlite3
from datetime import date

from auth import verificar_acesso, sidebar_usuario

# ── Proteção: MASTER ou GESTOR ──
verificar_acesso(perfis=["MASTER", "GESTOR"])
sidebar_usuario()

st.set_page_config(
    page_title="Importar OS",
    layout="wide"
)

st.title("📥 Importar Ordens de Serviço")

unidade_importacao = st.selectbox(
    "Unidade das OS importadas",
    [
        "ULITEC SP",
        "ULITEC RS"
    ]
)

arquivo = st.file_uploader(
    "Selecione o relatório de OS",
    type=["xlsx", "xls"]
)

if arquivo:

    try:

        df = pd.read_excel(arquivo, header=None)

        # ═══════════════════════════════════════════════════════════
        # LOCALIZAR CABEÇALHO
        # ═══════════════════════════════════════════════════════════

        keywords_header = {
            "os":          ["cod", "cod.controle", "controle"],
            "abertura":    ["dt abert", "dt.abert", "abertura", "data abertura"]
        }

        header_row = None
        for i in range(min(30, len(df))):
            acertos = 0
            for campo, palavras in keywords_header.items():
                for j in range(df.shape[1]):
                    try:
                        val = str(df.iloc[i, j]).strip().lower() if pd.notna(df.iloc[i, j]) else ""
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
        for j in range(df.shape[1]):
            try:
                val = str(df.iloc[header_row, j]).strip() if pd.notna(df.iloc[header_row, j]) else ""
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
                for i in range(header_row + 1, min(header_row + 100, len(df))):
                    v = df.iloc[i, idx]
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

        conn = sqlite3.connect("crm.db")
        cursor = conn.cursor()

        clientes = pd.read_sql_query(
            "SELECT id, codigo_erp FROM clientes", conn
        )
        clientes["codigo_erp"] = clientes["codigo_erp"].astype(str).str.strip()

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

        for i in range(header_row + 1, len(df)):

            try:

                linha = df.iloc[i]

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
                cliente_match = clientes[
                    clientes["codigo_erp"] == codigo_cliente
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
                        registro["cliente_id"], unidade_importacao,
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
                        unidade_importacao,
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
        conn.close()

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