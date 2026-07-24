"""
MIGRAÇÃO EM MASSA: Substituir sqlite3 direto pela camada de abstração
======================================================================
Escopo: pages/, services/, utils/, auth.py, database.py, app.py

NÃO modifica: debug/, legacy/, scripts/ (exceto este), tests/, backup/

REGRAS:
- Substitui import sqlite3 por from database import get_connection
- Substitui sqlite3.connect(...) por get_connection()
- Substitui sqlite3.Row por referência à camada
- Substitui sqlite3.OperationalError, sqlite3.Error por Exception
- Remove import sqlite3 quando não mais usado
"""

import os
import re

ROOT = r'c:\ULITEC_CRM'
PASTAS_PROD = {'pages', 'services', 'utils', 'components'}
ARQUIVOS_EXTRA = {'auth.py', 'database.py', 'app.py', 'config.py', 'permissions.py', 'passenger_wsgi.py'}
EXCLUIR = {'__pycache__', 'backup', 'debug', 'legacy', 'scripts', 'tests', '.git', 'docs'}

def arquivos_producao():
    for root, dirs, files in os.walk(ROOT):
        # Pular pastas não-prod
        rel = os.path.relpath(root, ROOT).replace('\\', '/')
        primeira_pasta = rel.split('/')[0] if rel != '.' else ''
        if primeira_pasta in EXCLUIR:
            dirs[:] = []  # não entrar
            continue
        if any(p in root.split(os.sep) for p in EXCLUIR):
            dirs[:] = []
            continue
        for f in files:
            if not f.endswith('.py'):
                continue
            filepath = os.path.join(root, f)
            # Só arquivos nas pastas de produção + extra
            if rel == '.' and f in ARQUIVOS_EXTRA:
                yield filepath
            elif rel != '.' and primeira_pasta in PASTAS_PROD:
                yield filepath

def migrar_arquivo(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        conteudo = f.read()
    
    original = conteudo
    
    # 1. Identificar se precisa de import da camada
    precisa_get_conn = bool(re.search(r'sqlite3\.connect\(', conteudo))
    precisa_commit = bool(re.search(r'sqlite3\.', conteudo))
    
    # 2. Substituir import sqlite3 (linha inteira)
    conteudo = re.sub(
        r'^import sqlite3\s*$',
        '',  # remove, vamos adicionar o import correto depois
        conteudo,
        flags=re.MULTILINE
    )
    conteudo = re.sub(
        r'^from sqlite3.*$',
        '',
        conteudo,
        flags=re.MULTILINE
    )
    
    # 3. sqlite3.connect(str(DB_PATH)) ou sqlite3.connect(DB_PATH) → get_connection()
    conteudo = re.sub(
        r'sqlite3\.connect\([^)]*\)',
        'get_connection()',
        conteudo
    )
    
    # 4. sqlite3.Row → dict (a camada retorna tuplas)
    conteudo = re.sub(
        r'sqlite3\.Row',
        'dict',  # compatível pois tuplas já são indexáveis
        conteudo
    )
    
    # 5. sqlite3.OperationalError → Exception
    conteudo = re.sub(
        r'sqlite3\.OperationalError',
        'Exception',
        conteudo
    )
    
    # 6. sqlite3.Error → Exception
    conteudo = re.sub(
        r'sqlite3\.Error',
        'Exception',
        conteudo
    )
    
    # 7. Qualquer outro sqlite3.X que sobrou
    conteudo = re.sub(
        r'\bsqlite3\b',
        '',
        conteudo
    )
    
    # 8. Limpar linhas vazias extras (duas ou mais linhas vazias seguidas)
    conteudo = re.sub(r'\n\s*\n\s*\n', '\n\n', conteudo)
    
    # 9. Adicionar import da camada SE o arquivo usa funções de banco
    if precisa_get_conn:
        # Verifica se já importa de database
        if 'from database import' not in conteudo and 'import database' not in conteudo:
            # Adicionar após último import existente
            imports = re.findall(r'^(import |from .* import )', conteudo, re.MULTILINE)
            if imports:
                # Encontrar a última linha de import
                last_import = 0
                for m in re.finditer(r'^(import |from .* import ).*$', conteudo, re.MULTILINE):
                    last_import = m.end()
                # Inserir depois do último import
                insert_point = conteudo.find('\n', last_import) + 1 if conteudo[last_import:].startswith('\n') else last_import
                conteudo = conteudo[:insert_point] + '\nfrom database import get_connection\n' + conteudo[insert_point:]
    
    if conteudo != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(conteudo)
        return True, None
    return False, None

# Executar
migrados = []
erros = []
for fp in arquivos_producao():
    try:
        mudou, erro = migrar_arquivo(fp)
        if mudou:
            rel = os.path.relpath(fp, ROOT)
            migrados.append(rel)
            print(f'  ✓ {rel}')
    except Exception as e:
        rel = os.path.relpath(fp, ROOT)
        erros.append((rel, str(e)))
        print(f'  ✗ {rel}: {e}')

print(f'\nTotal migrados: {len(migrados)}')
print(f'Erros: {len(erros)}')
if erros:
    for f, e in erros:
        print(f'  {f}: {e}')
print(f'\nArquivos migrados:')
for f in migrados:
    print(f'  {f}')