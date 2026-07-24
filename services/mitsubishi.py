import pandas as pd

import re
from rapidfuzz import process, fuzz

from config import DB_PATH

from database import get_connection

def _get_conn():
    return get_connection()

# ============================================================
# INDICADORES
# ============================================================

def get_indicadores():
    """Retorna dict com indicadores da base Mitsubishi."""
    conn = _get_conn()
    try:
        total_maquinas = conn.execute(
            "SELECT COUNT(*) FROM maquinas_mitsubishi"
        ).fetchone()[0]

        total_clientes = conn.execute(
            "SELECT COUNT(DISTINCT cliente_id) FROM maquinas_mitsubishi WHERE cliente_id IS NOT NULL"
        ).fetchone()[0]

        conciliadas = conn.execute(
            "SELECT COUNT(*) FROM maquinas_mitsubishi WHERE cliente_id IS NOT NULL AND validado = 1"
        ).fetchone()[0]

        pendentes = conn.execute(
            "SELECT COUNT(*) FROM maquinas_mitsubishi WHERE cliente_id IS NULL"
        ).fetchone()[0]

        pcts = (conciliadas / total_maquinas * 100) if total_maquinas > 0 else 0

        return {
            "total_maquinas": total_maquinas,
            "total_clientes": total_clientes,
            "conciliadas": conciliadas,
            "pendentes": pendentes,
            "percentual_conciliado": round(pcts, 1),
        }
    finally:
        conn.close()

def get_nc_series_agrupado():
    conn = _get_conn()
    try:
        return pd.read_sql_query(
            """
            SELECT nc_series, COUNT(*) as total
            FROM maquinas_mitsubishi
            WHERE nc_series != ''
            GROUP BY nc_series
            ORDER BY total DESC
            """,
            conn,
        )
    finally:
        conn.close()

def get_maquinas_por_estado():
    conn = _get_conn()
    try:
        return pd.read_sql_query(
            """
            SELECT uf, COUNT(*) as total
            FROM maquinas_mitsubishi
            WHERE uf != ''
            GROUP BY uf
            ORDER BY total DESC
            """,
            conn,
        )
    finally:
        conn.close()

def get_top_clientes_mitsubishi(limite=20):
    conn = _get_conn()
    try:
        return pd.read_sql_query(
            f"""
            SELECT c.razao_social, c.cidade, c.estado, COUNT(m.id) as maquinas
            FROM maquinas_mitsubishi m
            JOIN clientes c ON c.id = m.cliente_id
            WHERE m.cliente_id IS NOT NULL
            GROUP BY m.cliente_id
            ORDER BY maquinas DESC
            LIMIT {limite}
            """,
            conn,
        )
    finally:
        conn.close()

def get_todos_clientes_mitsubishi():
    """Retorna todos os clientes com máquinas Mitsubishi sem limite."""
    conn = _get_conn()
    try:
        return pd.read_sql_query(
            """
            SELECT c.razao_social, c.cidade, c.estado, COUNT(m.id) as maquinas
            FROM maquinas_mitsubishi m
            JOIN clientes c ON c.id = m.cliente_id
            WHERE m.cliente_id IS NOT NULL
            GROUP BY m.cliente_id
            ORDER BY maquinas DESC
            """,
            conn,
        )
    finally:
        conn.close()

def get_maquinas_por_nc_series(nc_series=None):
    """Retorna máquinas filtradas por série CNC. Se None, lista todas as séries disponíveis."""
    conn = _get_conn()
    try:
        if nc_series:
            return pd.read_sql_query(
                """
                SELECT m.id, m.customer, m.city, m.uf, m.machine,
                       m.serial_number, m.nc_series, m.ano,
                       c.razao_social AS cliente, m.validado
                FROM maquinas_mitsubishi m
                LEFT JOIN clientes c ON c.id = m.cliente_id
                WHERE m.nc_series = ?
                ORDER BY m.customer
                """,
                conn,
                params=[nc_series],
            )
        else:
            return pd.read_sql_query(
                """
                SELECT DISTINCT nc_series
                FROM maquinas_mitsubishi
                WHERE nc_series != ''
                ORDER BY nc_series
                """,
                conn,
            )
    finally:
        conn.close()

