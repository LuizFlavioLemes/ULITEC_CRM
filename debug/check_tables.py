import sqlite3
from pathlib import Path

db_path = Path(__file__).resolve().parent.parent / "crm.db"
print(f"Verificando banco: {db_path}")
print(f"Arquivo existe: {db_path.exists()}, tamanho: {db_path.stat().st_size if db_path.exists() else 0}")

conn = sqlite3.connect(str(db_path))
tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print(f"\nTotal de tabelas: {len(tables)}")
print("Tabelas existentes:")
for t in sorted(tables):
    count = conn.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
    print(f"  - {t} ({count} registros)")

print(f"\nFaltando pendencias_comerciais: {'pendencias_comerciais' not in tables}")
print(f"Faltando produtos_importados: {'produtos_importados' not in tables}")
conn.close()