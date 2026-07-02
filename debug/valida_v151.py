import ast
import sys

arquivos = [
    "services/inteligencia_comercial.py",
    "pages/10_Central_Oportunidades.py"
]

ok = True
for arq in arquivos:
    try:
        with open(arq, encoding="utf-8") as f:
            ast.parse(f.read(), filename=arq)
        print(f"OK: {arq}")
    except SyntaxError as e:
        print(f"ERRO: {arq} - {e}")
        ok = False

if ok:
    print("\nTodos os arquivos validados com sucesso.")
    sys.exit(0)
else:
    print("\nErros encontrados!")
    sys.exit(1)