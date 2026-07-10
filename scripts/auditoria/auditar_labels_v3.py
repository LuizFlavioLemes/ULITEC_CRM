#!/usr/bin/env python3
"""
Auditoria v3 - Busca ESPECÍFICA por widgets Streamlit com label vazio.
Ignora comentários e docstrings, foca apenas em código executável.
"""
import re
import os
import sys

skip_dirs = ['legacy', 'debug', 'docs', 'tests', 'backup', 
             '.git', '__pycache__', '.venv', 'venv', 'node_modules', '.mypy_cache',
             'scripts']

# Widgets Streamlit que ACEITAM label
WIDGETS_COM_LABEL = [
    'button', 'download_button', 'checkbox', 'toggle',
    'radio', 'selectbox', 'multiselect', 'slider', 'select_slider',
    'text_input', 'text_area', 'number_input', 'date_input', 'time_input',
    'file_uploader', 'color_picker', 'camera_input',
    'form_submit_button',
    'chat_input',
    'data_editor', 'dataframe',
    'metric',
    'progress',
]

results = []

# Pattern para identificar widget Streamlit com label='' ou label=""
# Captura: st.widget(..., label='', ...) ou st.widget(..., label="", ...)
# Precisamos capturar linhas que contenham st.algumacoisa(... label='' ...)
widget_pattern = re.compile(
    r'st\.(\w+)\s*\([^)]*label\s*=\s*[\'\"][\s]*[\'\"]'
)

docstring_pattern = re.compile(r'^\s*#|^\s*\"\"\"|^\s*\'\'\'|^\s*@')

for root, dirs, files in os.walk('.'):
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
                lines = f.readlines()
        except Exception as e:
            print(f"Erro lendo {filepath}: {e}", file=sys.stderr)
            continue
        
        for i, line in enumerate(lines, 1):
            line_stripped = line.strip()
            
            # Pula comentários e docstrings
            if docstring_pattern.match(line_stripped):
                continue
            if line_stripped.startswith('#'):
                continue
                
            match = widget_pattern.search(line)
            if match:
                widget_name = match.group(1)
                # Só considera widgets da lista
                if widget_name in WIDGETS_COM_LABEL:
                    results.append((filepath, i, line_stripped, widget_name))

print("=" * 100)
print("AUDITORIA DE LABELS VAZIOS EM WIDGETS STREAMLIT")
print("=" * 100)
print()

if not results:
    print("NENHUM widget Streamlit com label vazio encontrado.")
    print()
    print("Isso significa que o projeto já está em conformidade com")
    print("as boas práticas de acessibilidade do Streamlit.")
    sys.exit(0)

print(f"Total de warnings de acessibilidade: {len(results)}")
print()

from collections import defaultdict, Counter
by_file = defaultdict(list)
for fp, ln, code, wgt in results:
    by_file[fp].append((ln, code, wgt))

for fp, occurrences in sorted(by_file.items()):
    print(f"📄 {fp}")
    print(f"   Ocorrências: {len(occurrences)}")
    for ln, code, wgt in occurrences:
        print(f"   Linha {ln}: st.{wgt} | {code[:100]}")
    print()

print("=" * 100)
print("DETALHAMENTO POR TIPO DE WIDGET:")
print("=" * 100)
widget_counts = Counter(w[3] for w in results)
for widget, count in sorted(widget_counts.items(), key=lambda x: -x[1]):
    print(f"  st.{widget}: {count} ocorrência(s)")

print()
print("=" * 100)
print("LISTAGEM COMPLETA (formato: arquivo:linha: código)")
print("=" * 100)
for fp, ln, code, wgt in sorted(results):
    print(f"{fp}:{ln}: {code[:150]}")