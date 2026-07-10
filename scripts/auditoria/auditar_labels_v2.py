#!/usr/bin/env python3
"""
Auditoria v2 - Busca label='' e label="" em todo o código fonte.
Analisa TODOS os arquivos .py do projeto.
"""
import re
import os
import sys

skip_dirs = ['legacy', 'debug', 'docs', 'tests', 'backup', 
             '.git', '__pycache__', '.venv', 'venv', 'node_modules', '.mypy_cache']

results = []

for root, dirs, files in os.walk('.'):
    # Verifica se algum skip_dir está no path
    normalized_root = root.replace('\\', '/')
    parts = normalized_root.split('/')
    if any(skip in parts for skip in skip_dirs):
        continue
    
    for file in files:
        if not file.endswith('.py'):
            continue
        
        filepath = os.path.join(root, file)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Erro lendo {filepath}: {e}", file=sys.stderr)
            continue
        
        # Busca label='' ou label="" (com qualquer espaçamento)
        # Pattern 1: label='' ou label=' '
        pattern1 = re.compile(r"""
            label       # literal 'label'
            \s*=\s*     # spaces around =
            ['\"]      # quote open
            \s*         # possible space inside
            ['\"]      # quote close
        """, re.VERBOSE)
        
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if pattern1.search(line):
                # Extrai contexto (widget streamlit ou não)
                results.append((filepath, i, line.strip()))

print("=" * 100)
print("AUDITORIA DE LABELS VAZIOS (label='' / label=\"\")")
print("=" * 100)
print()

if not results:
    print("NENHUM label vazio encontrado.")
    sys.exit(0)

print(f"Total de ocorrências: {len(results)}")
print()

# Agrupa por arquivo
from collections import defaultdict
by_file = defaultdict(list)
for fp, ln, code in results:
    by_file[fp].append((ln, code))

for fp, occurrences in sorted(by_file.items()):
    print(f"📄 {fp}")
    print(f"   Ocorrências: {len(occurrences)}")
    for ln, code in occurrences:
        print(f"   Linha {ln}: {code[:120]}")
    print()

# Estatísticas
print("=" * 100)
print("LISTAGEM COMPLETA (arquivo:linha: código)")
print("=" * 100)
for fp, ln, code in sorted(results):
    print(f"{fp}:{ln}: {code}")