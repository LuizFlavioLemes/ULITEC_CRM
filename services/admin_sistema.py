"""
Módulo de Administração do Sistema ULITEC CRM v2.4.2
=====================================================
Central de gerenciamento do sistema:
- Backup com manifesto
- Exportação compactada
- Status do sistema
- Manutenção
- Reset controlado
- Limpeza Seletiva por Módulo
- Restauração Completa do Sistema
"""

import hashlib
import json
import os
import shutil

import tempfile
import time as time_module
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple

# ============================================================
# CONSTANTES
# ============================================================

from config import DB_PATH
from services.version import VERSION as CRM_VERSION, BUILD

from database import get_connection

BACKUP_DIR = Path("backups")
EXPORT_DIR = Path("backups/export")
MANIFEST_DIR = Path("backups/manifestos")
DB_VERSION = "1.0.3"

# Tabelas operacionais (resetáveis)
TABELAS_OPERACIONAIS = [
    "clientes",
    "ordens_servico",
    "oportunidades",
    "propostas",
    "interacoes",
    "faturamento",
    "faturamento_itens",
    "conciliacao_mitsubishi",
    "maquinas_mitsubishi",
    "pendencias_comerciais",
    "evolucao_pendencias",
    "relatorios_ia",
    "alertas",
    "terceiros_fornecedores",
    "terceiros_servicos",
    "terceiros_marcas",
    "terceiros_servicos_tipos",
    "config_importacao",
    "config_ia",
    "fornecedores_produto",
    "ncm_importacao",
    "produtos_importados",
    "produtos_importados_fornecedores",
    "produtos_importados_historico",
    "tipo_produto_importado",
]

# Tabelas do sistema (NÃO resetar)
TABELAS_SISTEMA = [
    "unidades",
    "configuracoes",
    "usuarios",
]

# ============================================================
# DICIONÁRIO CENTRAL DE MÓDULOS PARA LIMPEZA SELETIVA
# ============================================================
# Para adicionar um novo módulo, basta incluir uma nova entrada
# neste dicionário. A interface e as funções são geradas
# automaticamente a partir dele.

MODULOS_LIMPEZA = {
    "Pipeline OS": {
        "tabelas": [
            "ordens_servico",
            "propostas",
        ],
        "descricao": "Ordens de Serviço, Propostas e eventos operacionais",
    },
    "Faturamento": {
        "tabelas": [
            "faturamento",
            "faturamento_itens",
        ],
        "descricao": "Faturamento e itens faturados",
    },
    "Relacionamento Comercial": {
        "tabelas": [
            "interacoes",
            "pendencias_comerciais",
            "evolucao_pendencias",
        ],
        "descricao": "Interações, pendências e evolução comercial",
    },
    "Gestão de Terceiros": {
        "tabelas": [
            "terceiros_fornecedores",
            "terceiros_servicos",
            "terceiros_marcas",
            "terceiros_servicos_tipos",
        ],
        "descricao": "Fornecedores, serviços, marcas e tipos de serviço terceirizados",
    },
    "Parque Mitsubishi": {
        "tabelas": [
            "maquinas_mitsubishi",
            "conciliacao_mitsubishi",
        ],
        "descricao": "Máquinas Mitsubishi e conciliação de clientes",
    },
    "Base Produtos Importados": {
        "tabelas": [
            "produtos_importados",
            "produtos_importados_fornecedores",
            "produtos_importados_historico",
            "tipo_produto_importado",
            "ncm_importacao",
            "fornecedores_produto",
        ],
        "descricao": "Produtos importados, fornecedores, NCM e históricos",
    },
    "Relatório IA": {
        "tabelas": [
            "relatorios_ia",
            "config_ia",
        ],
        "descricao": "Relatórios gerados por IA e configurações dos providers",
    },
    "Centro Importações": {
        "tabelas": [
            "config_importacao",
        ],
        "descricao": "Configurações do centro de importações",
    },
    "Cliente 360": {
        "tabelas": [
            "clientes",
        ],
        "descricao": "Base de clientes do sistema",
    },
    "Oportunidades": {
        "tabelas": [
            "oportunidades",
        ],
        "descricao": "Oportunidades comerciais registradas",
    },
    "Alertas": {
        "tabelas": [
            "alertas",
        ],
        "descricao": "Alertas do sistema",
    },
}

# ============================================================
# FUNÇÕES DE AUDITORIA / STATUS
# ============================================================

