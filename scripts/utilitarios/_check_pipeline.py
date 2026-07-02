import sqlite3
conn = sqlite3.connect('crm.db')
cursor = conn.cursor()

# Listar todas as tabelas
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cursor.fetchall()
for t in tables:
    name = t[0]
    if 'pipeline' in name.lower() or 'os' in name.lower() or 'ordem' in name.lower() or 'servico' in name.lower():
        print(f'Tabela: {name}')
        cursor.execute(f'PRAGMA table_info({name})')
        cols = cursor.fetchall()
        for c in cols:
            print(f'  {c}')
        # Ver primeiros 3 registros
        try:
            cursor.execute(f'SELECT * FROM {name} LIMIT 3')
            rows = cursor.fetchall()
            print(f'  Amostra ({len(rows)} registros):')
            for r in rows:
                print(f'    {r}')
        except:
            pass
        print()
conn.close()