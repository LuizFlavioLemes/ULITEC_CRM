"""
Consultas de negócio — Gestão Comercial ULITEC CRM v1.0

Orquestra consultas combinando dados de múltiplas fontes.
Toda consulta SQL pura está em comissoes_db.py.
Este módulo APENAS combina dados em memória (sem regras de cálculo financeiro).
"""

from datetime import date, datetime
from typing import Optional

from services.comissoes_db import (
    query_parceiros_ativos,
    query_parceiro_por_id,
    query_carteira_parceiro,
    query_faturamento_periodo,
    query_faturamento_periodo_unidade,
    query_fechamentos_por_competencia,
    query_comissoes_avulsas_abertas,
    get_conn,
)


def listar_parceiros_com_carteira() -> list:
    """
    Retorna lista de parceiros ativos com:
    - id, nome, quantidade de clientes na carteira
    """
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.id, p.nome, p.percentual, p.base_calculo,
               p.aliquota_impostos, p.faturamento_considerado,
               p.dias_pagamento, p.status,
               COUNT(cc.id) as qtd_clientes
        FROM parceiros p
        LEFT JOIN carteira_clientes cc ON cc.parceiro_id = p.id
        GROUP BY p.id
        ORDER BY p.nome
    """)
    rows = cursor.fetchall()
    conn.close()

    resultados = []
    for r in rows:
        resultados.append({
            "id": r[0],
            "nome": r[1],
            "percentual": r[2],
            "base_calculo": r[3],
            "aliquota_impostos": r[4],
            "faturamento_considerado": r[5],
            "dias_pagamento": r[6],
            "status": r[7],
            "qtd_clientes": r[8],
        })
    return resultados


def listar_clientes_carteira(parceiro_id: int) -> list:
    """
    Retorna dados completos dos clientes da carteira de um parceiro.
    """
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.id, c.razao_social, c.nome_fantasia, c.cidade, c.estado,
               c.cnpj, c.faturamento_12m
        FROM carteira_clientes cc
        JOIN clientes c ON c.id = cc.cliente_id
        WHERE cc.parceiro_id = ?
        ORDER BY c.razao_social
    """, (parceiro_id,))
    rows = cursor.fetchall()
    conn.close()

    resultados = []
    for r in rows:
        resultados.append({
            "id": r[0],
            "razao_social": r[1],
            "nome_fantasia": r[2],
            "cidade": r[3],
            "estado": r[4],
            "cnpj": r[5],
            "faturamento_12m": r[6],
        })
    return resultados


def listar_fechamentos_para_historico(ano: Optional[int] = None,
                                      parceiro_id: Optional[int] = None) -> list:
    """
    Retorna fechamentos com filtros opcionais para a tela de histórico.
    """
    conn = get_conn()
    cursor = conn.cursor()

    where = []
    params = []

    if ano:
        where.append("fm.competencia LIKE ?")
        params.append(f"{ano}%")
    if parceiro_id:
        where.append("fm.parceiro_id = ?")
        params.append(parceiro_id)

    sql_where = " AND ".join(where) if where else "1=1"

    cursor.execute(f"""
        SELECT fm.id, fm.competencia, p.nome as parceiro_nome,
               fm.percentual, fm.base_calculo,
               fm.valor_bruto, fm.valor_liquido, fm.valor_comissao,
               fm.quantidade_clientes,
               fm.status, fm.fechado_em, fm.fechado_por,
               fm.data_pagamento, fm.usuario_pagamento,
               fm.observacao_pagamento
        FROM fechamento_mensal fm
        JOIN parceiros p ON p.id = fm.parceiro_id
        WHERE {sql_where}
        ORDER BY fm.competencia DESC, p.nome
    """, tuple(params))
    rows = cursor.fetchall()
    conn.close()

    resultados = []
    for r in rows:
        resultados.append({
            "id": r[0],
            "competencia": r[1],
            "parceiro_nome": r[2],
            "percentual": r[3],
            "base_calculo": r[4],
            "valor_bruto": r[5],
            "valor_liquido": r[6],
            "valor_comissao": r[7],
            "quantidade_clientes": r[8],
            "status": r[9],
            "fechado_em": r[10],
            "fechado_por": r[11],
            "data_pagamento": r[12],
            "usuario_pagamento": r[13],
            "observacao_pagamento": r[14],
        })
    return resultados


def listar_comissoes_avulsas(parceiro_id: Optional[int] = None) -> list:
    """
    Retorna comissões avulsas com filtro opcional por parceiro.
    """
    conn = get_conn()
    cursor = conn.cursor()

    if parceiro_id:
        cursor.execute("""
            SELECT ca.id, ca.parceiro_id, p.nome as parceiro_nome,
                   ca.cliente_id, c.razao_social as cliente_nome,
                   ca.os_id, ca.descricao,
                   ca.valor_faturado, ca.percentual, ca.valor_comissao,
                   ca.data_prevista, ca.data_pagamento,
                   ca.status, ca.observacoes,
                   ca.criado_em
            FROM comissoes_avulsas ca
            JOIN parceiros p ON p.id = ca.parceiro_id
            LEFT JOIN clientes c ON c.id = ca.cliente_id
            WHERE ca.parceiro_id = ?
            ORDER BY ca.criado_em DESC
        """, (parceiro_id,))
    else:
        cursor.execute("""
            SELECT ca.id, ca.parceiro_id, p.nome as parceiro_nome,
                   ca.cliente_id, c.razao_social as cliente_nome,
                   ca.os_id, ca.descricao,
                   ca.valor_faturado, ca.percentual, ca.valor_comissao,
                   ca.data_prevista, ca.data_pagamento,
                   ca.status, ca.observacoes,
                   ca.criado_em
            FROM comissoes_avulsas ca
            JOIN parceiros p ON p.id = ca.parceiro_id
            LEFT JOIN clientes c ON c.id = ca.cliente_id
            ORDER BY ca.criado_em DESC
        """)

    rows = cursor.fetchall()
    conn.close()

    resultados = []
    for r in rows:
        resultados.append({
            "id": r[0],
            "parceiro_id": r[1],
            "parceiro_nome": r[2],
            "cliente_id": r[3],
            "cliente_nome": r[4],
            "os_id": r[5],
            "descricao": r[6],
            "valor_faturado": r[7],
            "percentual": r[8],
            "valor_comissao": r[9],
            "data_prevista": r[10],
            "data_pagamento": r[11],
            "status": r[12],
            "observacoes": r[13],
            "criado_em": r[14],
        })
    return resultados


def listar_clientes_para_select() -> tuple:
    """
    Retorna lista e dicionário de clientes para select box.
    """
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, razao_social, cidade, estado, codigo_erp
        FROM clientes
        WHERE status = 'ATIVO'
        ORDER BY razao_social
    """)
    rows = cursor.fetchall()
    conn.close()

    opcoes = []
    mapa = {}
    for r in rows:
        cliente_id, razao, cidade, estado, codigo = r
        label = razao
        if cidade and estado:
            label += f" - {cidade}/{estado}"
        if codigo:
            label += f" ({codigo})"
        opcoes.append(label)
        mapa[label] = cliente_id

    return opcoes, mapa