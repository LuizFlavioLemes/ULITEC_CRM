"""
BOOTSTRAP ÚNICO & IDEMPOTENTE — ULITEC CRM
===========================================
Executado ANTES de qualquer página carregar.
Ordem: .env → caminhos absolutos → WAL → schema → monkey-patch .connect
"""

import os
import sys
import sqlite3
from pathlib import Path

from database import db

# ── 1. Determinar diretório raiz (funciona Windows + Linux/cPanel) ──
_BOOTSTRAP_FILE = Path(__file__).resolve()
ROOT_DIR = _BOOTSTRAP_FILE.parent.parent  # utils/ → raiz/

# ── 2. Carregar .env ──
try:
    from dotenv import load_dotenv
    _env_path = ROOT_DIR / ".env"
    if _env_path.exists():
        load_dotenv(dotenv_path=str(_env_path), override=True)
except ImportError:
    pass  # dotenv não instalado — sem crash

# ── 3. Caminho do banco (único ponto: config.DB_PATH) ──
# Importa config DEPOIS do .env para que DB_PATH env var já esteja carregada.
from config import DB_PATH
DB_ABSOLUTE_PATH = str(DB_PATH)

# ═══════════════════════════════════════════════════════════
# 4. MONKEY-PATCH .connect (interceptação global)
#    Mantido para compatibilidade com código legado que ainda
#    chama get_connection() diretamente (pages/, debug/, scripts/).
#    NOVO CÓDIGO deve usar database.db.get_connection() em vez disso.
# ═══════════════════════════════════════════════════════════
_original_connect = sqlite3.connect

def _conexao_segura(database, *args, **kwargs):
    """Força o caminho absoluto correto, ignorando paths relativos."""
    return _original_connect(DB_ABSOLUTE_PATH, *args, **kwargs)

sqlite3.connect = _conexao_segura

