"""
Script de migração V1.9.X - Refatoração da Base de Produtos Importados

Nova modelagem:
  - produtos_importados → apenas dados do PRODUTO (sem fornecedor/FOB)
  - fornecedores_produto → cadastro de fornecedores (CRUD)
  - produtos_importados_fornecedores → OFERTA: produto + fornecedor + FOB

Migra dados existentes sem perder nada.
"""
import sqlite3
import os
import sys

DB_PATH = "crm.db"
BACKUP_PATH = "backups/crm_backup_pre_v1_9.db"


def get_conn():
    return sqlite3.connect(DB_PATH)


def fazer_backup():
    """Faz backup do banco antes da migração."""
    import shutil
    if os.path.exists(BACKUP_PATH):
        print(f"⚠️  Backup já existe em {BACKUP_PATH}")
        return True
    shutil.copy2(DB_PATH, BACKUP_PATH)
    print(f"✅ Backup criado: {BACKUP_PATH}")
    return True


def criar_tabelas():
    """Cria as novas tabelas se não existirem."""
    conn = get_conn()
    
    # 1. Tabela de fornecedores
    conn.execute("""
        CREATE TABLE IF NOT EXISTS fornecedores_produto (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE,
            pais TEXT,
            observacoes TEXT,
            ativo INTEGER DEFAULT 1,
            criado_em DATE DEFAULT (date('now')),
            atualizado_em DATE DEFAULT (date('now'))
        )
    """)
    
    # 2. Tabela de ofertas (produto + fornecedor)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS produtos_importados_fornecedores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER NOT NULL,
            fornecedor_id INTEGER NOT NULL,
            fob_atual_usd REAL,
            data_fob DATE,
            observacoes TEXT,
            ativo INTEGER DEFAULT 1,
            criado_em DATE DEFAULT (date('now')),
            atualizado_em DATE DEFAULT (date('now')),
            UNIQUE(produto_id, fornecedor_id),
            FOREIGN KEY (produto_id) REFERENCES produtos_importados(id),
            FOREIGN KEY (fornecedor_id) REFERENCES fornecedores_produto(id)
        )
    """)
    
    conn.commit()
    conn.close()
    print("✅ Tabelas criadas: fornecedores_produto, produtos_importados_fornecedores")


def migrar_dados():
    """
    Migra dados da estrutura antiga para a nova:
    1. Extrai fornecedores únicos da tabela produtos_importados
    2. Extrai produtos únicos (remove duplicatas por modelo_busca)
    3. Cria ofertas para cada combinação produto+fornecedor
    4. Preserva histórico vinculando ao produto correto
    """
    conn = get_conn()
    
    # ---- PASSO 1: Extrair fornecedores únicos ----
    print("\n📦 Passo 1: Extraindo fornecedores únicos...")
    fornecedores_existentes = conn.execute("""
        SELECT DISTINCT TRIM(fornecedor) as nome
        FROM produtos_importados
        WHERE fornecedor IS NOT NULL AND TRIM(fornecedor) != ''
        ORDER BY fornecedor
    """).fetchall()
    
    fornecedores_map = {}  # nome_original -> id_fornecedor
    for (nome,) in fornecedores_existentes:
        nome = nome.strip()
        if not nome:
            continue
        # Verificar se já existe (evitar duplicatas na migração)
        existente = conn.execute(
            "SELECT id FROM fornecedores_produto WHERE nome = ?",
            (nome,)
        ).fetchone()
        if existente:
            fornecedores_map[nome] = existente[0]
        else:
            conn.execute(
                "INSERT INTO fornecedores_produto (nome, ativo) VALUES (?, 1)",
                (nome,)
            )
            fornecedores_map[nome] = conn.execute(
                "SELECT id FROM fornecedores_produto WHERE nome = ?",
                (nome,)
            ).fetchone()[0]
    
    conn.commit()
    print(f"   → {len(fornecedores_map)} fornecedores extraídos")
    
    # ---- PASSO 2: Extrair produtos únicos por modelo_busca ----
    print("\n📦 Passo 2: Consolidando produtos únicos...")
    
    # Buscar todos os produtos ativos ordenados - manter o primeiro de cada modelo_busca
    produtos_antigos = conn.execute("""
        SELECT id, modelo, modelo_busca, descricao, tipo_produto_id, ncm_id,
               observacoes, ativo
        FROM produtos_importados
        WHERE ativo = 1
        ORDER BY modelo_busca, id
    """).fetchall()
    
    modelos_dedicados = {}  # modelo_busca -> id do produto mantido
    produtos_para_manter = []  # ids dos produtos que viram registros de PRODUTO
    
    for p in produtos_antigos:
        pid, modelo, modelo_busca, descricao, tipo_id, ncm_id, obs, ativo = p
        if modelo_busca not in modelos_dedicados:
            # Este é o primeiro registro com este modelo_busca → vira o PRODUTO
            modelos_dedicados[modelo_busca] = {
                "produto_id": pid,
                "modelo": modelo,
                "descricao": descricao,
                "tipo_produto_id": tipo_id,
                "ncm_id": ncm_id,
                "observacoes": obs,
            }
            produtos_para_manter.append(pid)
    
    # Atualizar a tabela produtos_importados: limpar dados de fornecedor dos produtos mantidos
    # Os demais registros (mesmo modelo, fornecedor diferente) serão convertidos em ofertas
    
    print(f"   → {len(produtos_para_manter)} produtos únicos identificados")
    
    # ---- PASSO 3: Criar ofertas ----
    print("\n📦 Passo 3: Criando ofertas de fornecedores...")
    
    ofertas_criadas = 0
    ofertas_pulado = 0
    produtos_antigos_todos = conn.execute("""
        SELECT id, modelo_busca, fornecedor, fob_atual_usd, data_fob, observacoes
        FROM produtos_importados
        WHERE ativo = 1
        ORDER BY modelo_busca, id
    """).fetchall()
    
    for p in produtos_antigos_todos:
        pid, modelo_busca, fornecedor_antigo, fob, data_fob, obs = p
        
        fornecedor_nome = fornecedor_antigo.strip() if fornecedor_antigo else ""
        if not fornecedor_nome:
            continue
        
        fornecedor_id = fornecedores_map.get(fornecedor_nome)
        if not fornecedor_id:
            continue
        
        # Encontrar o produto_id correto (o mantido na tabela produtos)
        produto_info = modelos_dedicados.get(modelo_busca)
        if not produto_info:
            continue
        
        produto_id = produto_info["produto_id"]
        
        # Verificar se já existe oferta para este produto+fornecedor
        oferta_existente = conn.execute("""
            SELECT id FROM produtos_importados_fornecedores
            WHERE produto_id = ? AND fornecedor_id = ?
        """, (produto_id, fornecedor_id)).fetchone()
        
        if oferta_existente:
            # Atualizar FOB se o valor atual for diferente
            conn.execute("""
                UPDATE produtos_importados_fornecedores
                SET fob_atual_usd = COALESCE(?, fob_atual_usd),
                    data_fob = COALESCE(?, data_fob),
                    observacoes = COALESCE(?, observacoes)
                WHERE id = ?
            """, (fob, data_fob, obs, oferta_existente[0]))
            ofertas_pulado += 1
        else:
            conn.execute("""
                INSERT INTO produtos_importados_fornecedores
                (produto_id, fornecedor_id, fob_atual_usd, data_fob, observacoes)
                VALUES (?, ?, ?, ?, ?)
            """, (produto_id, fornecedor_id, fob, data_fob, obs))
            ofertas_criadas += 1
    
    conn.commit()
    print(f"   → {ofertas_criadas} ofertas criadas, {ofertas_pulado} já existentes")
    
    # ---- PASSO 4: Migrar histórico ----
    print("\n📦 Passo 4: Migrando histórico FOB...")
    
    # O histórico já tem produto_id e fornecedor, precisamos vincular ao fornecedor correto
    conn.execute("""
        UPDATE produtos_importados_historico AS h
        SET fornecedor_busca = (
            SELECT fp.nome
            FROM fornecedores_produto fp
            WHERE TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
                LOWER(h.fornecedor), '.', ''), '-', ''), ',', ''), '  ', ' '), '  ', ' ')) 
                = TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
                LOWER(fp.nome), '.', ''), '-', ''), ',', ''), '  ', ' '), '  ', ' '))
            LIMIT 1
        )
        WHERE fornecedor_busca IS NULL
    """)
    conn.commit()
    
    print("   ✅ Histórico migrado")
    
    conn.close()
    print("\n✅ Migração concluída com sucesso!")


def verificar_integridade():
    """Verifica se a migração foi bem-sucedida."""
    conn = get_conn()
    
    total_produtos = conn.execute("SELECT COUNT(*) FROM produtos_importados WHERE ativo = 1").fetchone()[0]
    total_fornecedores = conn.execute("SELECT COUNT(*) FROM fornecedores_produto WHERE ativo = 1").fetchone()[0]
    total_ofertas = conn.execute("SELECT COUNT(*) FROM produtos_importados_fornecedores WHERE ativo = 1").fetchone()[0]
    total_historico = conn.execute("SELECT COUNT(*) FROM produtos_importados_historico").fetchone()[0]
    
    conn.close()
    
    print(f"\n📊 Verificação de integridade:")
    print(f"   Produtos: {total_produtos}")
    print(f"   Fornecedores: {total_fornecedores}")
    print(f"   Ofertas (Produto x Fornecedor): {total_ofertas}")
    print(f"   Registros Histórico: {total_historico}")


if __name__ == "__main__":
    print("=" * 60)
    print("  MIGRAÇÃO V1.9.X - PRODUTOS IMPORTADOS")
    print("=" * 60)
    
    resposta = input("Deseja iniciar a migração? (S/N): ")
    if resposta.upper() != "S":
        print("Migração cancelada.")
        sys.exit(0)
    
    fazer_backup()
    criar_tabelas()
    migrar_dados()
    verificar_integridade()
    
    print("\n" + "=" * 60)
    print("  MIGRAÇÃO FINALIZADA")
    print("=" * 60)