"""
Dashboard de Indicadores — Gestão Comercial ULITEC CRM v1.0

APENAS consultas de indicadores e KPIs.
NENHUMA regra de cálculo financeiro.
NENHUM cálculo de projeção.
Usa services/comissoes_consultas.py para dados brutos.
"""

from datetime import date, datetime, timedelta
from typing import Optional

from services.comissoes_db import get_conn

def _calcular_periodo(periodo: str) -> tuple:
    """
    Retorna (data_inicio, data_fim) com base no periodo selecionado.
    """
    hoje = date.today()
    if periodo == "Mes atual":
        data_inicio = date(hoje.year, hoje.month, 1)
        data_fim = hoje
    elif periodo == "Mes anterior":
        if hoje.month == 1:
            data_inicio = date(hoje.year - 1, 12, 1)
            data_fim = date(hoje.year - 1, 12, 31)
        else:
            data_inicio = date(hoje.year, hoje.month - 1, 1)
            ultimo_dia = (date(hoje.year, hoje.month, 1) - timedelta(days=1)).day
            data_fim = date(hoje.year, hoje.month - 1, ultimo_dia)
    elif periodo == "Ultimos 3 meses":
        data_inicio = hoje - timedelta(days=90)
        data_fim = hoje
    elif periodo == "Ultimos 6 meses":
        data_inicio = hoje - timedelta(days=180)
        data_fim = hoje
    elif periodo == "Ultimos 12 meses":
        data_inicio = hoje - timedelta(days=365)
        data_fim = hoje
    elif periodo == "Ano atual":
        data_inicio = date(hoje.year, 1, 1)
        data_fim = hoje
    else:
        data_inicio = date(2020, 1, 1)
        data_fim = hoje
    return data_inicio.isoformat(), data_fim.isoformat()

def indicadores_gerais() -> dict:
    """
    Retorna KPIs gerais do módulo:
    - parceiros_ativos: int
    - total_carteiras: int (parceiros com pelo menos 1 cliente)
    - total_clientes_carteira: int
    - total_fechamentos: int
    - total_pagos: int
    - total_pendentes: int (FECHADO mas não PAGO)
    - total_comissao_fechada: float
    - total_comissao_paga: float
    - total_comissao_pendente: float
    - maior_parceiro: str (nome)
    - maior_comissao_parceiro: float
    """
    conn = get_conn()
    cursor = conn.cursor()

    resultado = {
        "parceiros_ativos": 0,
        "total_carteiras": 0,
        "total_clientes_carteira": 0,
        "total_fechamentos": 0,
        "total_pagos": 0,
        "total_pendentes": 0,
        "total_comissao_fechada": 0.0,
        "total_comissao_paga": 0.0,
        "total_comissao_pendente": 0.0,
        "maior_parceiro": "-",
        "maior_comissao_parceiro": 0.0,
    }

    # Parceiros ativos
    cursor.execute("SELECT COUNT(*) FROM parceiros WHERE status = 'ATIVO'")
    resultado["parceiros_ativos"] = cursor.fetchone()[0]

    # Carteiras (parceiros com clientes)
    cursor.execute("""
        SELECT COUNT(DISTINCT parceiro_id) FROM carteira_clientes
    """)
    resultado["total_carteiras"] = cursor.fetchone()[0]

    # Total clientes em carteiras
    cursor.execute("SELECT COUNT(*) FROM carteira_clientes")
    resultado["total_clientes_carteira"] = cursor.fetchone()[0]

    # Totais de fechamento
    cursor.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN status = 'PAGO' THEN 1 ELSE 0 END) as pagos,
            SUM(CASE WHEN status = 'FECHADO' THEN 1 ELSE 0 END) as pendentes,
            COALESCE(SUM(CASE WHEN status IN ('FECHADO', 'PAGO') THEN valor_comissao ELSE 0 END), 0) as total_fechado,
            COALESCE(SUM(CASE WHEN status = 'PAGO' THEN valor_comissao ELSE 0 END), 0) as total_pago,
            COALESCE(SUM(CASE WHEN status = 'FECHADO' THEN valor_comissao ELSE 0 END), 0) as total_pendente
        FROM fechamento_mensal
    """)
    row = cursor.fetchone()
    if row:
        resultado["total_fechamentos"] = row[0] or 0
        resultado["total_pagos"] = row[1] or 0
        resultado["total_pendentes"] = row[2] or 0
        resultado["total_comissao_fechada"] = row[3] or 0.0
        resultado["total_comissao_paga"] = row[4] or 0.0
        resultado["total_comissao_pendente"] = row[5] or 0.0

    # Maior parceiro (por valor de comissão)
    cursor.execute("""
        SELECT p.nome, SUM(fm.valor_comissao) as total
        FROM fechamento_mensal fm
        JOIN parceiros p ON p.id = fm.parceiro_id
        WHERE fm.status IN ('FECHADO', 'PAGO')
        GROUP BY p.id, p.nome
        ORDER BY total DESC
        LIMIT 1
    """)
    row = cursor.fetchone()
    if row:
        resultado["maior_parceiro"] = row[0]
        resultado["maior_comissao_parceiro"] = row[1] or 0.0

    conn.close()
    return resultado

def indicadores_por_periodo(ano: int, mes: Optional[int] = None) -> dict:
    """
    Retorna KPIs filtrados por período.
    Se mes for None, considera o ano inteiro.

    - total_fechado: float
    - total_pago: float
    - total_pendente: float
    - quantidade_fechamentos: int
    - quantidade_pagos: int
    """
    conn = get_conn()
    cursor = conn.cursor()

    if mes:
        like_pattern = f"{ano:04d}-{mes:02d}"
        where_comp = "fm.competencia = ?"
        params = [like_pattern]
    else:
        like_pattern = f"{ano:04d}%"
        where_comp = "fm.competencia LIKE ?"
        params = [like_pattern]

    cursor.execute(f"""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN fm.status = 'PAGO' THEN 1 ELSE 0 END) as pagos,
            COALESCE(SUM(CASE WHEN fm.status IN ('FECHADO', 'PAGO')
                          THEN fm.valor_comissao ELSE 0 END), 0) as total_fechado,
            COALESCE(SUM(CASE WHEN fm.status = 'PAGO'
                          THEN fm.valor_comissao ELSE 0 END), 0) as total_pago,
            COALESCE(SUM(CASE WHEN fm.status = 'FECHADO'
                          THEN fm.valor_comissao ELSE 0 END), 0) as total_pendente
        FROM fechamento_mensal fm
        WHERE {where_comp}
    """, params)
    row = cursor.fetchone()
    conn.close()

    return {
        "total_fechamentos": row[0] or 0,
        "quantidade_pagos": row[1] or 0,
        "total_fechado": round(row[2] or 0.0, 2),
        "total_pago": round(row[3] or 0.0, 2),
        "total_pendente": round(row[4] or 0.0, 2),
    }

def top_parceiros(limite: int = 5) -> list:
    """
    Retorna ranking de parceiros por comissão fechada.
    """
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.nome,
               COUNT(fm.id) as qtd_fechamentos,
               COALESCE(SUM(fm.valor_comissao), 0) as total_comissao
        FROM parceiros p
        LEFT JOIN fechamento_mensal fm ON fm.parceiro_id = p.id
            AND fm.status IN ('FECHADO', 'PAGO')
        GROUP BY p.id, p.nome
        ORDER BY total_comissao DESC
        LIMIT ?
    """, (limite,))
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "nome": r[0],
            "qtd_fechamentos": r[1],
            "total_comissao": round(r[2], 2),
        }
        for r in rows
    ]

