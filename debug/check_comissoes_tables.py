import sqlite3
from config import DB_PATH

conn = sqlite3.connect(str(DB_PATH))
cursor = conn.cursor()

print("=== CONFIRMACAO DOS PONTOS SOLICITADOS ===")
print()

# Ponto 1: quantidade_clientes
cursor.execute("PRAGMA table_info(fechamento_mensal)")
cols = {c[1] for c in cursor.fetchall()}
print(f"[1] Campo quantidade_clientes: {'OK' if 'quantidade_clientes' in cols else 'FALTA'}")

# Ponto 2: cliente_id e os_id opcionais em comissoes_avulsas
cursor.execute("PRAGMA table_info(comissoes_avulsas)")
cols_info = cursor.fetchall()
cliente_nullable = any(c[1] == 'cliente_id' and c[3] == 0 for c in cols_info)
os_nullable = any(c[1] == 'os_id' and c[3] == 0 for c in cols_info)
print(f"[2] cliente_id opcional: {'OK' if cliente_nullable else 'FALTA'}")
print(f"    os_id opcional: {'OK' if os_nullable else 'FALTA'}")

# Ponto 3: descricao e observacoes TEXT sem limitacao
descricao_type = next((c[2] for c in cols_info if c[1] == 'descricao'), '')
observacoes_type = next((c[2] for c in cols_info if c[1] == 'observacoes'), '')
print(f"[3] descricao tipo TEXT: {'OK' if 'TEXT' in descricao_type else 'FALTA'}")
print(f"    observacoes tipo TEXT: {'OK' if 'TEXT' in observacoes_type else 'FALTA'}")

# Ponto 4: Indices
cursor.execute("SELECT name FROM sqlite_master WHERE type='index' ORDER BY name")
indices = {r[0] for r in cursor.fetchall()}
indices_esperados = [
    'idx_fechamento_competencia',
    'idx_fechamento_parceiro',
    'idx_fechamento_status',
    'idx_carteira_parceiro',
    'idx_carteira_cliente',
    'idx_comissoes_avulsas_parceiro',
    'idx_comissoes_avulsas_status',
    'idx_comissoes_avulsas_data',
]
print(f"[4] Indices de performance:")
for idx in indices_esperados:
    status = 'OK' if idx in indices else 'FALTA'
    print(f"    {status} {idx}")

# Ponto 5: UNIQUE(parceiro_id, cliente_id) na carteira
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='carteira_clientes'")
sql = cursor.fetchone()[0]
has_unique = 'UNIQUE' in sql and 'parceiro_id' in sql and 'cliente_id' in sql
print(f"[5] UNIQUE(parceiro_id, cliente_id): {'OK' if has_unique else 'FALTA'}")

print()
print("=== RESUMO ===")
cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index'")
total_idx = cursor.fetchone()[0]
total_modulo = sum(1 for i in indices if i.startswith('idx_'))
print(f"Total indices no banco: {total_idx}")
print(f"Indices do modulo: {total_modulo}/8")

conn.close()