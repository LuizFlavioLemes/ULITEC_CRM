import sqlite3

from config import DB_PATH


def init_connection():
    """Configura PRAGMAs recomendados para performance e segurança."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.close()


def criar_banco():

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # ==================================================
    # UNIDADES
    # ==================================================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS unidades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        sigla TEXT,
        cidade TEXT,
        estado TEXT
    )
    """)

    # ==================================================
    # FATURAMENTO ITENS
    # ==================================================

    cursor.execute("""
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

    # ==================================================
    # USUARIOS
    # ==================================================

    cursor.execute("""
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

    # ==================================================
    # CLIENTES
    # ==================================================

    cursor.execute("""
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

    # ==================================================
    # INTERACOES
    # ==================================================

    cursor.execute("""
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
        -- v1.0.5: contato e próxima ação estruturada
        contato_nome TEXT,
        contato_cargo TEXT,
        contato_telefone TEXT,
        contato_email TEXT,
        tipo_prox_acao TEXT,
        obs_prox_acao TEXT
    )
    """)

    # ==================================================
    # PROPOSTAS
    # ==================================================

    cursor.execute("""
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

    # ==================================================
    # ORDENS DE SERVICO / PIPELINE
    # ==================================================

    cursor.execute("""
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

    # ==================================================
    # FATURAMENTO
    # ==================================================

    cursor.execute("""
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

    # ==================================================
    # MAQUINAS MITSUBISHI
    # ==================================================

    cursor.execute("""
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

    # ==================================================
    # CONCILIACAO MITSUBISHI
    # ==================================================

    cursor.execute("""
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

    # ==================================================
    # OPORTUNIDADES
    # ==================================================

    cursor.execute("""
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

    # ==================================================
    # ALERTAS
    # ==================================================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alertas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo TEXT,
        descricao TEXT,
        data_alerta DATE,
        resolvido INTEGER DEFAULT 0
    )
    """)

    # ==================================================
    # CONFIGURACOES
    # ==================================================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS configuracoes (
        chave TEXT PRIMARY KEY,
        valor TEXT,
        descricao TEXT
    )
    """)

    # ==================================================
    # PENDENCIAS COMERCIAIS (Módulo Relacionamento Comercial v1.0.3)
    # ==================================================

    cursor.execute("""
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

    # ==================================================
    # TABELA DE EVOLUCOES DE PENDENCIAS (v1.3)
    # ==================================================

    cursor.execute("""
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

    # ==================================================
    # TABELAS DO MODULO BASE DE PRODUTOS IMPORTADOS
    # ==================================================

    cursor.execute("""
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

    cursor.execute("""
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

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS config_importacao (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chave TEXT NOT NULL UNIQUE,
        valor REAL NOT NULL,
        descricao TEXT DEFAULT ''
    )
    """)

    cursor.execute("""
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

    cursor.execute("""
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

    # ==================================================
    # TABELAS DO MODULO GESTAO DE TERCEIROS (v1.8.0)
    # ==================================================

    cursor.execute("""
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

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS terceiros_servicos_tipos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL UNIQUE,
        categoria TEXT DEFAULT '',
        ativo INTEGER DEFAULT 1,
        criado_em DATE DEFAULT (date('now'))
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS terceiros_marcas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL UNIQUE,
        ativo INTEGER DEFAULT 1,
        criado_em DATE DEFAULT (date('now'))
    )
    """)

    cursor.execute("""
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
        -- campos preparados para expansao futura
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

    # ==================================================
    # TABELAS DO MODULO IA
    # ==================================================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS config_ia (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        api_key TEXT,
        modelo TEXT DEFAULT 'gpt-4o-mini',
        ativo INTEGER DEFAULT 1,
        criado_em TEXT DEFAULT (datetime('now', 'localtime')),
        atualizado_em TEXT DEFAULT (datetime('now', 'localtime'))
    )
    """)

    cursor.execute("""
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

    # ==================================================
    # UNIDADES PADRAO
    # ==================================================

    cursor.execute("""
    INSERT OR IGNORE INTO unidades
    (id, nome, sigla, cidade, estado)
    VALUES
    (1, 'ULITEC SP', 'SP', 'Jundiaí', 'SP')
    """)

    cursor.execute("""
    INSERT OR IGNORE INTO unidades
    (id, nome, sigla, cidade, estado)
    VALUES
    (2, 'ULITEC RS', 'RS', 'Caxias do Sul', 'RS')
    """)

    # ==================================================
    # TIPOS DE PRODUTO PADRAO
    # ==================================================

    tipos_iniciais = [
        ('ENCODER', 12.60, 3.25, 2.10, 10.25, 18.00),
        ('MOTOR', 12.60, 3.25, 2.10, 10.25, 18.00),
        ('SERVO DRIVE', 12.60, 3.25, 2.10, 10.25, 18.00),
        ('SPINDLE DRIVE', 12.60, 3.25, 2.10, 10.25, 18.00),
        ('FONTE', 12.60, 3.25, 2.10, 10.25, 18.00),
        ('PLACA CNC', 12.60, 3.25, 2.10, 10.25, 18.00),
        ('CNC', 12.60, 3.25, 2.10, 10.25, 18.00),
        ('CABO', 12.60, 3.25, 2.10, 10.25, 18.00),
        ('VENTILADOR', 12.60, 3.25, 2.10, 10.25, 18.00),
        ('BATERIA', 12.60, 3.25, 2.10, 10.25, 18.00),
        ('CONECTOR', 12.60, 3.25, 2.10, 10.25, 18.00),
        ('MONITOR', 12.60, 3.25, 2.10, 10.25, 18.00),
        ('TECLADO', 12.60, 3.25, 2.10, 10.25, 18.00),
        ('OUTROS', 12.60, 3.25, 2.10, 10.25, 18.00),
    ]

    for t in tipos_iniciais:
        cursor.execute("""
        INSERT OR IGNORE INTO tipo_produto_importado
        (descricao, ii, ipi, pis, cofins, icms, ativo)
        VALUES (?, ?, ?, ?, ?, ?, 1)
        """, t)

    # ==================================================
    # NCMS PADRAO
    # ==================================================

    ncms_iniciais = [
        ('84145910', 'Ventilador até 90cm²', 'VENTILADOR'),
        ('84145990', 'Ventilador acima 90cm²', 'VENTILADOR'),
        ('84716052', 'Teclados', 'TECLADO'),
        ('84716053', 'Mouse / Apontadores', 'OUTROS'),
        ('85015190', 'Motores abaixo 750W', 'MOTOR'),
        ('85015290', 'Motores acima 750W', 'MOTOR'),
        ('85044050', 'Acionamentos Servo/Spindle', 'SERVO DRIVE'),
        ('85044090', 'Fonte Família CV', 'FONTE'),
        ('85045000', 'Filtros e Bobinas', 'OUTROS'),
        ('85049040', 'Placa Conversores', 'PLACA CNC'),
        ('85065010', 'Bateria de Lítio', 'BATERIA'),
        ('85182990', 'Alto Falante', 'OUTROS'),
        ('85234920', 'Compact Disk', 'OUTROS'),
        ('85235110', 'Cartão Memória', 'OUTROS'),
        ('85249100', 'Monitor Colorido', 'MONITOR'),
        ('85299020', 'Backlight', 'OUTROS'),
        ('85322200', 'Capacitor Eletrolítico', 'OUTROS'),
        ('85366910', 'Conectores', 'CONECTOR'),
        ('85371011', 'CNC com Monitor', 'CNC'),
        ('85371019', 'CNC sem Monitor', 'CNC'),
        ('85389010', 'Placas CNC', 'PLACA CNC'),
        ('85412920', 'Transistor IGBT', 'OUTROS'),
        ('85444200', 'Cabos com Conectores', 'CABO'),
        ('85447010', 'Fibra Óptica', 'CABO'),
        ('90318099', 'Encoder', 'ENCODER'),
        ('84717012', 'Hard Disk', 'OUTROS'),
    ]

    for ncm, descricao, tipo_nome in ncms_iniciais:
        cursor.execute("""
        INSERT OR IGNORE INTO ncm_importacao (ncm, descricao, tipo_produto_id)
        SELECT ?, ?, tp.id FROM tipo_produto_importado tp WHERE tp.descricao = ?
        """, (ncm, descricao, tipo_nome))

    # ==================================================
    # CONFIGURACOES PADRAO IMPORTACAO
    # ==================================================

    configs_iniciais = [
        ('dolar_atual', 5.80, 'Dólar atual para cálculos'),
        ('rateio_frete_usd', 50.0, 'Rateio de frete por produto em USD'),
        ('despesas_aduaneiras_brl', 200.0, 'Despesas aduaneiras em R$'),
        ('markup_padrao', 2.0, 'Markup padrão para preço de venda'),
    ]

    for chave, valor, descricao in configs_iniciais:
        cursor.execute("""
        INSERT OR IGNORE INTO config_importacao
        (chave, valor, descricao)
        VALUES (?, ?, ?)
        """, (chave, valor, descricao))

    # ==================================================
    # MIGRACAO: adicionar colunas para cliente provisorio
    # ==================================================
    for coluna in ['status', 'data_cadastro', 'origem_cadastro']:
        try:
            cursor.execute(f"ALTER TABLE clientes ADD COLUMN {coluna} TEXT")
        except sqlite3.OperationalError:
            pass  # coluna ja existe

    try:
        cursor.execute("UPDATE clientes SET status = 'ATIVO' WHERE status IS NULL")
    except sqlite3.OperationalError:
        pass

    # ==================================================
    # MIGRACAO v1.0.3: novas colunas na tabela interacoes
    # ==================================================
    for coluna_mig in [
        ('assunto', 'TEXT'),
        ('resultado', 'TEXT'),
        ('usuario_id', 'INTEGER'),
        ('status_interacao', 'TEXT DEFAULT \'ABERTA\''),
    ]:
        try:
            cursor.execute(f"ALTER TABLE interacoes ADD COLUMN {coluna_mig[0]} {coluna_mig[1]}")
        except sqlite3.OperationalError:
            pass

    # ==================================================
    # MIGRACAO v1.0.5: colunas de contato e próx. ação
    # ==================================================
    for coluna_mig in [
        ('contato_nome', 'TEXT'),
        ('contato_cargo', 'TEXT'),
        ('contato_telefone', 'TEXT'),
        ('contato_email', 'TEXT'),
        ('tipo_prox_acao', 'TEXT'),
        ('obs_prox_acao', 'TEXT'),
    ]:
        try:
            cursor.execute(f"ALTER TABLE interacoes ADD COLUMN {coluna_mig[0]} {coluna_mig[1]}")
        except sqlite3.OperationalError:
            pass

    # Renomear coluna antiga 'status' para 'status_interacao' se existir
    try:
        colunas_inter = [row[1] for row in cursor.execute("PRAGMA table_info(interacoes)").fetchall()]
        if 'status' in colunas_inter and 'status_interacao' not in colunas_inter:
            cursor.execute("ALTER TABLE interacoes RENAME COLUMN status TO status_interacao")
    except sqlite3.OperationalError:
        pass

    # Migrar dados da tabela antiga pendencias -> pendencias_comerciais
    try:
        cursor.execute("SELECT COUNT(*) FROM pendencias")
        if cursor.fetchone()[0] > 0:
            cursor.execute("""
                INSERT INTO pendencias_comerciais (cliente_id, interacao_id, descricao, prioridade, responsavel, data_limite, status, criado_em)
                SELECT cliente_id, interacao_id, descricao, prioridade, responsavel, data_limite, status, criado_em FROM pendencias
            """)
        cursor.execute("DROP TABLE IF EXISTS pendencias")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()

    print("Banco ULITEC criado com sucesso!")


if __name__ == "__main__":
    criar_banco()