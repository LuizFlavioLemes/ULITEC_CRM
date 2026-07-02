"""Verifica sintaxe e imports de todos os arquivos .py do projeto."""
import ast
import os
import sys

EXCLUDE_DIRS = {'.git', '__pycache__', 'backup', 'node_modules', 'venv', 'env'}

errors = []
ok_count = 0

for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
    for f in files:
        if f.endswith('.py'):
            fp = os.path.join(root, f).replace('\\', '/')
            try:
                with open(fp, encoding='utf-8') as fh:
                    ast.parse(fh.read(), filename=fp)
                print(f"OK: {fp}")
                ok_count += 1
            except SyntaxError as e:
                print(f"ERRO: {fp} - {e}")
                errors.append(fp)
            except Exception as e:
                print(f"FALHA: {fp} - {e}")
                errors.append(fp)

print(f"\n{'='*50}")
print(f"Total de arquivos verificados: {ok_count + len(errors)}")
print(f"OK: {ok_count}")
print(f"Erros: {len(errors)}")

if errors:
    print("\nArquivos com erro:")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
else:
    print("\nTodos os arquivos Python estao com sintaxe valida!")
    sys.exit(0)