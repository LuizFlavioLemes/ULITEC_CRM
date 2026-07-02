"""
Deployment Manager — ULITEC CRM v0.8 (SPRINT 0.8)
===================================================

Infraestrutura definitiva de instalação, atualização e validação.

Responsável por:
- Estrutura de pastas do projeto
- Validação de ambiente (.env, banco, arquivos essenciais)
- Health check completo do sistema
- Detecção de primeira instalação
- Relatório de instalação formatado
- Preparação para migrações futuras

Regras:
- NÃO altera regras de negócio
- NÃO modifica páginas, consultas SQL, permissões, autenticação, IA
- Compatível com Windows, Linux, cPanel Passenger, GitHub
- Usa pathlib exclusivamente
- Nenhum caminho absoluto
- Nenhum código específico para SO
"""

import os
import sqlite3
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from config import (
    ROOT_DIR,
    DB_PATH,
    LOGS_DIR,
    BACKUPS_DIR,
    EXPORTS_DIR,
    MANIFESTOS_DIR,
    UPLOADS_DIR,
    TEMP_DIR,
    DOCS_DIR,
    AMBIENTE,
    MASTER_PASSWORD,
    IA_PROVIDER,
)

# ============================================================
# DATACLASS
# ============================================================


@dataclass
class HealthResult:
    """Resultado completo do health check do sistema."""

    status: str = "OK"  # "OK" | "WARNING" | "ERROR"
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    directories: Dict = field(default_factory=dict)
    database: Dict = field(default_factory=dict)
    environment: Dict = field(default_factory=dict)
    files: Dict = field(default_factory=dict)
    version: str = ""
    timestamp: str = ""


# ============================================================
# 1) ESTRUTURA DE PASTAS
# ============================================================


def get_project_structure() -> Dict[str, Path]:
    """
    Retorna todas as pastas oficiais do CRM.

    Cada chave é um nome amigável e o valor é o Path absoluto
    (resolvido a partir de ROOT_DIR).

    Returns:
        Dict com nome_da_pasta -> Path
    """
    return {
        "logs": LOGS_DIR,
        "backups": BACKUPS_DIR,
        "backups_export": EXPORTS_DIR,
        "backups_manifestos": MANIFESTOS_DIR,
        "uploads": UPLOADS_DIR,
        "temp": TEMP_DIR,
        "docs": DOCS_DIR,
        "scripts": ROOT_DIR / "scripts",
        "legacy": ROOT_DIR / "legacy",
        "debug": ROOT_DIR / "debug",
        "services": ROOT_DIR / "services",
        "services_ia": ROOT_DIR / "services" / "ia",
        "pages": ROOT_DIR / "pages",
        "components": ROOT_DIR / "components",
        "tests": ROOT_DIR / "tests",
    }


# ============================================================
# 2) CRIAÇÃO DE PASTAS
# ============================================================


def ensure_directories() -> Dict[str, bool]:
    """
    Cria automaticamente todas as pastas obrigatórias.

    Utiliza os caminhos definidos em config.py.
    Caso já existam, não faz nada.

    Returns:
        Dict com nome_da_pasta -> True se já existia, False se foi criada agora
    """
    estrutura = get_project_structure()
    resultado = {}

    for nome, pasta in estrutura.items():
        ja_existia = pasta.exists()
        if not ja_existia:
            pasta.mkdir(parents=True, exist_ok=True)
        resultado[nome] = ja_existia

    return resultado


# ============================================================
# 3) VALIDAÇÃO DE AMBIENTE (.env)
# ============================================================


def validate_env() -> Dict:
    """
    Verifica se o arquivo .env existe e contém as variáveis obrigatórias.

    NUNCA imprime. SEMPRE retorna dict.

    Returns:
        {
            "existe": bool,
            "variaveis": {
                "MASTER_PASSWORD": {"configurada": bool, "valor_oculto": str},
                "ULITEC_AMBIENTE": {"configurada": bool, "valor": str},
                "IA_PROVIDER": {"configurada": bool, "valor": str},
            },
            "faltantes": [str, ...],
            "status": "OK" | "WARNING" | "ERROR",
        }
    """
    env_path = ROOT_DIR / ".env"
    existe = env_path.exists()

    variaveis = {}
    faltantes = []

    # MASTER_PASSWORD
    if MASTER_PASSWORD:
        variaveis["MASTER_PASSWORD"] = {
            "configurada": True,
            "valor_oculto": "***",
        }
    else:
        variaveis["MASTER_PASSWORD"] = {
            "configurada": False,
            "valor_oculto": "(não definida)",
        }
        faltantes.append("MASTER_PASSWORD")

    # ULITEC_AMBIENTE
    if AMBIENTE:
        variaveis["ULITEC_AMBIENTE"] = {
            "configurada": True,
            "valor": AMBIENTE,
        }
    else:
        variaveis["ULITEC_AMBIENTE"] = {
            "configurada": False,
            "valor": "DEV (default)",
        }

    # IA_PROVIDER
    if IA_PROVIDER:
        variaveis["IA_PROVIDER"] = {
            "configurada": True,
            "valor": IA_PROVIDER,
        }
    else:
        variaveis["IA_PROVIDER"] = {
            "configurada": False,
            "valor": "(não definido)",
        }
        faltantes.append("IA_PROVIDER")

    # Status
    if not existe:
        status = "ERROR"
    elif faltantes:
        status = "WARNING"
    else:
        status = "OK"

    return {
        "existe": existe,
        "variaveis": variaveis,
        "faltantes": faltantes,
        "status": status,
    }


