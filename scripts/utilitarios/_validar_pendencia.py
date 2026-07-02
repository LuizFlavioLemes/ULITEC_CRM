import sqlite3
import datetime

hoje = datetime.date.today().strftime("%Y-%m-%d")
conn = sqlite3.connect("crm.db")

# Buscar pendência específica
rows = conn.execute("""
    SELECT p.id, c.razao_social AS cliente, p.descricao, p.data_limite, p.status
    FROM pendencias_comerciais p
    LEFT JOIN clientes c ON p.cliente_id = c.id
    WHERE p.descricao LIKE '%ligar PC%'
""").fetchall()

print("=== DADOS DA PENDÊNCIA 'ligar PC' ===")
for r in rows:
    print(f"ID={r[0]}, Cliente={r[1]}, Desc={r[2]}, Data={r[3]}, Status={r[4]}")

# Validar se aparece em Pendências (sem filtro de data)
print("\n=== TESTE 1: get_pendencias() ===")
rows2 = conn.execute("""
    SELECT COUNT(*) FROM pendencias_comerciais p
    LEFT JOIN clientes c ON p.cliente_id = c.id
    WHERE p.status = 'ABERTA'
""").fetchone()
print(f"Total pendências abertas (sem filtro data): {rows2[0]}")

# Validar se aparece em Alertas (ANTES: data_limite < hoje)
print("\n=== TESTE 2: Alertas ANTES da correção (data_limite < hoje) ===")
rows3 = conn.execute("""
    SELECT COUNT(*) FROM pendencias_comerciais p
    LEFT JOIN clientes c ON p.cliente_id = c.id
    WHERE p.status = 'ABERTA' AND p.data_limite < ?
""", (hoje,)).fetchone()
print(f"Pendências com data_limite < hoje: {rows3[0]}")

# Validar se aparece em Alertas (DEPOIS: data_limite <= hoje)
print("\n=== TESTE 3: Alertas APÓS correção (data_limite <= hoje) ===")
rows4 = conn.execute("""
    SELECT COUNT(*) FROM pendencias_comerciais p
    LEFT JOIN clientes c ON p.cliente_id = c.id
    WHERE p.status = 'ABERTA' AND p.data_limite <= ?
""", (hoje,)).fetchone()
print(f"Pendências com data_limite <= hoje: {rows4[0]}")

# Listar as que aparecem com <=
print("\n=== Detalhe pendências com data_limite <= hoje ===")
rows5 = conn.execute("""
    SELECT p.id, c.razao_social, p.descricao, p.data_limite,
           CASE WHEN p.data_limite < ? THEN 'VENCIDA' ELSE 'VENCE HOJE' END AS classificacao
    FROM pendencias_comerciais p
    LEFT JOIN clientes c ON p.cliente_id = c.id
    WHERE p.status = 'ABERTA' AND p.data_limite <= ?
    ORDER BY p.data_limite
""", (hoje, hoje)).fetchall()
for r in rows5:
    print(f"  ID={r[0]} | {r[1]} | '{r[2]}' | {r[3]} | {r[4]}")

conn.close()