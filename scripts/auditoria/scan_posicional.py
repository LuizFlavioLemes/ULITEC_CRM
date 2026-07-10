"""
Auditoria de labels vazios em argumento POSICIONAL de widgets Streamlit.
Detecta: st.checkbox("", ...) ou st.checkbox('', ...)
Onde o PRIMEIRO argumento (posicional) do widget Streamlit eh uma string vazia.
"""
import re, os, glob

SKIP = {'legacy', 'debug', 'docs', 'tests', 'backup', '.git', '__pycache__',
        '.venv', 'venv', 'node_modules', '.mypy_cache', 'scripts'}

# Widgets onde o primeiro argumento posicional eh o LABEL
WIDGETS_POSICIONAL = [
    'checkbox', 'toggle', 'radio', 'selectbox', 'multiselect',
    'slider', 'select_slider', 'text_input', 'text_area',
    'number_input', 'date_input', 'time_input', 'file_uploader',
    'color_picker', 'camera_input', 'button', 'download_button',
    'form_submit_button', 'chat_input', 'metric',
]

# Pattern: st.widget("" ou st.widget('' como primeiro argumento
# Captura st.widget("", ...) ou st.widget('', ...) ou st.widget( "" ...)
PAT_POSICIONAL = re.compile(
    r'st\.(\w+)\s*\(\s*[\'\"][\s]*[\'\"]\s*[,\)]'
)

# Pattern para st.widget(label_ ou st.sidebar.widget(
PAT_TODOS = re.compile(
    r'(st\.(?:sidebar\.)?(\w+))\s*\([^)]*'
)

results = []  # (filepath, line_num, code, widget_name, tipo)

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
                lines = f.readlines()
        except:
            continue

        for i, raw in enumerate(lines, 1):
            stripped = raw.strip()
            if not stripped or stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
                continue

            # 1) Procura por argumento posicional vazio: st.widget("" ...
            m = PAT_POSICIONAL.search(raw)
            if m:
                wname = m.group(1)
                if wname in WIDGETS_POSICIONAL:
                    results.append((fpath, i, stripped, wname, 'posicional'))

            # 2) Procura por keyword label vazio: st.widget(label="" ...)
            m2 = re.search(r'st\.(\w+)\s*\([^)]*label\s*=\s*[\'\"][\s]*[\'\"]', raw)
            if m2:
                wname2 = m2.group(1)
                if wname2 in WIDGETS_POSICIONAL or wname2 in ('button', 'download_button', 'form_submit_button'):
                    if wname2 in WIDGETS_POSICIONAL:
                        # Evita duplicata se ja foi capturado como posicional
                        if (fpath, i, wname2, 'posicional') not in results:
                            results.append((fpath, i, stripped, wname2, 'keyword'))

print("=" * 100)
print("AUDITORIA DE LABELS VAZIOS - ARGUMENTO POSICIONAL E KEYWORD")
print("=" * 100)
print()

if not results:
    print("NENHUM widget Streamlit com label vazio encontrado (posicional ou keyword).")
    import sys
    sys.exit(0)

print(f"Total de warnings encontrados: {len(results)}")
print()

from collections import defaultdict, Counter
by_file = defaultdict(list)
for fp, ln, code, wgt, tp in results:
    by_file[fp].append((ln, code, wgt, tp))

for fp, occs in sorted(by_file.items()):
    print(f"📄 {fp.replace('./', '')} ({len(occs)} ocorrencia(s))")
    for ln, code, wgt, tp in occs:
        print(f"   Linha {ln:4d} | st.{wgt:25s} | tipo={tp:10s} | {code[:100]}")
    print()

print("=" * 100)
print("DISTRIBUICAO POR TIPO DE WIDGET")
print("=" * 100)
wc = Counter(w[3] for w in results)
for wname, count in sorted(wc.items(), key=lambda x: -x[1]):
    print(f"  st.{wname:25s} -> {count} ocorrencia(s)")

print()
print("=" * 100)
print("LISTAGEM COMPLETA (formato: arquivo:linha:widget:tipo:código)")
print("=" * 100)
for fp, ln, code, wgt, tp in sorted(results):
    print(f"{fp}:{ln}:st.{wgt}:{tp}: {code[:150]}")