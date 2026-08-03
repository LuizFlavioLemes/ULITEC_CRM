"""
garantir_schema(db_path)
───────────────────────
Inicialização defensiva do schema SQLite antes de qualquer página rodar.
Garante que TODAS as tabelas e colunas críticas existam no .db,
evitando crashes em produção por schema ausente.
"""

import os
from database import db

def garantir_schema(db_path: str):
    """Cria tabelas faltantes e adiciona colunas críticas se ausentes."""

    # Se o arquivo .db não existe, o provider já cria. Mas se o
    # diretório não existir, criamos.
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

    conn = db.get_connection()
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    cur = conn.cursor()

    # ──────────────────────────────────────────────────
    # CREATE TABLE IF NOT EXISTS (todas as tabelas do sistema)
    # ──────────────────────────────────────────────────

    cur.execute("""
    CREATE TABLE IF NOT EXISTS unidades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        sigla TEXT,
        cidade TEXT,
        estado TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS faturamento_itens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id INTEGER,
        unidade TEXT,
        descricao_item TEXT,
        tipo_item TEXT,
        data_venda DATE,
        valor_total REAL,
        origem TEXT,
        data_importacao DATE
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT,
        senha TEXT,
        perfil TEXT,
        unidade_id INTEGER,
        ativo INTEGER DEFAULT 1
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo_erp TEXT UNIQUE,
        razao_social TEXT,
        nome_fantasia TEXT,
        cnpj TEXT,
        cidade TEXT,
        estado TEXT,
        telefone TEXT,
        email TEXT,
        segmento TEXT,
        parque_maquinas INTEGER DEFAULT 0,
        maquinas_mitsubishi INTEGER DEFAULT 0,
        frequencia_visita INTEGER DEFAULT 90,
        tipo_conta TEXT DEFAULT 'LEAD FRIO',
        classe_abc TEXT DEFAULT 'D',
        faturamento_12m REAL DEFAULT 0,
        ultima_visita DATE,
        ultimo_faturamento DATE,
        origem_erp TEXT,
        observacoes TEXT,
        ultima_importacao DATE,
        status TEXT DEFAULT 'ATIVO',
        data_cadastro DATE DEFAULT (date('now')),
        origem_cadastro TEXT DEFAULT 'IMPORTACAO_CLIENTES'
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS interacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id INTEGER,
        data_interacao DATE,
        tipo_interacao TEXT,
        assunto TEXT,
        responsavel TEXT,
        usuario_id INTEGER,
        unidade TEXT,
        qtd_maquinas INTEGER,
        qtd_mitsubishi INTEGER,
        brinde_entregue TEXT,
        status_cliente TEXT,
        nivel_producao TEXT,
        perspectiva_6m TEXT,
        concorrentes TEXT,
        resumo TEXT,
        resultado TEXT,
        proxima_acao TEXT,
        data_proxima_acao DATE,
        status_interacao TEXT DEFAULT 'ABERTA',
        contato_nome TEXT,
        contato_cargo TEXT,
        contato_telefone TEXT,
        contato_email TEXT,
        tipo_prox_acao TEXT,
        obs_prox_acao TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS propostas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero_os TEXT,
        cliente_id INTEGER,
        unidade TEXT,
        data_recebimento DATE,
        data_envio_proposta DATE,
        data_aprovacao DATE,
        data_faturamento DATE,
        data_expedicao DATE,
        valor_proposta REAL,
        status TEXT,
        observacoes TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS ordens_servico (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero_os TEXT UNIQUE,
        cliente_id INTEGER,
        unidade TEXT,
        responsavel TEXT,
        equipamento TEXT,
        marca TEXT,
        modelo TEXT,
        serial_number TEXT,
        data_recebimento DATE,
        data_envio_proposta DATE,
        data_aprovacao DATE,
        data_faturamento DATE,
        data_expedicao DATE,
        data_perda DATE,
        valor_estimado REAL DEFAULT 0,
        valor_proposta REAL DEFAULT 0,
        status TEXT DEFAULT 'RECEBIDA',
        motivo_perda TEXT,
        proximo_followup DATE,
        observacoes TEXT,
        origem TEXT DEFAULT 'MANUAL',
        data_criacao DATE,
        data_atualizacao DATE
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS faturamento (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id INTEGER,
        unidade TEXT,
        data_faturamento DATE,
        valor REAL,
        tipo TEXT,
        origem TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS maquinas_mitsubishi (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer TEXT,
        address TEXT,
        city TEXT,
        uf TEXT,
        machine TEXT,
        serial_number TEXT,
        nc_series TEXT,
        nc_type TEXT,
        dealer TEXT,
        warranty_start TEXT,
        warranty_end TEXT,
        ano INTEGER,
        cliente_id INTEGER,
        score_match REAL,
        validado INTEGER DEFAULT 0
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS conciliacao_mitsubishi (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        maquina_id INTEGER,
        cliente_sugerido_id INTEGER,
        customer TEXT,
        cliente_sugerido TEXT,
        score REAL,
        status TEXT DEFAULT 'REVISAO'
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS oportunidades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id INTEGER,
        unidade TEXT,
        data_abertura DATE,
        origem TEXT,
        descricao TEXT,
        valor_estimado REAL,
        status TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS alertas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo TEXT,
        descricao TEXT,
        data_alerta DATE,
        resolvido INTEGER DEFAULT 0
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS configuracoes (
        chave TEXT PRIMARY KEY,
        valor TEXT,
        descricao TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS pendencias_comerciais (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id INTEGER,
        interacao_id INTEGER,
        descricao TEXT,
        prioridade TEXT DEFAULT 'MEDIA',
        responsavel TEXT,
        data_limite DATE,
        status TEXT DEFAULT 'ABERTA',
        criado_em DATE DEFAULT (date('now')),
        FOREIGN KEY (cliente_id) REFERENCES clientes(id),
        FOREIGN KEY (interacao_id) REFERENCES interacoes(id)
    )
    """)

    cur.execute("""
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

    cur.execute("""
    CREATE TABLE IF NOT EXISTS tipo_produto_importado (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        descricao TEXT NOT NULL UNIQUE,
        ii REAL DEFAULT 0,
        ipi REAL DEFAULT 0,
        pis REAL DEFAULT 0,
        cofins REAL DEFAULT 0,
        icms REAL DEFAULT 0,
        ativo INTEGER DEFAULT 1
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS ncm_importacao (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ncm TEXT NOT NULL UNIQUE,
        descricao TEXT DEFAULT '',
        tipo_produto_id INTEGER,
        ativo INTEGER DEFAULT 1,
        criado_em DATE DEFAULT (date('now')),
        atualizado_em DATE DEFAULT (date('now')),
        FOREIGN KEY (tipo_produto_id) REFERENCES tipo_produto_importado(id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS config_importacao (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chave TEXT NOT NULL UNIQUE,
        valor REAL NOT NULL,
        descricao TEXT DEFAULT ''
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS produtos_importados (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        modelo TEXT NOT NULL UNIQUE,
        modelo_busca TEXT DEFAULT '',
        descricao TEXT DEFAULT '',
        tipo_produto_id INTEGER,
        ncm_id INTEGER,
        fornecedor TEXT DEFAULT '',
        fob_atual_usd REAL DEFAULT 0,
        data_fob DATE,
        observacoes TEXT DEFAULT '',
        ativo INTEGER DEFAULT 1,
        ultimo_preco_venda REAL DEFAULT NULL,
        criado_em DATE DEFAULT (date('now')),
        atualizado_em DATE DEFAULT (date('now')),
        FOREIGN KEY (tipo_produto_id) REFERENCES tipo_produto_importado(id),
        FOREIGN KEY (ncm_id) REFERENCES ncm_importacao(id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS fornecedores_produto (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL UNIQUE,
        pais TEXT DEFAULT '',
        observacoes TEXT DEFAULT '',
        ativo INTEGER DEFAULT 1,
        criado_em DATE DEFAULT (date('now')),
        atualizado_em DATE DEFAULT (date('now'))
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS produtos_importados_fornecedores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        produto_id INTEGER NOT NULL,
        fornecedor_id INTEGER NOT NULL,
        fob_atual_usd REAL DEFAULT 0,
        data_fob DATE,
        observacoes TEXT DEFAULT '',
        ativo INTEGER DEFAULT 1,
        criado_em DATE DEFAULT (date('now')),
        atualizado_em DATE DEFAULT (date('now')),
        FOREIGN KEY (produto_id) REFERENCES produtos_importados(id),
        FOREIGN KEY (fornecedor_id) REFERENCES fornecedores_produto(id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS produtos_importados_historico (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        produto_id INTEGER,
        fornecedor TEXT DEFAULT '',
        valor_fob_usd REAL DEFAULT 0,
        data_atualizacao DATE,
        usuario_id INTEGER,
        observacao TEXT DEFAULT '',
        criado_em DATE DEFAULT (date('now')),
        FOREIGN KEY (produto_id) REFERENCES produtos_importados(id),
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS terceiros_fornecedores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL UNIQUE,
        cidade TEXT DEFAULT '',
        estado TEXT DEFAULT '',
        contato TEXT DEFAULT '',
        telefone TEXT DEFAULT '',
        observacoes TEXT DEFAULT '',
        ativo INTEGER DEFAULT 1,
        criado_em DATE DEFAULT (date('now')),
        atualizado_em DATE DEFAULT (date('now'))
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS terceiros_servicos_tipos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL UNIQUE,
        categoria TEXT DEFAULT '',
        ativo INTEGER DEFAULT 1,
        criado_em DATE DEFAULT (date('now'))
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS terceiros_marcas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL UNIQUE,
        ativo INTEGER DEFAULT 1,
        criado_em DATE DEFAULT (date('now'))
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS terceiros_servicos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fornecedor_id INTEGER NOT NULL,
        marca_id INTEGER NOT NULL,
        servico_id INTEGER NOT NULL,
        modelo TEXT NOT NULL,
        descricao TEXT DEFAULT '',
        valor REAL DEFAULT 0,
        status TEXT DEFAULT 'ENVIADO',
        data_envio DATE,
        data_retorno DATE,
        observacoes TEXT DEFAULT '',
        usuario TEXT DEFAULT '',
        data_cadastro DATE DEFAULT (date('now')),
        ultima_atualizacao DATE DEFAULT (date('now')),
        os_erp TEXT DEFAULT NULL,
        cliente_id INTEGER DEFAULT NULL,
        equipamento_id INTEGER DEFAULT NULL,
        numero_serie TEXT DEFAULT NULL,
        custo_interno REAL DEFAULT NULL,
        valor_cobrado_cliente REAL DEFAULT NULL,
        FOREIGN KEY (fornecedor_id) REFERENCES terceiros_fornecedores(id),
        FOREIGN KEY (marca_id) REFERENCES terceiros_marcas(id),
        FOREIGN KEY (servico_id) REFERENCES terceiros_servicos_tipos(id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS config_ia (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        api_key TEXT,
        modelo TEXT DEFAULT 'gpt-4o-mini',
        ativo INTEGER DEFAULT 1,
        criado_em TEXT DEFAULT (datetime('now', 'localtime')),
        atualizado_em TEXT DEFAULT (datetime('now', 'localtime'))
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS relatorios_ia (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id INTEGER,
        modelo TEXT,
        prompt_tokens INTEGER DEFAULT 0,
        completion_tokens INTEGER DEFAULT 0,
        tempo_execucao REAL DEFAULT 0,
        custo_estimado REAL DEFAULT 0,
        criado_em TEXT DEFAULT (datetime('now', 'localtime'))
    )
    """)

    # ──────────────────────────────────────────────────
    # ALTER TABLE defensivo — colunas críticas
    # ──────────────────────────────────────────────────

    _add_column_if_missing(cur, "fornecedores_produto", "ativo", "INTEGER DEFAULT 1")
    _add_column_if_missing(cur, "fornecedores_produto", "criado_em", "DATE DEFAULT (date('now'))")
    _add_column_if_missing(cur, "fornecedores_produto", "atualizado_em", "DATE DEFAULT (date('now'))")

    _add_column_if_missing(cur, "produtos_importados_fornecedores", "principal", "INTEGER DEFAULT 0")
    _add_column_if_missing(cur, "comissoes_avulsas", "modo_calculo", "TEXT DEFAULT 'AUTOMATICO'")

    _add_column_if_missing(cur, "ordens_servico", "tecnico", "TEXT DEFAULT ''")

    _add_column_if_missing(cur, "clientes", "status", "TEXT DEFAULT 'ATIVO'")
    _add_column_if_missing(cur, "clientes", "data_cadastro", "DATE DEFAULT (date('now'))")
    _add_column_if_missing(cur, "clientes", "origem_cadastro", "TEXT DEFAULT 'IMPORTACAO_CLIENTES'")

    _add_column_if_missing(cur, "usuarios", "senha_hash", "TEXT")
    _add_column_if_missing(cur, "usuarios", "ultimo_login", "TEXT")
    _add_column_if_missing(cur, "usuarios", "login", "TEXT")
    _add_column_if_missing(cur, "usuarios", "perfil", "TEXT DEFAULT 'OPERADOR'")
    _add_column_if_missing(cur, "usuarios", "unidade_id", "INTEGER")
    _add_column_if_missing(cur, "usuarios", "ativo", "INTEGER DEFAULT 1")

    _add_column_if_missing(cur, "interacoes", "assunto", "TEXT")
    _add_column_if_missing(cur, "interacoes", "resultado", "TEXT")
    _add_column_if_missing(cur, "interacoes", "usuario_id", "INTEGER")
    _add_column_if_missing(cur, "interacoes", "status_interacao", "TEXT DEFAULT 'ABERTA'")
    _add_column_if_missing(cur, "interacoes", "contato_nome", "TEXT")
    _add_column_if_missing(cur, "interacoes", "contato_cargo", "TEXT")
    _add_column_if_missing(cur, "interacoes", "contato_telefone", "TEXT")
    _add_column_if_missing(cur, "interacoes", "contato_email", "TEXT")
    _add_column_if_missing(cur, "interacoes", "tipo_prox_acao", "TEXT")
    _add_column_if_missing(cur, "interacoes", "obs_prox_acao", "TEXT")

    # ──────────────────────────────────────────────────
    # Inserções padrão (idempotentes)
    # ──────────────────────────────────────────────────

    cur.execute("""
    INSERT OR IGNORE INTO unidades (id, nome, sigla, cidade, estado)
    VALUES (1, 'ULITEC SP', 'SP', 'Jundiaí', 'SP')
    """)
    cur.execute("""
    INSERT OR IGNORE INTO unidades (id, nome, sigla, cidade, estado)
    VALUES (2, 'ULITEC RS', 'RS', 'Caxias do Sul', 'RS')
    """)

    conn.commit()
    conn.close()

def _add_column_if_missing(cur, table: str, column: str, col_def: str):
    """Adiciona coluna se não existir, ignorando erro silenciosamente."""
    try:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_def}")
    except Exception:
        pass  # coluna já existe
