import sqlite3
import pandas as pd

conn = sqlite3.connect('crm.db')

# Listar todas as tabelas
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print("=== TABELAS E COLUNAS COM TIPOS MISTOS ===")
print()

for t in tables:
    table_name = t[0]
    # Ler schema da tabela
    cols = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    for col in cols:
        col_name = col[1]
        col_type = col[2]
        # Verificar tipos reais no banco
        try:
            query = f"SELECT typeof({col_name}) as tipo, count(*) as qtd FROM {table_name} GROUP BY typeof({col_name})"
            df_types = pd.read_sql_query(query, conn)
            if len(df_types) > 1:
                # Mostrar detalhes
                tipos_str = ", ".join([f"{r['tipo']}: {r['qtd']}" for _, r in df_types.iterrows()])
                print(f"[MISTO] {table_name}.{col_name} (schema: {col_type}) -> {tipos_str}")
        except Exception as e:
            pass

print()
print("=== VERIFICACAO FINAL - coluna ano ===")
df_ano = pd.read_sql_query("SELECT typeof(ano) as tipo, count(*) as qtd FROM maquinas_mitsubishi GROUP BY typeof(ano)", conn)
print(df_ano.to_string())

conn.close()
print()
print("Auditoria preventiva concluida.")