# ============================================================
# 4) VALIDAÇÃO DE BANCO DE DADOS
# ============================================================


def validate_database() -> Dict:
    """
    Verifica a integridade e configuração do banco SQLite.

    Returns:
        {
            "existe": bool,
            "tamanho_kb": float,
            "integridade": "OK" | "FALHA",
            "journal_mode": str,
            "foreign_keys": bool,
            "schema_version": int,
            "quantidade_tabelas": int,
            "tabelas": [str, ...],
            "erros": [str, ...],
            "status": "OK" | "ERROR",
        }
    """
    erros = []

    # Verificar existência
    existe = DB_PATH.exists()
    if not existe:
        return {
            "existe": False,
            "tamanho_kb": 0.0,
            "integridade": "N/A",
            "journal_mode": "N/A",
            "foreign_keys": False,
            "schema_version": 0,
            "quantidade_tabelas": 0,
            "tabelas": [],
            "erros": ["Banco crm.db não encontrado"],
            "status": "ERROR",
        }

    tamanho_kb = DB_PATH.stat().st_size / 1024.0

    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        # Integrity check
        cursor.execute("PRAGMA integrity_check;")
        integridade_result = cursor.fetchone()[0]
        integridade = "OK" if integridade_result == "ok" else str(integridade_result)

        # journal_mode
        cursor.execute("PRAGMA journal_mode;")
        journal_mode = cursor.fetchone()[0]

        # foreign_keys
        cursor.execute("PRAGMA foreign_keys;")
        foreign_keys = bool(cursor.fetchone()[0])

        # schema_version
        cursor.execute("PRAGMA schema_version;")
        schema_version = cursor.fetchone()[0]

        # Tabelas
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
        )
        tabelas = [row[0] for row in cursor.fetchall()]
        quantidade_tabelas = len(tabelas)

        conn.close()

    except Exception as e:
        erros.append(f"Erro ao conectar/consultar banco: {e}")
        return {
            "existe": True,
            "tamanho_kb": tamanho_kb,
            "integridade": "ERRO",
            "journal_mode": "N/A",
            "foreign_keys": False,
            "schema_version": 0,
            "quantidade_tabelas": 0,
            "tabelas": [],
            "erros": erros,
            "status": "ERROR",
        }

    status = "ERROR" if erros else ("OK" if integridade == "OK" else "ERROR")

    return {
        "existe": True,
        "tamanho_kb": round(tamanho_kb, 2),
        "integridade": integridade,
        "journal_mode": journal_mode,
        "foreign_keys": foreign_keys,
        "schema_version": schema_version,
        "quantidade_tabelas": quantidade_tabelas,
        "tabelas": tabelas,
        "erros": erros,
        "status": status,
    }


# ============================================================
# 5) VALIDAÇÃO DE ARQUIVOS ESSENCIAIS
# ============================================================


def validate_requirements() -> Dict:
    """
    Verifica a existência dos arquivos essenciais do projeto.

    Returns:
        {
            "arquivos": {
                "requirements.txt": bool,
                "passenger_wsgi.py": bool,
                "config.py": bool,
                "CHANGELOG.md": bool,
                "README_DEPLOY.md": bool,
                "VERSAO.md": bool,
            },
            "total_presentes": int,
            "total_esperados": int,
            "faltantes": [str, ...],
            "status": "OK" | "WARNING" | "ERROR",
        }
    """
    arquivos_esperados = [
        "requirements.txt",
        "passenger_wsgi.py",
        "config.py",
        "CHANGELOG.md",
        "README_DEPLOY.md",
        "VERSAO.md",
    ]

    resultado = {}
    faltantes = []

    for nome in arquivos_esperados:
        caminho = ROOT_DIR / nome
        presente = caminho.exists()
        resultado[nome] = presente
        if not presente:
            faltantes.append(nome)

    total_presentes = sum(1 for v in resultado.values() if v)
    total_esperados = len(arquivos_esperados)

    if faltantes:
        status = "WARNING"
    else:
        status = "OK"

    return {
        "arquivos": resultado,
        "total_presentes": total_presentes,
        "total_esperados": total_esperados,
        "faltantes": faltantes,
        "status": status,
    }


