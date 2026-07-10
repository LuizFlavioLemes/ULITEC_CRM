import re, os, glob

# Arquivos principais do projeto
files = (
    glob.glob('pages/*.py') +
    glob.glob('services/*.py') +
    glob.glob('services/ia/*.py') +
    glob.glob('components/*.py') +
    glob.glob('utils/*.py') +
    ['app.py', 'auth.py', 'config.py', 'database.py', 'permissions.py']
)

total_label_lines = 0
total_widgets_empty = 0
non_empty_ok = 0

# Widgets que aceitam label
WIDGETS = {
    'checkbox', 'toggle', 'radio', 'selectbox', 'multiselect',
    'slider', 'select_slider', 'text_input', 'text_area',
    'number_input', 'date_input', 'time_input', 'file_uploader',
    'color_picker', 'camera_input', 'button', 'download_button',
    'form_submit_button', 'chat_input', 'data_editor', 'dataframe',
    'metric', 'progress'
}

print("=" * 90)
print("SCAN FINAL: VERIFICACAO DE LABELS EM TODOS OS ARQUIVOS")
print("=" * 90)
print()

for fp in sorted(files):
    if not os.path.isfile(fp):
        continue
    try:
        with open(fp, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        continue

    lines = content.split('\n')
    file_label_count = 0
    file_widget_empty = 0

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # Pula comentarios e docstrings
        if stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
            continue

        # Verifica se tem label=
        if 'label=' in line:
            total_label_lines += 1
            file_label_count += 1

            # Verifica se o label esta vazio
            # Pattern: label='' ou label="" ou label= '' ou label= ""
            if re.search(r"label\s*=\s*['\"]\s*['\"]", line):
                # Verifica se eh um widget streamlit
                widget_match = re.search(r'st\.(\w+)', line)
                if widget_match and widget_match.group(1) in WIDGETS:
                    total_widgets_empty += 1
                    file_widget_empty += 1
                    print(f"  ⚠️  {fp}:{i} -> st.{widget_match.group(1)} com label vazio!")
                    print(f"      Código: {stripped[:120]}")
                else:
                    print(f"  ℹ️  {fp}:{i} -> label vazio {stripped[:80]}")
            else:
                non_empty_ok += 1

    if file_label_count > 0:
        print(f"📄 {fp}: {file_label_count} labels encontrados, {file_widget_empty} vazios em widgets")
        print()

print("=" * 90)
print("RESUMO FINAL")
print("=" * 90)
print(f"  Total de linhas com 'label=' (codigo ativo): {total_label_lines}")
print(f"  Labels nao vazios (OK):                     {non_empty_ok}")
print(f"  Labels vazios em widgets Streamlit:          {total_widgets_empty}")
print()

if total_widgets_empty == 0:
    print("  ✅ CONCLUSAO: NENHUM WIDGET STREAMLIT COM LABEL VAZIO ENCONTRADO.")
    print()
    print("  O projeto ULITEC CRM ja esta em conformidade com as boas praticas")
    print("  de acessibilidade do Streamlit. Nenhuma correcao foi necessaria.")
else:
    print(f"  ⚠️  {total_widgets_empty} widgets com label vazio precisam ser corrigidos.")

print()
print("=" * 90)