def get_ultimas_importadas(limite=20):
    conn = _get_conn()
    try:
        return pd.read_sql_query(
            f"""
            SELECT id, customer, city, uf, machine, serial_number,
                   nc_series, ano, cliente_id, validado
            FROM maquinas_mitsubishi
            ORDER BY id DESC
            LIMIT {limite}
            """,
            conn,
        )
    finally:
        conn.close()

# ============================================================
# IMPORTAÇÃO
# ============================================================

def importar_arquivo(arquivo_bytes):
    """
    Recebe bytes de um arquivo XLSX e importa para maquinas_mitsubishi.
    Retorna dict com resultado da operação.
    """
    df = pd.read_excel(arquivo_bytes, sheet_name="Base", dtype=str)
    df = df.fillna("")
    df.columns = df.columns.astype(str).str.strip()

    conn = _get_conn()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM maquinas_mitsubishi")

        importados = 0
        for _, row in df.iterrows():
            customer = str(row.get("CUSTOMER", "")).strip()
            address = str(row.get("ADDRESS", "")).strip()
            city = str(row.get("CITY", "")).strip()
            uf = str(row.get("UF", "")).strip()
            machine = str(row.get("MACHINE", "")).strip()
            serial_number = str(row.get("SERIAL NUMBER", "")).strip()
            nc_series = str(row.get("NC Series", "")).strip()
            nc_type = str(row.get("NC TYPE", "")).strip()
            dealer = str(row.get("DEALER", "")).strip()
            warranty_start = str(row.get("WARRANTY START", "")).strip()
            warranty_end = str(row.get("WARRANTY END", "")).strip()
            try:
                ano_raw = row.get("Year", "")
                if pd.isna(ano_raw) or str(ano_raw).strip() == "":
                    ano = None
                else:
                    ano = int(float(str(ano_raw).strip()))
            except (ValueError, TypeError):
                ano = None

            cursor.execute(
                """
                INSERT INTO maquinas_mitsubishi
                (customer, address, city, uf, machine, serial_number,
                 nc_series, nc_type, dealer, warranty_start, warranty_end, ano)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (customer, address, city, uf, machine, serial_number,
                 nc_series, nc_type, dealer, warranty_start, warranty_end, ano),
            )
            importados += 1

        conn.commit()

        total_gravado = conn.execute(
            "SELECT COUNT(*) FROM maquinas_mitsubishi"
        ).fetchone()[0]

        return {
            "sucesso": True,
            "registros_lidos": len(df),
            "importados": importados,
            "total_gravado": total_gravado,
            "colunas": list(df.columns),
        }

    except Exception as e:
        conn.rollback()
        return {"sucesso": False, "erro": str(e)}
    finally:
        conn.close()

# ============================================================
# CONCILIAÇÃO
# ============================================================

def limpar_nome(nome):
    """Limpa nome comercial para fuzzy match."""
    nome = str(nome).upper()
    remover = [
        " LTDA", " LTDA.", " S/A", " SA", " EIRELI", " EPP", " ME", " MEI",
        " DO BRASIL", " BRASIL",
        " INDUSTRIA", " INDUSTRIAL", " COMERCIO", " COMERCIAL",
        " METALURGICA", " IMPORTADORA", " EXPORTADORA",
        " FERRAMENTARIA", " MATRIZER", " USINAGEM", " METALURGICO",
        " EQUIPAMENTOS", " MAQUINAS", " MAQUINA", " SISTEMAS",
        " SERVICOS", " SERVIÇOS", " MANUTENCAO", " MANUTENÇÃO",
        " AUTOMACAO", " AUTOMAÇÃO", " ENGENHARIA", " TECNOLOGIA",
        " TECNOLOGIAS", " SOLUCOES", " SOLUÇÕES",
    ]
    for item in remover:
        nome = nome.replace(item, "")
    nome = re.sub(r"[^A-Z0-9 ]", " ", nome)
    nome = re.sub(r"\s+", " ", nome)
    return nome.strip()

def executar_conciliacao():
    """
    Executa conciliação automática entre maquinas_mitsubishi e clientes.
    Retorna dict com resultados.
    """
    conn = _get_conn()
    cursor = conn.cursor()

    try:
        # Limpa revisões anteriores
        cursor.execute("DELETE FROM conciliacao_mitsubishi")

        # Carrega dados
        clientes = pd.read_sql_query(
            "SELECT id, codigo_erp, razao_social FROM clientes", conn
        )
        mitsubishi = pd.read_sql_query(
            "SELECT * FROM maquinas_mitsubishi WHERE cliente_id IS NULL", conn
        )

        if clientes.empty:
            return {"sucesso": False, "erro": "Nenhum cliente cadastrado para conciliar."}

        clientes["nome_limpo"] = clientes["razao_social"].apply(limpar_nome)

        automaticos = []
        revisar = []
        nao_encontrados = []
        total = len(mitsubishi)

        for _, row in mitsubishi.iterrows():
            nome_original = str(row["customer"])
            nome_limpo_str = limpar_nome(nome_original)

            match = process.extractOne(
                nome_limpo_str,
                clientes["nome_limpo"],
                scorer=fuzz.token_sort_ratio,
            )

            if not match:
                nao_encontrados.append({"customer": nome_original})
                continue

            score = float(match[1])
            cliente_match = clientes[clientes["nome_limpo"] == match[0]].iloc[0]

            if score >= 87:
                cursor.execute(
                    """
                    UPDATE maquinas_mitsubishi
                    SET cliente_id = ?, score_match = ?, validado = 1
                    WHERE id = ?
                    """,
                    (int(cliente_match["id"]), score, int(row["id"])),
                )
                automaticos.append({
                    "customer": nome_original,
                    "cliente": cliente_match["razao_social"],
                    "score": round(score, 2),
                })

            elif score >= 70:
                cursor.execute(
                    """
                    INSERT INTO conciliacao_mitsubishi
                    (maquina_id, cliente_sugerido_id, customer, cliente_sugerido, score, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (int(row["id"]), int(cliente_match["id"]),
                     nome_original, cliente_match["razao_social"], score, "REVISAO"),
                )
                revisar.append({
                    "customer": nome_original,
                    "cliente_sugerido": cliente_match["razao_social"],
                    "score": round(score, 2),
                })
            else:
                nao_encontrados.append({
                    "customer": nome_original,
                    "score": round(score, 2),
                })

        conn.commit()

        return {
            "sucesso": True,
            "total": total,
            "automaticos": automaticos,
            "revisar": revisar,
            "nao_encontrados": nao_encontrados,
        }

    except Exception as e:
        conn.rollback()
        return {"sucesso": False, "erro": str(e)}
    finally:
        conn.close()

def get_conciliacao_pendencias(limite=200):
    """Retorna DataFrame com pendências de conciliação em revisão."""
    conn = _get_conn()
    try:
        return pd.read_sql_query(
            """
            SELECT
                cm.id AS conciliacao_id,
                cm.maquina_id,
                cm.customer,
                cm.cliente_sugerido_id,
                cm.cliente_sugerido,
                cm.score,
                m.city,
                m.uf,
                m.machine,
                m.serial_number,
                m.nc_series,
                m.ano
            FROM conciliacao_mitsubishi cm
            LEFT JOIN maquinas_mitsubishi m ON m.id = cm.maquina_id
            WHERE cm.status = 'REVISAO'
            ORDER BY cm.score DESC, cm.customer
            LIMIT ?
            """,
            conn,
            params=[limite],
        )
    finally:
        conn.close()

def get_clientes_para_vinculo():
    """Retorna DataFrame de clientes para selectbox."""
    conn = _get_conn()
    try:
        return pd.read_sql_query(
            """
            SELECT id, codigo_erp, razao_social, cidade, estado
            FROM clientes
            ORDER BY razao_social
            """,
            conn,
        )
    finally:
        conn.close()

def get_maquinas_sem_cliente():
    """Retorna máquinas Mitsubishi sem cliente vinculado."""
    conn = _get_conn()
    try:
        return pd.read_sql_query(
            """
            SELECT *
            FROM maquinas_mitsubishi
            WHERE cliente_id IS NULL
            ORDER BY customer
            """,
            conn,
        )
    finally:
        conn.close()

def get_maquinas_por_filtro(filtro="TODOS"):
    """
    Retorna máquinas Mitsubishi com info de cliente.
    filtro: TODOS, CONCILIADOS, PENDENTES
    """
    conn = _get_conn()
    try:
        query = """
            SELECT m.id, m.customer, m.city, m.uf, m.machine,
                   m.serial_number, m.nc_series, m.ano,
                   c.razao_social AS cliente_nome, m.validado,
                   m.score_match
            FROM maquinas_mitsubishi m
            LEFT JOIN clientes c ON c.id = m.cliente_id
        """
        if filtro == "CONCILIADOS":
            query += " WHERE m.cliente_id IS NOT NULL AND m.validado = 1"
        elif filtro == "PENDENTES":
            query += " WHERE m.cliente_id IS NULL OR m.validado = 0"
        query += " ORDER BY m.id DESC"
        return pd.read_sql_query(query, conn)
    finally:
        conn.close()

# ============================================================
# REVISÃO / VALIDAÇÃO
# ============================================================

def aprovar_sugestao(conciliacao_id, maquina_id, cliente_sugerido_id, score):
    """Aprova sugestão de conciliação automática."""
    conn = _get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE maquinas_mitsubishi
            SET cliente_id = ?, score_match = ?, validado = 1
            WHERE id = ?
            """,
            (int(cliente_sugerido_id), float(score), int(maquina_id)),
        )
        cursor.execute(
            "UPDATE conciliacao_mitsubishi SET status = 'APROVADO' WHERE id = ?",
            (conciliacao_id,),
        )
        _atualizar_contagem(conn)
        conn.commit()
        return {"sucesso": True}
    except Exception as e:
        conn.rollback()
        return {"sucesso": False, "erro": str(e)}
    finally:
        conn.close()

def vincular_manual(conciliacao_id, maquina_id, cliente_id, score, cliente_nome):
    """Vincula máquina a um cliente manualmente selecionado."""
    conn = _get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE maquinas_mitsubishi
            SET cliente_id = ?, score_match = ?, validado = 1
            WHERE id = ?
            """,
            (int(cliente_id), float(score), int(maquina_id)),
        )
        cursor.execute(
            """
            UPDATE conciliacao_mitsubishi
            SET status = 'VINCULADO_MANUAL', cliente_sugerido_id = ?, cliente_sugerido = ?
            WHERE id = ?
            """,
            (int(cliente_id), cliente_nome, conciliacao_id),
        )
        _atualizar_contagem(conn)
        conn.commit()
        return {"sucesso": True}
    except Exception as e:
        conn.rollback()
        return {"sucesso": False, "erro": str(e)}
    finally:
        conn.close()

