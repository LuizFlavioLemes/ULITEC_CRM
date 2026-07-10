"""
Auditoria MULTILINHA de labels vazios em widgets Streamlit.
Detecta:
  - st.checkbox("" ...)                     # mesmalinha posicional
  - st.checkbox(                            # multilinha posicional
        ""...
    )
  - st.checkbox(label="" ...)               # mesmalinha keyword
  - st.checkbox(                            # multilinha keyword
        label="" ...
    )
  - st.checkbox(variavel_que_pode_ser_vazia) # runtime
"""
import re, os, sys

SKIP = {'legacy', 'debug', 'docs', 'tests', 'backup', '.git', '__pycache__',
        '.venv', 'venv', 'node_modules', '.mypy_cache', 'scripts'}

WIDGETS = {
    'checkbox', 'toggle', 'radio', 'selectbox', 'multiselect',
    'slider', 'select_slider', 'text_input', 'text_area',
    'number_input', 'date_input', 'time_input', 'file_uploader',
    'color_picker', 'camera_input', 'button', 'download_button',
    'form_submit_button', 'chat_input', 'metric',
}

results = []
pending_widgets = {}  # filepath -> {line_start: {'widget': str, 'lines': list}}

for root, dirs, files in os.walk('.'):
    parts = root.replace('\\', '/').split('/')
    if any(s in parts for s in SKIP):
        continue
    for fname in files:
        if not fname.endswith('.py'):
            continue
        fpath = os.path.join(root, fname)
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
            lines = content.split('\n')
        except:
            continue

        # Approach: find all st.widget( patterns and track their opening paren depth
        for i, raw in enumerate(lines, 1):
            stripped = raw.strip()
            if not stripped or stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
                continue

            # Find st.widget( patterns
            for m in re.finditer(r'st\.(\w+)\s*\(', raw):
                wname = m.group(1)
                if wname not in WIDGETS:
                    continue
                
                start_line = i
                start_col = m.start()
                
                # Walk forward to find the matching close paren
                # Accumulate content across lines
                paren_depth = 1
                j = i - 1  # 0-indexed
                col = m.end()
                call_parts = []
                
                # Check same line first
                rest_of_line = raw[col:]
                call_parts.append(raw)
                
                # Parse paren depth
                depth = 1
                pos = col
                current_line_idx = j
                
                while depth > 0 and current_line_idx < len(lines):
                    line_content = lines[current_line_idx]
                    # Start from pos if same line, else from 0
                    search_start = pos if current_line_idx == j else 0
                    
                    for ci in range(search_start, len(line_content)):
                        ch = line_content[ci]
                        if ch == '(':
                            depth += 1
                        elif ch == ')':
                            depth -= 1
                            if depth == 0:
                                # Got the full call
                                full_call = '\n'.join(lines[j:current_line_idx+1])
                                # Now check if it has empty label
                                has_empty = False
                                tipo = ''
                                
                                # Check posicional: first arg is ""
                                # Extract first argument after opening paren
                                # Look for st.checkbox(\n    "" or st.checkbox(""
                                first_arg_pattern = re.compile(
                                    r'st\.\w+\s*\([\s\n]*([\'\"][\s]*[\'\"])[\s\n,)]'
                                )
                                if first_arg_pattern.search(full_call):
                                    has_empty = True
                                    tipo = 'posicional'
                                
                                # Check keyword label=""
                                if not has_empty:
                                    kw_pattern = re.compile(
                                        r'label\s*=\s*[\'\"][\s]*[\'\"]'
                                    )
                                    if kw_pattern.search(full_call):
                                        has_empty = True
                                        tipo = 'keyword'
                                
                                # Check for variable that might be empty
                                # This catches st.checkbox(nome_da_variavel, ...)
                                if not has_empty:
                                    # Extract first arg - it's between ( and first comma or )
                                    # Get text between opening ( and first comma or closing )
                                    between_parens = full_call[full_call.index('(')+1:]
                                    # Find first comma that's not inside nested parens
                                    first_comma = -1
                                    nd = 0
                                    for ci, c in enumerate(between_parens):
                                        if c == '(':
                                            nd += 1
                                        elif c == ')':
                                            nd -= 1
                                        elif c == ',' and nd == 0:
                                            first_comma = ci
                                            break
                                    
                                    first_arg = between_parens[:first_comma] if first_comma > -1 else between_parens.rstrip(')')
                                    first_arg = first_arg.strip()
                                    
                                    # If it's a variable name (not string literal, not keyword arg)
                                    if first_arg and not first_arg.startswith(("'", '"')):
                                        # Check if it's a keyword arg like key=..., value=...
                                        if '=' in first_arg:
                                            kw_name = first_arg.split('=')[0].strip()
                                            if kw_name == 'label':
                                                # label=VARIAVEL, check if variavel can be empty
                                                val = '='.join(first_arg.split('=')[1:]).strip()
                                                if val in ('None', "''", '""', 'None'):
                                                    has_empty = True
                                                    tipo = f'keyword_var={val}'
                                                else:
                                                    tipo = f'keyword_var=({val}) - VERIFICAR RUNTIME'
                                                    results.append((fpath, start_line, full_call[:100], wname, tipo))
                                        else:
                                            # Positional variable arg
                                            tipo = f'posicional_var=({first_arg}) - VERIFICAR RUNTIME'
                                            results.append((fpath, start_line, full_call[:100], wname, tipo))
                                
                                if has_empty:
                                    # Extrair a linha do label vazio
                                    label_line = ""
                                    for scan_i in range(j, min(j+5, len(lines))):
                                        if any(q in lines[scan_i] for q in ["''", '""', "label"]):
                                            label_line = lines[scan_i].strip()
                                            break
                                    if not label_line:
                                        label_line = lines[j].strip()[:80]
                                    
                                    results.append((fpath, start_line, 
                                        f"st.{wname} | label vazio ({tipo}) | line content: {label_line[:80]}",
                                        wname, tipo))
                                break
                    if depth == 0:
                        break
                    current_line_idx += 1
                    if current_line_idx < len(lines):
                        pos = 0

print("=" * 100)
print("AUDITORIA MULTILINHA DE LABELS VAZIOS EM WIDGETS STREAMLIT")
print("=" * 100)
print()

if not results:
    print("NENHUM widget Streamlit com label vazio encontrado.")
    print()
    sys.exit(0)

print(f"Total de warnings encontrados: {len(results)}")
print()

from collections import defaultdict, Counter
by_file = defaultdict(list)
for fp, ln, code, wgt, tp in results:
    by_file[fp].append((ln, code, wgt, tp))

for fp, occs in sorted(by_file.items()):
    print(f"📄 {fp} ({len(occs)} ocorrencia(s))")
    for ln, code, wgt, tp in occs:
        print(f"   Linha {ln:4d} | st.{wgt:25s} | {tp:20s}")
        print(f"     {code[:120]}")
    print()

print("=" * 100)
print("DISTRIBUICAO POR TIPO")
print("=" * 100)
wc = Counter(w[3] for w in results)
for wname, count in sorted(wc.items(), key=lambda x: -x[1]):
    print(f"  st.{wname:25s} -> {count} ocorrencia(s)")

print()
print("=" * 100)
print("LISTAGEM COMPLETA")
print("=" * 100)
for fp, ln, code, wgt, tp in sorted(results):
    print(f"{fp}:{ln}:st.{wgt}:{tp}: {code[:120]}")