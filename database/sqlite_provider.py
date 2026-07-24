"""
SQLiteProvider — Implementação concreta do provider SQLite
===========================================================
Encapsula todo o acesso a sqlite3 em um único lugar.

REGRAS:
    - Único arquivo do sistema que importa sqlite3 (exceto legados).
    - Gerencia conexão única por instância (compatível com o padrão atual).
    - A conexão concreta (sqlite3.Connection) é retornada diretamente
      para compatibilidade com código existente que chama .execute() no conn.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Optional

from database.provider import DatabaseProvider


class SQLiteProvider(DatabaseProvider):
    """Provider SQLite — implementação concreta.

    Gerencia uma conexão SQLite com:
        - WAL mode (performance)
        - Foreign Keys habilitadas
        - Synchronous NORMAL

    Uso:
        db = SQLiteProvider("crm.db")
        conn = db.get_connection()
        cursor = conn.execute("SELECT * FROM clientes")
    """

    def __init__(self, db_path: str):
        """Inicializa o provider com o caminho do arquivo .db.

        Args:
            db_path: Caminho para o arquivo SQLite (ex: "crm.db")
        """
        self._db_path = str(Path(db_path).resolve())
        self._conn: Optional[sqlite3.Connection] = None

    # ──────────────────────────────────────────────
    # Conexão — NOVA A CADA CHAMADA
    # ──────────────────────────────────────────────
    # Diferentemente do singleton anterior, cada chamada a get_connection()
    # cria uma NOVA conexão. Isso evita o problema de código externo
    # fechar a conexão singleton (ex: auth.py, services/*.py).
    #
    # SQLite com WAL mode já é thread-safe e performático com múltiplas
    # conexões concorrentes.

    def _create_connection(self) -> sqlite3.Connection:
        """Cria e configura uma nova conexão SQLite."""
        conn = sqlite3.connect(self._db_path, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def get_connection(self) -> sqlite3.Connection:
        """Retorna uma NOVA conexão SQLite a cada chamada.

        Comportamento equivalente ao original `sqlite3.connect(str(DB_PATH))`
        que era usado antes da refatoração da camada de abstração.
        """
        return self._create_connection()

    def _ensure_connection(self) -> sqlite3.Connection:
        """Garante que a conexão existe e a retorna.

        Método interno usado por execute/commit/rollback.
        Mantém compatibilidade com o padrão anterior.
        """
        if self._conn is None or not self._is_conn_alive(self._conn):
            self._conn = self._create_connection()
        return self._conn

    def _is_conn_alive(self, conn: sqlite3.Connection) -> bool:
        """Verifica se a conexão ainda está aberta."""
        try:
            conn.execute("SELECT 1")
            return True
        except sqlite3.ProgrammingError:
            return False

    # ──────────────────────────────────────────────
    # Execução de queries
    # ──────────────────────────────────────────────

    def execute(self, sql: str, params: Optional[tuple | list | dict] = None) -> sqlite3.Cursor:
        """Executa uma instrução SQL e retorna o cursor.

        Compatível com conn.execute(sql, params) do sqlite3.

        Args:
            sql: Instrução SQL
            params: Parâmetros (tuple, list, dict ou None)

        Returns:
            sqlite3.Cursor executado
        """
        conn = self._ensure_connection()
        if params is not None:
            return conn.execute(sql, params)
        return conn.execute(sql)

    def executar_many(self, sql: str, params_list: list) -> None:
        """Executa uma instrução SQL para múltiplos conjuntos de parâmetros.

        Args:
            sql: Instrução SQL
            params_list: Lista de tuplas/dicts
        """
        conn = self._ensure_connection()
        conn.executemany(sql, params_list)

    # ──────────────────────────────────────────────
    # Gerenciamento de transações
    # ──────────────────────────────────────────────

    def commit(self) -> None:
        """Confirma a transação atual."""
        conn = self._ensure_connection()
        conn.commit()

    def rollback(self) -> None:
        """Desfaz a transação atual."""
        conn = self._ensure_connection()
        conn.rollback()

    def close(self) -> None:
        """Fecha a conexão se estiver aberta."""
        if self._conn is not None:
            try:
                self._conn.close()
            except Exception:
                pass
            finally:
                self._conn = None

    # ──────────────────────────────────────────────
    # Context manager (with statement)
    # ──────────────────────────────────────────────

    @contextmanager
    def conectar(self):
        """Gerenciador de contexto para uso com 'with'.

        Abre uma NOVA conexão, executa o bloco e fecha ao sair.
        Útil para operações que precisam de conexão isolada.

        Uso:
            with db.conectar() as conn:
                cursor = conn.execute("SELECT * FROM clientes")
        """
        conn = sqlite3.connect(self._db_path)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        try:
            yield conn
        finally:
            conn.close()

    # ──────────────────────────────────────────────
    # Utilitários
    # ──────────────────────────────────────────────

    @property
    def db_path(self) -> str:
        """Caminho do arquivo de banco."""
        return self._db_path

    @property
    def is_connected(self) -> bool:
        """Indica se há uma conexão ativa."""
        return self._conn is not None


# ═══════════════════════════════════════════════════════════
# Row Factory — substitui sqlite3.Row (uso via database.Row)
# ═══════════════════════════════════════════════════════════

def _row_factory(cursor, row):
    """Factory que retorna sqlite3.Row para compatibilidade com código legado.

    Uso:
        conn.row_factory = database.sqlite_provider._row_factory
    """
    return sqlite3.Row(cursor, row)