import sqlite3
conn = sqlite3.connect('crm.db')
cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cursor.fetchall()
for t in tables:
    print(f'\n=== {t[0]} ===')
    cols = conn.execute(f'PRAGMA table_info({t[0]})').fetchall()
    for c in cols:
        print(f'  {c[1]:30s} {c[2]:15s} nullable={not c[3]}')
conn.close()