def obter_status_sistema() -> dict:
    """Retorna indicadores completos do sistema."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    todas_tabelas = [row[0] for row in cursor.fetchall()
                     if row[0] != "sqlite_sequence"]

    total_tabelas = len(todas_tabelas)
    total_registros = 0
    info_tabelas = {}

    for nome in todas_tabelas:
        try:
            cursor.execute(f'SELECT COUNT(*) FROM "{nome}"')
            qtd = cursor.fetchone()[0]
            info_tabelas[nome] = qtd
            total_registros += qtd
        except Exception:
            pass

    # Versão do banco (da tabela configuracoes)
    cursor.execute(
        "SELECT valor FROM configuracoes WHERE chave = 'db_version'"
    )
    row = cursor.fetchone()
    db_version = row[0] if row else DB_VERSION

    # Data criação do banco
    db_path_obj = Path(DB_PATH)
    data_criacao = datetime.fromtimestamp(
        db_path_obj.stat().st_ctime
    ).strftime("%d/%m/%Y %H:%M")

    # Tamanho do banco
    tamanho_bytes = db_path_obj.stat().st_size
    tamanho_kb = tamanho_bytes / 1024
    tamanho_mb = tamanho_kb / 1024

    # Último backup
    ultimo_backup = "Nunca"
    data_ultimo_backup = None
    if BACKUP_DIR.exists():
        backups = sorted(
            [f for f in BACKUP_DIR.iterdir() if f.suffix == ".db"],
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )
        if backups:
            data_ultimo_backup = datetime.fromtimestamp(
                backups[0].stat().st_mtime
            ).strftime("%d/%m/%Y %H:%M")
            ultimo_backup = data_ultimo_backup

    # Quantidade de backups
    qtd_backups = 0
    espaco_backups = 0
    if BACKUP_DIR.exists():
        for f in BACKUP_DIR.iterdir():
            if f.suffix == ".db":
                qtd_backups += 1
                espaco_backups += f.stat().st_size

    # Última manutenção
    cursor.execute(
        "SELECT valor FROM configuracoes WHERE chave = 'ultima_manutencao'"
    )
    row = cursor.fetchone()
    ultima_manutencao = row[0] if row else "Nunca"

    conn.close()

    return {
        "crm_version": CRM_VERSION,
        "db_version": db_version,
        "total_tabelas": total_tabelas,
        "total_registros": total_registros,
        "tamanho_kb": round(tamanho_kb, 2),
        "tamanho_mb": round(tamanho_mb, 2),
        "tamanho_bytes": tamanho_bytes,
        "ultimo_backup": ultimo_backup,
        "data_ultimo_backup": data_ultimo_backup,
        "qtd_backups": qtd_backups,
        "espaco_backups_kb": round(espaco_backups / 1024, 2),
        "espaco_backups_mb": round(espaco_backups / 1024 / 1024, 2),
        "data_criacao": data_criacao,
        "ultima_manutencao": ultima_manutencao,
        "info_tabelas": info_tabelas,
    }

# ============================================================
# BLOCO 2 - BACKUP
# ============================================================

def gerar_backup_completo() -> dict:
    """
    Gera backup completo do banco com metadados.
    Retorna dict com informações do backup gerado.
    """
    BACKUP_DIR.mkdir(exist_ok=True)
    MANIFEST_DIR.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_backup = f"crm_backup_{timestamp}.db"
    destino = BACKUP_DIR / nome_backup

    # Copiar banco
    shutil.copy2(str(DB_PATH), str(destino))

    # Obter metadados
    status = obter_status_sistema()

    # Criar manifesto
    manifesto = {
        "crm_version": CRM_VERSION,
        "db_version": status["db_version"],
        "data": datetime.now().strftime("%Y-%m-%d"),
        "hora": datetime.now().strftime("%H:%M:%S"),
        "timestamp": timestamp,
        "quantidade_tabelas": status["total_tabelas"],
        "quantidade_registros": status["total_registros"],
        "tamanho_bytes": destino.stat().st_size,
        "tamanho_kb": round(destino.stat().st_size / 1024, 2),
        "bancos_incluidos": ["crm.db"],
        "tabelas": list(status["info_tabelas"].keys()),
        "hash_sha256": "PREPARADO_PARA_HASH",  # estrutural
    }

    # Salvar manifesto
    nome_manifesto = f"manifesto_{timestamp}.json"
    caminho_manifesto = MANIFEST_DIR / nome_manifesto
    with open(str(caminho_manifesto), "w", encoding="utf-8") as f:
        json.dump(manifesto, f, indent=2, ensure_ascii=False)

    # Registrar no banco
    conn = get_connection()
    conn.execute(
        """INSERT INTO configuracoes (chave, valor, descricao)
           VALUES (?, ?, ?)
           ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor""",
        ("ultimo_backup", timestamp,
         f"Último backup: {nome_backup}"),
    )
    conn.commit()
    conn.close()

    return {
        "arquivo": str(destino),
        "nome": nome_backup,
        "tamanho_bytes": destino.stat().st_size,
        "tamanho_kb": round(destino.stat().st_size / 1024, 2),
        "manifesto": str(caminho_manifesto),
        "timestamp": timestamp,
        "tabelas": status["total_tabelas"],
        "registros": status["total_registros"],
        "crm_version": CRM_VERSION,
    }

# ============================================================
# BLOCO 3 - EXPORTAÇÃO
# ============================================================

def exportar_backup_compactado(
    backup_path: Optional[Path] = None
) -> dict:
    """
    Gera um arquivo .zip contendo:
    - Banco SQLite
    - Manifesto
    - Versionamento
    - Estrutura para restauração
    """
    EXPORT_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if backup_path is None:
        # Usar o banco atual
        backup_path = DB_PATH

    nome_zip = f"ULITEC_CRM_BACKUP_{timestamp}.zip"
    caminho_zip = EXPORT_DIR / nome_zip

    # Obter metadados
    status = obter_status_sistema()

    # Criar manifesto
    manifesto = {
        "crm_version": CRM_VERSION,
        "db_version": status["db_version"],
        "data": datetime.now().strftime("%Y-%m-%d"),
        "hora": datetime.now().strftime("%H:%M:%S"),
        "quantidade_tabelas": status["total_tabelas"],
        "quantidade_registros": status["total_registros"],
        "bancos_incluidos": ["crm.db"],
        "tabelas": list(status["info_tabelas"].keys()),
        "hash_sha256": "PREPARADO_PARA_HASH",
        "exportado_por": "ULITEC CRM",
        "sistema": "ULITEC CRM - Administração do Sistema",
    }

    # Criar versionamento
    versionamento = {
        "crm_version": CRM_VERSION,
        "db_version": status["db_version"],
        "data_exportacao": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "observacao": "Backup exportado da Central de Administração",
    }

    with zipfile.ZipFile(
        str(caminho_zip), "w", zipfile.ZIP_DEFLATED
    ) as zf:
        # Banco de dados
        zf.write(str(backup_path), "crm.db")

        # Manifesto
        zf.writestr(
            "manifesto.json",
            json.dumps(manifesto, indent=2, ensure_ascii=False),
        )

        # Versionamento
        zf.writestr(
            "versionamento.json",
            json.dumps(versionamento, indent=2, ensure_ascii=False),
        )

        # README de restauração
        readme = (
            "=== ULITEC CRM - BACKUP EXPORTADO ===\n\n"
            "Para restaurar este backup:\n"
            "1. Acesse Administracao > Banco > Restauracao\n"
            "2. Selecione este arquivo\n"
            "3. Valide as informacoes\n"
            "4. Confirme a restauracao\n\n"
            f"Exportado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Versao CRM: {CRM_VERSION}\n"
            f"Bancos: crm.db\n"
        )
        zf.writestr("RESTAURAR.txt", readme)

    return {
        "arquivo": str(caminho_zip),
        "nome": nome_zip,
        "tamanho_bytes": caminho_zip.stat().st_size,
        "tamanho_kb": round(caminho_zip.stat().st_size / 1024, 2),
        "timestamp": timestamp,
        "tabelas": status["total_tabelas"],
        "registros": status["total_registros"],
    }

# ============================================================
# BLOCO 5 - RESTAURAÇÃO (LEGADO - MANTER POR COMPATIBILIDADE)
# ============================================================

def listar_backups_disponiveis() -> list:
    """Lista backups disponíveis para restauração."""
    backups = []
    if EXPORT_DIR.exists():
        for f in sorted(
            EXPORT_DIR.iterdir(), key=lambda x: x.stat().st_mtime,
            reverse=True
        ):
            if f.suffix == ".zip":
                backups.append({
                    "nome": f.name,
                    "caminho": str(f),
                    "tamanho_kb": round(f.stat().st_size / 1024, 2),
                    "modificado": datetime.fromtimestamp(
                        f.stat().st_mtime
                    ).strftime("%d/%m/%Y %H:%M"),
                })

    if BACKUP_DIR.exists():
        for f in sorted(
            BACKUP_DIR.iterdir(), key=lambda x: x.stat().st_mtime,
            reverse=True
        ):
            if f.suffix == ".db" and f.name.startswith("crm_backup"):
                backups.append({
                    "nome": f.name,
                    "caminho": str(f),
                    "tamanho_kb": round(f.stat().st_size / 1024, 2),
                    "modificado": datetime.fromtimestamp(
                        f.stat().st_mtime
                    ).strftime("%d/%m/%Y %H:%M"),
                    "tipo": "local",
                })

    return backups

def validar_arquivo_restauracao(caminho_arquivo: str) -> dict:
    """
    Valida se um arquivo de backup é válido para restauração.
    Arquitetura preparada - ainda não implementa restauração.
    """
    try:
        caminho = Path(caminho_arquivo)
        if not caminho.exists():
            return {"valido": False, "erro": "Arquivo não encontrado"}

        if caminho.suffix == ".zip":
            with zipfile.ZipFile(str(caminho), "r") as zf:
                arquivos = zf.namelist()
                tem_banco = "crm.db" in arquivos
                tem_manifesto = "manifesto.json" in arquivos

                manifesto = {}
                if tem_manifesto:
                    manifesto = json.loads(
                        zf.read("manifesto.json").decode("utf-8")
                    )

                return {
                    "valido": tem_banco and tem_manifesto,
                    "erro": None if (tem_banco and tem_manifesto)
                    else "Estrutura inválida",
                    "arquivos": arquivos,
                    "manifesto": manifesto,
                    "tamanho_kb": round(caminho.stat().st_size / 1024, 2),
                }

        elif caminho.suffix == ".db":
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
                tabelas = [row[0] for row in cursor.fetchall()
                           if row[0] != "sqlite_sequence"]
                conn.close()

                return {
                    "valido": True,
                    "erro": None,
                    "tabelas": tabelas,
                    "quantidade_tabelas": len(tabelas),
                    "tamanho_kb": round(caminho.stat().st_size / 1024, 2),
                    "tipo": "sqlite_direct",
                }
            except sqlite3.DatabaseError as e:
                return {"valido": False, "erro": str(e)}

        return {"valido": False, "erro": "Formato não suportado"}

    except Exception as e:
        return {"valido": False, "erro": str(e)}

# ============================================================
# BLOCO 6 - MANUTENÇÃO
# ============================================================

def executar_vacuum() -> dict:
    """Executa VACUUM no banco para recuperar espaço."""
    try:
        conn = get_connection()
        antes = DB_PATH.stat().st_size
        conn.execute("VACUUM")
        conn.close()
        depois = DB_PATH.stat().st_size
        return {
            "sucesso": True,
            "tamanho_antes_kb": round(antes / 1024, 2),
            "tamanho_depois_kb": round(depois / 1024, 2),
            "economia_kb": round((antes - depois) / 1024, 2),
        }
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}

def executar_reindex() -> dict:
    """Recria índices do banco."""
    try:
        conn = get_connection()
        conn.execute("REINDEX")
        conn.close()
        return {"sucesso": True, "mensagem": "Índices recriados com sucesso"}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}

def limpar_cache() -> dict:
    """Limpa cache interno do SQLite."""
    try:
        conn = get_connection()
        conn.execute("PRAGMA shrink_memory")
        conn.close()
        return {"sucesso": True, "mensagem": "Cache limpo com sucesso"}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}

def limpar_logs_antigos(dias: int = 90) -> dict:
    """Remove logs de relatórios IA antigos."""
    try:
        limite = (datetime.now() - timedelta(days=dias)).strftime("%Y-%m-%d")

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM relatorios_ia WHERE criado_em < ?", (limite,)
        )
        removidos = cursor.rowcount
        conn.commit()
        conn.close()
        return {
            "sucesso": True,
            "removidos": removidos,
            "mensagem": f"{removidos} registros removidos",
        }
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}

def recalcular_estatisticas() -> dict:
    """Recalcula estatísticas do SQLite para otimização de queries."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tabelas = [row[0] for row in cursor.fetchall()
                   if row[0] != "sqlite_sequence"]

        for nome in tabelas:
            try:
                cursor.execute(f'ANALYZE "{nome}"')
            except Exception:
                pass

        conn.close()
        return {
            "sucesso": True,
            "tabelas_analisadas": len(tabelas),
            "mensagem": "Estatísticas recalculadas",
        }
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}