# ============================================================
# 6) SYSTEM HEALTH (completo)
# ============================================================


def system_health() -> HealthResult:
    """
    Executa TODAS as validações do sistema.

    Returns:
        HealthResult com status consolidado, warnings, errors,
        e dicts individuais de cada validação.
    """
    warnings: List[str] = []
    errors_list: List[str] = []

    # ── Diretórios ──
    dirs_result = ensure_directories()
    dirs_ok = all(dirs_result.values())  # True se todas já existiam
    if not dirs_ok:
        novas = [nome for nome, ja_existia in dirs_result.items() if not ja_existia]
        warnings.append(f"Pastas criadas: {', '.join(novas)}")

    # ── Ambiente ──
    env_result = validate_env()
    if env_result["status"] == "ERROR":
        errors_list.append(f".env não encontrado em {ROOT_DIR}")
    elif env_result["status"] == "WARNING":
        faltantes_env = env_result.get("faltantes", [])
        warnings.append(f"Variáveis não definidas no .env: {', '.join(faltantes_env)}")

    # ── Banco ──
    db_result = validate_database()
    if db_result["status"] == "ERROR":
        for err in db_result.get("erros", []):
            errors_list.append(f"Banco: {err}")

    # ── Arquivos ──
    files_result = validate_requirements()
    if files_result["status"] == "WARNING":
        warnings.append(
            f"Arquivos essenciais ausentes: {', '.join(files_result['faltantes'])}"
        )

    # ── Versão ──
    from services.version import VERSION, BUILD, AMBIENTE as VER_AMBIENTE

    # ── Status consolidado ──
    if errors_list:
        overall_status = "ERROR"
    elif warnings:
        overall_status = "WARNING"
    else:
        overall_status = "OK"

    return HealthResult(
        status=overall_status,
        warnings=warnings,
        errors=errors_list,
        directories={
            "todas_existiam": dirs_ok,
            "pastas": {
                nome: ("já existia" if ja_existia else "criada agora")
                for nome, ja_existia in dirs_result.items()
            },
        },
        database=db_result,
        environment=env_result,
        files=files_result,
        version=f"v{VERSION} (build {BUILD}) [{VER_AMBIENTE}]",
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )


# ============================================================
# 7) DETECÇÃO DE PRIMEIRA INSTALAÇÃO
# ============================================================


def is_first_install() -> bool:
    """
    Detecta se é a primeira instalação do sistema.

    Retorna True quando:
        - crm.db NÃO existe, OU
        - crm.db existe mas NÃO tem tabelas

    Returns:
        bool
    """
    if not DB_PATH.exists():
        return True

    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table';"
        )
        qtd = cursor.fetchone()[0]
        conn.close()
        return qtd == 0
    except Exception:
        return True


# ============================================================
# 8) RELATÓRIO DE INSTALAÇÃO
# ============================================================


