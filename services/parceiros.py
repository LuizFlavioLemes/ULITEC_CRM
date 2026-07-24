"""
CRUD de Parceiros e Carteira — Gestão Comercial ULITEC CRM v1.0

Responsável por:
  - Cadastro, edição, exclusão de parceiros
  - Gerenciamento da carteira de clientes

Nenhum SQL direto — usa exclusivamente services/comissoes_db.py
Nenhuma regra de cálculo financeiro.
"""

from typing import Optional

from services.comissoes_db import get_conn, query_parceiro_por_id

# ═══════════════════════════════════════════════════════════
# PARCEIROS
# ═══════════════════════════════════════════════════════════

def criar_parceiro(dados: dict) -> int:
    """
    Cria um novo parceiro com dados do contrato.

    dados: {
        "nome", "telefone", "email", "pix", "observacoes",
        "percentual", "base_calculo", "aliquota_impostos",
        "faturamento_considerado", "dias_pagamento"
    }
    Retorna: id do parceiro criado.
    """
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO parceiros
            (nome, telefone, email, pix, observacoes, status,
             percentual, base_calculo, aliquota_impostos,
             faturamento_considerado, dias_pagamento)
        VALUES (?, ?, ?, ?, ?, 'ATIVO',
                ?, ?, ?,
                ?, ?)
    """, (
        dados.get("nome", ""),
        dados.get("telefone", ""),
        dados.get("email", ""),
        dados.get("pix", ""),
        dados.get("observacoes", ""),
        float(dados.get("percentual", 0)),
        dados.get("base_calculo", "BRUTO"),
        float(dados.get("aliquota_impostos", 0)),
        dados.get("faturamento_considerado", "GRUPO"),
        int(dados.get("dias_pagamento", 10)),
    ))
    parceiro_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return parceiro_id

def atualizar_parceiro(parceiro_id: int, dados: dict):
    """
    Atualiza dados de um parceiro existente.
    NÃO atualiza status (usar ativar/desativar).
    """
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE parceiros SET
            nome = ?,
            telefone = ?,
            email = ?,
            pix = ?,
            observacoes = ?,
            percentual = ?,
            base_calculo = ?,
            aliquota_impostos = ?,
            faturamento_considerado = ?,
            dias_pagamento = ?,
            atualizado_em = date('now')
        WHERE id = ?
    """, (
        dados.get("nome", ""),
        dados.get("telefone", ""),
        dados.get("email", ""),
        dados.get("pix", ""),
        dados.get("observacoes", ""),
        float(dados.get("percentual", 0)),
        dados.get("base_calculo", "BRUTO"),
        float(dados.get("aliquota_impostos", 0)),
        dados.get("faturamento_considerado", "GRUPO"),
        int(dados.get("dias_pagamento", 10)),
        parceiro_id,
    ))
    conn.commit()
    conn.close()

def ativar_parceiro(parceiro_id: int):
    """Ativa um parceiro (status = 'ATIVO')."""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("UPDATE parceiros SET status = 'ATIVO', atualizado_em = date('now') WHERE id = ?",
                   (parceiro_id,))
    conn.commit()
    conn.close()

def desativar_parceiro(parceiro_id: int):
    """Desativa um parceiro (status = 'INATIVO')."""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("UPDATE parceiros SET status = 'INATIVO', atualizado_em = date('now') WHERE id = ?",
                   (parceiro_id,))
    conn.commit()
    conn.close()

def excluir_parceiro(parceiro_id: int):
    """
    Exclui permanentemente um parceiro.
    Carteira é removida automaticamente (ON DELETE CASCADE).
    """
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM parceiros WHERE id = ?", (parceiro_id,))
    conn.commit()
    conn.close()

# ═══════════════════════════════════════════════════════════
# CARTEIRA DE CLIENTES
# ═══════════════════════════════════════════════════════════

def adicionar_cliente_carteira(parceiro_id: int, cliente_id: int) -> bool:
    """
    Adiciona um cliente à carteira do parceiro.
    Retorna False se o cliente já estiver na carteira.
    """
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO carteira_clientes (parceiro_id, cliente_id)
            VALUES (?, ?)
        """, (parceiro_id, cliente_id))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def remover_cliente_carteira(parceiro_id: int, cliente_id: int):
    """Remove um cliente da carteira do parceiro."""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM carteira_clientes
        WHERE parceiro_id = ? AND cliente_id = ?
    """, (parceiro_id, cliente_id))
    conn.commit()
    conn.close()

def substituir_carteira(parceiro_id: int, novos_cliente_ids: list):
    """
    Substitui a carteira inteira de um parceiro.
    Remove todos os atuais e insere os novos.
    """
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM carteira_clientes WHERE parceiro_id = ?", (parceiro_id,))
    for cid in novos_cliente_ids:
        try:
            cursor.execute("""
                INSERT INTO carteira_clientes (parceiro_id, cliente_id)
                VALUES (?, ?)
            """, (parceiro_id, cid))
        except sqlite3.IntegrityError:
            pass
    conn.commit()
    conn.close()

def obter_ids_carteira(parceiro_id: int) -> list:
    """Retorna lista de cliente_ids da carteira de um parceiro."""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT cliente_id FROM carteira_clientes WHERE parceiro_id = ?
    """, (parceiro_id,))
    ids = [r[0] for r in cursor.fetchall()]
    conn.close()
    return ids