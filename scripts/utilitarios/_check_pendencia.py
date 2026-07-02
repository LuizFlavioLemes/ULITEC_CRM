import sqlite3
conn = sqlite3.connect("crm.db")
rows = conn.execute("SELECT id, cliente_id, descricao, data_limite, status FROM pendencias_comerciais").fetchall()
print(f"Total de pendências: {len(rows)}")
for r in rows:
    print(r)
conn.close()