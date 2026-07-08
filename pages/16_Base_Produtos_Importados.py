import sqlite3
from datetime import date, timedelta

import openpyxl
import pandas as pd
import streamlit as st

from auth import sidebar_usuario
from permissions import verificar_acesso_pagina

# ── Proteção ──
verificar_acesso_pagina()
sidebar_usuario()

st.set_page_config(page_title="Base de Produtos Importados", layout="wide")

st.title("📦 Base de Produtos Importados")


# ============================================================
# FUNÇÃO DE NORMALIZAÇÃO ÚNICA
# ============================================================

def normalizar_modelo(texto):
    """Normaliza modelo para buscas e inserções: upper, trim, sem hífens."""
    if texto is None:
        return ""
    return str(texto).strip().upper().replace("-", "").replace(" ", "")


# ============================================================
# FUNÇÕES DE BANCO DE DADOS
# ============================================================

def get_conn():
    return sqlite3.connect("crm.db")


def carregar_config():
    conn = get_conn()
    configs = {}
    try:
        rows = conn.execute("SELECT chave, valor FROM config_importacao").fetchall()
        for chave, valor in rows:
            configs[chave] = valor
    except Exception:
        pass
    conn.close()
    return configs


def salvar_config(chave, valor):
    conn = get_conn()
    conn.execute("""
        INSERT INTO config_importacao (chave, valor, descricao)
        VALUES (?, ?, ?)
        ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor
    """, (chave, valor, ""))
    conn.commit()
    conn.close()


def carregar_tipos_produto():
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM tipo_produto_importado WHERE ativo = 1 ORDER BY descricao", conn)
    conn.close()
    return df


def salvar_tipo_produto(id, ii, ipi, pis, cofins, icms):
    conn = get_conn()
    conn.execute("""
        UPDATE tipo_produto_importado
        SET ii = ?, ipi = ?, pis = ?, cofins = ?, icms = ?
        WHERE id = ?
    """, (ii, ipi, pis, cofins, icms, id))
    conn.commit()
    conn.close()


def carregar_ncms():
    conn = get_conn()
    df = pd.read_sql("""
        SELECT n.id, n.ncm, n.descricao, tp.descricao AS tipo_produto, n.ativo
        FROM ncm_importacao n
        LEFT JOIN tipo_produto_importado tp ON n.tipo_produto_id = tp.id
        WHERE n.ativo = 1
        ORDER BY n.ncm
    """, conn)
    conn.close()
    return df


def buscar_ncm_por_tipo_produto(tipo_produto_id):
    """Retorna o primeiro NCM ativo vinculado ao tipo_produto_id."""
    conn = get_conn()
    row = conn.execute("""
        SELECT id, ncm, descricao
        FROM ncm_importacao
        WHERE tipo_produto_id = ? AND ativo = 1
        ORDER BY ncm
        LIMIT 1
    """, (tipo_produto_id,)).fetchone()
    conn.close()
    if row:
        return {"id": row[0], "ncm": row[1], "descricao": row[2]}
    return None


def calcular_nacionalizacao(fob_usd, frete_rateado, dolar, ii_pct, ipi_pct, pis_pct, cofins_pct, icms_pct, despesas_aduaneiras):
    fob_freight_usd = fob_usd + frete_rateado
    valor_base_brl = fob_freight_usd * dolar

    ii = valor_base_brl * (ii_pct / 100)
    ipi = valor_base_brl * (ipi_pct / 100)
    pis = valor_base_brl * (pis_pct / 100)
    cofins = valor_base_brl * (cofins_pct / 100)

    subtotal = valor_base_brl + ii + ipi + pis + cofins

    icms_decimal = icms_pct / 100
    if icms_decimal >= 1:
        icms_decimal = 0.99
    valor_com_icms = subtotal / (1 - icms_decimal)
    icms_valor = valor_com_icms - subtotal

    valor_nacionalizado = valor_com_icms + despesas_aduaneiras

    return {
        "fob_freight_usd": fob_freight_usd,
        "valor_base_brl": valor_base_brl,
        "ii": ii,
        "ipi": ipi,
        "pis": pis,
        "cofins": cofins,
        "subtotal": subtotal,
        "icms_valor": icms_valor,
        "valor_com_icms": valor_com_icms,
        "despesas_aduaneiras": despesas_aduaneiras,
        "valor_nacionalizado": valor_nacionalizado,
    }


# ============================================================
# NOVAS FUNÇÕES - FORNECEDORES
# ============================================================

def carregar_fornecedores(apenas_ativos=True):
    """Carrega lista de fornecedores cadastrados."""
    conn = get_conn()
    if apenas_ativos:
        df = pd.read_sql("SELECT * FROM fornecedores_produto WHERE ativo = 1 ORDER BY nome", conn)
    else:
        df = pd.read_sql("SELECT * FROM fornecedores_produto ORDER BY nome", conn)
    conn.close()
    return df


def cadastrar_fornecedor(nome, pais="", observacoes="", ativo=1):
    """Cadastra um novo fornecedor.
    Se o nome já existir, retorna mensagem informando."""
    conn = get_conn()
    try:
        nome_clean = nome.strip()
        # Verificar se já existe
        existente = conn.execute(
            "SELECT id FROM fornecedores_produto WHERE nome = ?",
            (nome_clean,)
        ).fetchone()
        if existente:
            conn.close()
            return True, f"Fornecedor '{nome_clean}' já estava cadastrado (ID {existente[0]})."
        conn.execute("""
            INSERT INTO fornecedores_produto (nome, pais, observacoes, ativo)
            VALUES (?, ?, ?, ?)
        """, (nome_clean, pais.strip(), observacoes.strip(), ativo))
        conn.commit()
        conn.close()
        return True, "Fornecedor cadastrado com sucesso!"
    except Exception as e:
        conn.close()
        return False, str(e)


def atualizar_fornecedor(fornecedor_id, nome, pais, observacoes, ativo):
    """Atualiza dados de um fornecedor."""
    conn = get_conn()
    try:
        conn.execute("""
            UPDATE fornecedores_produto
            SET nome = ?, pais = ?, observacoes = ?, ativo = ?, atualizado_em = date('now')
            WHERE id = ?
        """, (nome.strip(), pais.strip(), observacoes.strip(), ativo, fornecedor_id))
        conn.commit()
        conn.close()
        return True, "Fornecedor atualizado!"
    except Exception as e:
        conn.close()
        return False, str(e)


# ============================================================
# NOVAS FUNÇÕES - PRODUTOS (APENAS DADOS DO ITEM)
# ============================================================

def buscar_produtos(termo):
    """Busca produtos (apenas dados do item, sem fornecedor)."""
    conn = get_conn()
    termo_normalizado = normalizar_modelo(termo)
    query = """
        SELECT p.id, p.modelo, p.descricao, p.tipo_produto_id, p.ncm_id,
               tp.descricao AS tipo_produto,
               n.ncm, n.descricao AS descricao_ncm,
               p.modelo_busca
        FROM produtos_importados p
        LEFT JOIN tipo_produto_importado tp ON p.tipo_produto_id = tp.id
        LEFT JOIN ncm_importacao n ON p.ncm_id = n.id
        WHERE p.ativo = 1
        AND (
            p.modelo LIKE ?
            OR p.descricao LIKE ?
            OR p.id LIKE ?
            OR p.modelo_busca LIKE ?
        )
        ORDER BY p.modelo
        LIMIT 30
    """
    param = f"%{termo}%"
    param_busca = f"%{termo_normalizado}%"
    df = pd.read_sql(query, conn, params=(param, param, param, param_busca))
    conn.close()
    return df


def sugerir_produtos(termo, limite=10):
    """
    Busca parcial por modelo para a aba de cadastro.
    Reutiliza normalizar_modelo para ignorar hífens, espaços, maiúsculas.
    Retorna lista de produtos cujo modelo_busca contenha o termo normalizado.
    """
    if not termo or len(termo.strip()) < 2:
        return []
    conn = get_conn()
    termo_norm = normalizar_modelo(termo)
    param = f"%{termo_norm}%"
    rows = conn.execute("""
        SELECT p.id, p.modelo, p.modelo_busca, p.descricao,
               tp.descricao AS tipo_produto,
               n.ncm
        FROM produtos_importados p
        LEFT JOIN tipo_produto_importado tp ON p.tipo_produto_id = tp.id
        LEFT JOIN ncm_importacao n ON p.ncm_id = n.id
        WHERE p.ativo = 1
          AND p.modelo_busca LIKE ?
        ORDER BY
          CASE WHEN p.modelo_busca = ? THEN 0
               WHEN p.modelo_busca LIKE ? THEN 1
               ELSE 2 END,
          p.modelo
        LIMIT ?
    """, (param, termo_norm, f"{termo_norm}%", limite))
    resultados = []
    for r in rows:
        resultados.append({
            "id": r[0],
            "modelo": r[1],
            "modelo_busca": r[2],
            "descricao": r[3],
            "tipo_produto": r[4] or "",
            "ncm": r[5] or "",
        })
    conn.close()
    return resultados


def buscar_ofertas_por_produto(produto_id):
    """Busca todas as ofertas (fornecedores) de um produto."""
    conn = get_conn()
    query = """
        SELECT of.id AS oferta_id, of.produto_id, of.fornecedor_id,
               f.nome AS fornecedor, f.pais AS pais_fornecedor,
               of.fob_atual_usd, of.data_fob, of.observacoes,
               of.ativo
        FROM produtos_importados_fornecedores of
        INNER JOIN fornecedores_produto f ON of.fornecedor_id = f.id
        WHERE of.produto_id = ? AND of.ativo = 1 AND f.ativo = 1
        ORDER BY of.fob_atual_usd ASC
    """
    df = pd.read_sql(query, conn, params=(produto_id,))
    conn.close()
    return df


def buscar_oferta_por_produto_fornecedor(produto_id, fornecedor_id):
    """Verifica se existe oferta para produto+fornecedor."""
    conn = get_conn()
    row = conn.execute("""
        SELECT id, fob_atual_usd, data_fob, observacoes
        FROM produtos_importados_fornecedores
        WHERE produto_id = ? AND fornecedor_id = ? AND ativo = 1
    """, (produto_id, fornecedor_id)).fetchone()
    conn.close()
    if row:
        return {
            "id": row[0],
            "fob_atual_usd": row[1],
            "data_fob": row[2],
            "observacoes": row[3],
        }
    return None


