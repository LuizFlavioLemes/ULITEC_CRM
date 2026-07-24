"""
Script de auditoria de produção — ULITEC CRM
Verifica: banco, imports, tabelas, dependências, prints, arquivos deploy
"""
import os, sys, sqlite3
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# ── 1. BANCO ──
db_path = Path("crm.db").resolve()
print(f"[BANCO] Existe: {db_path.exists()}")
print(f"[BANCO] Caminho: {db_path}")
print(f"[BANCO] Tamanho: {db_path.stat().st_size} bytes")

conn = sqlite3.connect(str(db_path))
cur = conn.cursor()
for pragma in ["journal_mode", "synchronous", "foreign_keys"]:
    cur.execute(f"PRAGMA {pragma}")
    print(f"[BANCO] {pragma}: {cur.fetchone()[0]}")

tables = cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
print(f"[BANCO] Tabelas ({len(tables)}):")
for t in tables:
    count = cur.execute(f"SELECT COUNT(*) FROM {t[0]}").fetchone()[0]
    print(f"   - {t[0]}: {count} registros")
conn.close()

# ── 2. IMPORTS ──
ok = True
modules = [
    "database, db, get_connection",
    "config, DB_PATH, ROOT_DIR",
    "auth, init_auth, verificar_login, mostrar_login",
    "permissions, pode_selecionar_unidade",
    "services.version, VERSION",
    "services.inteligencia_comercial",
    "services.mitsubishi",
    "services.parceiros",
    "services.relacionamento",
    "services.admin_sistema",
    "services.comissoes_db",
    "services.comissoes_calculo",
    "services.comissoes_consultas",
    "services.comissoes_dashboard",
    "services.comissoes_fechamento",
    "services.ia.data_collector",
    "services.ia.prompt_builder",
    "services.ia.gemini_client",
    "services.ia.groq_client",
    "services.ia.openai_client",
    "services.ia.ia_client",
    "services.ia.engine",
    "services.ia.relatorio_ulitec",
    "database.sqlite_provider",
    "database.provider",
    "components.ui",
    "utils.bootstrap",
    "utils.db_init",
    "services.deploy_manager",
]
for mod in modules:
    try:
        parts = mod.split(",")[0].strip()
        exec(f"from {parts} import *" if "*" not in parts else f"import {parts}")
    except Exception as e:
        print(f"[IMPORT] FALHA: {mod} -> {e}")
        ok = False
if ok:
    print("[IMPORT] Todos os 28 módulos importaram OK")
else:
    print("[IMPORT] HOUVE FALHA(S)!")

# ── 3. REQUIREMENTS ──
req_path = Path("requirements.txt")
if req_path.exists():
    libs = req_path.read_text().strip().split("\n")
    print(f"[REQUIREMENTS] {len(libs)} dependências listadas")
    for lib in libs:
        lib = lib.strip()
        if not lib or lib.startswith("#"):
            continue
        pkg = lib.split(">=")[0].split("==")[0].strip()
        try:
            __import__(pkg.replace("-", "_"))
        except ImportError:
            print(f"[REQUIREMENTS] FALTA: {pkg}")

# ── 4. DEPLOY FILES ──
for f in ["passenger_wsgi.py", "requirements.txt", ".gitignore"]:
    print(f"[DEPLOY] {f}: {'EXISTE' if Path(f).exists() else 'FALTA'}")
print(f"[DEPLOY] Procfile: {'EXISTE' if Path('Procfile').exists() else 'NÃO CRIADO'}")
print(f"[DEPLOY] runtime.txt: {'EXISTE' if Path('runtime.txt').exists() else 'NÃO CRIADO'}")

# ── 5. ENV VARs OBRIGATÓRIAS ──
from dotenv import load_dotenv
load_dotenv(override=True)
obrigatorias = ["IA_PROVIDER", "GROQ_API_KEY"]
for var in obrigatorias:
    val = os.getenv(var, "")
    print(f"[ENV] {var}: {'CONFIGURADO' if val else 'FALTANDO!'}")

# ── 6. LOGS (TODO, FIXME, DEBUG, print() suspeitos) ──
print("\n[LOGS] Verificando prints e marcadores...")
for root, dirs, files in os.walk("."):
    dirs[:] = [d for d in dirs if d not in ("__pycache__", ".git", "backup", "debug", "scripts", "docs", "legacy")]
    for fname in files:
        if not fname.endswith(".py"):
            continue
        fpath = Path(root) / fname
        lines = fpath.read_text(encoding="utf-8", errors="ignore").split("\n")
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            # print() sem ser de warning/error/info
            if stripped == 'print("Banco ULITEC criado com sucesso!")':
                continue
            if 'print(' in stripped and 'st.' not in stripped and 'logging' not in stripped:
                if stripped.startswith("#") or 'debug' in fname:
                    continue
                print(f"   PRINT: {fpath}:{i}: {stripped[:80]}")
            if 'TODO' in stripped and 'never executed' not in stripped:
                print(f"   TODO: {fpath}:{i}: {stripped[:80]}")
            # FIXME e DEBUG
            if 'FIXME' in stripped and stripped.startswith("#"):
                print(f"   FIXME: {fpath}:{i}: {stripped[:80]}")

print("\n=== AUDITORIA CONCLUIDA ===")