def top_clientes(limite: int = 5) -> list:
    """
    Retorna ranking de clientes que mais geraram comissão.
    Lê do clientes_json dos fechamentos FECHADO/PAGO.
    """
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT clientes_json
        FROM fechamento_mensal
        WHERE status IN ('FECHADO', 'PAGO')
          AND clientes_json != '[]'
    """)
    rows = cursor.fetchall()
    conn.close()

    import json
    clientes = {}
    for (json_str,) in rows:
        try:
            dados = json.loads(json_str)
            for c in dados:
                nome = c.get("cliente", "Desconhecido")
                valor = c.get("valor_comissao", 0)
                clientes[nome] = clientes.get(nome, 0) + valor
        except (json.JSONDecodeError, TypeError):
            pass

    ranking = sorted(clientes.items(), key=lambda x: x[1], reverse=True)
    return [
        {"nome": nome, "total_comissao": round(valor, 2)}
        for nome, valor in ranking[:limite]
    ]

def avulsas_proximas() -> list:
    """
    Retorna comissões avulsas com pagamento previsto para os próximos 7 dias.
    """
    from services.comissoes_db import query_comissoes_avulsas_abertas
    return query_comissoes_avulsas_abertas()

def resumo_competencia(competencia: str) -> dict:
    """
    Retorna resumo de uma competência específica.
    """
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            COUNT(*) as total,
            COALESCE(SUM(valor_comissao), 0) as total_comissao,
            COALESCE(SUM(valor_bruto), 0) as total_bruto,
            COALESCE(SUM(valor_liquido), 0) as total_liquido,
            COUNT(CASE WHEN status = 'PAGO' THEN 1 END) as pagos,
            COUNT(CASE WHEN status = 'FECHADO' THEN 1 END) as fechados,
            COUNT(CASE WHEN status = 'PREVIEW' THEN 1 END) as previews
        FROM fechamento_mensal
        WHERE competencia = ?
    """, (competencia,))
    row = cursor.fetchone()
    conn.close()

    if row and row[0] > 0:
        return {
            "total": row[0],
            "total_comissao": round(row[1], 2),
            "total_bruto": round(row[2], 2),
            "total_liquido": round(row[3], 2),
            "pagos": row[4] or 0,
            "fechados": row[5] or 0,
            "previews": row[6] or 0,
        }
    return {}