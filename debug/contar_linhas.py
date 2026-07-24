import os

arquivos = [
    'pages/50_Gestao_Comissoes.py',
    'components/comissoes/dashboard.py',
    'components/comissoes/parceiros.py',
    'components/comissoes/fechamento.py',
    'components/comissoes/historico.py',
    'components/comissoes/avulsas.py',
    'services/comissoes_db.py',
    'services/comissoes_consultas.py',
    'services/parceiros.py',
    'services/comissoes_calculo.py',
    'services/comissoes_fechamento.py',
    'services/comissoes_dashboard.py',
]

total = 0
for a in arquivos:
    lines = len(open(a, encoding='utf-8').readlines())
    ok = 'OK' if lines <= 300 else 'EXCEDE'
    print(f'  {ok} {a:45s} {lines:3d} linhas')
    total += lines

print(f'\n  TOTAL: {total} linhas')
print(f'  Arquivos: {len(arquivos)}')