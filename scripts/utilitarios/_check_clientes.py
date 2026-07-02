import sqlite3
conn = sqlite3.connect('crm.db')
cursor = conn.cursor()

# Tabelas com cliente
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%cliente%' OR name LIKE '%clientes%' ORDER BY name")
tables = cursor.fetchall()
print("Tabelas relacionadas a clientes:")
for t in tables:
    print(f"  {t[0]}")

# Ver colunas da tabela clientes
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
for t in cursor.fetchall():
    name = t[0]
    if 'client' in name.lower():
        print(f"\n--- {name} ---")
        cursor.execute(f"PRAGMA table_info({name})")
        for c in cursor.fetchall():
            print(f"  {c}")
        # Amostra
        cursor.execute(f"SELECT * FROM {name} LIMIT 5")
        rows = cursor.fetchall()
        for r in rows:
            print(f"  {r}")

# Ver os cliente_ids da tabela ordens_servico para cruzar
print("\n\n--- ordens_servico (cliente_id sample) ---")
cursor.execute("SELECT DISTINCT cliente_id FROM ordens_servico LIMIT 10")
for r in cursor.fetchall():
    print(f"  cliente_id: {r[0]}")

conn.close()