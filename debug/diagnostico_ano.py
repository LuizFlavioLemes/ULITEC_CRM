import sqlite3
import pandas as pd

conn = sqlite3.connect('crm.db')

# 1. Verificar tipos na tabela maquinas_mitsubishi
print('=== maquinas_mitsubishi.ano ===')
df = pd.read_sql_query('SELECT ano, typeof(ano) as tipo, COUNT(*) as qtd FROM maquinas_mitsubishi GROUP BY typeof(ano)', conn)
print(df.to_string())
print()

# Amostra dos valores
print('Amostra:')
df2 = pd.read_sql_query('SELECT ano FROM maquinas_mitsubishi LIMIT 20', conn)
print(df2.to_string())
print()

# 2. Verificar se há registros com ano vazio
cursor = conn.execute("SELECT COUNT(*) as vazios FROM maquinas_mitsubishi WHERE ano = '' OR ano IS NULL")
row = cursor.fetchone()
print(f'Registros com ano vazio/nulo: {row[0]}')
print()

# 3. Amostra de registros com ano vazio se existir
if row[0] > 0:
    print('Amostra de registros com ano vazio:')
    df_vazio = pd.read_sql_query("SELECT id, customer, machine, ano FROM maquinas_mitsubishi WHERE ano = '' OR ano IS NULL LIMIT 5", conn)
    print(df_vazio.to_string())
    print()

# 4. Verificar se ano como string tem valores não numéricos
print('Valores de ano que nao sao numeros puros:')
df_misto = pd.read_sql_query("SELECT DISTINCT ano FROM maquinas_mitsubishi WHERE ano != '' AND ano IS NOT NULL AND typeof(ano) = 'text' AND ano NOT GLOB '[0-9]*'", conn)
print(df_misto.to_string())
print()

# 5. Verificar faturamento - data_faturamento
print('=== faturamento.data_faturamento (amostra) ===')
df4 = pd.read_sql_query('SELECT data_faturamento FROM faturamento LIMIT 10', conn)
print(df4.to_string())
print()

# Verificar formatos variados
print('Formatos distintos de data_faturamento:')
df5 = pd.read_sql_query("SELECT data_faturamento, COUNT(*) as qtd FROM faturamento GROUP BY data_faturamento ORDER BY qtd DESC LIMIT 10", conn)
print(df5.to_string())

conn.close()