def desativar_oferta(oferta_id, usuario_id=None):
    """Desativa (exclui logicamente) uma oferta de produto+fornecedor.
    Nunca exclui o produto, apenas a oferta."""
    conn = get_conn()
    try:
        # Buscar dados da oferta antes de desativar
        oferta = conn.execute("""
            SELECT of.produto_id, f.nome, of.fob_atual_usd
            FROM produtos_importados_fornecedores of
            INNER JOIN fornecedores_produto f ON of.fornecedor_id = f.id
            WHERE of.id = ?
        """, (oferta_id,)).fetchone()

        if not oferta:
            conn.close()
            return False, "Oferta não encontrada."

        # Verificar se existem outras ofertas ativas para o mesmo produto
        outras_ofertas = conn.execute("""
            SELECT COUNT(*) FROM produtos_importados_fornecedores
            WHERE produto_id = ? AND ativo = 1 AND id != ?
        """, (oferta[0], oferta_id)).fetchone()[0]

        conn.execute("""
            UPDATE produtos_importados_fornecedores
            SET ativo = 0, atualizado_em = date('now')
            WHERE id = ?
        """, (oferta_id,))

        # Registrar histórico
        if usuario_id:
            conn.execute("""
                INSERT INTO produtos_importados_historico
                (produto_id, fornecedor, valor_fob_usd, data_atualizacao, usuario_id, observacao)
                VALUES (?, ?, ?, date('now'), ?, 'Oferta removida')
            """, (oferta[0], oferta[1], oferta[2], usuario_id))

        conn.commit()
        conn.close()
        return True, "Oferta removida com sucesso!"
    except Exception as e:
        conn.close()
        return False, str(e)


def atualizar_oferta(oferta_id, fob_usd, data_fob, observacoes, usuario_id=None):
    """Atualiza apenas os dados da oferta (FOB, data, observações).
    Nunca altera dados do produto."""
    conn = get_conn()
    try:
        # Buscar dados da oferta antes de atualizar
        oferta = conn.execute("""
            SELECT of.produto_id, f.nome, of.fob_atual_usd
            FROM produtos_importados_fornecedores of
            INNER JOIN fornecedores_produto f ON of.fornecedor_id = f.id
            WHERE of.id = ?
        """, (oferta_id,)).fetchone()

        if not oferta:
            conn.close()
            return False, "Oferta não encontrada."

        fob_anterior = oferta[2]

        conn.execute("""
            UPDATE produtos_importados_fornecedores
            SET fob_atual_usd = ?, data_fob = ?, observacoes = ?,
                atualizado_em = date('now')
            WHERE id = ?
        """, (fob_usd, data_fob, observacoes, oferta_id))

        # Registrar histórico
        if usuario_id:
            mensagem_hist = f"FOB atualizado de ${fob_anterior:.2f} para ${fob_usd:.2f}"
            conn.execute("""
                INSERT INTO produtos_importados_historico
                (produto_id, fornecedor, valor_fob_usd, data_atualizacao, usuario_id, observacao)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (oferta[0], oferta[1], fob_usd, data_fob, usuario_id, mensagem_hist))

        conn.commit()
        conn.close()
        return True, "Oferta atualizada com sucesso!"
    except Exception as e:
        conn.close()
        return False, str(e)


def buscar_produto_por_modelo_norm(modelo):
    """Busca produto pelo modelo normalizado."""
    conn = get_conn()
    modelo_norm = normalizar_modelo(modelo)
    row = conn.execute("""
        SELECT p.id, p.modelo, p.modelo_busca, p.descricao, p.tipo_produto_id,
               p.ncm_id, p.observacoes, tp.descricao AS tipo_produto,
               n.ncm, n.descricao AS descricao_ncm
        FROM produtos_importados p
        LEFT JOIN tipo_produto_importado tp ON p.tipo_produto_id = tp.id
        LEFT JOIN ncm_importacao n ON p.ncm_id = n.id
        WHERE p.modelo_busca = ? AND p.ativo = 1
    """, (modelo_norm,)).fetchone()
    conn.close()
    if row:
        return {
            "id": row[0],
            "modelo": row[1],
            "modelo_busca": row[2],
            "descricao": row[3],
            "tipo_produto_id": row[4],
            "ncm_id": row[5],
            "observacoes": row[6],
            "tipo_produto": row[7],
            "ncm": row[8],
            "descricao_ncm": row[9],
        }
    return None


def cadastrar_ou_atualizar_oferta(modelo, descricao, tipo_produto_id, ncm_id, fornecedor_id, fob_usd, data_fob, observacoes, usuario_id):
    """
    Cadastra ou atualiza oferta de produto+fornecedor.
    - Se o PRODUTO não existe (modelo), cria o produto e a oferta.
    - Se o PRODUTO existe, cadastra NOVA oferta se for fornecedor diferente.
    - Se PRODUTO + FORNECEDOR existem, atualiza apenas o FOB.
    """
    conn = get_conn()
    try:
        modelo_norm = normalizar_modelo(modelo)

        # 1. Buscar ou criar o PRODUTO
        produto = conn.execute("""
            SELECT id, descricao
            FROM produtos_importados
            WHERE modelo_busca = ? AND ativo = 1
        """, (modelo_norm,)).fetchone()

        if produto:
            produto_id = produto[0]
            produto_novo = False
        else:
            cursor = conn.execute("""
                INSERT INTO produtos_importados
                (modelo, modelo_busca, descricao, tipo_produto_id, ncm_id)
                VALUES (?, ?, ?, ?, ?)
            """, (modelo.strip(), modelo_norm, descricao, tipo_produto_id, ncm_id))
            produto_id = cursor.lastrowid
            produto_novo = True

        # 2. Verificar se já existe oferta para produto + fornecedor
        oferta = conn.execute("""
            SELECT id, fob_atual_usd
            FROM produtos_importados_fornecedores
            WHERE produto_id = ? AND fornecedor_id = ? AND ativo = 1
        """, (produto_id, fornecedor_id)).fetchone()

        if oferta:
            # Atualizar FOB
            oferta_id = oferta[0]
            fob_anterior = oferta[1]
            conn.execute("""
                UPDATE produtos_importados_fornecedores
                SET fob_atual_usd = ?, data_fob = ?, observacoes = ?,
                    atualizado_em = date('now')
                WHERE id = ?
            """, (fob_usd, data_fob, observacoes, oferta_id))
            mensagem = f"FOB atualizado para este fornecedor (anterior: ${fob_anterior:.2f})"
        else:
            # Criar nova oferta
            conn.execute("""
                INSERT INTO produtos_importados_fornecedores
                (produto_id, fornecedor_id, fob_atual_usd, data_fob, observacoes)
                VALUES (?, ?, ?, ?, ?)
            """, (produto_id, fornecedor_id, fob_usd, data_fob, observacoes))
            mensagem = "Nova oferta de fornecedor cadastrada!"

        # 3. Registrar histórico (com o nome do fornecedor para compatibilidade)
        fornecedor_nome = conn.execute(
            "SELECT nome FROM fornecedores_produto WHERE id = ?",
            (fornecedor_id,)
        ).fetchone()[0]

        conn.execute("""
            INSERT INTO produtos_importados_historico
            (produto_id, fornecedor, valor_fob_usd, data_atualizacao, usuario_id, observacao)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (produto_id, fornecedor_nome, fob_usd, data_fob, usuario_id,
              f"Via cadastro - {mensagem}"))

        conn.commit()
        conn.close()
        return True, mensagem, produto_id
    except Exception as e:
        conn.close()
        return False, str(e), None


# ============================================================
# FUNÇÕES DE IMPORTACAO (ATUALIZADAS)
# ============================================================

def obter_ou_criar_fornecedor(nome_fornecedor):
    """Obtém ID do fornecedor ou cria se não existir."""
    conn = get_conn()
    nome = nome_fornecedor.strip()
    if not nome:
        conn.close()
        return None
    row = conn.execute(
        "SELECT id FROM fornecedores_produto WHERE nome = ?",
        (nome,)
    ).fetchone()
    if row:
        conn.close()
        return row[0]
    conn.execute(
        "INSERT INTO fornecedores_produto (nome, ativo) VALUES (?, 1)",
        (nome,)
    )
    conn.commit()
    novo_id = conn.execute(
        "SELECT id FROM fornecedores_produto WHERE nome = ?",
        (nome,)
    ).fetchone()[0]
    conn.close()
    return novo_id


# ============================================================
# FUNÇÕES DE HISTÓRICO
# ============================================================

def carregar_historico(produto_id=None, fornecedor_nome=None, fornecedor_id=None, data_inicio=None, data_fim=None):
    """
    Carrega histórico de FOB.
    Cada fornecedor possui seu próprio histórico.
    - Se fornecedor_id for informado, busca match EXATO do nome do fornecedor.
    - Se fornecedor_nome for informado, busca LIKE.
    - Ordenação ASC para mostrar evolução temporal do FOB.
    """
    conn = get_conn()
    query = """
        SELECT h.id, p.modelo AS produto, h.fornecedor, h.valor_fob_usd,
               h.data_atualizacao, u.nome AS usuario, h.observacao
        FROM produtos_importados_historico h
        LEFT JOIN produtos_importados p ON h.produto_id = p.id
        LEFT JOIN usuarios u ON h.usuario_id = u.id
        WHERE 1=1
    """
    params = []
    if produto_id:
        query += " AND h.produto_id = ?"
        params.append(produto_id)
    if fornecedor_id:
        # Match exato pelo nome do fornecedor
        nome_forn = conn.execute(
            "SELECT nome FROM fornecedores_produto WHERE id = ?",
            (fornecedor_id,)
        ).fetchone()
        if nome_forn:
            query += " AND h.fornecedor = ?"
            params.append(nome_forn[0])
    elif fornecedor_nome:
        query += " AND h.fornecedor LIKE ?"
        params.append(f"%{fornecedor_nome}%")
    if data_inicio:
        query += " AND h.data_atualizacao >= ?"
        params.append(data_inicio)
    if data_fim:
        query += " AND h.data_atualizacao <= ?"
        params.append(data_fim)
    query += " ORDER BY h.data_atualizacao ASC LIMIT 200"
    df = pd.read_sql(query, conn, params=params)
    conn.close()
    return df


