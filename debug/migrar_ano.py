import sqlite3

conn = sqlite3.connect('crm.db')

# 1. Corrigir registros existentes: converter '' para NULL
conn.execute("UPDATE maquinas_mitsubishi SET ano = NULL WHERE ano = '' OR ano IS NULL")
conn.commit()

# 2. Verificar resultado
c = conn.execute("SELECT typeof(ano) as tipo, COUNT(*) as qtd FROM maquinas_mitsubishi GROUP BY typeof(ano)")
print("Tipos de ano apos correcao:")
for row in c.fetchall():
    tipo = row[0]
    qtd = row[1]
    print(f"  {tipo}: {qtd}")

# 3. Verificar se ainda há strings
c2 = conn.execute("SELECT COUNT(*) FROM maquinas_mitsubishi WHERE typeof(ano) = 'text'")
print(f"Ainda como text: {c2.fetchone()[0]}")

conn.close()
print("Migracao concluida com sucesso.")