import sqlite3
import datetime

conn = sqlite3.connect("crm.db")
hoje = datetime.date.today().strftime("%Y-%m-%d")

print("=== ESTRUTURA ===")
for r in conn.execute("PRAGMA table_info(pendencias_comerciais)"):
    print(r)

print()

total = conn.execute("SELECT COUNT(*) FROM pendencias_comerciais").fetchone()[0]
abertas = conn.execute("SELECT COUNT(*) FROM pendencias_comerciais WHERE status='ABERTA'").fetchone()[0]
vencidas = conn.execute("SELECT COUNT(*) FROM pendencias_comerciais WHERE status='ABERTA' AND data_limite < ?", (hoje,)).fetchone()[0]
hoje_qtd = conn.execute("SELECT COUNT(*) FROM pendencias_comerciais WHERE status='ABERTA' AND data_limite = ?", (hoje,)).fetchone()[0]

print(f"Total de registros: {total}")
print(f"Abertas: {abertas}")
print(f"Vencidas (data_limite < hoje): {vencidas}")
print(f"Vence hoje (data_limite == hoje): {hoje_qtd}")

conn.close()