def cadastrar_ncm(ncm, descricao, tipo_produto_id):
    conn = get_conn()
    try:
        conn.execute("""
            INSERT INTO ncm_importacao (ncm, descricao, tipo_produto_id, ativo)
            VALUES (?, ?, ?, 1)
        """, (ncm, descricao, tipo_produto_id))
        conn.commit()
        conn.close()
        return True, "NCM cadastrado com sucesso!"
    except Exception as e:
        conn.close()
        return False, str(e)


# ============================================================
# FUNÇÕES DE DASHBOARD / INDICADORES
# ============================================================

def calcular_indicadores():
    """Calcula indicadores para o dashboard de inteligência de compras."""
    conn = get_conn()
    
    # Quantidade de produtos
    qtd_produtos = conn.execute(
        "SELECT COUNT(*) FROM produtos_importados WHERE ativo = 1"
    ).fetchone()[0]
    
    # Quantidade de fornecedores
    qtd_fornecedores = conn.execute(
        "SELECT COUNT(*) FROM fornecedores_produto WHERE ativo = 1"
    ).fetchone()[0]
    
    # Total de combinações Produto x Fornecedor
    total_combinacoes = conn.execute(
        "SELECT COUNT(*) FROM produtos_importados_fornecedores WHERE ativo = 1"
    ).fetchone()[0]
    
    # FOB médio
    row_fob = conn.execute("""
        SELECT AVG(fob_atual_usd) FROM produtos_importados_fornecedores
        WHERE ativo = 1 AND fob_atual_usd IS NOT NULL
    """).fetchone()
    fob_medio = row_fob[0] if row_fob and row_fob[0] else 0
    
    # Fornecedor com maior quantidade de itens
    row_top = conn.execute("""
        SELECT f.nome, COUNT(*) as qtd
        FROM produtos_importados_fornecedores of
        INNER JOIN fornecedores_produto f ON of.fornecedor_id = f.id
        WHERE of.ativo = 1 AND f.ativo = 1
        GROUP BY of.fornecedor_id
        ORDER BY qtd DESC
        LIMIT 1
    """).fetchone()
    fornecedor_top = row_top[0] if row_top else "—"
    qtd_top = row_top[1] if row_top else 0
    
    conn.close()
    
    return {
        "qtd_produtos": qtd_produtos,
        "qtd_fornecedores": qtd_fornecedores,
        "total_combinacoes": total_combinacoes,
        "fob_medio": fob_medio,
        "fornecedor_top": fornecedor_top,
        "qtd_top": qtd_top,
    }


