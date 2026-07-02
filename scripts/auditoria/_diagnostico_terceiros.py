import sqlite3

conn = sqlite3.connect('crm.db')
cursor = conn.cursor()

# Ver status existentes
cursor.execute('SELECT DISTINCT status FROM terceiros_servicos')
status = cursor.fetchall()
print('=== STATUS EXISTENTES ===')
for s in status:
    print(f'  "{s[0]}"')
print()

# Ver quantos registros
cursor.execute('SELECT COUNT(*) FROM terceiros_servicos')
print(f'Total registros: {cursor.fetchone()[0]}')

# Ver alguns registros de exemplo
cursor.execute('SELECT id, status, data_envio, data_retorno FROM terceiros_servicos LIMIT 10')
rows = cursor.fetchall()
print()
print('=== AMOSTRA DE REGISTROS ===')
for r in rows:
    print(r)

# Verificar se colunas existem
cursor.execute("PRAGMA table_info(terceiros_servicos)")
cols = cursor.fetchall()
col_names = [c[1] for c in cols]
print()
print('=== COLUNAS ===')
print('\n'.join(col_names))

conn.close()