import ast, os

erros = []
for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in ('__pycache__', '.git', 'venv', 'backup', 'legacy')]
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            try:
                with open(path, 'r', encoding='utf-8') as fh:
                    ast.parse(fh.read())
            except SyntaxError as e:
                lines = open(path, 'r', encoding='utf-8').read().split('\n')
                line = lines[e.lineno - 1] if 1 <= e.lineno <= len(lines) else 'N/A'
                erros.append((path, e.lineno, str(e), line))

if erros:
    for p, l, msg, line in erros:
        print(f'{p}:{l}: {msg}')
        print(f'  >> {line}')
        print()
    print(f'TOTAL: {len(erros)} ERRO(S) DE SINTAXE')
else:
    print('ZERO ERROS DE SINTAXE')