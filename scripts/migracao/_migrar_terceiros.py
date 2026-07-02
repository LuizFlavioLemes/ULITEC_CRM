"""
Migração da tabela terceiros_servicos:
- Adiciona colunas data_orcamento, data_aprovacao, data_recebimento
- Preserva todos os dados existentes
- Mantém compatibilidade com status existentes: ENVIADO, ORÇADO, APROVADO, RECEBIDO, CANCELADO
"""
import sqlite3
import os

DB_PATH = 'crm.db'

def coluna_existe(cursor, tabela, coluna):
    cursor.execute(f"PRAGMA table_info({tabela})")
    colunas = [c[1] for c in cursor.fetchall()]
    return coluna in colunas

def migrar():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("=== DIAGNÓSTICO INICIAL ===")
    cursor.execute('SELECT COUNT(*) FROM terceiros_servicos')
    print(f"Registros existentes: {cursor.fetchone()[0]}")
    
    # Verificar colunas que precisam ser adicionadas
    novas_colunas = {
        'data_orcamento': 'DATE',
        'data_aprovacao': 'DATE',
        'data_recebimento': 'DATE'
    }
    
    colunas_adicionadas = []
    for col, tipo in novas_colunas.items():
        if not coluna_existe(cursor, 'terceiros_servicos', col):
            sql = f"ALTER TABLE terceiros_servicos ADD COLUMN {col} {tipo}"
            cursor.execute(sql)
            colunas_adicionadas.append(col)
            print(f"Coluna '{col}' adicionada.")
        else:
            print(f"Coluna '{col}' já existe.")
    
    conn.commit()
    
    print("\n=== VERIFICAÇÃO PÓS-MIGRAÇÃO ===")
    cursor.execute("PRAGMA table_info(terceiros_servicos)")
    print("\nEstrutura final da tabela:")
    for c in cursor.fetchall():
        print(f"  {c[1]:25s} {c[2]:10s} nullable={c[3]} default={c[4]}")
    
    cursor.execute('SELECT id, status, data_envio, data_orcamento, data_aprovacao, data_recebimento, data_retorno FROM terceiros_servicos')
    print("\nDados preservados:")
    for r in cursor.fetchall():
        print(f"  id={r[0]} status={r[1]} envio={r[2]} orcamento={r[3]} aprovacao={r[4]} recebimento={r[5]} retorno={r[6]}")
    
    conn.close()
    print("\nMigração concluída com sucesso!")

if __name__ == '__main__':
    migrar()