def rejeitar_sugestao(conciliacao_id):
    """Rejeita sugestão de conciliação."""
    conn = _get_conn()
    try:
        conn.execute(
            "UPDATE conciliacao_mitsubishi SET status = 'REJEITADO' WHERE id = ?",
            (conciliacao_id,),
        )
        conn.commit()
        return {"sucesso": True}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}
    finally:
        conn.close()

def excluir_vinculo(maquina_id):
    """Remove vínculo entre máquina e cliente."""
    conn = _get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE maquinas_mitsubishi SET cliente_id = NULL, score_match = NULL, validado = 0 WHERE id = ?",
            (int(maquina_id),),
        )
        _atualizar_contagem(conn)
        conn.commit()
        return {"sucesso": True}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}
    finally:
        conn.close()

def _atualizar_contagem(conn):
    conn.execute(
        """
        UPDATE clientes
        SET maquinas_mitsubishi = (
            SELECT COUNT(*)
            FROM maquinas_mitsubishi m
            WHERE m.cliente_id = clientes.id
        )
        """
    )

def get_duplicidades():
    """Retorna máquinas com mesmo serial_number duplicado."""
    conn = _get_conn()
    try:
        return pd.read_sql_query(
            """
            SELECT m1.id, m1.customer, m1.machine, m1.serial_number,
                   m1.city, m1.uf, m1.cliente_id, c.razao_social AS cliente_nome
            FROM maquinas_mitsubishi m1
            JOIN maquinas_mitsubishi m2
                ON m1.serial_number = m2.serial_number
                AND m1.id != m2.id
            LEFT JOIN clientes c ON c.id = m1.cliente_id
            WHERE m1.serial_number != ''
            ORDER BY m1.serial_number
            """,
            conn,
        )
    finally:
        conn.close()