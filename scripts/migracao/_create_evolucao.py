import sqlite3

conn = sqlite3.connect("crm.db")

conn.execute("""
CREATE TABLE IF NOT EXISTS evolucao_pendencias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pendencia_id INTEGER NOT NULL,
    descricao TEXT NOT NULL,
    tipo_evolucao TEXT DEFAULT 'COMENTARIO',
    usuario_id INTEGER,
    usuario_nome TEXT,
    criado_em TEXT DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (pendencia_id) REFERENCES pendencias_comerciais(id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
)
""")
conn.commit()

c = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='evolucao_pendencias'")
print("Tabela criada:", c.fetchone()[0])

c2 = conn.execute("PRAGMA table_info(evolucao_pendencias)")
print("Colunas:", [(col[1], col[2]) for col in c2.fetchall()])

conn.close()