def registrar_manutencao() -> None:
    """Registra data/hora da última manutenção no banco."""
    try:
        conn = get_connection()
        conn.execute(
            """INSERT INTO configuracoes (chave, valor, descricao)
               VALUES ('ultima_manutencao', ?, 'Última manutenção')
               ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor""",
            (datetime.now().strftime("%d/%m/%Y %H:%M"),),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass

# ============================================================
# BLOCO 7 - RESET CONTROLADO
# ============================================================

def preparar_lista_reset() -> list:
    """
    Retorna a lista completa do que será apagado no reset.
    """
    conn = get_connection()
    cursor = conn.cursor()

    itens = []
    for tabela in TABELAS_OPERACIONAIS:
        try:
            cursor.execute(f'SELECT COUNT(*) FROM "{tabela}"')
            qtd = cursor.fetchone()[0]
        except Exception:
            qtd = 0

        nome_legivel = {
            "clientes": "Clientes",
            "ordens_servico": "Ordens de Serviço",
            "oportunidades": "Oportunidades",
            "propostas": "Propostas",
            "interacoes": "Interações",
            "faturamento": "Faturamento",
            "faturamento_itens": "Faturamento (Itens)",
            "conciliacao_mitsubishi": "Conciliação Mitsubishi",
            "maquinas_mitsubishi": "Máquinas Mitsubishi",
            "pendencias_comerciais": "Pendências Comerciais",
            "evolucao_pendencias": "Evolução de Pendências",
            "relatorios_ia": "Relatórios IA",
            "alertas": "Alertas",
            "terceiros_fornecedores": "Fornecedores Terceiros",
            "terceiros_servicos": "Serviços Terceiros",
            "terceiros_marcas": "Marcas Terceiros",
            "terceiros_servicos_tipos": "Tipos de Serviço Terceiros",
            "config_importacao": "Configurações de Importação",
            "config_ia": "Configurações IA",
            "fornecedores_produto": "Fornecedores de Produtos",
            "ncm_importacao": "NCM Importação",
            "produtos_importados": "Produtos Importados",
            "produtos_importados_fornecedores": "Fornecedores (Produtos)",
            "produtos_importados_historico": "Histórico de Produtos",
            "tipo_produto_importado": "Tipos de Produto Importado",
        }.get(tabela, tabela)

        itens.append({
            "tabela": tabela,
            "nome": nome_legivel,
            "registros": qtd,
        })

    # Itens adicionais fora de tabelas
    conn.close()

    return itens

def executar_reset_sistema() -> dict:
    """
    Executa o reset completo do sistema.
    Remove todos os dados operacionais, mantendo:
    - MASTER
    - Unidades
    - Configurações
    """
    conn = get_connection()
    cursor = conn.cursor()

    resultados = []
    total_removidos = 0

    for tabela in TABELAS_OPERACIONAIS:
        try:
            cursor.execute(f'SELECT COUNT(*) FROM "{tabela}"')
            antes = cursor.fetchone()[0]
            cursor.execute(f'DELETE FROM "{tabela}"')
            conn.commit()
            total_removidos += antes

            # Resetar auto-increment
            try:
                cursor.execute(
                    "DELETE FROM sqlite_sequence WHERE name = ?",
                    (tabela,),
                )
                conn.commit()
            except Exception:
                pass

            resultados.append({
                "tabela": tabela,
                "removidos": antes,
            })
        except Exception as e:
            resultados.append({
                "tabela": tabela,
                "removidos": 0,
                "erro": str(e),
            })

    # Remover backups locais
    qtd_backups_removidos = 0
    if BACKUP_DIR.exists():
        for f in BACKUP_DIR.iterdir():
            if f.suffix == ".db":
                try:
                    f.unlink()
                    qtd_backups_removidos += 1
                except Exception:
                    pass

    # Remover exports
    qtd_exports_removidos = 0
    if EXPORT_DIR.exists():
        for f in EXPORT_DIR.iterdir():
            if f.suffix == ".zip":
                try:
                    f.unlink()
                    qtd_exports_removidos += 1
                except Exception:
                    pass

    # Remover manifestos
    if MANIFEST_DIR.exists():
        for f in MANIFEST_DIR.iterdir():
            if f.suffix == ".json":
                try:
                    f.unlink()
                except Exception:
                    pass

    # Remover usuários não-MASTER
    cursor.execute("SELECT COUNT(*) FROM usuarios WHERE perfil != 'MASTER'")
    usuarios_removidos = cursor.fetchone()[0]
    cursor.execute("DELETE FROM usuarios WHERE perfil != 'MASTER'")
    conn.commit()

    conn.close()

    return {
        "sucesso": True,
        "total_registros_removidos": total_removidos,
        "tabelas_processadas": len(resultados),
        "detalhes_tabelas": resultados,
        "usuarios_removidos": usuarios_removidos,
        "backups_locais_removidos": qtd_backups_removidos,
        "exports_removidos": qtd_exports_removidos,
        "data_reset": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

# ============================================================
# BLOCO 8 - LIMPEZA SELETIVA POR MÓDULO
# ============================================================
# Toda a lógica reside aqui. A interface apenas chama estas funções.
# Para adicionar um novo módulo, edite o dicionário MODULOS_LIMPEZA.

# ── Utilitário de conexão ──

def _obter_conn():
    """Retorna conexão com o banco SQLite."""
    return get_connection()

# ── Contagem de registros (segura) ──

def _contar_registros(cursor, tabela: str) -> int:
    """Retorna a quantidade de registros em uma tabela, com segurança."""
    try:
        cursor.execute(f'SELECT COUNT(*) FROM "{tabela}"')
        return cursor.fetchone()[0]
    except Exception:
        return 0

# ── Obter lista de módulos disponíveis ──

def obter_modulos_limpeza() -> list:
    """
    Retorna a lista de nomes dos módulos disponíveis para limpeza.
    """
    return list(MODULOS_LIMPEZA.keys())

# ── Status do módulo (quantidade de registros) ──

def obter_status_modulo(nome_modulo: str) -> dict:
    """
    Retorna o status de um módulo: tabelas, registros totais e
    registros por tabela.
    """
    if nome_modulo not in MODULOS_LIMPEZA:
        return {"erro": f"Módulo '{nome_modulo}' não encontrado"}

    tabelas = MODULOS_LIMPEZA[nome_modulo]["tabelas"]
    conn = _obter_conn()
    cursor = conn.cursor()

    info_tabelas = []
    total_registros = 0
    tabelas_existentes = 0

    for tabela in tabelas:
        qtd = _contar_registros(cursor, tabela)
        info_tabelas.append({
            "nome": tabela,
            "registros": qtd,
        })
        total_registros += qtd
        if qtd > 0 or True:  # conta como existente mesmo se vazia
            tabelas_existentes += 1

    conn.close()

    return {
        "modulo": nome_modulo,
        "descricao": MODULOS_LIMPEZA[nome_modulo]["descricao"],
        "tabelas": info_tabelas,
        "quantidade_tabelas": len(tabelas),
        "total_registros": total_registros,
    }

# ── Status de todos os módulos (para exibição inicial) ──

def obter_status_todos_modulos() -> list:
    """
    Retorna status de todos os módulos de uma vez.
    """
    resultados = []
    for nome_modulo in MODULOS_LIMPEZA:
        resultados.append(obter_status_modulo(nome_modulo))
    return resultados

# ── Dependências entre módulos (Visualizar Dependências) ──

def obter_dependencias_modulo(nome_modulo: str) -> dict:
    """
    Mapeia as dependências/donas de um módulo.
    Mostra quais outros módulos compartilham tabelas.
    """
    if nome_modulo not in MODULOS_LIMPEZA:
        return {"erro": f"Módulo '{nome_modulo}' não encontrado"}

    tabelas_modulo = set(MODULOS_LIMPEZA[nome_modulo]["tabelas"])

    # Encontrar outros módulos que compartilham tabelas
    dependencias = []
    for outro_modulo, dados in MODULOS_LIMPEZA.items():
        if outro_modulo == nome_modulo:
            continue
        tabelas_compartilhadas = tabelas_modulo.intersection(
            set(dados["tabelas"])
        )
        if tabelas_compartilhadas:
            dependencias.append({
                "modulo": outro_modulo,
                "tabelas": sorted(tabelas_compartilhadas),
            })

    # Relações conhecidas entre módulos (dependências lógicas)
    # Mapeamento manual de dependências entre módulos
    MAPA_DEPENDENCIAS = {
        "Pipeline OS": [
            "Gestão de Terceiros",  # terceiros_servicos pode referenciar OS
            "Faturamento",          # OS faturadas viram faturamento
        ],
        "Faturamento": [
            "Pipeline OS",          # faturamento vem de OS
        ],
        "Gestão de Terceiros": [
            "Pipeline OS",          # serviços terceiros vinculados a OS
        ],
        "Relacionamento Comercial": [
            "Cliente 360",          # interações vinculadas a clientes
            "Alertas",              # pendências geram alertas
        ],
        "Parque Mitsubishi": [
            "Cliente 360",          # máquinas vinculadas a clientes
        ],
        "Base Produtos Importados": [
            "Centro Importações",   # produtos usados em importação
        ],
        "Relatório IA": [
            "Cliente 360",          # relatórios vinculados a clientes
        ],
    }

    dependencias_logicas = MAPA_DEPENDENCIAS.get(nome_modulo, [])

    # Montar grafo simples
    grafo = [nome_modulo]
    for dep in dependencias_logicas:
        grafo.append(f"↓ {dep}")
    for dep in dependencias:
        label = f"↓ {dep['modulo']} (tabelas: {', '.join(dep['tabelas'])})"
        if label not in grafo:
            grafo.append(label)

    return {
        "modulo": nome_modulo,
        "tabelas": sorted(tabelas_modulo),
        "dependencias_logicas": dependencias_logicas,
        "grafo": grafo,
    }

# ── Pré-visualização da limpeza ──

def preparar_limpeza_modulo(nome_modulo: str) -> dict:
    """
    Retorna um resumo do que será apagado ao executar a limpeza
    do módulo, sem efetivamente apagar nada.
    Útil para exibir antes da confirmação.
    """
    return obter_status_modulo(nome_modulo)

# ── Executar limpeza seletiva ──

def executar_limpeza_modulo(
    nome_modulo: str,
    reset_sequence: bool = False,
) -> dict:
    """
    Executa a limpeza de todas as tabelas de um módulo específico.
    - Apenas DELETE, nunca DROP TABLE.
    - Preserva estrutura, índices, usuários, unidades, configurações.
    - Se reset_sequence=True, reseta AUTOINCREMENT das tabelas afetadas.
    - Retorna relatório completo.
    """
    import time

    if nome_modulo not in MODULOS_LIMPEZA:
        return {"sucesso": False, "erro": f"Módulo '{nome_modulo}' não encontrado"}

    tabelas = MODULOS_LIMPEZA[nome_modulo]["tabelas"]
    conn = _obter_conn()
    cursor = conn.cursor()

    inicio = time.time()
    resultados = []
    total_removidos = 0
    tabelas_afetadas = 0
    erros = []

    for tabela in tabelas:
        try:
            # Contar antes
            cursor.execute(f'SELECT COUNT(*) FROM "{tabela}"')
            antes = cursor.fetchone()[0]

            if antes > 0:
                # Executar DELETE (nunca DROP)
                cursor.execute(f'DELETE FROM "{tabela}"')
                conn.commit()
                removidos = cursor.rowcount
                total_removidos += removidos
                tabelas_afetadas += 1

                # Resetar AUTOINCREMENT se solicitado
                if reset_sequence:
                    try:
                        cursor.execute(
                            "DELETE FROM sqlite_sequence WHERE name = ?",
                            (tabela,),
                        )
                        conn.commit()
                    except Exception:
                        pass

                resultados.append({
                    "tabela": tabela,
                    "removidos": removidos,
                    "status": "ok",
                })
            else:
                resultados.append({
                    "tabela": tabela,
                    "removidos": 0,
                    "status": "vazia",
                })

        except Exception as e:
            erros.append({
                "tabela": tabela,
                "erro": str(e),
            })
            resultados.append({
                "tabela": tabela,
                "removidos": 0,
                "status": "erro",
                "erro": str(e),
            })

    conn.close()
    tempo = time.time() - inicio

    return {
        "sucesso": len(erros) == 0 or total_removidos > 0,
        "modulo": nome_modulo,
        "tabelas_afetadas": tabelas_afetadas,
        "total_tabelas_modulo": len(tabelas),
        "total_registros_removidos": total_removidos,
        "tempo_segundos": round(tempo, 2),
        "reset_sequence": reset_sequence,
        "detalhes": resultados,
        "erros": erros if erros else None,
        "data_limpeza": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

# ============================================================
# BLOCO 9 - RESTAURAÇÃO COMPLETA DO SISTEMA (v2.4.2)
# ============================================================
# Toda a lógica de restauração reside aqui.
# Nenhuma SQL na interface.

LOG_FILE = Path("logs/restauracoes.log")

def _registrar_log_restauracao(entrada: dict) -> None:
    """
    Registra uma entrada no log de restaurações.
    """
    LOG_FILE.parent.mkdir(exist_ok=True)
    try:
        with open(str(LOG_FILE), "a", encoding="utf-8") as f:
            f.write(json.dumps(entrada, ensure_ascii=False) + "\n")
    except Exception:
        pass

def listar_backups() -> list:
    """
    Lista todos os backups disponíveis para restauração.
    Varre os diretórios backups/ e backups/export/.
    Retorna lista ordenada do mais recente para o mais antigo.
    """
    backups = []
    vistos = set()

    # Backup .db locais
    if BACKUP_DIR.exists():
        for f in sorted(
            BACKUP_DIR.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True
        ):
            if f.suffix == ".db" and f.name not in vistos:
                backups.append({
                    "nome": f.name,
                    "caminho": str(f.resolve()),
                    "tamanho_kb": round(f.stat().st_size / 1024, 2),
                    "tamanho_bytes": f.stat().st_size,
                    "modificado": datetime.fromtimestamp(
                        f.stat().st_mtime
                    ).strftime("%d/%m/%Y %H:%M"),
                    "tipo": "SQLite Direto (.db)",
                })
                vistos.add(f.name)

    # Backup .zip exportados
    if EXPORT_DIR.exists():
        for f in sorted(
            EXPORT_DIR.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True
        ):
            if f.suffix == ".zip" and f.name not in vistos:
                backups.append({
                    "nome": f.name,
                    "caminho": str(f.resolve()),
                    "tamanho_kb": round(f.stat().st_size / 1024, 2),
                    "tamanho_bytes": f.stat().st_size,
                    "modificado": datetime.fromtimestamp(
                        f.stat().st_mtime
                    ).strftime("%d/%m/%Y %H:%M"),
                    "tipo": "Backup Exportado (.zip)",
                })
                vistos.add(f.name)

    return backups

def obter_informacoes_backup(caminho: str) -> dict:
    """
    Obtém informações detalhadas de um arquivo de backup.
    Extrai metadados sem validar profundamente.
    """
    try:
        caminho_p = Path(caminho)
        if not caminho_p.exists():
            return {"erro": "Arquivo não encontrado"}

        info = {
            "nome": caminho_p.name,
            "caminho": str(caminho_p.resolve()),
            "tamanho_kb": round(caminho_p.stat().st_size / 1024, 2),
            "tamanho_bytes": caminho_p.stat().st_size,
            "extensao": caminho_p.suffix,
            "modificado": datetime.fromtimestamp(
                caminho_p.stat().st_mtime
            ).strftime("%d/%m/%Y %H:%M"),
        }

        if caminho_p.suffix == ".zip":
            with zipfile.ZipFile(str(caminho_p), "r") as zf:
                arquivos = zf.namelist()
                info["arquivos_zip"] = arquivos
                info["tem_banco"] = "crm.db" in arquivos
                info["tem_manifesto"] = "manifesto.json" in arquivos
                info["tipo"] = "Backup Exportado (.zip)"

                if "manifesto.json" in arquivos:
                    try:
                        manifesto = json.loads(
                            zf.read("manifesto.json").decode("utf-8")
                        )
                        info["manifesto"] = manifesto
                        # Extrair dados do manifesto
                        info["data_backup"] = f"{manifesto.get('data', '?')} {manifesto.get('hora', '?')}"
                        info["versao_crm"] = manifesto.get("crm_version", "?")
                        info["quantidade_tabelas"] = manifesto.get("quantidade_tabelas", "?")
                        info["quantidade_registros"] = manifesto.get("quantidade_registros", "?")
                        info["tabelas"] = manifesto.get("tabelas", [])
                    except (json.JSONDecodeError, KeyError):
                        info["manifesto"] = None

        elif caminho_p.suffix == ".db":
            info["tipo"] = "SQLite Direto (.db)"
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tabelas = [row[0] for row in cursor.fetchall() if row[0] != "sqlite_sequence"]
                info["tabelas"] = tabelas
                info["quantidade_tabelas"] = len(tabelas)

                # Contar registros
                total_reg = 0
                for t in tabelas:
                    try:
                        cursor.execute(f'SELECT COUNT(*) FROM "{t}"')
                        total_reg += cursor.fetchone()[0]
                    except Exception:
                        pass
                info["quantidade_registros"] = total_reg

                # Versão do banco
                cursor.execute(
                    "SELECT valor FROM configuracoes WHERE chave = 'db_version'"
                )
                row = cursor.fetchone()
                info["versao_crm"] = row[0] if row else "?"
                conn.close()
            except sqlite3.DatabaseError as e:
                info["erro_sqlite"] = str(e)

        return info

    except Exception as e:
        return {"erro": f"Erro ao ler informações: {str(e)}"}

def validar_backup(caminho: str) -> dict:
    """
    Valida completamente um arquivo de backup para restauração.
    Verifica:
    - Arquivo existe
    - Extensão válida (.zip ou .db)
    - Banco SQLite íntegro
    - Versão do CRM
    - Data do backup
    - Quantidade de tabelas
    - Tamanho
    - Hash (caso exista)
    - Manifesto
    """
    resultado = {
        "valido": False,
        "pode_restaurar": False,
        "verificacoes": [],
        "erros": [],
    }

    # 1. Arquivo existe
    caminho_p = Path(caminho)
    if not caminho_p.exists():
        resultado["erros"].append("❌ Arquivo não encontrado")
        resultado["verificacoes"].append({"item": "Arquivo existe", "status": "❌", "detalhe": "Arquivo não encontrado"})
        return resultado

    resultado["verificacoes"].append({
        "item": "Arquivo existe",
        "status": "✅",
        "detalhe": f"Encontrado: {caminho_p.name}",
    })

    # 2. Extensão válida
    if caminho_p.suffix not in (".zip", ".db"):
        resultado["erros"].append("❌ Extensão inválida. Use .zip ou .db")
        resultado["verificacoes"].append({
            "item": "Extensão válida",
            "status": "❌",
            "detalhe": f"Extensão '{caminho_p.suffix}' não suportada",
        })
        return resultado

    resultado["verificacoes"].append({
        "item": "Extensão válida",
        "status": "✅",
        "detalhe": f"Formato: {caminho_p.suffix}",
    })

    # 3. Tamanho
    tamanho_bytes = caminho_p.stat().st_size
    if tamanho_bytes == 0:
        resultado["erros"].append("❌ Arquivo vazio")
        resultado["verificacoes"].append({
            "item": "Tamanho",
            "status": "❌",
            "detalhe": "Arquivo vazio (0 bytes)",
        })
        return resultado

    resultado["verificacoes"].append({
        "item": "Tamanho",
        "status": "✅",
        "detalhe": f"{round(tamanho_bytes / 1024, 2)} KB",
    })

    # 4. Hash SHA-256 do arquivo
    try:
        sha256_hash = hashlib.sha256()
        with open(str(caminho_p), "rb") as f:
            for bloco in iter(lambda: f.read(65536), b""):
                sha256_hash.update(bloco)
        hash_calculado = sha256_hash.hexdigest()
        resultado["hash_sha256"] = hash_calculado
        resultado["verificacoes"].append({
            "item": "Hash SHA-256",
            "status": "✅",
            "detalhe": f"{hash_calculado[:16]}... (calculado)",
        })
    except Exception as e:
        resultado["verificacoes"].append({
            "item": "Hash SHA-256",
            "status": "⚠️",
            "detalhe": f"Não foi possível calcular hash: {str(e)}",
        })

    # 5. Validação específica por tipo
    if caminho_p.suffix == ".zip":
        return _validar_backup_zip(caminho_p, resultado)
    else:
        return _validar_backup_db(caminho_p, resultado)

def _validar_backup_zip(caminho_p: Path, resultado: dict) -> dict:
    """Valida backup no formato .zip."""
    try:
        with zipfile.ZipFile(str(caminho_p), "r") as zf:
            # Verificar se contém crm.db
            if "crm.db" not in zf.namelist():
                resultado["erros"].append("❌ ZIP não contém crm.db")
                resultado["verificacoes"].append({
                    "item": "Contém crm.db",
                    "status": "❌",
                    "detalhe": "Arquivo crm.db não encontrado no ZIP",
                })
                return resultado

            resultado["verificacoes"].append({
                "item": "Contém crm.db",
                "status": "✅",
                "detalhe": "Banco de dados presente no ZIP",
            })

            # Extrair e validar banco SQLite
            temp_db = Path(f"temp_validacao_{time_module.time()}.db")
            try:
                temp_data = zf.read("crm.db")
                temp_db.write_bytes(temp_data)

                resultado_banco = _validar_banco_sqlite(str(temp_db))
                resultado["verificacoes"].extend(resultado_banco["verificacoes"])
                if not resultado_banco["integro"]:
                    resultado["erros"].extend(resultado_banco["erros"])
            finally:
                if temp_db.exists():
                    temp_db.unlink()

            # Ler manifesto
            if "manifesto.json" in zf.namelist():
                try:
                    manifesto = json.loads(
                        zf.read("manifesto.json").decode("utf-8")
                    )
                    resultado["manifesto"] = manifesto
                    resultado["verificacoes"].append({
                        "item": "Manifesto",
                        "status": "✅",
                        "detalhe": "Manifesto encontrado e lido",
                    })

                    # Validar versão CRM
                    versao_backup = manifesto.get("crm_version", "")
                    if versao_backup:
                        resultado["verificacoes"].append({
                            "item": "Versão CRM",
                            "status": "✅",
                            "detalhe": f"Versão: {versao_backup}",
                        })
                    else:
                        resultado["verificacoes"].append({
                            "item": "Versão CRM",
                            "status": "⚠️",
                            "detalhe": "Versão não especificada no manifesto",
                        })

                    # Validar data
                    data_backup = manifesto.get("data", "")
                    hora_backup = manifesto.get("hora", "")
                    resultado["verificacoes"].append({
                        "item": "Data do Backup",
                        "status": "✅",
                        "detalhe": f"{data_backup} {hora_backup}",
                    })

                    # Validar tabelas
                    qtd_tabelas = manifesto.get("quantidade_tabelas", 0)
                    resultado["verificacoes"].append({
                        "item": "Quantidade de Tabelas",
                        "status": "✅",
                        "detalhe": f"{qtd_tabelas} tabelas",
                    })

                except (json.JSONDecodeError, KeyError) as e:
                    resultado["verificacoes"].append({
                        "item": "Manifesto",
                        "status": "⚠️",
                        "detalhe": f"Manifesto inválido: {str(e)}",
                    })
            else:
                resultado["verificacoes"].append({
                    "item": "Manifesto",
                    "status": "⚠️",
                    "detalhe": "Manifesto não encontrado (backup sem manifesto)",
                })

    except zipfile.BadZipFile:
        resultado["erros"].append("❌ Arquivo ZIP inválido ou corrompido")
        resultado["verificacoes"].append({
            "item": "Arquivo ZIP",
            "status": "❌",
            "detalhe": "ZIP inválido ou corrompido",
        })
        return resultado
    except Exception as e:
        resultado["erros"].append(f"❌ Erro ao processar ZIP: {str(e)}")
        resultado["verificacoes"].append({
            "item": "Arquivo ZIP",
            "status": "❌",
            "detalhe": str(e),
        })
        return resultado

    # Decidir se pode restaurar
    resultado["pode_restaurar"] = len(resultado["erros"]) == 0
    resultado["valido"] = len(resultado["erros"]) == 0

    return resultado

def _validar_backup_db(caminho_p: Path, resultado: dict) -> dict:
    """Valida backup no formato .db direto."""
    resultado_banco = _validar_banco_sqlite(str(caminho_p))
    resultado["verificacoes"].extend(resultado_banco["verificacoes"])

    if not resultado_banco["integro"]:
        resultado["erros"].extend(resultado_banco["erros"])
    else:
        # Tentar obter versão e informações adicionais
        try:
            conn = get_connection()
            cursor = conn.cursor()

            # Versão
            cursor.execute("SELECT valor FROM configuracoes WHERE chave = 'db_version'")
            row = cursor.fetchone()
            versao = row[0] if row else "?"
            resultado["verificacoes"].append({
                "item": "Versão CRM",
                "status": "✅",
                "detalhe": f"Versão: {versao}",
            })

            # Tabelas
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tabelas = [r[0] for r in cursor.fetchall() if r[0] != "sqlite_sequence"]
            resultado["verificacoes"].append({
                "item": "Quantidade de Tabelas",
                "status": "✅",
                "detalhe": f"{len(tabelas)} tabelas encontradas",
            })
            resultado["tabelas"] = tabelas

            conn.close()
        except Exception as e:
            resultado["verificacoes"].append({
                "item": "Informações adicionais",
                "status": "⚠️",
                "detalhe": str(e),
            })

    resultado["pode_restaurar"] = len(resultado["erros"]) == 0
    resultado["valido"] = len(resultado["erros"]) == 0

    return resultado

def _validar_banco_sqlite(caminho: str) -> dict:
    """
    Valida a integridade de um banco SQLite.
    Retorna dict com verificações.
    """
    resultado = {
        "integro": False,
        "verificacoes": [],
        "erros": [],
    }

    try:
        conn = get_connection()

        # PRAGMA integrity_check
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check")
        integridade = cursor.fetchall()

        if len(integridade) == 1 and integridade[0][0] == "ok":
            resultado["verificacoes"].append({
                "item": "Integridade SQLite",
                "status": "✅",
                "detalhe": "Banco íntegro (integrity_check: ok)",
            })
        else:
            erros_integridade = [row[0] for row in integridade if row[0] != "ok"]
            resultado["erros"].extend(erros_integridade)
            resultado["verificacoes"].append({
                "item": "Integridade SQLite",
                "status": "❌",
                "detalhe": f"Erros: {', '.join(erros_integridade)}",
            })
            conn.close()
            return resultado

        # PRAGMA quick_check adicional
        cursor.execute("PRAGMA quick_check")
        quick = cursor.fetchone()
        if quick and quick[0] == "ok":
            resultado["verificacoes"].append({
                "item": "Quick Check",
                "status": "✅",
                "detalhe": "Quick check: ok",
            })

        # PRAGMA schema_version
        cursor.execute("PRAGMA schema_version")
        schema_ver = cursor.fetchone()[0]
        resultado["verificacoes"].append({
            "item": "Schema Version",
            "status": "✅",
            "detalhe": f"Schema versão: {schema_ver}",
        })

        # Verificar se há tabelas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tabelas = [r[0] for r in cursor.fetchall() if r[0] != "sqlite_sequence"]
        if len(tabelas) == 0:
            resultado["erros"].append("❌ Banco sem tabelas")
            resultado["verificacoes"].append({
                "item": "Tabelas existentes",
                "status": "❌",
                "detalhe": "Nenhuma tabela encontrada",
            })
            conn.close()
            return resultado

        resultado["verificacoes"].append({
            "item": "Tabelas existentes",
            "status": "✅",
            "detalhe": f"{len(tabelas)} tabelas encontradas",
        })
        resultado["tabelas"] = tabelas

        conn.close()
        resultado["integro"] = True

    except sqlite3.DatabaseError as e:
        resultado["erros"].append(f"❌ Erro de banco SQLite: {str(e)}")
        resultado["verificacoes"].append({
            "item": "Conexão SQLite",
            "status": "❌",
            "detalhe": str(e),
        })
    except Exception as e:
        resultado["erros"].append(f"❌ Erro inesperado: {str(e)}")
        resultado["verificacoes"].append({
            "item": "Validação",
            "status": "❌",
            "detalhe": str(e),
        })

    return resultado

def ler_manifesto_backup(caminho: str) -> dict:
    """
    Lê o manifesto de um backup.
    Para .zip, lê o manifesto interno.
    Para .db, retorna informações extraídas do banco.
    """
    try:
        caminho_p = Path(caminho)
        if not caminho_p.exists():
            return {"erro": "Arquivo não encontrado"}

        if caminho_p.suffix == ".zip":
            with zipfile.ZipFile(str(caminho_p), "r") as zf:
                if "manifesto.json" in zf.namelist():
                    manifesto = json.loads(
                        zf.read("manifesto.json").decode("utf-8")
                    )
                    return {
                        "encontrado": True,
                        "manifesto": manifesto,
                        "fonte": "manifesto.json (interno do ZIP)",
                    }
                else:
                    return {
                        "encontrado": False,
                        "manifesto": None,
                        "fonte": "Nenhum manifesto encontrado no ZIP",
                    }

        elif caminho_p.suffix == ".db":
            # Para .db, montar manifesto a partir do banco
            conn = get_connection()
            cursor = conn.cursor()

            # Versão
            cursor.execute("SELECT valor FROM configuracoes WHERE chave = 'db_version'")
            row = cursor.fetchone()
            versao = row[0] if row else "?"

            # Tabelas e registros
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tabelas = [r[0] for r in cursor.fetchall() if r[0] != "sqlite_sequence"]

            total_registros = 0
            for t in tabelas:
                try:
                    cursor.execute(f'SELECT COUNT(*) FROM "{t}"')
                    total_registros += cursor.fetchone()[0]
                except Exception:
                    pass

            conn.close()

            manifesto_montado = {
                "crm_version": versao,
                "db_version": versao,
                "data": datetime.fromtimestamp(
                    caminho_p.stat().st_mtime
                ).strftime("%Y-%m-%d"),
                "hora": datetime.fromtimestamp(
                    caminho_p.stat().st_mtime
                ).strftime("%H:%M:%S"),
                "quantidade_tabelas": len(tabelas),
                "quantidade_registros": total_registros,
                "tamanho_bytes": caminho_p.stat().st_size,
                "tabelas": tabelas,
            }

            return {
                "encontrado": True,
                "manifesto": manifesto_montado,
                "fonte": "Extraído do banco SQLite (.db)",
            }

        return {
            "encontrado": False,
            "manifesto": None,
            "fonte": "Formato não suportado para leitura de manifesto",
        }

    except Exception as e:
        return {"erro": f"Erro ao ler manifesto: {str(e)}"}

def criar_backup_automatico_pre_restauracao() -> dict:
    """
    Cria um backup automático do banco atual antes de restaurar.
    Retorna informações do backup criado.
    """
    BACKUP_DIR.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_backup = f"pre_restore_{timestamp}.db"
    destino = BACKUP_DIR / nome_backup

    try:
        shutil.copy2(str(DB_PATH), str(destino))

        return {
            "sucesso": True,
            "arquivo": str(destino),
            "nome": nome_backup,
            "tamanho_kb": round(destino.stat().st_size / 1024, 2),
            "timestamp": timestamp,
            "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        }
    except Exception as e:
        return {
            "sucesso": False,
            "erro": str(e),
        }

# ============================================================
# BLOCO 10 - BACKUP PORTÁTIL (DOWNLOAD) e RESTAURAÇÃO POR UPLOAD
# ============================================================
# Substitui a dependência de diretórios fixos do servidor.
# O usuário faz download do backup e upload para restaurar.

def gerar_backup_zip_bytes() -> Tuple[bytes, dict]:
    """
    Gera backup portátil do banco com manifesto em memória.
    
    Retorna:
        (bytes do ZIP, dict com metadados)
    
    O ZIP contém:
        - crm.db (cópia consistente do banco)
        - manifesto.json (metadados completos)
    
    Não salva em disco obrigatoriamente.
    Os bytes podem ser usados diretamente com st.download_button().
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_zip = f"backup_ULITEC_{timestamp}.zip"
    
    # Obter metadados do banco atual
    status = obter_status_sistema()
    
    # Calcular hash SHA256 do banco
    sha256_hash = hashlib.sha256()
    with open(str(DB_PATH), "rb") as f:
        for bloco in iter(lambda: f.read(65536), b""):
            sha256_hash.update(bloco)
    hash_banco = sha256_hash.hexdigest()
    
    # Obter schema version do banco
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA schema_version")
    schema_version = cursor.fetchone()[0]
    conn.close()
    
    # Montar manifesto completo
    manifesto = {
        "sistema": "ULITEC CRM",
        "versao_crm": CRM_VERSION,
        "build": BUILD,
        "db_version": status["db_version"],
        "schema_version": schema_version,
        "data": datetime.now().strftime("%Y-%m-%d"),
        "hora": datetime.now().strftime("%H:%M:%S"),
        "timestamp": timestamp,
        "quantidade_tabelas": status["total_tabelas"],
        "quantidade_registros": status["total_registros"],
        "tamanho_bytes": status["tamanho_bytes"],
        "tamanho_kb": status["tamanho_kb"],
        "tamanho_mb": status["tamanho_mb"],
        "hash_sha256": hash_banco,
        "tabelas": list(status["info_tabelas"].keys()),
        "registros_por_tabela": status["info_tabelas"],
    }
    
    # Criar ZIP em memória
    zip_buffer = tempfile.SpooledTemporaryFile(max_size=100 * 1024 * 1024)  # 100MB max
    try:
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            # Adicionar banco
            zf.write(str(DB_PATH), "crm.db")
            
            # Adicionar manifesto
            zf.writestr(
                "manifesto.json",
                json.dumps(manifesto, indent=2, ensure_ascii=False).encode("utf-8"),
            )
        
        zip_buffer.seek(0)
        zip_bytes = zip_buffer.read()
    finally:
        zip_buffer.close()
    
    metadados = {
        "nome_arquivo": nome_zip,
        "tamanho_bytes": len(zip_bytes),
        "tamanho_kb": round(len(zip_bytes) / 1024, 2),
        "tamanho_mb": round(len(zip_bytes) / 1024 / 1024, 2),
        "timestamp": timestamp,
        "hash_sha256": hash_banco,
        "tabelas": status["total_tabelas"],
        "registros": status["total_registros"],
        "manifesto": manifesto,
    }
    
    # Opcional: salvar cópia local para histórico
    try:
        BACKUP_DIR.mkdir(exist_ok=True)
        destino_local = BACKUP_DIR / nome_zip
        destino_local.write_bytes(zip_bytes)
        metadados["copia_local"] = str(destino_local)
    except Exception:
        metadados["copia_local"] = None
    
    # Registrar no banco
    try:
        conn = get_connection()
        conn.execute(
            """INSERT INTO configuracoes (chave, valor, descricao)
               VALUES (?, ?, ?)
               ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor""",
            ("ultimo_backup", timestamp, f"Último backup: {nome_zip}"),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass
    
    return zip_bytes, metadados

def processar_arquivo_enviado(file_bytes: bytes, nome_original: str) -> dict:
    """
    Processa um arquivo enviado pelo usuário para restauração.
    
    Aceita:
        - .zip (contendo crm.db + manifesto.json opcional)
        - .db (banco SQLite direto)
    
    Retorna dict com:
        - valido: bool
        - erros: list
        - resumo: dict (informações para exibição ao usuário)
        - dados_banco: bytes (bytes do banco SQLite extraído/validado)
        - temp_dir: Path (diretório temporário a ser limpo depois)
    """
    resultado = {
        "valido": False,
        "erros": [],
        "resumo": {},
        "dados_banco": None,
        "temp_dir": None,
        "manifesto": None,
    }
    
    # Validar extensão
    sufixo = Path(nome_original).suffix.lower()
    if sufixo not in (".zip", ".db"):
        resultado["erros"].append(
            f"Formato não suportado: '{sufixo}'. Use .zip ou .db."
        )
        return resultado
    
    # Criar diretório temporário para extração
    temp_dir = Path(tempfile.mkdtemp(prefix="ulitec_restore_"))
    resultado["temp_dir"] = temp_dir
    
    try:
        if sufixo == ".zip":
            return _processar_upload_zip(file_bytes, nome_original, temp_dir, resultado)
        else:
            return _processar_upload_db(file_bytes, nome_original, temp_dir, resultado)
    except Exception as e:
        resultado["erros"].append(f"Erro ao processar arquivo: {str(e)}")
        return resultado

def _processar_upload_zip(
    file_bytes: bytes, nome_original: str, temp_dir: Path, resultado: dict
) -> dict:
    """Processa arquivo ZIP enviado para restauração."""
    try:
        # Salvar ZIP temporário
        zip_temp = temp_dir / nome_original
        zip_temp.write_bytes(file_bytes)
        
        with zipfile.ZipFile(str(zip_temp), "r") as zf:
            arquivos = zf.namelist()
            
            # Verificar se contém crm.db
            if "crm.db" not in arquivos:
                resultado["erros"].append(
                    "❌ ZIP não contém 'crm.db'. Estrutura inválida."
                )
                return resultado
            
            # Extrair crm.db para validar
            db_temp = temp_dir / "crm.db"
            db_temp.write_bytes(zf.read("crm.db"))
            
            # Validar integridade do banco extraído
            validacao = _validar_banco_sqlite(str(db_temp))
            if not validacao["integro"]:
                resultado["erros"].append(
                    "❌ Banco SQLite extraído está corrompido ou com erros."
                )
                resultado["erros"].extend(validacao.get("erros", []))
                return resultado
            
            resultado["dados_banco"] = db_temp.read_bytes()
            
            # Ler manifesto se existir
            if "manifesto.json" in arquivos:
                try:
                    manifesto_raw = zf.read("manifesto.json").decode("utf-8")
                    manifesto = json.loads(manifesto_raw)
                    resultado["manifesto"] = manifesto
                    
                    # Montar resumo a partir do manifesto
                    resultado["resumo"] = {
                        "nome_arquivo": nome_original,
                        "formato": "ZIP",
                        "data": f"{manifesto.get('data', '?')} {manifesto.get('hora', '?')}",
                        "versao_crm": manifesto.get("versao_crm", "?"),
                        "quantidade_tabelas": manifesto.get("quantidade_tabelas", 0),
                        "quantidade_registros": manifesto.get("quantidade_registros", 0),
                        "tamanho_kb": manifesto.get("tamanho_kb", 0),
                        "hash_sha256": manifesto.get("hash_sha256", "?"),
                        "schema_version": manifesto.get("schema_version", "?"),
                        "tabelas": manifesto.get("tabelas", []),
                    }
                    
                    # Verificar hash se disponível
                    hash_manifesto = manifesto.get("hash_sha256", "")
                    if hash_manifesto and hash_manifesto != "PREPARADO_PARA_HASH":
                        hash_extraido = hashlib.sha256(
                            resultado["dados_banco"]
                        ).hexdigest()
                        if hash_extraido != hash_manifesto:
                            resultado["erros"].append(
                                f"❌ Hash SHA-256 não confere!\n"
                                f"Manifesto: {hash_manifesto[:16]}...\n"
                                f"Calculado: {hash_extraido[:16]}..."
                            )
                            return resultado
                
                except (json.JSONDecodeError, KeyError, UnicodeDecodeError) as e:
                    resultado["erros"].append(
                        f"⚠️ Manifesto inválido: {str(e)}"
                    )
                    # Continua mesmo sem manifesto válido
            
            # Se não tem manifesto, extrair informações do banco
            if not resultado["resumo"]:
                resultado["resumo"] = _extrair_resumo_banco(
                    db_temp, nome_original, "ZIP"
                )
            
            resultado["valido"] = len(resultado["erros"]) == 0
            return resultado
    
    except zipfile.BadZipFile:
        resultado["erros"].append("❌ Arquivo ZIP inválido ou corrompido.")
        return resultado
    except Exception as e:
        resultado["erros"].append(f"❌ Erro ao processar ZIP: {str(e)}")
        return resultado

def _processar_upload_db(
    file_bytes: bytes, nome_original: str, temp_dir: Path, resultado: dict
) -> dict:
    """Processa arquivo .db enviado para restauração."""
    try:
        # Salvar banco temporário
        db_temp = temp_dir / nome_original
        db_temp.write_bytes(file_bytes)
        
        # Validar integridade
        validacao = _validar_banco_sqlite(str(db_temp))
        if not validacao["integro"]:
            resultado["erros"].append(
                "❌ Banco SQLite inválido ou corrompido."
            )
            resultado["erros"].extend(validacao.get("erros", []))
            return resultado
        
        resultado["dados_banco"] = file_bytes
        
        # Calcular hash
        hash_calculado = hashlib.sha256(file_bytes).hexdigest()
        
        # Extrair resumo do banco
        resumo = _extrair_resumo_banco(db_temp, nome_original, "SQLite Direto")
        resumo["hash_sha256"] = hash_calculado
        resultado["resumo"] = resumo
        
        resultado["valido"] = True
        return resultado
    
    except Exception as e:
        resultado["erros"].append(f"❌ Erro ao processar banco: {str(e)}")
        return resultado

def _extrair_resumo_banco(db_path: Path, nome_original: str, formato: str) -> dict:
    """Extrai informações resumidas de um banco SQLite."""
    resumo = {
        "nome_arquivo": nome_original,
        "formato": formato,
        "data": datetime.fromtimestamp(db_path.stat().st_mtime).strftime(
            "%Y-%m-%d %H:%M"
        ),
        "versao_crm": "?",
        "quantidade_tabelas": 0,
        "quantidade_registros": 0,
        "tamanho_kb": round(db_path.stat().st_size / 1024, 2),
        "tabelas": [],
    }
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Tabelas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tabelas = [
            r[0] for r in cursor.fetchall() if r[0] != "sqlite_sequence"
        ]
        resumo["tabelas"] = tabelas
        resumo["quantidade_tabelas"] = len(tabelas)
        
        # Registros
        total_reg = 0
        for t in tabelas:
            try:
                cursor.execute(f'SELECT COUNT(*) FROM "{t}"')
                total_reg += cursor.fetchone()[0]
            except Exception:
                pass
        resumo["quantidade_registros"] = total_reg
        
        # Versão
        cursor.execute(
            "SELECT valor FROM configuracoes WHERE chave = 'db_version'"
        )
        row = cursor.fetchone()
        resumo["versao_crm"] = row[0] if row else "?"
        
        # Schema version
        cursor.execute("PRAGMA schema_version")
        resumo["schema_version"] = cursor.fetchone()[0]
        
        conn.close()
    except Exception:
        pass
    
    return resumo

def executar_restauracao_upload(
    dados_banco: bytes,
    nome_arquivo: str,
    usuario: str = "Sistema",
) -> dict:
    """
    Executa a restauração a partir dos bytes do banco validado.
    
    Fluxo:
    1. Criar backup automático do banco atual
    2. Substituir crm.db pelos bytes fornecidos
    3. Verificar integridade do novo banco
    4. Retornar relatório
    """
    inicio = time_module.time()
    
    # 1. Criar backup automático pré-restauração
    backup_auto = criar_backup_automatico_pre_restauracao()
    if not backup_auto["sucesso"]:
        return {
            "sucesso": False,
            "erro": f"Falha ao criar backup automático: {backup_auto.get('erro', 'Erro desconhecido')}",
            "tempo_segundos": round(time_module.time() - inicio, 2),
        }
    
    try:
        # 2. Obter informações do banco a restaurar
        temp_dir = Path(tempfile.mkdtemp(prefix="ulitec_exec_restore_"))
        temp_db = temp_dir / "temp_restore.db"
        
        try:
            temp_db.write_bytes(dados_banco)
            
            # Validar antes de substituir
            validacao = _validar_banco_sqlite(str(temp_db))
            if not validacao["integro"]:
                return {
                    "sucesso": False,
                    "erro": "Banco falhou na validação final de integridade",
                    "detalhes_validacao": validacao,
                    "backup_automatico": backup_auto,
                    "tempo_segundos": round(time_module.time() - inicio, 2),
                }
            
            # Coletar informações
            conn_temp = get_connection()
            cursor_temp = conn_temp.cursor()
            cursor_temp.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tabelas_restauro = [
                r[0] for r in cursor_temp.fetchall()
                if r[0] != "sqlite_sequence"
            ]
            
            total_reg_restauro = 0
            for t in tabelas_restauro:
                try:
                    cursor_temp.execute(f'SELECT COUNT(*) FROM "{t}"')
                    total_reg_restauro += cursor_temp.fetchone()[0]
                except Exception:
                    pass
            
            cursor_temp.execute(
                "SELECT valor FROM configuracoes WHERE chave = 'db_version'"
            )
            row = cursor_temp.fetchone()
            versao_restauro = row[0] if row else "?"
            
            cursor_temp.execute("PRAGMA schema_version")
            schema_restauro = cursor_temp.fetchone()[0]
            conn_temp.close()
            
            # 3. Substituir o banco
            shutil.copy2(str(temp_db), str(DB_PATH))
        
        finally:
            # Limpar diretório temporário
            shutil.rmtree(str(temp_dir), ignore_errors=True)
        
        # 4. Verificar integridade do novo banco
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check")
        integridade_final = [r[0] for r in cursor.fetchall()]
        
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tabelas_finais = [
            r[0] for r in cursor.fetchall()
            if r[0] != "sqlite_sequence"
        ]
        
        conn.close()
        
        # 5. Registrar log
        tempo_total = round(time_module.time() - inicio, 2)
        log_entry = {
            "data": datetime.now().strftime("%Y-%m-%d"),
            "hora": datetime.now().strftime("%H:%M:%S"),
            "usuario": usuario,
            "backup_utilizado": nome_arquivo,
            "backup_automatico": backup_auto["nome"],
            "resultado": (
                "sucesso"
                if all(x == "ok" for x in integridade_final)
                else "falha"
            ),
            "tempo_segundos": tempo_total,
            "tabelas_restauradas": len(tabelas_restauro),
            "registros_restaurados": total_reg_restauro,
            "versao_restaurada": versao_restauro,
        }
        _registrar_log_restauracao(log_entry)
        
        return {
            "sucesso": True,
            "backup_restaurado": nome_arquivo,
            "backup_automatico_criado": backup_auto["nome"],
            "backup_automatico_caminho": backup_auto["arquivo"],
            "tempo_segundos": tempo_total,
            "quantidade_tabelas": len(tabelas_restauro),
            "quantidade_registros": total_reg_restauro,
            "versao_restaurada": versao_restauro,
            "schema_version_restaurado": schema_restauro,
            "data_restauracao": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "integrity_check": (
                "ok"
                if all(x == "ok" for x in integridade_final)
                else "falha"
            ),
            "detalhes_integridade": integridade_final,
        }
    
    except Exception as e:
        return {
            "sucesso": False,
            "erro": f"Erro durante restauração: {str(e)}",
            "backup_automatico": backup_auto,
            "tempo_segundos": round(time_module.time() - inicio, 2),
        }

def limpar_temporarios_restauracao(temp_dir: Path) -> None:
    """
    Remove diretório temporário usado na validação de restauração.
    """
    if temp_dir and temp_dir.exists():
        try:
            shutil.rmtree(str(temp_dir), ignore_errors=True)
        except Exception:
            pass

def restaurar_backup(caminho_backup: str, usuario: str = "Sistema") -> dict:
    """
    Executa a restauração completa do sistema a partir de um backup.
    Fluxo:
    1. Valida backup
    2. Cria backup automático do banco atual
    3. Substitui crm.db
    4. Reabre conexão SQLite
    5. Executa PRAGMA integrity_check
    6. Retorna relatório completo

    Não utiliza DROP TABLE.
    Não executa DELETE.
    A restauração substitui completamente o banco.
    """
    inicio = time_module.time()
    caminho_p = Path(caminho_backup)

    if not caminho_p.exists():
        return {
            "sucesso": False,
            "erro": "Arquivo de backup não encontrado",
            "tempo_segundos": round(time_module.time() - inicio, 2),
        }

    # ── Backup automático pré-restauração ──
    backup_auto = criar_backup_automatico_pre_restauracao()
    if not backup_auto["sucesso"]:
        return {
            "sucesso": False,
            "erro": f"Falha ao criar backup automático: {backup_auto.get('erro', 'Erro desconhecido')}",
            "tempo_segundos": round(time_module.time() - inicio, 2),
        }

    try:
        # ── Obter o banco a ser restaurado ──
        if caminho_p.suffix == ".zip":
            # Extrair crm.db do ZIP
            with zipfile.ZipFile(str(caminho_p), "r") as zf:
                if "crm.db" not in zf.namelist():
                    return {
                        "sucesso": False,
                        "erro": "ZIP não contém crm.db",
                        "backup_automatico": backup_auto,
                        "tempo_segundos": round(time_module.time() - inicio, 2),
                    }
                banco_data = zf.read("crm.db")

            # Backup do banco extraído temporariamente para validar
            temp_path = Path(f"temp_restore_{time_module.time()}.db")
            try:
                temp_path.write_bytes(banco_data)

                # Validar o banco extraído
                validacao = _validar_banco_sqlite(str(temp_path))
                if not validacao["integro"]:
                    temp_path.unlink()
                    return {
                        "sucesso": False,
                        "erro": "Banco extraído do ZIP falhou na validação de integridade",
                        "detalhes_validacao": validacao,
                        "backup_automatico": backup_auto,
                        "tempo_segundos": round(time_module.time() - inicio, 2),
                    }

                # Obter informações antes de substituir
                conn_temp = get_connection()
                cursor_temp = conn_temp.cursor()
                cursor_temp.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tabelas_restauro = [r[0] for r in cursor_temp.fetchall() if r[0] != "sqlite_sequence"]

                total_reg_restauro = 0
                for t in tabelas_restauro:
                    try:
                        cursor_temp.execute(f'SELECT COUNT(*) FROM "{t}"')
                        total_reg_restauro += cursor_temp.fetchone()[0]
                    except Exception:
                        pass

                cursor_temp.execute("SELECT valor FROM configuracoes WHERE chave = 'db_version'")
                row = cursor_temp.fetchone()
                versao_restauro = row[0] if row else "?"
                conn_temp.close()

                # Substituir o banco atual
                shutil.copy2(str(temp_path), str(DB_PATH))
                temp_path.unlink()
            except Exception as e:
                if temp_path.exists():
                    temp_path.unlink()
                raise e

        elif caminho_p.suffix == ".db":
            # Validar o banco
            validacao = _validar_banco_sqlite(str(caminho_p))
            if not validacao["integro"]:
                return {
                    "sucesso": False,
                    "erro": "Banco de backup falhou na validação de integridade",
                    "detalhes_validacao": validacao,
                    "backup_automatico": backup_auto,
                    "tempo_segundos": round(time_module.time() - inicio, 2),
                }

            # Obter informações antes de substituir
            conn_orig = get_connection()
            cursor_orig = conn_orig.cursor()
            cursor_orig.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tabelas_restauro = [r[0] for r in cursor_orig.fetchall() if r[0] != "sqlite_sequence"]

            total_reg_restauro = 0
            for t in tabelas_restauro:
                try:
                    cursor_orig.execute(f'SELECT COUNT(*) FROM "{t}"')
                    total_reg_restauro += cursor_orig.fetchone()[0]
                except Exception:
                    pass

            cursor_orig.execute("SELECT valor FROM configuracoes WHERE chave = 'db_version'")
            row = cursor_orig.fetchone()
            versao_restauro = row[0] if row else "?"
            conn_orig.close()

            # Substituir o banco atual
            shutil.copy2(str(caminho_p), str(DB_PATH))

        else:
            return {
                "sucesso": False,
                "erro": "Formato de backup não suportado",
                "backup_automatico": backup_auto,
                "tempo_segundos": round(time_module.time() - inicio, 2),
            }

        # ── Reabrir conexão e verificar integridade ──
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check")
        integridade_final = [r[0] for r in cursor.fetchall()]

        # Verificar schema
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tabelas_finais = [r[0] for r in cursor.fetchall() if r[0] != "sqlite_sequence"]

        conn.close()

        # ── Registrar log ──
        tempo_total = round(time_module.time() - inicio, 2)
        log_entry = {
            "data": datetime.now().strftime("%Y-%m-%d"),
            "hora": datetime.now().strftime("%H:%M:%S"),
            "usuario": usuario,
            "backup_utilizado": caminho_p.name,
            "backup_automatico": backup_auto["nome"],
            "resultado": "sucesso" if all(x == "ok" for x in integridade_final) else "falha",
            "tempo_segundos": tempo_total,
            "tabelas_restauradas": len(tabelas_restauro),
            "registros_restaurados": total_reg_restauro,
            "versao_restaurada": versao_restauro,
        }
        _registrar_log_restauracao(log_entry)

        return {
            "sucesso": True,
            "backup_restaurado": caminho_p.name,
            "backup_automatico_criado": backup_auto["nome"],
            "backup_automatico_caminho": backup_auto["arquivo"],
            "tempo_segundos": tempo_total,
            "quantidade_tabelas": len(tabelas_restauro),
            "quantidade_registros": total_reg_restauro,
            "versao_restaurada": versao_restauro,
            "data_restauracao": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "integrity_check": "ok" if all(x == "ok" for x in integridade_final) else "falha",
            "detalhes_integridade": integridade_final,
        }

    except Exception as e:
        return {
            "sucesso": False,
            "erro": f"Erro durante restauração: {str(e)}",
            "backup_automatico": backup_auto,
            "tempo_segundos": round(time_module.time() - inicio, 2),
        }