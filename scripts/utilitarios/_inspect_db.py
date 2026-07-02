import sqlite3
conn = sqlite3.connect('crm.db')
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
for t in tables:
    name = t[0]
    cols = conn.execute(f"PRAGMA table_info({name})").fetchall()
    print(f'\n=== {name} ===')
    for c in cols:
        print(f'  {c[1]} ({c[2]})')
conn.close()