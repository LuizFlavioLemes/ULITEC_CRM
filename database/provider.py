"""
DatabaseProvider — Interface abstrata para providers de banco
=============================================================
Define o contrato que todo provider (SQLite, PostgreSQL, etc.) deve implementar.

REGRAS:
    - NÃO contém lógica específica de nenhum banco.
    - A implementação concreta decide como abrir/fechar conexões.
    - O restante do sistema depende APENAS desta interface.
"""

from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Any, Optional


class DatabaseProvider(ABC):
    """Interface abstrata para acesso a banco de dados.

    Métodos que todo provider deve implementar:
        get_connection  — Retorna uma conexão
        execute         — Executa SQL com parâmetros
        executar_many   — Executa SQL para múltiplos conjuntos
        commit          — Confirma transação
        rollback        — Desfaz transação
        close           — Fecha conexão
        conectar        — Gerenciador de contexto (with)
    """

    @abstractmethod
    def get_connection(self) -> Any:
        """Retorna uma conexão ativa com o banco."""
        ...

    @abstractmethod
    def execute(self, sql: str, params: Optional[tuple | list | dict] = None) -> Any:
        """Executa uma instrução SQL e retorna o cursor.

        Args:
            sql: Instrução SQL
            params: Parâmetros (tuple, list, dict ou None)

        Returns:
            Cursor executado (fetchall/fetchone disponíveis)
        """
        ...

    @abstractmethod
    def executar_many(self, sql: str, params_list: list) -> Any:
        """Executa uma instrução SQL para múltiplos conjuntos de parâmetros.

        Args:
            sql: Instrução SQL
            params_list: Lista de tuplas/dicts

        Returns:
            Cursor executado
        """
        ...

    @abstractmethod
    def commit(self) -> None:
        """Confirma a transação atual."""
        ...

    @abstractmethod
    def rollback(self) -> None:
        """Desfaz a transação atual."""
        ...

    @abstractmethod
    def close(self) -> None:
        """Fecha a conexão ativa."""
        ...

    @abstractmethod
    @contextmanager
    def conectar(self):
        """Gerenciador de contexto para uso com 'with'.

        Uso:
            with db.conectar() as conn:
                cursor = conn.execute("SELECT ...")
        A conexão é fechada automaticamente ao sair do bloco.
        """
        ...