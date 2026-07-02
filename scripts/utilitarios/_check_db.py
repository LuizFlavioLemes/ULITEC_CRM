import sqlite3

conn = sqlite3.connect("crm.db")

# Tabelas
c = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in c.fetchall()]
print("TODAS TABELAS:", tables)

# Verificar tabelas específicas
for tbl in ["pendencias_comerciais", "evolucao_pendencias"]:
    if tbl in tables:
        cols = conn.execute(f"PRAGMA table_info({tbl})").fetchall()
        print(f"\nCOLUNAS {tbl}:", [(col[1], col[2]) for col in cols])
    else:
        print(f"\n{tbl}: NAO EXISTE")

conn.close()