def installation_report() -> str:
    """
    Gera um relatório formatado da instalação atual.

    NÃO salva em arquivo. Somente retorna string.

    Returns:
        String multilinha com relatório completo.
    """
    health = system_health()
    from services.version import VERSION, BUILD, AMBIENTE as VER_AMBIENTE

    status_icon = {"OK": "✔", "WARNING": "⚠", "ERROR": "✖"}.get(
        health.status, "?"
    )

    linhas = [
        "=" * 56,
        "  ULITEC CRM — Relatório de Instalação",
        "=" * 56,
        "",
        f"  Data/Hora:      {health.timestamp}",
        f"  Versão:         v{VERSION} (build {BUILD})",
        f"  Ambiente:       {VER_AMBIENTE}",
        f"  Status Global:  {status_icon} {health.status}",
        "",
        "-" * 56,
        "  📁 PASTAS",
        "-" * 56,
    ]

    for nome, status_str in health.directories.get("pastas", {}).items():
        icon = "✔" if "já existia" in status_str else "➕"
        linhas.append(f"  {icon} {nome}")

    linhas.extend([
        "",
        "-" * 56,
        "  🗄️ BANCO DE DADOS",
        "-" * 56,
    ])

    db = health.database
    if db.get("existe"):
        linhas.append(f"  Arquivo:        crm.db ({db.get('tamanho_kb', 0):.1f} KB)")
        linhas.append(f"  Integridade:    {db.get('integridade', 'N/A')}")
        linhas.append(f"  Journal Mode:   {db.get('journal_mode', 'N/A')}")
        linhas.append(f"  Foreign Keys:   {'ON' if db.get('foreign_keys') else 'OFF'}")
        linhas.append(f"  Schema Version: {db.get('schema_version', 'N/A')}")
        linhas.append(f"  Tabelas:        {db.get('quantidade_tabelas', 0)}")
    else:
        linhas.append("  ❌ Banco de dados NÃO encontrado.")

    linhas.extend([
        "",
        "-" * 56,
        "  ⚙️ CONFIGURAÇÃO (.env)",
        "-" * 56,
    ])

    env = health.environment
    linhas.append(f"  .env existe:    {'✔' if env.get('existe') else '✖'}")
    for var_nome, var_info in env.get("variaveis", {}).items():
        icon = "✔" if var_info.get("configurada") else "✖"
        valor = var_info.get("valor") or var_info.get("valor_oculto", "?")
        linhas.append(f"  {icon} {var_nome}: {valor}")

    linhas.extend([
        "",
        "-" * 56,
        "  📄 ARQUIVOS ESSENCIAIS",
        "-" * 56,
    ])

    files = health.files
    for nome_arq, presente in files.get("arquivos", {}).items():
        icon = "✔" if presente else "✖"
        linhas.append(f"  {icon} {nome_arq}")
    linhas.append(
        f"  Total: {files.get('total_presentes', 0)}/{files.get('total_esperados', 0)}"
    )

    # Warnings e erros
    if health.warnings:
        linhas.extend([
            "",
            "-" * 56,
            "  ⚠ AVISOS",
            "-" * 56,
        ])
        for w in health.warnings:
            linhas.append(f"  ⚠ {w}")

    if health.errors:
        linhas.extend([
            "",
            "-" * 56,
            "  ❌ ERROS",
            "-" * 56,
        ])
        for e in health.errors:
            linhas.append(f"  ❌ {e}")

    linhas.extend([
        "",
        "=" * 56,
        f"  {status_icon} Health Check concluído: {health.status}",
        "=" * 56,
    ])

    return "\n".join(linhas)


# ============================================================
# ETAPA 3 — PREPARAÇÃO PARA MIGRAÇÕES FUTURAS
# ============================================================


def apply_pending_migrations() -> Dict:
    """
    Verifica e aplica migrações pendentes baseadas na versão.

    NESTE MOMENTO: Não executa nenhuma migração.
    Somente infraestrutura preparada para uso futuro.

    Mecanismo:
        - Compara VERSION atual com versões alvo
        - No futuro, cada bloco if executará as migrações necessárias

    Returns:
        {
            "executou": False,
            "motivo": "Nenhuma migração pendente (infraestrutura preparada)",
            "versoes_verificadas": [str, ...],
        }
    """
    from services.version import VERSION as CURRENT_VERSION

    # Placeholder — será preenchido em sprints futuras
    # Exemplo de como será usado:
    #
    # if CURRENT_VERSION < "1.1.0":
    #     # Executar migração para v1.1.0
    #     pass
    #
    # if CURRENT_VERSION < "1.2.0":
    #     # Executar migração para v1.2.0
    #     pass

    return {
        "executou": False,
        "motivo": "Nenhuma migração pendente (infraestrutura preparada para uso futuro)",
        "versoes_verificadas": [],
    }


# ═══════════════════════════════════════════════════════════
# AUTO-TESTE
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=== Deploy Manager — Teste Local ===\n")

    print("1) get_project_structure():")
    estrutura = get_project_structure()
    for nome, path in estrutura.items():
        print(f"   {nome}: {path}")

    print("\n2) ensure_directories():")
    resultado = ensure_directories()
    for nome, ja_existia in resultado.items():
        status = "já existia" if ja_existia else "criada agora"
        print(f"   {nome}: {status}")

    print("\n3) validate_env():")
    env = validate_env()
    print(f"   .env existe: {env['existe']}")
    print(f"   status: {env['status']}")
    print(f"   faltantes: {env['faltantes']}")

    print("\n4) validate_database():")
    db = validate_database()
    print(f"   existe: {db['existe']}")
    print(f"   integridade: {db['integridade']}")
    print(f"   tabelas: {db['quantidade_tabelas']}")
    print(f"   status: {db['status']}")

    print("\n5) validate_requirements():")
    files = validate_requirements()
    print(f"   status: {files['status']}")
    print(f"   presentes: {files['total_presentes']}/{files['total_esperados']}")

    print("\n6) system_health():")
    health = system_health()
    print(f"   status: {health.status}")
    print(f"   warnings: {health.warnings}")
    print(f"   errors: {health.errors}")

    print("\n7) is_first_install():")
    print(f"   primeira instalação? {is_first_install()}")

    print("\n8) installation_report():")
    print(installation_report())

    print("\n9) apply_pending_migrations():")
    print(f"   {apply_pending_migrations()}")