# ═══════════════════════════════════════════════════════════
# 5. Inicializar banco: WAL + schema + migrações + seeds
# ═══════════════════════════════════════════════════════════
def _init_database():
    conn = _original_connect(DB_ABSOLUTE_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    cur = conn.cursor()

    # ── CREATE TABLE IF NOT EXISTS (todas as tabelas) ──
    TABLES = [
        """CREATE TABLE IF NOT EXISTS unidades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL, sigla TEXT, cidade TEXT, estado TEXT)""",
        """CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL, email TEXT, senha TEXT, login TEXT,
            senha_hash TEXT, ultimo_login TEXT,
            perfil TEXT DEFAULT 'OPERADOR', unidade_id INTEGER, ativo INTEGER DEFAULT 1)""",
        """CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_erp TEXT UNIQUE, razao_social TEXT, nome_fantasia TEXT,
            cnpj TEXT, cidade TEXT, estado TEXT, telefone TEXT, email TEXT,
            segmento TEXT, parque_maquinas INTEGER DEFAULT 0,
            maquinas_mitsubishi INTEGER DEFAULT 0, frequencia_visita INTEGER DEFAULT 90,
            tipo_conta TEXT DEFAULT 'LEAD FRIO', classe_abc TEXT DEFAULT 'D',
            faturamento_12m REAL DEFAULT 0, ultima_visita DATE,
            ultimo_faturamento DATE, origem_erp TEXT, observacoes TEXT,
            ultima_importacao DATE, status TEXT DEFAULT 'ATIVO',
            data_cadastro DATE DEFAULT (date('now')),
            origem_cadastro TEXT DEFAULT 'IMPORTACAO_CLIENTES')""",
        """CREATE TABLE IF NOT EXISTS interacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER, data_interacao DATE, tipo_interacao TEXT,
            assunto TEXT, responsavel TEXT, usuario_id INTEGER, unidade TEXT,
            qtd_maquinas INTEGER, qtd_mitsubishi INTEGER, brinde_entregue TEXT,
            status_cliente TEXT, nivel_producao TEXT, perspectiva_6m TEXT,
            concorrentes TEXT, resultado_comercial TEXT, resumo TEXT, resultado TEXT, proxima_acao TEXT,
            data_proxima_acao DATE, status_interacao TEXT DEFAULT 'ABERTA',
            contato_nome TEXT, contato_cargo TEXT, contato_telefone TEXT,
            contato_email TEXT, tipo_prox_acao TEXT, obs_prox_acao TEXT)""",
        """CREATE TABLE IF NOT EXISTS propostas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_os TEXT, cliente_id INTEGER, unidade TEXT,
            data_recebimento DATE, data_envio_proposta DATE,
            data_aprovacao DATE, data_faturamento DATE, data_expedicao DATE,
            valor_proposta REAL, status TEXT, observacoes TEXT)""",
        """CREATE TABLE IF NOT EXISTS ordens_servico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_os TEXT UNIQUE, cliente_id INTEGER, unidade TEXT,
            responsavel TEXT, equipamento TEXT, marca TEXT, modelo TEXT,
            serial_number TEXT, data_recebimento DATE, data_envio_proposta DATE,
            data_aprovacao DATE, data_faturamento DATE, data_expedicao DATE,
            data_perda DATE, valor_estimado REAL DEFAULT 0,
            valor_proposta REAL DEFAULT 0, valor_faturado REAL DEFAULT 0,
            status TEXT DEFAULT 'RECEBIDA',
            motivo_perda TEXT, proximo_followup DATE, observacoes TEXT,
            origem TEXT DEFAULT 'MANUAL', data_criacao DATE,
            data_atualizacao DATE, tecnico TEXT DEFAULT '')""",
        """CREATE TABLE IF NOT EXISTS faturamento (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER, unidade TEXT, data_faturamento DATE,
            valor REAL, tipo TEXT, origem TEXT)""",
        """CREATE TABLE IF NOT EXISTS faturamento_itens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER, unidade TEXT, descricao_item TEXT,
            tipo_item TEXT, data_venda DATE, valor_total REAL,
            origem TEXT, data_importacao DATE)""",
        """CREATE TABLE IF NOT EXISTS maquinas_mitsubishi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer TEXT, address TEXT, city TEXT, uf TEXT, machine TEXT,
            serial_number TEXT, nc_series TEXT, nc_type TEXT, dealer TEXT,
            warranty_start TEXT, warranty_end TEXT, ano INTEGER,
            cliente_id INTEGER, score_match REAL, validado INTEGER DEFAULT 0)""",
        """CREATE TABLE IF NOT EXISTS conciliacao_mitsubishi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            maquina_id INTEGER, cliente_sugerido_id INTEGER,
            customer TEXT, cliente_sugerido TEXT, score REAL,
            status TEXT DEFAULT 'REVISAO')""",
        """CREATE TABLE IF NOT EXISTS oportunidades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER, unidade TEXT, data_abertura DATE,
            origem TEXT, descricao TEXT, valor_estimado REAL, status TEXT)""",
        """CREATE TABLE IF NOT EXISTS alertas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT, descricao TEXT, data_alerta DATE,
            resolvido INTEGER DEFAULT 0)""",
        """CREATE TABLE IF NOT EXISTS configuracoes (
            chave TEXT PRIMARY KEY, valor TEXT, descricao TEXT)""",
        """CREATE TABLE IF NOT EXISTS pendencias_comerciais (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER, interacao_id INTEGER, descricao TEXT,
            prioridade TEXT DEFAULT 'MEDIA', responsavel TEXT,
            data_limite DATE, status TEXT DEFAULT 'ABERTA',
            criado_em DATE DEFAULT (date('now')),
            FOREIGN KEY (cliente_id) REFERENCES clientes(id),
            FOREIGN KEY (interacao_id) REFERENCES interacoes(id))""",
        """CREATE TABLE IF NOT EXISTS evolucao_pendencias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pendencia_id INTEGER NOT NULL, descricao TEXT NOT NULL,
            tipo_evolucao TEXT DEFAULT 'COMENTARIO', usuario_id INTEGER,
            usuario_nome TEXT, criado_em TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (pendencia_id) REFERENCES pendencias_comerciais(id) ON DELETE CASCADE,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id))""",
        """CREATE TABLE IF NOT EXISTS tipo_produto_importado (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT NOT NULL UNIQUE, ii REAL DEFAULT 0,
            ipi REAL DEFAULT 0, pis REAL DEFAULT 0, cofins REAL DEFAULT 0,
            icms REAL DEFAULT 0, ativo INTEGER DEFAULT 1)""",
        """CREATE TABLE IF NOT EXISTS ncm_importacao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ncm TEXT NOT NULL UNIQUE, descricao TEXT DEFAULT '',
            tipo_produto_id INTEGER, ativo INTEGER DEFAULT 1,
            criado_em DATE DEFAULT (date('now')),
            atualizado_em DATE DEFAULT (date('now')),
            FOREIGN KEY (tipo_produto_id) REFERENCES tipo_produto_importado(id))""",
        """CREATE TABLE IF NOT EXISTS config_importacao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chave TEXT NOT NULL UNIQUE, valor REAL NOT NULL,
            descricao TEXT DEFAULT '')""",
        """CREATE TABLE IF NOT EXISTS produtos_importados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            modelo TEXT NOT NULL UNIQUE, modelo_busca TEXT DEFAULT '',
            descricao TEXT DEFAULT '', tipo_produto_id INTEGER, ncm_id INTEGER,
            fornecedor TEXT DEFAULT '', fob_atual_usd REAL DEFAULT 0,
            data_fob DATE, observacoes TEXT DEFAULT '', ativo INTEGER DEFAULT 1,
            ultimo_preco_venda REAL DEFAULT NULL,
            criado_em DATE DEFAULT (date('now')),
            atualizado_em DATE DEFAULT (date('now')),
            FOREIGN KEY (tipo_produto_id) REFERENCES tipo_produto_importado(id),
            FOREIGN KEY (ncm_id) REFERENCES ncm_importacao(id))""",
        """CREATE TABLE IF NOT EXISTS fornecedores_produto (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE, pais TEXT DEFAULT '',
            observacoes TEXT DEFAULT '', ativo INTEGER DEFAULT 1,
            criado_em DATE DEFAULT (date('now')),
            atualizado_em DATE DEFAULT (date('now')))""",
        """CREATE TABLE IF NOT EXISTS produtos_importados_fornecedores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER NOT NULL, fornecedor_id INTEGER NOT NULL,
            fob_atual_usd REAL DEFAULT 0, data_fob DATE,
            observacoes TEXT DEFAULT '', ativo INTEGER DEFAULT 1,
            criado_em DATE DEFAULT (date('now')),
            atualizado_em DATE DEFAULT (date('now')),
            FOREIGN KEY (produto_id) REFERENCES produtos_importados(id),
            FOREIGN KEY (fornecedor_id) REFERENCES fornecedores_produto(id))""",
        """CREATE TABLE IF NOT EXISTS produtos_importados_historico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER, fornecedor TEXT DEFAULT '',
            valor_fob_usd REAL DEFAULT 0, data_atualizacao DATE,
            usuario_id INTEGER, observacao TEXT DEFAULT '',
            criado_em DATE DEFAULT (date('now')),
            FOREIGN KEY (produto_id) REFERENCES produtos_importados(id),
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id))""",
        """CREATE TABLE IF NOT EXISTS terceiros_fornecedores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE, cidade TEXT DEFAULT '',
            estado TEXT DEFAULT '', contato TEXT DEFAULT '',
            telefone TEXT DEFAULT '', observacoes TEXT DEFAULT '',
            ativo INTEGER DEFAULT 1, criado_em DATE DEFAULT (date('now')),
            atualizado_em DATE DEFAULT (date('now')))""",
        """CREATE TABLE IF NOT EXISTS terceiros_servicos_tipos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE, categoria TEXT DEFAULT '',
            ativo INTEGER DEFAULT 1, criado_em DATE DEFAULT (date('now')))""",
        """CREATE TABLE IF NOT EXISTS terceiros_marcas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE, ativo INTEGER DEFAULT 1,
            criado_em DATE DEFAULT (date('now')))""",
        """CREATE TABLE IF NOT EXISTS terceiros_servicos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fornecedor_id INTEGER NOT NULL, marca_id INTEGER NOT NULL,
            servico_id INTEGER NOT NULL, modelo TEXT NOT NULL,
            descricao TEXT DEFAULT '', valor REAL DEFAULT 0,
            status TEXT DEFAULT 'ENVIADO', data_envio DATE,
            data_retorno DATE, observacoes TEXT DEFAULT '',
            usuario TEXT DEFAULT '', data_cadastro DATE DEFAULT (date('now')),
            ultima_atualizacao DATE DEFAULT (date('now')),
            os_erp TEXT DEFAULT NULL, cliente_id INTEGER DEFAULT NULL,
            equipamento_id INTEGER DEFAULT NULL, numero_serie TEXT DEFAULT NULL,
            custo_interno REAL DEFAULT NULL, valor_cobrado_cliente REAL DEFAULT NULL,
            FOREIGN KEY (fornecedor_id) REFERENCES terceiros_fornecedores(id),
            FOREIGN KEY (marca_id) REFERENCES terceiros_marcas(id),
            FOREIGN KEY (servico_id) REFERENCES terceiros_servicos_tipos(id))""",
        """CREATE TABLE IF NOT EXISTS config_ia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_key TEXT, modelo TEXT DEFAULT 'gpt-4o-mini',
            ativo INTEGER DEFAULT 1,
            criado_em TEXT DEFAULT (datetime('now','localtime')),
            atualizado_em TEXT DEFAULT (datetime('now','localtime')))""",
        """CREATE TABLE IF NOT EXISTS relatorios_ia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER, modelo TEXT, prompt_tokens INTEGER DEFAULT 0,
            completion_tokens INTEGER DEFAULT 0, tempo_execucao REAL DEFAULT 0,
            custo_estimado REAL DEFAULT 0,
            criado_em TEXT DEFAULT (datetime('now','localtime')))""",
    ]
    for sql in TABLES:
        cur.execute(sql)

    # ── ALTER TABLE defensivo (colunas que podem faltar em bases antigas) ──
    _add_col(cur, "fornecedores_produto", "ativo", "INTEGER DEFAULT 1")
    _add_col(cur, "fornecedores_produto", "criado_em", "DATE DEFAULT (date('now'))")
    _add_col(cur, "fornecedores_produto", "atualizado_em", "DATE DEFAULT (date('now'))")
    _add_col(cur, "ordens_servico", "tecnico", "TEXT DEFAULT ''")
    _add_col(cur, "ordens_servico", "valor_faturado", "REAL DEFAULT 0")
    _add_col(cur, "clientes", "status", "TEXT DEFAULT 'ATIVO'")
    _add_col(cur, "clientes", "data_cadastro", "DATE DEFAULT (date('now'))")
    _add_col(cur, "clientes", "origem_cadastro", "TEXT DEFAULT 'IMPORTACAO_CLIENTES'")
    _add_col(cur, "usuarios", "senha_hash", "TEXT")
    _add_col(cur, "usuarios", "ultimo_login", "TEXT")
    _add_col(cur, "usuarios", "login", "TEXT")
    _add_col(cur, "usuarios", "perfil", "TEXT DEFAULT 'OPERADOR'")
    _add_col(cur, "usuarios", "unidade_id", "INTEGER")
    _add_col(cur, "usuarios", "ativo", "INTEGER DEFAULT 1")
    _add_col(cur, "usuarios", "nivel_acesso", "TEXT")
    _add_col(cur, "usuarios", "perfil_migrado_v2", "INTEGER DEFAULT 0")
    _add_col(cur, "interacoes", "assunto", "TEXT")
    _add_col(cur, "interacoes", "resultado", "TEXT")
    _add_col(cur, "interacoes", "usuario_id", "INTEGER")
    _add_col(cur, "interacoes", "status_interacao", "TEXT DEFAULT 'ABERTA'")
    _add_col(cur, "interacoes", "contato_nome", "TEXT")
    _add_col(cur, "interacoes", "contato_cargo", "TEXT")
    _add_col(cur, "interacoes", "contato_telefone", "TEXT")
    _add_col(cur, "interacoes", "contato_email", "TEXT")
    _add_col(cur, "interacoes", "tipo_prox_acao", "TEXT")
    _add_col(cur, "interacoes", "obs_prox_acao", "TEXT")
    _add_col(cur, "interacoes", "resultado_comercial", "TEXT")

    # ── Renomear coluna 'status' → 'status_interacao' se necessário ──
    try:
        cols = [r[1] for r in cur.execute("PRAGMA table_info(interacoes)").fetchall()]
        if 'status' in cols and 'status_interacao' not in cols:
            cur.execute("ALTER TABLE interacoes RENAME COLUMN status TO status_interacao")
    except Exception:
        pass

    # ── Migrar pendencias → pendencias_comerciais ──
    try:
        cur.execute("SELECT COUNT(*) FROM pendencias")
        if cur.fetchone()[0] > 0:
            cur.execute("""INSERT INTO pendencias_comerciais
                (cliente_id, interacao_id, descricao, prioridade, responsavel, data_limite, status, criado_em)
                SELECT cliente_id, interacao_id, descricao, prioridade, responsavel, data_limite, status, criado_em
                FROM pendencias""")
        cur.execute("DROP TABLE IF EXISTS pendencias")
    except Exception:
        pass

    # ── Seeds: unidades ──
    cur.execute("INSERT OR IGNORE INTO unidades (id, nome, sigla, cidade, estado) VALUES (1,'ULITEC SP','SP','Jundiaí','SP')")
    cur.execute("INSERT OR IGNORE INTO unidades (id, nome, sigla, cidade, estado) VALUES (2,'ULITEC RS','RS','Caxias do Sul','RS')")

    # ── Seeds: tipos de produto ──
    tipos = [
        ('ENCODER',12.60,3.25,2.10,10.25,18.00),('MOTOR',12.60,3.25,2.10,10.25,18.00),
        ('SERVO DRIVE',12.60,3.25,2.10,10.25,18.00),('SPINDLE DRIVE',12.60,3.25,2.10,10.25,18.00),
        ('FONTE',12.60,3.25,2.10,10.25,18.00),('PLACA CNC',12.60,3.25,2.10,10.25,18.00),
        ('CNC',12.60,3.25,2.10,10.25,18.00),('CABO',12.60,3.25,2.10,10.25,18.00),
        ('VENTILADOR',12.60,3.25,2.10,10.25,18.00),('BATERIA',12.60,3.25,2.10,10.25,18.00),
        ('CONECTOR',12.60,3.25,2.10,10.25,18.00),('MONITOR',12.60,3.25,2.10,10.25,18.00),
        ('TECLADO',12.60,3.25,2.10,10.25,18.00),('OUTROS',12.60,3.25,2.10,10.25,18.00),
    ]
    for t in tipos:
        cur.execute("INSERT OR IGNORE INTO tipo_produto_importado (descricao,ii,ipi,pis,cofins,icms,ativo) VALUES (?,?,?,?,?,?,1)", t)

    # ── Seeds: NCMs ──
    ncms = [
        ('84145910','Ventilador até 90cm²','VENTILADOR'),('84145990','Ventilador acima 90cm²','VENTILADOR'),
        ('84716052','Teclados','TECLADO'),('84716053','Mouse / Apontadores','OUTROS'),
        ('85015190','Motores abaixo 750W','MOTOR'),('85015290','Motores acima 750W','MOTOR'),
        ('85044050','Acionamentos Servo/Spindle','SERVO DRIVE'),('85044090','Fonte Família CV','FONTE'),
        ('85045000','Filtros e Bobinas','OUTROS'),('85049040','Placa Conversores','PLACA CNC'),
        ('85065010','Bateria de Lítio','BATERIA'),('85182990','Alto Falante','OUTROS'),
        ('85234920','Compact Disk','OUTROS'),('85235110','Cartão Memória','OUTROS'),
        ('85249100','Monitor Colorido','MONITOR'),('85299020','Backlight','OUTROS'),
        ('85322200','Capacitor Eletrolítico','OUTROS'),('85366910','Conectores','CONECTOR'),
        ('85371011','CNC com Monitor','CNC'),('85371019','CNC sem Monitor','CNC'),
        ('85389010','Placas CNC','PLACA CNC'),('85412920','Transistor IGBT','OUTROS'),
        ('85444200','Cabos com Conectores','CABO'),('85447010','Fibra Óptica','CABO'),
        ('90318099','Encoder','ENCODER'),('84717012','Hard Disk','OUTROS'),
    ]
    for ncm, desc, tipo in ncms:
        cur.execute("INSERT OR IGNORE INTO ncm_importacao (ncm, descricao, tipo_produto_id) SELECT ?,?,tp.id FROM tipo_produto_importado tp WHERE tp.descricao=?", (ncm, desc, tipo))

    # ── Seeds: config_importacao ──
    configs = [
        ('dolar_atual',5.80,'Dólar atual para cálculos'),('rateio_frete_usd',50.0,'Rateio de frete por produto em USD'),
        ('despesas_aduaneiras_brl',200.0,'Despesas aduaneiras em R$'),('markup_padrao',2.0,'Markup padrão para preço de venda'),
    ]
    for chave, valor, desc in configs:
        cur.execute("INSERT OR IGNORE INTO config_importacao (chave,valor,descricao) VALUES (?,?,?)", (chave, valor, desc))

    conn.commit()
    conn.close()

def _add_col(cur, table, column, col_def):
    try:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_def}")
    except Exception:
        pass

# ── Executar inicialização do banco ──
_init_database()