"""
Módulo Central de Configuração — ULITEC CRM
============================================
Único ponto de definição de caminhos, constantes e
configurações globais do sistema.

Uso:
    from config import ROOT_DIR, DB_PATH, BACKUPS_DIR, AMBIENTE

Todos os caminhos utilizam pathlib.Path.
Nenhum caminho string manual em qualquer outro módulo.
"""

import os
from pathlib import Path

# ═══════════════════════════════════════════════════════════
# AMBIENTE
# ═══════════════════════════════════════════════════════════

AMBIENTE = os.getenv("ULITEC_AMBIENTE", "DEV").upper()  # DEV | CLOUD

# ═══════════════════════════════════════════════════════════
# DIRETÓRIO RAIZ
# ═══════════════════════════════════════════════════════════

ROOT_DIR = Path(__file__).resolve().parent

# ═══════════════════════════════════════════════════════════
# BANCO DE DADOS
# ═══════════════════════════════════════════════════════════

DB_PATH = ROOT_DIR / "crm.db"

# ═══════════════════════════════════════════════════════════
# PASTAS DO SISTEMA (criadas automaticamente se necessário)
# ═══════════════════════════════════════════════════════════

LOGS_DIR = ROOT_DIR / "logs"
BACKUPS_DIR = ROOT_DIR / "backups"
EXPORTS_DIR = BACKUPS_DIR / "export"
MANIFESTOS_DIR = BACKUPS_DIR / "manifestos"
UPLOADS_DIR = ROOT_DIR / "uploads"
TEMP_DIR = ROOT_DIR / "temp"
DOCS_DIR = ROOT_DIR / "docs"

# ═══════════════════════════════════════════════════════════
# METADADOS DO SISTEMA
# ═══════════════════════════════════════════════════════════

SYSTEM_NAME = "CRM Industrial ULITEC"

# Versão e metadados do sistema — FONTE ÚNICA em services/version.py
from services.version import VERSION as SYSTEM_VERSION
from services.version import get_version_info, get_version_string, get_banner
DB_VERSION = SYSTEM_VERSION

# ═══════════════════════════════════════════════════════════
# TIMEZONE
# ═══════════════════════════════════════════════════════════

TIMEZONE = "America/Sao_Paulo"

# ═══════════════════════════════════════════════════════════
# CHAVES DE CONFIGURAÇÃO NO .ENV
# ═══════════════════════════════════════════════════════════

MASTER_PASSWORD = os.getenv("MASTER_PASSWORD", "")

# ── Fallback para Streamlit Cloud: tenta ler de st.secrets se disponível ──
if not MASTER_PASSWORD:
    try:
        import streamlit as st
        MASTER_PASSWORD = st.secrets.get("MASTER_PASSWORD", "")
    except Exception:
        pass  # st.secrets não disponível (não estamos no Streamlit Cloud)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
IA_PROVIDER = os.getenv("IA_PROVIDER", "groq").strip().lower()

# ═══════════════════════════════════════════════════════════
# CONVENIÊNCIA — CRIAÇÃO DE PASTAS
# ═══════════════════════════════════════════════════════════

def ensure_directories():
    """Garante que todas as pastas do sistema existam."""
    dirs = [
        LOGS_DIR,
        BACKUPS_DIR,
        EXPORTS_DIR,
        MANIFESTOS_DIR,
        UPLOADS_DIR,
        TEMP_DIR,
        DOCS_DIR,
    ]
    for d in dirs:
        d.mkdir(exist_ok=True, parents=True)