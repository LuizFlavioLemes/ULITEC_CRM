"""
Módulo Central de Versionamento — ULITEC CRM
============================================
Fonte única e oficial de metadados da versão do sistema.

Uso:
    from services.version import (
        VERSION, BUILD, AMBIENTE, RELEASE_DATE,
        get_version_info, get_version_string, get_banner,
    )

Regras:
    - NENHUM outro arquivo deve declarar versão do sistema.
    - Toda consulta de versão passa exclusivamente por este módulo.
    - Este módulo é a base para futuras releases automáticas.

Atualização de versão:
    - Bump manual nos campos VERSION, BUILD e RELEASE_DATE.
    - Futuramente: CI/CD pipeline pode injetar BUILD automaticamente.
"""

import os
import sys
import sqlite3
from datetime import date
from pathlib import Path

# ═══════════════════════════════════════════════════════════
# METADADOS OFICIAIS DA VERSÃO
# ═══════════════════════════════════════════════════════════

VERSION = "1.0.4"
BUILD = "2026.0707.0"          # Formato: YYYY.MMDD.PATCH
RELEASE_DATE = "2026-07-07"
AMBIENTE = os.getenv("ULITEC_AMBIENTE", "DEV").upper()

SYSTEM_NAME = "ULITEC CRM"
SYSTEM_FULL_NAME = "CRM Industrial ULITEC"

# ═══════════════════════════════════════════════════════════
# DETECÇÃO DE AMBIENTE PYTHON
# ═══════════════════════════════════════════════════════════

PYTHON_VERSION = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

# ═══════════════════════════════════════════════════════════
# DETECÇÃO DE BANCO
# ═══════════════════════════════════════════════════════════

def _detect_db_version() -> str:
    """Tenta detectar a versão do SQLite em uso."""
    try:
        ROOT_DIR = Path(__file__).resolve().parent.parent
        db_path = ROOT_DIR / "crm.db"
        if db_path.exists():
            conn = sqlite3.connect(str(db_path))
            cursor = conn.execute("SELECT sqlite_version()")
            ver = cursor.fetchone()[0]
            conn.close()
            return ver
        return "N/A (banco não encontrado)"
    except Exception:
        return "N/A"


def _detect_sqlite_version() -> str:
    """Versão do módulo sqlite3 em uso."""
    return sqlite3.sqlite_version


# ═══════════════════════════════════════════════════════════
# API PÚBLICA
# ═══════════════════════════════════════════════════════════

def get_version_string() -> str:
    """Retorna string resumida: 'ULITEC CRM v1.0.3 (build 2025.0702.0)'."""
    return f"{SYSTEM_NAME} v{VERSION} (build {BUILD})"


def get_version_badge() -> str:
    """Retorna string curta: 'v1.0.3'."""
    return f"v{VERSION}"


def get_banner() -> str:
    """Retorna banner completo para uso em HTML/terminal."""
    return f"{SYSTEM_FULL_NAME} — {get_version_string()} [{AMBIENTE}]"


def get_version_info() -> dict:
    """
    Retorna dicionário completo com todas as informações da instalação.

    Usado pela Administração (Informações da Instalação) e por
    futuras APIs de health check.
    """
    return {
        "sistema": SYSTEM_FULL_NAME,
        "versao": VERSION,
        "build": BUILD,
        "ambiente": AMBIENTE,
        "data_release": RELEASE_DATE,
        "python": PYTHON_VERSION,
        "sqlite_modulo": _detect_sqlite_version(),
        "sqlite_banco": _detect_db_version(),
    }


def get_version_short_info() -> dict:
    """Versão resumida para rodapé e banners."""
    return {
        "sistema": SYSTEM_NAME,
        "versao": VERSION,
        "ambiente": AMBIENTE,
    }


# ═══════════════════════════════════════════════════════════
# INFRAESTRUTURA PARA RELEASES FUTURAS
# ═══════════════════════════════════════════════════════════

def get_version_tuple() -> tuple:
    """
    Retorna tupla de versão para comparações programáticas.
    Ex: (1, 0, 3)
    Útil para migrações condicionais e scripts de upgrade.
    """
    return tuple(int(x) for x in VERSION.split("."))


def check_minimum_version(min_version: str) -> bool:
    """
    Verifica se a versão atual é >= versão mínima exigida.

    Args:
        min_version: Versão mínima no formato "X.Y.Z"

    Returns:
        True se versão atual >= min_version
    """
    actual = get_version_tuple()
    required = tuple(int(x) for x in min_version.split("."))
    return actual >= required


# ═══════════════════════════════════════════════════════════
# AUTO-VALIDAÇÃO
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    import json
    print(get_banner())
    print(json.dumps(get_version_info(), indent=2, ensure_ascii=False))