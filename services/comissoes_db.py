"""Migracoes e queries SQL do modulo Gestao Comercial. Sem regras de negocio."""

import sqlite3
from config import DB_PATH


def get_conn():
    """Retorna conexão com o banco SQLite."""
    return sqlite3.connect(str(DB_PATH))


def run_comissoes_migrations():
    """
    Cria as 4 tabelas do módulo Gestão Comercial.
    Seguro para executar múltiplas vezes (IF NOT EXISTS).
    Não altera tabelas existentes de outros módulos.
    """
    conn = get_conn()
    cursor = conn.cursor()

    # ═══════════════════════════════════════════════════════════
    # 1. PARCEIROS (cadastro + contrato embutido)
    # ═══════════════════════════════════════════════════════════
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS parceiros (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        telefone TEXT,
        email TEXT,
        pix TEXT,
        observacoes TEXT,
        status TEXT DEFAULT 'ATIVO',
        -- Dados do CONTRATO (1 contrato ativo por parceiro)
        percentual REAL DEFAULT 0,
        base_calculo TEXT DEFAULT 'BRUTO',
        aliquota_impostos REAL DEFAULT 0,
        faturamento_considerado TEXT DEFAULT 'GRUPO',
        dias_pagamento INTEGER DEFAULT 10,
        -- Metadados
        criado_em DATE DEFAULT (date('now')),
        atualizado_em DATE DEFAULT (date('now'))
    )
    """)

    # ═══════════════════════════════════════════════════════════
    # 2. CARTEIRA DE CLIENTES
    # ═══════════════════════════════════════════════════════════
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS carteira_clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        parceiro_id INTEGER NOT NULL,
        cliente_id INTEGER NOT NULL,
        FOREIGN KEY (parceiro_id) REFERENCES parceiros(id) ON DELETE CASCADE,
        FOREIGN KEY (cliente_id) REFERENCES clientes(id),
        UNIQUE(parceiro_id, cliente_id)
    )
    """)

    # ═══════════════════════════════════════════════════════════
    # 3. FECHAMENTO MENSAL (snapshot auto-contido)
    # ═══════════════════════════════════════════════════════════
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS fechamento_mensal (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        parceiro_id INTEGER NOT NULL,
        competencia TEXT NOT NULL,
        -- SNAPSHOT: copia dos dados do contrato no momento do fechamento
        percentual REAL NOT NULL,
        base_calculo TEXT NOT NULL,
        aliquota_impostos REAL NOT NULL,
        faturamento_considerado TEXT NOT NULL,
        -- SNAPSHOT: clientes em JSON (array de objetos)
        clientes_json TEXT NOT NULL DEFAULT '[]',
        -- Valores calculados
        quantidade_clientes INTEGER DEFAULT 0,
        valor_bruto REAL DEFAULT 0,
        valor_impostos REAL DEFAULT 0,
        valor_liquido REAL DEFAULT 0,
        valor_comissao REAL DEFAULT 0,
        -- Ciclo de vida
        status TEXT DEFAULT 'PREVIEW',
        fechado_em DATE,
        fechado_por TEXT,
        -- Pagamento
        data_pagamento DATE,
        usuario_pagamento TEXT,
        observacao_pagamento TEXT,
        -- Metadados
        criado_em DATE DEFAULT (date('now')),
        FOREIGN KEY (parceiro_id) REFERENCES parceiros(id)
    )
    """)

    # ═══════════════════════════════════════════════════════════
    # 4. COMISSOES AVULSAS
    # ═══════════════════════════════════════════════════════════
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS comissoes_avulsas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        parceiro_id INTEGER NOT NULL,
        cliente_id INTEGER,
        os_id INTEGER,
        descricao TEXT,
        valor_faturado REAL DEFAULT 0,
        percentual REAL DEFAULT 0,
        valor_comissao REAL DEFAULT 0,
        data_prevista DATE,
        data_pagamento DATE,
        status TEXT DEFAULT 'AGUARDANDO_FATURAMENTO',
        observacoes TEXT,
        criado_em DATE DEFAULT (date('now')),
        atualizado_em DATE DEFAULT (date('now')),
        FOREIGN KEY (parceiro_id) REFERENCES parceiros(id),
        FOREIGN KEY (cliente_id) REFERENCES clientes(id)
    )
    """)

    # ═══════════════════════════════════════════════════════════
    # MIGRACOES: alterar coluna escopo -> faturamento_considerado
    # ═══════════════════════════════════════════════════════════
    try:
        cursor.execute("ALTER TABLE parceiros RENAME COLUMN escopo TO faturamento_considerado")
        conn.commit()
    except sqlite3.OperationalError:
        pass

    # ═══════════════════════════════════════════════════════════
    # MIGRACAO: adicionar quantidade_clientes (se nao existir)
    # ═══════════════════════════════════════════════════════════
    try:
        cursor.execute("ALTER TABLE fechamento_mensal ADD COLUMN quantidade_clientes INTEGER DEFAULT 0")
        conn.commit()
    except sqlite3.OperationalError:
        pass

    # ═══════════════════════════════════════════════════════════
    # INDICES DE PERFORMANCE
    # ═══════════════════════════════════════════════════════════
    indices = [
        ("idx_fechamento_competencia", "fechamento_mensal", "competencia"),
        ("idx_fechamento_parceiro", "fechamento_mensal", "parceiro_id"),
        ("idx_fechamento_status", "fechamento_mensal", "status"),
        ("idx_carteira_parceiro", "carteira_clientes", "parceiro_id"),
        ("idx_carteira_cliente", "carteira_clientes", "cliente_id"),
        ("idx_comissoes_avulsas_parceiro", "comissoes_avulsas", "parceiro_id"),
        ("idx_comissoes_avulsas_status", "comissoes_avulsas", "status"),
        ("idx_comissoes_avulsas_data", "comissoes_avulsas", "data_prevista"),
    ]
    for idx_name, tbl, col in indices:
        try:
            cursor.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {tbl}({col})")
        except sqlite3.OperationalError:
            pass

    conn.commit()
    conn.close()


