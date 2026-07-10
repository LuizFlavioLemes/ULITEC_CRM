#!/usr/bin/env python3
"""
Auditoria de labels vazios em widgets Streamlit.
Identifica todos os st.* widgets com label="" ou label='' ou label=' '.
"""
import re
import os
import sys

warnings_found = []

# Pastas para ignorar
skip_dirs = ['legacy', 'debug', 'docs', 'tests', 'scripts', 'backup', 
             '.git', '__pycache__', '.venv', 'venv', 'node_modules', '.mypy_cache']

for root, dirs, files in os.walk('.'):
    # Normalizar path para verificar skip
    if any(skip in root.replace('\\', '/').split('/') for skip in skip_dirs):
        continue
    for file in files:
        if not file.endswith('.py'):
            continue
        filepath = os.path.join(root, file)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Erro ao ler {filepath}: {e}", file=sys.stderr)
            continue

        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            # Procura por st.widget(label=''), st.widget(label=""), st.widget(label= '') etc.
            # Captura o nome do widget e a label
            match = re.search(
                r'(st\.(\w+))\([^)]*label\s*=\s*[\"\'][\s]*[\"\']',
                line
            )
            if match:
                widget = match.group(2)
                # Ignora st.markdown, st.write, st.title, st.header, st.subheader, 
                # st.caption, st.latex, st.code, st.html, st.image, st.video, st.audio
                # que nao sao widgets interativos
                if widget in ('markdown', 'write', 'title', 'header', 'subheader',
                              'caption', 'latex', 'code', 'html', 'image', 'video',
                              'audio', 'error', 'warning', 'info', 'success',
                              'exception', 'progress', 'spinner', 'balloons',
                              'snow', 'toast', 'sidebar', 'columns', 'column',
                              'container', 'expander', 'empty', 'tabs', 'tab',
                              'form', 'form_submit_button', 'button',
                              'plotly_chart', 'pyplot', 'line_chart',
                              'area_chart', 'bar_chart', 'map', 'altair_chart',
                              'vega_lite_chart', 'graphviz_chart', 'bokeh_chart'):
                    continue
                warnings_found.append((filepath, i, line.strip(), widget))

print("=" * 80)
print("RELATÓRIO DE AUDITORIA - LABELS VAZIOS EM WIDGETS STREAMLIT")
print("=" * 80)
print()
print(f"Total de warnings encontrados: {len(warnings_found)}")
print()

if warnings_found:
    # Agrupar por arquivo
    from collections import defaultdict
    by_file = defaultdict(list)
    for fp, ln, code, wgt in warnings_found:
        by_file[fp].append((ln, code, wgt))
    
    for fp, occurrences in sorted(by_file.items()):
        print(f"Arquivo: {fp}")
        print(f"  Ocorrências: {len(occurrences)}")
        for ln, code, wgt in occurrences:
            print(f"    Linha {ln}: st.{wgt} | Código: {code[:80]}")
        print()
    
    print("=" * 80)
    print("DETALHAMENTO POR WIDGET:")
    print("=" * 80)
    from collections import Counter
    widget_counts = Counter(w[3] for w in warnings_found)
    for widget, count in sorted(widget_counts.items(), key=lambda x: -x[1]):
        print(f"  st.{widget}: {count} ocorrência(s)")
else:
    print("Nenhum warning encontrado.")