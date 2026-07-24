"""
database — Camada de abstração de banco de dados
=================================================
Ponto único de acesso a banco para todo o CRM.

Uso:
    from database import get_connection, execute, executar
    from database import db  # Provider ativo (SQLiteProvider)

Futuramente:
    from database import db  # Provider trocado via config
    db = create_provider("postgresql", ...)

REGRAS:
    - NENHUM outro módulo deve importar sqlite3 diretamente.
    - Toda operação de banco passa por esta camada.
    - A implementação concreta (SQLite/PostgreSQL) é transparente.
"""

from database.provider import DatabaseProvider
from database.sqlite_provider import SQLiteProvider


# ── Provider ativo — SINGLETON lazy ──
# Inicializado apenas quando necessário para evitar import circular
# (config → services.version → database → config).
_db_instance: DatabaseProvider = None


def _get_db() -> DatabaseProvider:
    """Retorna a instância singleton do provider, inicializando se necessário."""
    global _db_instance
    if _db_instance is None:
        # Importa config APÓS a função para evitar import circular.
        # config importa services.version, que pode importar database.
        # Este import tardio quebra o ciclo.
        from config import DB_PATH
        _db_instance = SQLiteProvider(str(DB_PATH))
    return _db_instance


# ═══════════════════════════════════════════════════════════
# SINGLETON PÚBLICO — compatível com código legado
# ═══════════════════════════════════════════════════════════

db = _get_db()

# ═══════════════════════════════════════════════════════════
# API PÚBLICA — variável e funções de conveniência
# ═══════════════════════════════════════════════════════════


def get_connection():
    """Retorna uma conexão do provider ativo.

    Compatível com a assinatura anterior `sqlite3.connect(str(DB_PATH))`.
    """
    return _get_db().get_connection()


def execute(sql: str, params=None):
    """Executa uma instrução SQL e retorna o cursor.

    Args:
        sql: Instrução SQL
        params: Parâmetros (tuple, list ou dict)

    Returns:
        Cursor com resultados (se houver)
    """
    return _get_db().execute(sql, params)


def executar(sql: str, params=None):
    """Alias para execute(). Mantido por consistência com o código existente."""
    return execute(sql, params)


def executar_many(sql: str, params_list: list):
    """Executa uma instrução SQL para múltiplos conjuntos de parâmetros.

    Args:
        sql: Instrução SQL
        params_list: Lista de tuplas/dicts de parâmetros
    """
    return _get_db().executar_many(sql, params_list)


def commit():
    """Confirma a transação atual na conexão ativa."""
    return _get_db().commit()


def rollback():
    """Desfaz a transação atual na conexão ativa."""
    return _get_db().rollback()


def close():
    """Fecha a conexão ativa."""
    return _get_db().close()


# ═══════════════════════════════════════════════════════════
# CONTEXTO GERENCIADO (with statement)
# ═══════════════════════════════════════════════════════════


def conectar():
    """Retorna um gerenciador de contexto para uso com 'with'.

    Uso:
        with conectar() as conn:
            cursor = conn.execute("SELECT * FROM clientes")
            dados = cursor.fetchall()
        # conexão fechada automaticamente
    """
    return _get_db().conectar()


# ═══════════════════════════════════════════════════════════
# ROW FACTORY — substitui sqlite3.Row
# ═══════════════════════════════════════════════════════════


class Row:
    """Tipo linha que permite acesso por nome de coluna (como sqlite3.Row).

    Uso:
        conn.row_factory = database.Row
        row = conn.execute("SELECT id, nome FROM clientes").fetchone()
        print(row["nome"])  # acesso por nome
        print(row[0])       # acesso por índice
    """
    def __new__(cls, cursor, row):
        # Retorna um sqlite3.Row internamente (vindo do provider)
        from database.sqlite_provider import _row_factory
        return _row_factory(cursor, row)