# ═══════════════════════════════════════════════════════════
# QUERIES SQL (sem regras de negocio)
# ═══════════════════════════════════════════════════════════

def query_faturamento_periodo(data_inicio: str, data_fim: str) -> list:
    """Retorna faturamento agregado por cliente em um periodo. UMA UNICA QUERY."""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT cliente_id, SUM(valor) as total
        FROM faturamento
        WHERE data_faturamento BETWEEN ? AND ?
        GROUP BY cliente_id
    """, (data_inicio, data_fim))
    rows = cursor.fetchall()
    conn.close()
    return rows


def query_faturamento_periodo_unidade(data_inicio: str, data_fim: str, unidade: str) -> list:
    """Retorna faturamento agregado por cliente filtrando por unidade."""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT cliente_id, SUM(valor) as total
        FROM faturamento
        WHERE data_faturamento BETWEEN ? AND ?
          AND unidade = ?
        GROUP BY cliente_id
    """, (data_inicio, data_fim, unidade))
    rows = cursor.fetchall()
    conn.close()
    return rows


def query_carteira_parceiro(parceiro_id: int) -> list:
    """Retorna os cliente_ids da carteira de um parceiro."""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT cliente_id
        FROM carteira_clientes
        WHERE parceiro_id = ?
    """, (parceiro_id,))
    rows = [row[0] for row in cursor.fetchall()]
    conn.close()
    return rows


def query_parceiros_ativos() -> list:
    """Retorna todos os parceiros ativos com dados do contrato."""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, nome, percentual, base_calculo,
               aliquota_impostos, faturamento_considerado,
               dias_pagamento
        FROM parceiros
        WHERE status = 'ATIVO'
        ORDER BY nome
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows


def query_parceiro_por_id(parceiro_id: int) -> dict:
    """Retorna dados completos de um parceiro."""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, nome, telefone, email, pix, observacoes, status,
               percentual, base_calculo, aliquota_impostos,
               faturamento_considerado, dias_pagamento
        FROM parceiros
        WHERE id = ?
    """, (parceiro_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "id": row[0], "nome": row[1], "telefone": row[2],
            "email": row[3], "pix": row[4], "observacoes": row[5],
            "status": row[6], "percentual": row[7],
            "base_calculo": row[8], "aliquota_impostos": row[9],
            "faturamento_considerado": row[10], "dias_pagamento": row[11],
        }
    return {}


def query_fechamentos_por_competencia(competencia: str) -> list:
    """Retorna fechamentos de uma competencia especifica."""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT fm.id, fm.parceiro_id, p.nome as parceiro_nome,
               fm.percentual, fm.base_calculo, fm.aliquota_impostos,
               fm.faturamento_considerado,
               fm.valor_bruto, fm.valor_impostos, fm.valor_liquido,
               fm.valor_comissao,
               fm.status, fm.fechado_em, fm.fechado_por,
               fm.data_pagamento, fm.usuario_pagamento,
               fm.observacao_pagamento
        FROM fechamento_mensal fm
        JOIN parceiros p ON p.id = fm.parceiro_id
        WHERE fm.competencia = ?
        ORDER BY p.nome
    """, (competencia,))
    rows = cursor.fetchall()
    conn.close()
    return rows


def query_fechamentos_por_parceiro(parceiro_id: int) -> list:
    """Retorna historico de fechamentos de um parceiro."""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, competencia, percentual, base_calculo,
               valor_bruto, valor_liquido, valor_comissao,
               status, fechado_em, data_pagamento
        FROM fechamento_mensal
        WHERE parceiro_id = ?
        ORDER BY competencia DESC
    """, (parceiro_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows


def query_comissoes_avulsas_abertas() -> list:
    """Retorna comissoes avulsas com pagamento previsto para breve (7 dias)."""
    import datetime
    hoje = datetime.date.today()
    limite = hoje + datetime.timedelta(days=7)
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ca.id, ca.parceiro_id, p.nome as parceiro_nome,
               ca.descricao, ca.valor_comissao,
               ca.data_prevista, ca.status
        FROM comissoes_avulsas ca
        JOIN parceiros p ON p.id = ca.parceiro_id
        WHERE ca.status != 'PAGO'
          AND ca.data_prevista BETWEEN ? AND ?
        ORDER BY ca.data_prevista
    """, (hoje.isoformat(), limite.isoformat()))
    rows = cursor.fetchall()
    conn.close()
    return rows


def query_comissoes_avulsas_vencidas() -> list:
    """Retorna comissoes avulsas com data prevista <= hoje e nao pagas."""
    import datetime
    hoje = datetime.date.today()
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ca.id, ca.parceiro_id, p.nome as parceiro_nome,
               ca.descricao, ca.valor_comissao,
               ca.data_prevista, ca.status
        FROM comissoes_avulsas ca
        JOIN parceiros p ON p.id = ca.parceiro_id
        WHERE ca.status != 'PAGO'
          AND ca.data_prevista <= ?
        ORDER BY ca.data_prevista
    """, (hoje.isoformat(),))
    rows = cursor.fetchall()
    conn.close()
    return rows
