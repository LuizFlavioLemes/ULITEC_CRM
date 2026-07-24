import re, os

fixes = [
    (r'return get_connection\(\)\)', 'return get_connection()'),
    (r'conn = get_connection\(\)\)', 'conn = get_connection()'),
    (r'conn_temp = get_connection\(\)\)', 'conn_temp = get_connection()'),
    (r'conn_usr = get_connection\(\)\)', 'conn_usr = get_connection()'),
    (r'conn_orig = get_connection\(\)\)', 'conn_orig = get_connection()'),
    (r'except \.IntegrityError', 'except sqlite3.IntegrityError'),
    (r'except \.DatabaseError', 'except sqlite3.DatabaseError'),
]

import_fixes = [
    ("from services.relacionamento import (\n\nfrom database import get_connection", "from database import get_connection\nfrom services.relacionamento import ("),
    ("from config import (\n\nfrom database import get_connection", "from database import get_connection\nfrom config import ("),
]

total = 0
for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in ('__pycache__', '.git', 'venv', 'backup', 'legacy')]
    for f in files:
        if not f.endswith('.py'):
            continue
        path = os.path.join(root, f)
        with open(path, 'r', encoding='utf-8') as fh:
            content = fh.read()
        original = content
        
        for pattern, replacement in fixes:
            content = re.sub(pattern, replacement, content)
        
        for pattern, replacement in import_fixes:
            if pattern in content:
                content = content.replace(pattern, replacement)
        
        if content != original:
            with open(path, 'w', encoding='utf-8') as fh:
                fh.write(content)
            total += 1
            print(f'[OK] {path}')

print(f'TOTAL: {total} arquivo(s) corrigido(s)')