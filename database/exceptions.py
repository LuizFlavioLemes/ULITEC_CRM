"""
DatabaseException — Exceções customizadas da camada de abstração
==================================================================
Substitui sqlite3.OperationalError, sqlite3.Error, etc.

Uso:
    from database.exceptions import DatabaseError, ConnectionError
    raise DatabaseError("Falha na query")
"""


class DatabaseError(Exception):
    """Erro genérico de banco de dados. Substitui sqlite3.Error."""
    pass


class ConnectionError(DatabaseError):
    """Erro de conexão com o banco. Substitui sqlite3.OperationalError."""
    pass


class QueryError(DatabaseError):
    """Erro de execução de query."""
    pass