def calcular_ranking_fornecedores():
    """Ranking completo de fornecedores com indicadores."""
    conn = get_conn()
    
    query = """
        SELECT f.id, f.nome,
               COUNT(of.id) AS qtd_produtos,
               AVG(of.fob_atual_usd) AS fob_medio,
               MIN(of.fob_atual_usd) AS menor_fob,
               MAX(of.fob_atual_usd) AS maior_fob
        FROM fornecedores_produto f
        INNER JOIN produtos_importados_fornecedores of ON of.fornecedor_id = f.id
        WHERE f.ativo = 1 AND of.ativo = 1
        GROUP BY f.id, f.nome
        ORDER BY qtd_produtos DESC
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df


def calcular_melhor_fornecedor():
    """
    Para cada produto, descobre qual fornecedor tem o menor FOB.
    Retorna contagem de vezes que cada fornecedor foi o mais barato.
    """
    conn = get_conn()
    
    query = """
        SELECT of.produto_id, of.fornecedor_id, f.nome, of.fob_atual_usd
        FROM produtos_importados_fornecedores of
        INNER JOIN fornecedores_produto f ON of.fornecedor_id = f.id
        WHERE of.ativo = 1 AND f.ativo = 1 AND of.fob_atual_usd IS NOT NULL
        ORDER BY of.produto_id, of.fob_atual_usd ASC
    """
    rows = conn.execute(query).fetchall()
    conn.close()
    
    # Para cada produto, pegar o fornecedor com menor FOB
    menores = {}
    for row in rows:
        produto_id, fornecedor_id, nome, fob = row
        if produto_id not in menores or fob < menores[produto_id]["fob"]:
            menores[produto_id] = {"fornecedor_id": fornecedor_id, "nome": nome, "fob": fob}
    
    # Contar vitórias por fornecedor
    vitorias = {}
    for info in menores.values():
        nome = info["nome"]
        vitorias[nome] = vitorias.get(nome, 0) + 1
    
    # Ordenar
    ranking = sorted(vitorias.items(), key=lambda x: x[1], reverse=True)
    return ranking


def calcular_economia_potencial():
    """
    Para cada produto, calcula a diferença entre maior e menor FOB.
    """
    conn = get_conn()
    
    query = """
        SELECT p.modelo, p.descricao,
               MIN(of.fob_atual_usd) AS menor_fob,
               MAX(of.fob_atual_usd) AS maior_fob,
               (SELECT f.nome FROM produtos_importados_fornecedores of2
                INNER JOIN fornecedores_produto f ON of2.fornecedor_id = f.id
                WHERE of2.produto_id = p.id AND of2.ativo = 1 AND f.ativo = 1
                ORDER BY of2.fob_atual_usd ASC LIMIT 1) AS fornecedor_barato,
               (SELECT f.nome FROM produtos_importados_fornecedores of2
                INNER JOIN fornecedores_produto f ON of2.fornecedor_id = f.id
                WHERE of2.produto_id = p.id AND of2.ativo = 1 AND f.ativo = 1
                ORDER BY of2.fob_atual_usd DESC LIMIT 1) AS fornecedor_caro
        FROM produtos_importados p
        INNER JOIN produtos_importados_fornecedores of ON of.produto_id = p.id
        WHERE p.ativo = 1 AND of.ativo = 1 AND of.fob_atual_usd IS NOT NULL
        GROUP BY p.id, p.modelo, p.descricao
        HAVING COUNT(of.id) > 1
        ORDER BY (MAX(of.fob_atual_usd) - MIN(of.fob_atual_usd)) DESC
        LIMIT 20
    """
    df = pd.read_sql(query, conn)
    conn.close()
    
    if not df.empty:
        df["diferenca"] = df["maior_fob"] - df["menor_fob"]
    
    return df


# ============================================================
# ABAS
# ============================================================

abas = st.tabs([
    "📊 Dashboard",
    "📦 Consulta Produtos",
    "➕ Cadastro Produto",
    "📤 Importar Planilha",
    "⚙️ Configurações",
    "📊 Histórico FOB",
])

# ============================================================
# ABA 0 - DASHBOARD / INDICADORES
# ============================================================

with abas[0]:
    st.subheader("📊 Dashboard de Inteligência de Compras")

    indicadores = calcular_indicadores()

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("📦 Produtos", indicadores["qtd_produtos"])
    with col2:
        st.metric("🏭 Fornecedores", indicadores["qtd_fornecedores"])
    with col3:
        st.metric("🔄 Combinações", indicadores["total_combinacoes"])
    with col4:
        st.metric("💰 FOB Médio", f"${indicadores['fob_medio']:.2f}")
    with col5:
        st.metric(f"🥇 {indicadores['fornecedor_top']}", f"{indicadores['qtd_top']} itens")

    st.markdown("---")

    # Ranking de fornecedores
    st.subheader("🏆 Ranking de Fornecedores")
    df_ranking = calcular_ranking_fornecedores()
    if not df_ranking.empty:
        st.dataframe(
            df_ranking,
            column_config={
                "nome": "Fornecedor",
                "qtd_produtos": st.column_config.NumberColumn("Qtd Produtos", format="%d"),
                "fob_medio": st.column_config.NumberColumn("FOB Médio", format="$ %.2f"),
                "menor_fob": st.column_config.NumberColumn("Menor FOB", format="$ %.2f"),
                "maior_fob": st.column_config.NumberColumn("Maior FOB", format="$ %.2f"),
            },
            hide_index=True,
            width="stretch",
        )
    else:
        st.info("Nenhum dado disponível para ranking.")

    st.markdown("---")

    # Melhor fornecedor (mais vezes como menor FOB)
    st.subheader("🥇 Melhor Fornecedor (Menor FOB)")
    ranking_melhor = calcular_melhor_fornecedor()
    if ranking_melhor:
        col_melhor_left, col_melhor_right = st.columns([1, 2])
        with col_melhor_left:
            for nome, qtd in ranking_melhor:
                st.markdown(f"- **{nome}**: {qtd} produtos com menor FOB")
        with col_melhor_right:
            df_melhor = pd.DataFrame(ranking_melhor, columns=["Fornecedor", "Qtd"])
            if not df_melhor.empty:
                st.bar_chart(df_melhor, x="Fornecedor", y="Qtd", width="stretch")
    else:
        st.info("Nenhum dado disponível.")

    st.markdown("---")

    # Economia potencial
    st.subheader("💰 Economia Potencial por Produto")
    df_economia = calcular_economia_potencial()
    if not df_economia.empty:
        st.dataframe(
            df_economia,
            column_config={
                "modelo": "Modelo",
                "descricao": "Descrição",
                "fornecedor_barato": "Fornecedor (Barato)",
                "menor_fob": st.column_config.NumberColumn("Menor FOB", format="$ %.2f"),
                "fornecedor_caro": "Fornecedor (Caro)",
                "maior_fob": st.column_config.NumberColumn("Maior FOB", format="$ %.2f"),
                "diferenca": st.column_config.NumberColumn("Diferença 💰", format="$ %.2f"),
            },
            hide_index=True,
            width="stretch",
        )

        economia_media = df_economia["diferenca"].mean()
        economia_total = df_economia["diferenca"].sum()

        st.success(f"📊 **Economia potencial média:** ${economia_media:.2f} por produto")
        st.metric("💰 **Economia potencial total (soma das diferenças)**", f"${economia_total:.2f}")

        # Gráfico: Produtos mais competitivos (maior diferença)
        st.markdown("### 📊 Produtos com Maior Diferença de Preço")
        df_graf_eco = df_economia.sort_values("diferenca", ascending=True).tail(10)
        st.bar_chart(
            df_graf_eco,
            x="modelo",
            y="diferenca",
            width="stretch",
        )
    else:
        st.info("⚠️ Cadastre mais de um fornecedor para o mesmo produto para gerar indicadores de economia potencial.")

    st.markdown("---")

    # Gráfico: Distribuição das ofertas por fornecedor
    st.subheader("📊 Distribuição de Ofertas por Fornecedor")
    df_ranking = calcular_ranking_fornecedores()
    if not df_ranking.empty:
        col_graf_left, col_graf_right = st.columns([1, 1])
        with col_graf_left:
            st.markdown("**Quantidade de Produtos por Fornecedor**")
            st.bar_chart(df_ranking, x="nome", y="qtd_produtos", width="stretch")
        with col_graf_right:
            st.markdown("**FOB Médio por Fornecedor**")
            df_fob_medio = df_ranking.sort_values("fob_medio")
            st.bar_chart(df_fob_medio, x="nome", y="fob_medio", width="stretch")
    else:
        st.info("Nenhum dado disponível para gráficos de fornecedores.")


# ============================================================
# ABA 1 - CONSULTA PRODUTOS
# ============================================================

with abas[1]:
    st.subheader("🔍 Consultar Produto")

    col_pesq, col_info = st.columns([3, 1])

    with col_pesq:
        termo_pesquisa = st.text_input(
            "Buscar por Modelo, Descrição ou Código",
            placeholder="Ex: OSA24RS, ENCODER, 123, A06B2467",
            key="pesquisa_produto",
            help="Busca normal e busca aproximada (ignora hífens, maiúsculas/minúsculas)",
        )

    with col_info:
        st.markdown("**🔎 Busca inteligente**")
        st.caption("Funciona mesmo com hífens, espaços ou caixa alta/baixa diferentes")
        configs_consulta = carregar_config()
        data_ultimo_dolar = configs_consulta.get("data_ultimo_dolar", "")
        if data_ultimo_dolar:
            st.caption(f"🔄 Última atualização dólar: {data_ultimo_dolar}")
        else:
            st.caption("🔄 Última atualização dólar: não registrada")

    if termo_pesquisa:
        resultados = buscar_produtos(termo_pesquisa.strip())

        if resultados.empty:
            st.warning("Produto não encontrado.")
            
            with st.expander("➕ Cadastro rápido de produto + oferta", expanded=True):
                st.caption("Preencha os dados abaixo para cadastrar um novo produto com fornecedor.")
                
                conn_rapido = get_conn()
                tipos_rapido = conn_rapido.execute(
                    "SELECT id, descricao FROM tipo_produto_importado WHERE ativo = 1 ORDER BY descricao"
                ).fetchall()
                ncms_rapido = conn_rapido.execute("""
                    SELECT n.id, n.ncm, n.descricao, n.tipo_produto_id
                    FROM ncm_importacao n WHERE n.ativo = 1 ORDER BY n.ncm
                """).fetchall()
                conn_rapido.close()
                
                tipo_opcoes_rapido = {t[1]: t[0] for t in tipos_rapido}
                ncm_opcoes_rapido = {n[1]: n[0] for n in ncms_rapido}
                df_forn_rapido = carregar_fornecedores()
                forn_opcoes_rapido = {}
                if not df_forn_rapido.empty:
                    for _, f_rap in df_forn_rapido.iterrows():
                        label_rap = f_rap['nome']
                        if f_rap.get('pais'):
                            label_rap += f" ({f_rap['pais']})"
                        forn_opcoes_rapido[label_rap] = f_rap['id']
                
                col_r1, col_r2 = st.columns(2)
                with col_r1:
                    modelo_rapido = st.text_input(
                        "Modelo",
                        value=termo_pesquisa.strip(),
                        key="modelo_rapido",
                    )
                    desc_rapido = st.text_area(
                        "Descrição Completa",
                        key="desc_rapido",
                    )
                    if not desc_rapido.strip():
                        desc_rapido = modelo_rapido
                    
                    if tipo_opcoes_rapido:
                        tipo_rapido = st.selectbox(
                            "Tipo Produto",
                            options=list(tipo_opcoes_rapido.keys()),
                            key="tipo_rapido",
                        )
                        tipo_id_rapido = tipo_opcoes_rapido[tipo_rapido]
                    else:
                        tipo_id_rapido = None
                        st.warning("Nenhum tipo de produto cadastrado.")
                
                with col_r2:
                    if ncm_opcoes_rapido:
                        ncm_rapido = st.selectbox(
                            "NCM (opcional)",
                            options=[""] + list(ncm_opcoes_rapido.keys()),
                            key="ncm_rapido",
                        )
                        ncm_id_rapido = ncm_opcoes_rapido.get(ncm_rapido) if ncm_rapido else None
                    else:
                        ncm_id_rapido = None
                        st.info("Nenhum NCM cadastrado.")
                    
                    if forn_opcoes_rapido:
                        forn_rapido = st.selectbox(
                            "Fornecedor *",
                            options=list(forn_opcoes_rapido.keys()),
                            key="forn_rapido",
                        )
                        forn_id_rapido = forn_opcoes_rapido[forn_rapido]
                    else:
                        forn_id_rapido = None
                        st.warning("Nenhum fornecedor cadastrado.")
                    
                    fob_rapido = st.number_input(
                        "FOB USD *",
                        min_value=0.0,
                        step=10.0,
                        format="%.2f",
                        key="fob_rapido",
                    )
                    data_rapido = st.date_input(
                        "Data FOB",
                        value=date.today(),
                        key="data_rapido",
                    )
                    obs_rapido = st.text_area(
                        "Observações",
                        key="obs_rapido",
                    )
                
                usuario_id_rapido = st.session_state.get("usuario_id", 1)
                
                if st.button("💾 Salvar Produto + Oferta", type="primary", width="stretch", key="btn_salvar_rapido"):
                    if not modelo_rapido:
                        st.error("Modelo é obrigatório.")
                    elif not forn_id_rapido:
                        st.error("Fornecedor é obrigatório.")
                    elif fob_rapido <= 0:
                        st.error("FOB USD deve ser maior que zero.")
                    else:
                        desc_final = desc_rapido.strip() if desc_rapido.strip() else modelo_rapido.strip()
                        sucesso, msg, _ = cadastrar_ou_atualizar_oferta(
                            modelo_rapido.strip(),
                            desc_final,
                            tipo_id_rapido,
                            ncm_id_rapido,
                            forn_id_rapido,
                            fob_rapido,
                            data_rapido.isoformat(),
                            obs_rapido.strip() if obs_rapido else "",
                            usuario_id_rapido,
                        )
                        if sucesso:
                            st.success(msg)
                            st.balloons()
                            st.rerun()
                        else:
                            st.error(f"Erro: {msg}")
        else:
            for _, row in resultados.iterrows():
                with st.container():
                    st.markdown("---")
                    col1, col2 = st.columns([2, 1])

                    with col1:
                        st.markdown(f"### {row['modelo']}")
                        st.markdown(f"**Descrição:** {row['descricao']}")

                        ncm_str = row['ncm'] if row['ncm'] else "—"
                        ncm_desc = row['descricao_ncm'] if row['descricao_ncm'] else ""
                        ncm_full = f"{ncm_str} — {ncm_desc}" if ncm_desc else ncm_str
                        st.markdown(f"**NCM:** {ncm_full}")
                        st.markdown(f"**Tipo Produto:** {row['tipo_produto']}")

                    with col2:
                        configs = carregar_config()
                        dolar = float(configs.get("dolar_atual", 5.80))
                        frete_rateado = float(configs.get("rateio_frete_usd", 50.0))
                        despesas_aduaneiras = float(configs.get("despesas_aduaneiras_brl", 200.0))
                        markup_padrao = float(configs.get("markup_padrao", 2.0))

                        conn = get_conn()
                        tipo = conn.execute(
                            "SELECT * FROM tipo_produto_importado WHERE id = ?",
                            (row["tipo_produto_id"],)
                        ).fetchone()
                        conn.close()

                        if tipo:
                            ii_pct = tipo[2]
                            ipi_pct = tipo[3]
                            pis_pct = tipo[4]
                            cofins_pct = tipo[5]
                            icms_pct = tipo[6]
                        else:
                            ii_pct = ipi_pct = pis_pct = cofins_pct = icms_pct = 0

                        # Usar o menor FOB para o cálculo de nacionalização
                        ofertas_prod = buscar_ofertas_por_produto(row['id'])
                        if not ofertas_prod.empty:
                            menor_fob = ofertas_prod['fob_atual_usd'].min()
                        else:
                            menor_fob = 0

                        calculo = calcular_nacionalizacao(
                            menor_fob,
                            frete_rateado,
                            dolar,
                            ii_pct, ipi_pct, pis_pct, cofins_pct, icms_pct,
                            despesas_aduaneiras,
                        )

                        st.markdown("#### 📐 Nacionalização (menor FOB)")
                        st.metric(
                            "✅ Valor Nacionalizado Final",
                            f"R$ {calculo['valor_nacionalizado']:.2f}",
                        )

                        st.markdown("#### 🎯 Markup Personalizado")
                        mk_personalizado = st.number_input(
                            "Markup",
                            min_value=1.0,
                            max_value=10.0,
                            value=float(markup_padrao),
                            step=0.05,
                            format="%.2f",
                            key=f"mk_{row['id']}",
                        )
                        preco_personalizado = calculo["valor_nacionalizado"] * mk_personalizado
                        st.metric(
                            f"Preço Venda (x{mk_personalizado})",
                            f"R$ {preco_personalizado:.2f}",
                        )

                    # ── Tabela de Fornecedores ──
                    st.markdown("#### 🏭 Fornecedores Disponíveis")
                    ofertas = buscar_ofertas_por_produto(row['id'])

                    if not ofertas.empty:
                        # Destacar menor FOB
                        menor_fob_val = ofertas['fob_atual_usd'].min()

                        # Cabeçalho da tabela
                        col_f1, col_f2, col_f3, col_f4, col_f5, col_f6 = st.columns([2, 1, 1, 2, 0.5, 1])
                        with col_f1:
                            st.markdown("**Fornecedor**")
                        with col_f2:
                            st.markdown("**FOB USD**")
                        with col_f3:
                            st.markdown("**Data**")
                        with col_f4:
                            st.markdown("**Observações**")
                        with col_f6:
                            st.markdown("**Ações**")

                        st.divider()

                        usuario_id = st.session_state.get("usuario_id", 1)

                        for _, of in ofertas.iterrows():
                            col_f1, col_f2, col_f3, col_f4, col_f5, col_f6 = st.columns([2, 1, 1, 2, 0.5, 1])

                            with col_f1:
                                nome_forn = of['fornecedor']
                                if of['fob_atual_usd'] == menor_fob_val:
                                    st.markdown(f"🏆 **{nome_forn}**")
                                else:
                                    st.markdown(nome_forn)

                            with col_f2:
                                st.markdown(f"**${of['fob_atual_usd']:.2f}**")

                            with col_f3:
                                st.markdown(of['data_fob'] if of['data_fob'] else "—")

                            with col_f4:
                                st.markdown(of['observacoes'] if of['observacoes'] else "")

                            with col_f5:
                                if of['fob_atual_usd'] == menor_fob_val:
                                    st.markdown("🏆")

                            with col_f6:
                                # Botão Editar
                                editar_key = f"editar_{of['oferta_id']}"
                                if st.button("✏️", key=editar_key, help="Editar oferta"):
                                    st.session_state["editar_oferta_id"] = of['oferta_id']
                                    st.session_state["editar_oferta_fornecedor"] = of['fornecedor']
                                    st.session_state["editar_oferta_fob"] = float(of['fob_atual_usd'])
                                    st.session_state["editar_oferta_data"] = of['data_fob'] if of['data_fob'] else date.today().isoformat()
                                    st.session_state["editar_oferta_obs"] = of['observacoes'] if of['observacoes'] else ""
                                    st.rerun()

                                # Botão Excluir
                                excluir_key = f"excluir_{of['oferta_id']}"
                                if st.button("🗑️", key=excluir_key, help="Remover oferta"):
                                    sucesso, msg = desativar_oferta(of['oferta_id'], usuario_id)
                                    if sucesso:
                                        st.success(msg)
                                        st.rerun()
                                    else:
                                        st.error(msg)

                        st.divider()

                        # Modal de edição de oferta
                        if "editar_oferta_id" in st.session_state:
                            oferta_id_edit = st.session_state["editar_oferta_id"]
                            st.markdown("---")
                            st.markdown(f"### ✏️ Editar Oferta: {st.session_state['editar_oferta_fornecedor']}")
                            st.caption("Apenas dados da oferta (FOB, data, observações) — dados do produto não são alterados.")

                            col_ed1, col_ed2 = st.columns(2)
                            with col_ed1:
                                novo_fob = st.number_input(
                                    "FOB USD",
                                    min_value=0.0,
                                    step=10.0,
                                    format="%.2f",
                                    value=st.session_state["editar_oferta_fob"],
                                    key="editar_fob_input",
                                )
                            with col_ed2:
                                nova_data = st.date_input(
                                    "Data Atualização",
                                    value=date.fromisoformat(st.session_state["editar_oferta_data"]) if st.session_state["editar_oferta_data"] else date.today(),
                                    key="editar_data_input",
                                )

                            nova_obs = st.text_area(
                                "Observações",
                                value=st.session_state["editar_oferta_obs"],
                                key="editar_obs_input",
                            )

                            col_btn1, col_btn2 = st.columns(2)
                            with col_btn1:
                                if st.button("💾 Salvar Edição", type="primary", width="stretch"):
                                    sucesso, msg = atualizar_oferta(
                                        oferta_id_edit,
                                        novo_fob,
                                        nova_data.isoformat(),
                                        nova_obs.strip() if nova_obs else "",
                                        usuario_id,
                                    )
                                    if sucesso:
                                        st.success(msg)
                                        del st.session_state["editar_oferta_id"]
                                        del st.session_state["editar_oferta_fornecedor"]
                                        del st.session_state["editar_oferta_fob"]
                                        del st.session_state["editar_oferta_data"]
                                        del st.session_state["editar_oferta_obs"]
                                        st.rerun()
                                    else:
                                        st.error(msg)
                            with col_btn2:
                                if st.button("❌ Cancelar", width="stretch"):
                                    del st.session_state["editar_oferta_id"]
                                    del st.session_state["editar_oferta_fornecedor"]
                                    del st.session_state["editar_oferta_fob"]
                                    del st.session_state["editar_oferta_data"]
                                    del st.session_state["editar_oferta_obs"]
                                    st.rerun()

                    else:
                        st.info("Nenhum fornecedor cadastrado para este produto.")


# ============================================================
# ABA 2 - CADASTRO PRODUTO (BUSCA INTELIGENTE)
# ============================================================

with abas[2]:
    st.subheader("➕ Cadastro de Produto / Oferta de Fornecedor")
    st.caption("Digite parte do modelo. O sistema sugere produtos existentes automaticamente.")

    # ── Carregar dados de apoio ──
    conn = get_conn()
    tipos = conn.execute(
        "SELECT id, descricao FROM tipo_produto_importado WHERE ativo = 1 ORDER BY descricao"
    ).fetchall()
    ncms_com_tipo = conn.execute("""
        SELECT n.id, n.ncm, n.descricao, n.tipo_produto_id
        FROM ncm_importacao n WHERE n.ativo = 1 ORDER BY n.ncm
    """).fetchall()
    conn.close()

    tipo_opcoes = {t[1]: t[0] for t in tipos}
    ncm_opcoes = {n[1]: n[0] for n in ncms_com_tipo}

    # ── Fornecedores (SELECTBOX) ──
    df_fornecedores = carregar_fornecedores()
    fornecedor_opcoes = {}
    if not df_fornecedores.empty:
        for _, f in df_fornecedores.iterrows():
            label = f['nome']
            if f.get('pais'):
                label += f" ({f['pais']})"
            fornecedor_opcoes[label] = f['id']

    # ── Inicializar session_state ──
    if "produto_selecionado_cadastro" not in st.session_state:
        st.session_state["produto_selecionado_cadastro"] = None
    if "ncm_automatico_id" not in st.session_state:
        st.session_state["ncm_automatico_id"] = None
    if "ncm_automatico_label" not in st.session_state:
        st.session_state["ncm_automatico_label"] = None
    if "sugestoes_produtos" not in st.session_state:
        st.session_state["sugestoes_produtos"] = []
    if "modelo_digitado" not in st.session_state:
        st.session_state["modelo_digitado"] = ""

    col1, col2 = st.columns(2)

    with col1:
        modelo_input = st.text_input(
            "Modelo *",
            placeholder="Digite parte do modelo — ex: OSA24, A06B, ENCODER",
            key="modelo_cadastro",
            help="Digite ao menos 2 caracteres. O sistema busca produtos semelhantes automaticamente.",
        )

        # ── Busca inteligente enquanto digita ──
        if modelo_input and modelo_input.strip() != st.session_state.get("modelo_digitado_anterior", ""):
            st.session_state["modelo_digitado_anterior"] = modelo_input.strip()
            st.session_state["produto_selecionado_cadastro"] = None
            st.session_state["sugestoes_produtos"] = sugerir_produtos(modelo_input.strip())

        # ── Exibir sugestões ──
        sugestoes = st.session_state.get("sugestoes_produtos", [])
        if sugestoes:
            opcoes_lista = [f"{s['modelo']} — {s['descricao'][:60]}" for s in sugestoes]
            opcoes_lista.insert(0, "➕ Nenhum — Cadastrar Novo Produto")
            selecao_idx = st.selectbox(
                "🔎 Produtos encontrados (selecione um)",
                options=range(len(opcoes_lista)),
                format_func=lambda i: opcoes_lista[i],
                key="sugestao_select",
                help="Selecione um produto existente ou a opção 'Cadastrar Novo'",
            )
            if selecao_idx > 0:
                sel = sugestoes[selecao_idx - 1]
                if st.session_state.get("produto_selecionado_cadastro") != sel["id"]:
                    # Carregar dados completos do produto selecionado
                    produto_info = buscar_produto_por_modelo_norm(sel["modelo"])
                    st.session_state["produto_selecionado_cadastro"] = sel["id"]
                    st.session_state["produto_info_cadastro"] = produto_info
                    st.rerun()
            else:
                if st.session_state.get("produto_selecionado_cadastro") is not None:
                    st.session_state["produto_selecionado_cadastro"] = None
                    st.session_state["produto_info_cadastro"] = None
        elif modelo_input and len(modelo_input.strip()) >= 2:
            st.caption("🔵 Produto novo — nenhum produto semelhante encontrado")

        # ── Produto selecionado ou novo ──
        produto_info = st.session_state.get("produto_info_cadastro")

        if produto_info:
            st.success(f"🟢 Produto existente localizado: **{produto_info['modelo']}**")
            with st.expander("📋 Dados atuais do produto", expanded=True):
                st.markdown(f"**Descrição:** {produto_info['descricao']}")
                st.markdown(f"**Tipo Produto:** {produto_info['tipo_produto']}")
                if produto_info.get('ncm'):
                    st.markdown(f"**NCM:** {produto_info['ncm']} — {produto_info['descricao_ncm']}")
                else:
                    st.markdown("**NCM:** —")

                # Mostrar fornecedores atuais
                ofertas_existentes = buscar_ofertas_por_produto(produto_info['id'])
                if not ofertas_existentes.empty:
                    st.markdown("**Fornecedores atuais:**")
                    for _, of in ofertas_existentes.iterrows():
                        st.markdown(
                            f"- {of['fornecedor']}: **${of['fob_atual_usd']:.2f}** "
                            f"(atualizado em {of['data_fob']})"
                        )

            # Dados do produto em modo leitura
            st.info("ℹ️ Produto já cadastrado. Apenas a oferta do fornecedor será registrada. Dados do produto não são alterados.")

            st.text_input(
                "Descrição Completa",
                value=produto_info["descricao"],
                disabled=True,
                key="desc_existente",
            )
            st.text_input(
                "Tipo Produto",
                value=produto_info["tipo_produto"],
                disabled=True,
                key="tipo_existente",
            )
            ncm_exib = f"{produto_info['ncm']} — {produto_info['descricao_ncm']}" if produto_info.get('ncm') else "—"
            st.text_input(
                "NCM",
                value=ncm_exib,
                disabled=True,
                key="ncm_existente",
            )

            tipo_produto_id = produto_info["tipo_produto_id"]
            ncm_id_usar = produto_info["ncm_id"]

        else:
            # ── Produto NOVO ──
            if modelo_input and len(modelo_input.strip()) >= 2:
                st.info("🔵 Produto novo — preencha os dados abaixo")

            descricao = st.text_area(
                "Descrição Completa",
                placeholder="Descrição do produto",
                value="",
                key="desc_novo",
            )

            # ── Tipo Produto ──
            tipo_index = 0
            tipo_selecionado = st.selectbox(
                "Tipo Produto *",
                options=list(tipo_opcoes.keys()),
                index=tipo_index,
                key="tipo_cadastro",
            )
            tipo_produto_id = tipo_opcoes[tipo_selecionado]

            # ── NCM automático ──
            ncm_auto = buscar_ncm_por_tipo_produto(tipo_produto_id)

            if ncm_auto:
                ncm_label = f"{ncm_auto['ncm']} — {ncm_auto['descricao']}"
                st.session_state["ncm_automatico_id"] = ncm_auto["id"]
                st.session_state["ncm_automatico_label"] = ncm_label
            else:
                st.session_state["ncm_automatico_id"] = None
                st.session_state["ncm_automatico_label"] = "Nenhum NCM vinculado"

            if ncm_auto:
                st.text_input(
                    "NCM (automático)",
                    value=ncm_label,
                    disabled=True,
                    key="ncm_auto_exibicao",
                    help="NCM definido automaticamente pelo Tipo de Produto",
                )
                st.caption("✅ NCM preenchido automaticamente")
                ncm_id_usar = ncm_auto["id"]
            else:
                st.warning("⚠️ Nenhum NCM vinculado a este Tipo de Produto")
                ncm_id_usar = None

            # Variável descricao precisa existir para salvar
            if not descricao.strip():
                descricao = modelo_input

        # ── Fornecedor como SELECTBOX ──
        if fornecedor_opcoes:
            fornecedor_selecionado = st.selectbox(
                "Fornecedor *",
                options=list(fornecedor_opcoes.keys()),
                key="fornecedor_cadastro",
                help="Selecione o fornecedor. Para cadastrar novos, vá em Configurações.",
            )
            fornecedor_id = fornecedor_opcoes[fornecedor_selecionado]
        else:
            st.warning("⚠️ Nenhum fornecedor cadastrado. Vá em Configurações > Cadastro de Fornecedores.")
            fornecedor_id = st.number_input("ID do Fornecedor (informe 0 se não houver)", min_value=0, value=0)
            if fornecedor_id == 0:
                fornecedor_id = None

    with col2:
        fob_usd = st.number_input(
            "FOB USD *",
            min_value=0.0,
            step=10.0,
            format="%.2f",
            value=0.0,
        )
        data_fob = st.date_input("Data Atualização FOB", value=date.today())
        observacoes = st.text_area(
            "Observações",
            placeholder="Observações adicionais sobre esta oferta",
        )

    usuario_id = st.session_state.get("usuario_id", 1)

    # ── Definir descricao correta para salvar ──
    if produto_info:
        descricao_salvar = produto_info["descricao"]
        modelo_salvar = produto_info["modelo"]
    else:
        descricao_salvar = descricao.strip() if descricao.strip() else modelo_input.strip()
        modelo_salvar = modelo_input.strip()

    # ── Botão de salvar ──
    if st.button("💾 Salvar Produto / Oferta", type="primary", width="stretch"):
        if not modelo_salvar:
            st.error("Modelo é obrigatório.")
        elif fob_usd <= 0:
            st.error("FOB USD deve ser maior que zero.")
        elif not fornecedor_id:
            st.error("Selecione um fornecedor válido.")
        else:
            sucesso, msg, _ = cadastrar_ou_atualizar_oferta(
                modelo_salvar,
                descricao_salvar,
                tipo_produto_id,
                ncm_id_usar,
                fornecedor_id,
                fob_usd,
                data_fob.isoformat(),
                observacoes.strip() if observacoes else "",
                usuario_id,
            )
            if sucesso:
                st.success(msg)
                st.balloons()
                for key in ["modelo_cadastro", "produto_info_cadastro", "produto_selecionado_cadastro",
                            "ncm_automatico_id", "ncm_automatico_label", "sugestoes_produtos",
                            "modelo_digitado_anterior"]:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
            else:
                st.error(f"Erro: {msg}")


# ============================================================
# ABA 3 - IMPORTAR PLANILHA FORNECEDOR
# ============================================================

with abas[3]:
    st.subheader("📤 Importar Planilha de Fornecedor")

    st.markdown("""
    Faça upload da planilha XLSX contendo:
    - **Coluna A**: Modelo do produto
    - **Coluna C**: FOB USD
    - **Coluna E**: NCM

    Regras:
    - Se **Modelo + Fornecedor** já existirem → Atualiza FOB
    - Se apenas **Modelo** existir, mas fornecedor for diferente → Cria novo registro
    - Se **Modelo** não existir → Cria produto + oferta
    
    ⚠️ O nome do fornecedor virá de um campo extra na planilha ou será solicitado.
    """)

    # Selecionar fornecedor para a importação
    df_forn_imp = carregar_fornecedores()
    forn_imp_opcoes = {}
    if not df_forn_imp.empty:
        for _, f in df_forn_imp.iterrows():
            label = f['nome']
            if f.get('pais'):
                label += f" ({f['pais']})"
            forn_imp_opcoes[label] = f['id']

    if forn_imp_opcoes:
        fornecedor_importacao = st.selectbox(
            "Fornecedor da planilha",
            options=list(forn_imp_opcoes.keys()),
            key="forn_import",
            help="Selecione o fornecedor ao qual esta planilha pertence",
        )
        fornecedor_imp_id = forn_imp_opcoes[fornecedor_importacao]
    else:
        st.warning("⚠️ Cadastre fornecedores antes de importar.")
        fornecedor_imp_id = None

    arquivo = st.file_uploader(
        "Selecionar arquivo XLSX",
        type=["xlsx"],
        key="upload_planilha",
    )

    if arquivo and fornecedor_imp_id:
        try:
            wb = openpyxl.load_workbook(arquivo, data_only=True)
            ws = wb.active

            linhas_ignoradas = 0
            linhas_sem_modelo = 0
            linhas_sem_fob = 0
            produtos_importar = []

            PALAVRAS_IGNORAR = [
                "freight", "ettori", "dolar hoje", "dólar hoje",
                "total", "subtotal", "frete",
            ]

            for row in ws.iter_rows(min_row=2, values_only=True):
                modelo = str(row[0]).strip() if row[0] else ""
                fob_valor = row[2] if len(row) > 2 else None
                ncm_valor = str(row[4]).strip() if len(row) > 4 and row[4] else ""

                if not modelo:
                    linhas_sem_modelo += 1
                    continue

                if any(palavra in modelo.lower() for palavra in PALAVRAS_IGNORAR):
                    linhas_ignoradas += 1
                    continue

                if not fob_valor or str(fob_valor).strip() == "":
                    linhas_sem_fob += 1
                    continue

                try:
                    fob = float(fob_valor)
                except (ValueError, TypeError):
                    linhas_sem_fob += 1
                    continue

                produtos_importar.append({
                    "modelo": modelo,
                    "fob_usd": fob,
                    "ncm": ncm_valor,
                })

            wb.close()

            if not produtos_importar:
                st.warning("Nenhum produto encontrado para importar.")
            else:
                conn = get_conn()

                dados_exibicao = []
                ncms_nao_cadastrados = set()
                qtd_novos = 0
                qtd_atualizar = 0
                qtd_novos_prod = 0

                # Buscar nome do fornecedor
                forn_nome = conn.execute(
                    "SELECT nome FROM fornecedores_produto WHERE id = ?",
                    (fornecedor_imp_id,)
                ).fetchone()[0]

                for p in produtos_importar:
                    modelo_norm = normalizar_modelo(p["modelo"])

                    # Verificar NCM
                    ncm_info = None
                    if p["ncm"]:
                        ncm_info = conn.execute(
                            "SELECT id, descricao FROM ncm_importacao WHERE ncm = ? AND ativo = 1",
                            (p["ncm"],)
                        ).fetchone()
                        if not ncm_info:
                            ncms_nao_cadastrados.add(p["ncm"])

                    # Verificar se produto existe
                    produto_existente = conn.execute(
                        "SELECT id FROM produtos_importados WHERE modelo_busca = ? AND ativo = 1",
                        (modelo_norm,)
                    ).fetchone()

                    if produto_existente:
                        produto_id = produto_existente[0]
                        # Verificar se já existe oferta para este produto+fornecedor
                        oferta_existente = conn.execute("""
                            SELECT id, fob_atual_usd FROM produtos_importados_fornecedores
                            WHERE produto_id = ? AND fornecedor_id = ? AND ativo = 1
                        """, (produto_id, fornecedor_imp_id)).fetchone()

                        if oferta_existente:
                            status = "ATUALIZAR FOB"
                            qtd_atualizar += 1
                            fob_anterior = oferta_existente[1]
                        else:
                            status = "NOVO FORNECEDOR"
                            qtd_novos += 1
                            fob_anterior = 0
                    else:
                        status = "NOVO PRODUTO"
                        qtd_novos_prod += 1
                        produto_id = None
                        fob_anterior = 0

                    dados_exibicao.append({
                        "modelo": p["modelo"],
                        "fob_novo": p["fob_usd"],
                        "fob_anterior": fob_anterior,
                        "ncm": p["ncm"],
                        "ncm_cadastrado": "✅" if ncm_info else "❌",
                        "ncm_invalido": ncm_info is None,
                        "status": status,
                        "produto_id": produto_id,
                        "ncm_id": ncm_info[0] if ncm_info else None,
                    })

                conn.close()

                st.success(f"""
                **Resumo da planilha ({forn_nome}):**
                - Produtos a importar: **{len(produtos_importar)}**
                - 🆕 **Novos produtos:** {qtd_novos_prod}
                - ➕ **Novos fornecedores:** {qtd_novos}
                - 🔄 **Atualizar FOB:** {qtd_atualizar}
                - ❌ **NCM não cadastrado:** {len(ncms_nao_cadastrados)}
                - Linhas ignoradas: {linhas_ignoradas + linhas_sem_modelo + linhas_sem_fob}
                """)

                df_previa = pd.DataFrame(dados_exibicao)

                st.markdown("### 📋 Prévia dos Dados")
                st.dataframe(
                    df_previa[["modelo", "fob_anterior", "fob_novo", "ncm", "ncm_cadastrado", "status"]],
                    column_config={
                        "modelo": "Modelo",
                        "fob_anterior": st.column_config.NumberColumn("FOB Anterior", format="$ %.2f"),
                        "fob_novo": st.column_config.NumberColumn("FOB Novo", format="$ %.2f"),
                        "ncm": "NCM",
                        "ncm_cadastrado": "NCM OK?",
                        "status": "Status",
                    },
                    hide_index=True,
                    width="stretch",
                )

                # NCMs não cadastrados
                if ncms_nao_cadastrados:
                    st.markdown("### ⚠️ NCMs Não Cadastrados")
                    st.warning(f"{len(ncms_nao_cadastrados)} NCM(s) não encontrado(s).")

                    conn = get_conn()
                    tipos = conn.execute(
                        "SELECT id, descricao FROM tipo_produto_importado WHERE ativo = 1 ORDER BY descricao"
                    ).fetchall()
                    conn.close()
                    tipo_opcoes_ncm = {t[1]: t[0] for t in tipos}

                    for ncm_novo in sorted(ncms_nao_cadastrados):
                        with st.expander(f"NCM {ncm_novo}"):
                            st.markdown(f"**NCM:** {ncm_novo}")
                            qtd = sum(1 for p in dados_exibicao if p["ncm"] == ncm_novo)
                            st.markdown(f"**Produtos com este NCM:** {qtd}")
                            desc_ncm = st.text_input(
                                f"Descrição para NCM {ncm_novo}",
                                key=f"desc_{ncm_novo}",
                            )
                            tipo_ncm = st.selectbox(
                                f"Tipo Produto para NCM {ncm_novo}",
                                options=list(tipo_opcoes_ncm.keys()),
                                key=f"tipo_{ncm_novo}",
                            )
                            if st.button(f"Cadastrar NCM {ncm_novo}", key=f"btn_{ncm_novo}"):
                                if desc_ncm and tipo_ncm:
                                    sucesso, msg = cadastrar_ncm(
                                        ncm_novo,
                                        desc_ncm.strip(),
                                        tipo_opcoes_ncm[tipo_ncm],
                                    )
                                    if sucesso:
                                        st.success(f"NCM {ncm_novo} cadastrado!")
                                        st.rerun()
                                    else:
                                        st.error(f"Erro: {msg}")
                                else:
                                    st.error("Preencha descrição e tipo do produto.")

                # Botão de importação
                if st.button(
                    "🚀 Executar Importação",
                    type="primary",
                    width="stretch",
                    disabled=len(ncms_nao_cadastrados) > 0,
                ):
                    conn = get_conn()
                    importados = 0
                    atualizados = 0
                    erros = 0

                    for item in dados_exibicao:
                        try:
                            modelo_norm = normalizar_modelo(item["modelo"])

                            if item["status"] == "NOVO PRODUTO":
                                # Criar produto
                                ncm_id = item["ncm_id"]
                                tipo_produto_id = None
                                if ncm_id:
                                    ncm_info = conn.execute(
                                        "SELECT tipo_produto_id FROM ncm_importacao WHERE id = ?",
                                        (ncm_id,)
                                    ).fetchone()
                                    if ncm_info:
                                        tipo_produto_id = ncm_info[0]

                                conn.execute("""
                                    INSERT INTO produtos_importados
                                    (modelo, modelo_busca, descricao, tipo_produto_id, ncm_id)
                                    VALUES (?, ?, ?, ?, ?)
                                """, (item["modelo"], modelo_norm, item["modelo"],
                                      tipo_produto_id, ncm_id))

                                produto_id = conn.execute(
                                    "SELECT id FROM produtos_importados WHERE modelo = ?",
                                    (item["modelo"],)
                                ).fetchone()[0]

                                # Criar oferta
                                conn.execute("""
                                    INSERT INTO produtos_importados_fornecedores
                                    (produto_id, fornecedor_id, fob_atual_usd, data_fob, observacoes)
                                    VALUES (?, ?, ?, date('now'), 'Importado via planilha')
                                """, (produto_id, fornecedor_imp_id, item["fob_novo"]))

                                conn.execute("""
                                    INSERT INTO produtos_importados_historico
                                    (produto_id, fornecedor, valor_fob_usd, data_atualizacao, usuario_id, observacao)
                                    VALUES (?, ?, ?, date('now'), ?, 'Importação via planilha XLSX')
                                """, (produto_id, forn_nome, item["fob_novo"], usuario_id))

                                importados += 1

                            elif item["status"] == "NOVO FORNECEDOR":
                                # Criar oferta para produto existente
                                conn.execute("""
                                    INSERT INTO produtos_importados_fornecedores
                                    (produto_id, fornecedor_id, fob_atual_usd, data_fob, observacoes)
                                    VALUES (?, ?, ?, date('now'), 'Importado via planilha')
                                """, (item["produto_id"], fornecedor_imp_id, item["fob_novo"]))

                                conn.execute("""
                                    INSERT INTO produtos_importados_historico
                                    (produto_id, fornecedor, valor_fob_usd, data_atualizacao, usuario_id, observacao)
                                    VALUES (?, ?, ?, date('now'), ?, 'Novo fornecedor via planilha')
                                """, (item["produto_id"], forn_nome, item["fob_novo"], usuario_id))

                                atualizados += 1

                            else:
                                # ATUALIZAR FOB - produto+fornecedor existe
                                fob_anterior_val = item["fob_anterior"]

                                conn.execute("""
                                    UPDATE produtos_importados_fornecedores
                                    SET fob_atual_usd = ?, data_fob = date('now'),
                                        atualizado_em = date('now')
                                    WHERE produto_id = ? AND fornecedor_id = ?
                                """, (item["fob_novo"], item["produto_id"], fornecedor_imp_id))

                                if item["ncm_id"]:
                                    conn.execute("""
                                        UPDATE produtos_importados
                                        SET ncm_id = COALESCE(?, ncm_id)
                                        WHERE id = ?
                                    """, (item["ncm_id"], item["produto_id"]))

                                conn.execute("""
                                    INSERT INTO produtos_importados_historico
                                    (produto_id, fornecedor, valor_fob_usd, data_atualizacao, usuario_id, observacao)
                                    VALUES (?, ?, ?, date('now'), ?, ?)
                                """, (
                                    item["produto_id"], forn_nome, item["fob_novo"],
                                    usuario_id,
                                    f"Atualização via Importação XLSX (FOB anterior: ${fob_anterior_val:.2f})"
                                ))

                                atualizados += 1

                        except Exception as e:
                            erros += 1
                            st.error(f"Erro no produto {item['modelo']}: {str(e)}")

                    conn.commit()
                    conn.close()

                    st.success(f"""
                    ✅ **Importação concluída!**
                    - 🆕 Produtos novos: {importados}
                    - ➕ Novos fornecedores: {qtd_novos}
                    - 🔄 FOBs atualizados: {atualizados}
                    - ❌ Erros: {erros}
                    """)
                    st.balloons()

        except Exception as e:
            st.error(f"Erro ao processar planilha: {str(e)}")


# ============================================================
# ABA 4 - CONFIGURAÇÕES
# ============================================================

with abas[4]:
    st.subheader("⚙️ Configurações Globais de Importação")

    configs = carregar_config()

    col1, col2 = st.columns(2)

    with col1:
        dolar_atual = st.number_input(
            "Cotação Dólar (R$)",
            min_value=0.0,
            value=float(configs.get("dolar_atual", 5.80)),
            step=0.01,
            format="%.2f",
            key="cfg_dolar",
            help="Cotação atual do dólar para cálculos de nacionalização",
        )
        data_ultimo_dolar_config = configs.get("data_ultimo_dolar", "")
        if data_ultimo_dolar_config:
            st.caption(f"🔄 Última atualização: {data_ultimo_dolar_config}")
        else:
            st.caption("🔄 Última atualização: nunca registrada")

        rateio_frete = st.number_input(
            "Frete Rateado Padrão (USD)",
            min_value=0.0,
            value=float(configs.get("rateio_frete_usd", 50.0)),
            step=1.0,
            format="%.2f",
            key="cfg_frete",
        )

    with col2:
        despesas_aduaneiras = st.number_input(
            "Despesas Aduaneiras Padrão (R$)",
            min_value=0.0,
            value=float(configs.get("despesas_aduaneiras_brl", 200.0)),
            step=10.0,
            format="%.2f",
            key="cfg_desp_adu",
        )
        markup_padrao = st.number_input(
            "Markup Padrão",
            min_value=1.0,
            value=float(configs.get("markup_padrao", 2.0)),
            step=0.1,
            format="%.2f",
            key="cfg_markup",
        )

    if st.button("💾 Salvar Configurações", type="primary", width="stretch"):
        salvar_config("dolar_atual", dolar_atual)
        salvar_config("data_ultimo_dolar", date.today().isoformat())
        salvar_config("rateio_frete_usd", rateio_frete)
        salvar_config("despesas_aduaneiras_brl", despesas_aduaneiras)
        salvar_config("markup_padrao", markup_padrao)
        st.success("Configurações salvas com sucesso!")
        st.rerun()

    st.markdown("---")
    st.subheader("📋 Configuração Tributária por Tipo de Produto")

    df_tipos = carregar_tipos_produto()

    if not df_tipos.empty:
        edited_df = st.data_editor(
            df_tipos[["id", "descricao", "ii", "ipi", "pis", "cofins", "icms"]],
            column_config={
                "id": "ID",
                "descricao": "Tipo Produto",
            "ii": st.column_config.NumberColumn("II (%)", min_value=0.0, max_value=100.0, step=0.01, format="%.2f"),
                "ipi": st.column_config.NumberColumn("IPI (%)", min_value=0.0, max_value=100.0, step=0.01, format="%.2f"),
                "pis": st.column_config.NumberColumn("PIS (%)", min_value=0.0, max_value=100.0, step=0.01, format="%.2f"),
                "cofins": st.column_config.NumberColumn("COFINS (%)", min_value=0.0, max_value=100.0, step=0.01, format="%.2f"),
                "icms": st.column_config.NumberColumn("ICMS (%)", min_value=0.0, max_value=100.0, step=0.01, format="%.2f"),
            },
            hide_index=True,
            width="stretch",
            num_rows="fixed",
            key="editor_tributos",
        )

        if st.button("💾 Salvar Tributos", type="primary", width="stretch"):
            for _, row in edited_df.iterrows():
                salvar_tipo_produto(
                    int(row["id"]),
                    float(row["ii"]),
                    float(row["ipi"]),
                    float(row["pis"]),
                    float(row["cofins"]),
                    float(row["icms"]),
                )
            st.success("Tributos atualizados com sucesso!")
            st.rerun()

    st.markdown("---")
    st.subheader("📋 NCMs Cadastrados")

    df_ncms = carregar_ncms()
    if not df_ncms.empty:
        st.dataframe(
            df_ncms[["ncm", "descricao", "tipo_produto"]],
            column_config={
                "ncm": "NCM",
                "descricao": "Descrição",
                "tipo_produto": "Tipo Produto",
            },
            hide_index=True,
            width="stretch",
        )
    else:
        st.info("Nenhum NCM cadastrado.")

    # ── CADASTRO DE NOVO NCM ──
    st.markdown("---")
    st.subheader("➕ Cadastrar Novo NCM")

    with st.form("cadastro_ncm"):
        col_ncm1, col_ncm2 = st.columns(2)

        with col_ncm1:
            novo_ncm = st.text_input(
                "NCM *",
                placeholder="Ex: 84145910",
                key="input_novo_ncm",
            )

        with col_ncm2:
            conn_tipos = get_conn()
            tipos_ncm = conn_tipos.execute(
                "SELECT id, descricao FROM tipo_produto_importado WHERE ativo = 1 ORDER BY descricao"
            ).fetchall()
            conn_tipos.close()
            tipo_ncm_opcoes = {t[1]: t[0] for t in tipos_ncm}
            tipo_selecionado = st.selectbox(
                "Tipo Produto *",
                options=list(tipo_ncm_opcoes.keys()),
                key="select_tipo_ncm",
            )

        descricao_ncm = st.text_input(
            "Descrição",
            placeholder="Descrição do NCM",
            key="input_desc_ncm",
        )

        submitted_ncm = st.form_submit_button(
            "📋 Cadastrar NCM",
            type="primary",
            width="stretch",
        )

        if submitted_ncm:
            if not novo_ncm.strip():
                st.error("O campo NCM é obrigatório.")
            elif not tipo_selecionado:
                st.error("Selecione um Tipo Produto.")
            else:
                tipo_id = tipo_ncm_opcoes[tipo_selecionado]
                sucesso, msg = cadastrar_ncm(
                    novo_ncm.strip(),
                    descricao_ncm.strip(),
                    tipo_id,
                )
                if sucesso:
                    st.success(f"✅ NCM {novo_ncm.strip()} cadastrado com sucesso!")
                    st.rerun()
                else:
                    # Tratar erro de duplicidade com mensagem amigável
                    if "UNIQUE constraint" in str(msg):
                        st.error(f"❌ NCM {novo_ncm.strip()} já está cadastrado no sistema.")
                    else:
                        st.error(f"Erro ao cadastrar NCM: {msg}")

    # ============================================================
    # NOVA SEÇÃO: CADASTRO DE FORNECEDORES
    # ============================================================
    st.markdown("---")
    st.subheader("🏭 Cadastro de Fornecedores")

    tab_listar, tab_novo = st.tabs(["📋 Fornecedores Cadastrados", "➕ Novo Fornecedor"])

    with tab_listar:
        df_forn = carregar_fornecedores(apenas_ativos=False)
        if not df_forn.empty:
            edited_forn = st.data_editor(
                df_forn[["id", "nome", "pais", "observacoes", "ativo"]],
                column_config={
                    "id": "ID",
                    "nome": "Nome Fornecedor",
                    "pais": "País",
                    "observacoes": "Observações",
                    "ativo": st.column_config.CheckboxColumn("Ativo"),
                },
                hide_index=True,
                width="stretch",
                num_rows="fixed",
                key="editor_fornecedores",
            )

            if st.button("💾 Salvar Alterações nos Fornecedores", key="btn_salvar_forn"):
                for _, row in edited_forn.iterrows():
                    atualizar_fornecedor(
                        int(row["id"]),
                        row["nome"],
                        str(row.get("pais", "") or ""),
                        str(row.get("observacoes", "") or ""),
                        int(row["ativo"]) if row["ativo"] else 0,
                    )
                st.success("Fornecedores atualizados!")
                st.rerun()
        else:
            st.info("Nenhum fornecedor cadastrado.")

    with tab_novo:
        with st.form("novo_fornecedor"):
            forn_nome = st.text_input("Nome do Fornecedor *", placeholder="Ex: ABC Import")
            forn_pais = st.text_input("País (opcional)", placeholder="Ex: Japão, China, EUA")
            forn_obs = st.text_area("Observações", placeholder="Informações adicionais")
            forn_ativo = st.checkbox("Ativo", value=True)

            if st.form_submit_button("✅ Cadastrar Fornecedor", type="primary", width="stretch"):
                if not forn_nome.strip():
                    st.error("Nome do fornecedor é obrigatório.")
                else:
                    sucesso, msg = cadastrar_fornecedor(forn_nome, forn_pais, forn_obs, 1 if forn_ativo else 0)
                    if sucesso:
                        st.success(msg)
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(msg)


# ============================================================
# ABA 5 - HISTÓRICO FOB
# ============================================================

with abas[5]:
    st.subheader("📊 Histórico de FOB")
    st.caption("Cada fornecedor possui seu próprio histórico de evolução de FOB para cada produto.")

    col1, col2, col3 = st.columns(3)

    with col1:
        conn = get_conn()
        produtos_lista = conn.execute(
            "SELECT id, modelo FROM produtos_importados WHERE ativo = 1 ORDER BY modelo"
        ).fetchall()
        conn.close()
        produto_opcoes = {p[1]: p[0] for p in produtos_lista}
        filtro_produto = st.selectbox(
            "Filtrar por Produto",
            options=["Todos"] + list(produto_opcoes.keys()),
            key="hist_filtro_produto",
        )

    with col2:
        # Fornecedores com ID para match exato
        df_forn_hist = carregar_fornecedores()
        forn_hist_opcoes = {"Todos": None}
        if not df_forn_hist.empty:
            for _, f in df_forn_hist.iterrows():
                forn_hist_opcoes[f['nome']] = f['id']
        filtro_fornecedor_nome = st.selectbox(
            "Filtrar por Fornecedor",
            options=list(forn_hist_opcoes.keys()),
            key="hist_filtro_forn",
        )
        fornecedor_id_hist = forn_hist_opcoes[filtro_fornecedor_nome]

    with col3:
        periodo = st.selectbox(
            "Período",
            options=["Últimos 30 dias", "Últimos 90 dias", "Últimos 180 dias", "Tudo"],
            index=3,
            key="hist_periodo",
        )

    produto_id_hist = None
    if filtro_produto != "Todos":
        produto_id_hist = produto_opcoes[filtro_produto]

    data_inicio = None
    data_fim = None
    if periodo == "Últimos 30 dias":
        data_inicio = (date.today() - timedelta(days=30)).isoformat()
    elif periodo == "Últimos 90 dias":
        data_inicio = (date.today() - timedelta(days=90)).isoformat()
    elif periodo == "Últimos 180 dias":
        data_inicio = (date.today() - timedelta(days=180)).isoformat()

    # Histórico com match exato do fornecedor (pelo ID)
    df_historico = carregar_historico(
        produto_id=produto_id_hist,
        fornecedor_id=fornecedor_id_hist,
        data_inicio=data_inicio,
        data_fim=data_fim,
    )

    if not df_historico.empty:
        st.dataframe(
            df_historico,
            column_config={
                "id": "ID",
                "produto": "Produto",
                "fornecedor": "Fornecedor",
                "valor_fob_usd": st.column_config.NumberColumn("FOB USD", format="$ %.2f"),
                "data_atualizacao": "Data Atualização",
                "usuario": "Usuário",
                "observacao": "Observação",
            },
            hide_index=True,
            width="stretch",
        )

        # Gráfico de evolução FOB por fornecedor
        st.markdown("### 📈 Evolução FOB")
        if produto_id_hist and fornecedor_id_hist:
            # Filtrar apenas o fornecedor selecionado para o gráfico
            df_graf = df_historico[df_historico['fornecedor'] == filtro_fornecedor_nome]
            if not df_graf.empty:
                st.markdown(f"**Evolução do FOB — {filtro_fornecedor_nome}**")
                df_graf['data_atualizacao'] = pd.to_datetime(df_graf['data_atualizacao'])
                df_graf = df_graf.sort_values('data_atualizacao')
                st.line_chart(
                    df_graf,
                    x='data_atualizacao',
                    y='valor_fob_usd',
                    color=None,
                    width="stretch",
                )
            else:
                # Se tem mais de um fornecedor, mostrar todos
                st.markdown("**Evolução do FOB por Fornecedor**")
                df_todos = df_historico.copy()
                df_todos['data_atualizacao'] = pd.to_datetime(df_todos['data_atualizacao'])
                df_todos = df_todos.sort_values('data_atualizacao')
                st.line_chart(
                    df_todos,
                    x='data_atualizacao',
                    y='valor_fob_usd',
                    color='fornecedor',
                    width="stretch",
                )
        else:
            # Sem filtro de produto+fornecedor, agrupar por fornecedor
            st.markdown("**Evolução do FOB por Fornecedor**")
            df_todos = df_historico.copy()
            df_todos['data_atualizacao'] = pd.to_datetime(df_todos['data_atualizacao'])
            df_todos = df_todos.sort_values('data_atualizacao')
            if not df_todos.empty and df_todos['fornecedor'].nunique() > 1:
                st.line_chart(
                    df_todos,
                    x='data_atualizacao',
                    y='valor_fob_usd',
                    color='fornecedor',
                    width="stretch",
                )
            elif not df_todos.empty:
                st.line_chart(
                    df_todos,
                    x='data_atualizacao',
                    y='valor_fob_usd',
                    color=None,
                    width="stretch",
                )
    else:
        st.info("Nenhum histórico encontrado para os filtros selecionados.")