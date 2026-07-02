import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import sqlite3
import pandas as pd
from services.inteligencia_comercial import classificar_abcd

conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), "..", "crm.db"))

# Total de clientes ativos
df_total = pd.read_sql_query("SELECT COUNT(*) as total FROM clientes WHERE status='ATIVO'", conn)
print("Total clientes ATIVOS:", df_total["total"].values[0])

# Clientes com faturamento_12m > 0
df_com_fat = pd.read_sql_query(
    "SELECT COUNT(*) as total FROM clientes WHERE status='ATIVO' AND COALESCE(faturamento_12m,0) > 0",
    conn,
)
print("Clientes com faturamento_12m > 0:", df_com_fat["total"].values[0])

# Clientes com faturamento_12m = 0 ou NULL
df_sem_fat = pd.read_sql_query(
    "SELECT COUNT(*) as total FROM clientes WHERE status='ATIVO' AND (faturamento_12m IS NULL OR faturamento_12m = 0)",
    conn,
)
print("Clientes com faturamento_12m = 0 ou NULL:", df_sem_fat["total"].values[0])

conn.close()

# Testar classificar_abcd SEM filtro de unidade (GRUPO)
print("\n" + "="*60)
print("classificar_abcd(unidade=None) - GRUPO")
print("="*60)
df_abc = classificar_abcd(unidade=None)
print("value_counts:")
print(df_abc["classe_abc"].value_counts(dropna=False))
print("Total:", len(df_abc))

# Amostra D
df_d = df_abc[df_abc["classe_abc"] == "D"]
print("\nAmostra D (primeiros 10):")
for _, row in df_d.head(10).iterrows():
    print(f"  id={row['id']} | razao={str(row['razao_social'])[:30]:30s} | fat_12m={row['faturamento_12m']:>10.2f}")

# Verificar se os D têm faturamento > 0
df_d_com_fat = df_d[df_d["faturamento_12m"] > 0]
print(f"\nClientes D com faturamento > 0: {len(df_d_com_fat)}")

# Testar com unidade SP
print("\n" + "="*60)
print("classificar_abcd(unidade='ULITEC SP')")
print("="*60)
df_sp = classificar_abcd(unidade="ULITEC SP")
print("value_counts:")
print(df_sp["classe_abc"].value_counts(dropna=False))
print("Total:", len(df_sp))

# Testar com unidade RS
print("\n" + "="*60)
print("classificar_abcd(unidade='ULITEC RS')")
print("="*60)
df_rs = classificar_abcd(unidade="ULITEC RS")
print("value_counts:")
print(df_rs["classe_abc"].value_counts(dropna=False))
print("Total:", len(df_rs))