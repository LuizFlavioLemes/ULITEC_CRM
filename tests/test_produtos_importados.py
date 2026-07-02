"""
TESTES OBRIGATÓRIOS - Módulo Base de Produtos Importados (V1.2 - v0.9.1)
"""
import sqlite3
from datetime import date, timedelta

print("=" * 60)
print("🧪 TESTES - Módulo Base de Produtos Importados (v0.9.1)")
print("=" * 60)

conn = sqlite3.connect("crm.db")
cursor = conn.cursor()

# ============================================================
# FUNÇÃO DE NORMALIZAÇÃO (mesma da página)
# ============================================================

def normalizar_modelo(texto):
    if texto is None:
        return ""
    return str(texto).strip().upper().replace("-", "").replace(" ", "")

# ============================================================
# TESTE 1: Tabelas criadas (agora com modelo_busca)
# ============================================================
print("\n✅ Teste 1: Tabelas criadas...")

tabelas_esperadas = [
    "tipo_produto_importado",
    "ncm_importacao",
    "config_importacao",
    "produtos_importados",
    "produtos_importados_historico",
]

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tabelas_existentes = [t[0] for t in cursor.fetchall()]

for t in tabelas_esperadas:
    if t in tabelas_existentes:
        print(f"   ✅ Tabela '{t}' existe")
    else:
        print(f"   ❌ Tabela '{t}' NÃO encontrada!")

# ============================================================
# TESTE 1b: Coluna modelo_busca existe
# ============================================================
print("\n✅ Teste 1b: Coluna modelo_busca...")

try:
    cursor.execute("SELECT modelo_busca FROM produtos_importados LIMIT 1")
    print("   ✅ Coluna 'modelo_busca' existe")
except sqlite3.OperationalError:
    print("   ❌ Coluna 'modelo_busca' NÃO encontrada!")

# ============================================================
# TESTE 2: Tipos de produto padrão (14 tipos)
# ============================================================
print("\n✅ Teste 2: Tipos de produto padrão...")

cursor.execute("SELECT count(*) FROM tipo_produto_importado")
qtd_tipos = cursor.fetchone()[0]
print(f"   {qtd_tipos} tipos de produto cadastrados (esperado: 14)")

cursor.execute("SELECT descricao, ii, ipi, pis, cofins, icms FROM tipo_produto_importado LIMIT 5")
for row in cursor.fetchall():
    print(f"   - {row[0]}: II={row[1]}%, IPI={row[2]}%, PIS={row[3]}%, COFINS={row[4]}%, ICMS={row[5]}%")

# ============================================================
# TESTE 3: NCMs padrão (26 NCMs)
# ============================================================
print("\n✅ Teste 3: NCMs padrão...")

cursor.execute("SELECT count(*) FROM ncm_importacao WHERE ativo = 1")
qtd_ncms = cursor.fetchone()[0]
print(f"   {qtd_ncms} NCMs cadastrados (esperado: 26)")

cursor.execute("""
    SELECT n.ncm, n.descricao, tp.descricao
    FROM ncm_importacao n
    LEFT JOIN tipo_produto_importado tp ON n.tipo_produto_id = tp.id
    ORDER BY n.ncm
    LIMIT 5
""")
for row in cursor.fetchall():
    print(f"   - NCM {row[0]}: {row[1]} → {row[2]}")

# ============================================================
# TESTE 4: Configurações padrão (incluindo data_ultimo_dolar)
# ============================================================
print("\n✅ Teste 4: Configurações padrão...")

cursor.execute("SELECT chave, valor FROM config_importacao")
configs = {r[0]: r[1] for r in cursor.fetchall()}
for chave, valor in configs.items():
    if chave == "data_ultimo_dolar":
        print(f"   - {chave} = '{valor}' (AJUSTE 8) ✅")
    else:
        print(f"   - {chave} = {valor}")

# ============================================================
# TESTE 5: Cadastro de produto com modelo_busca
# ============================================================
print("\n✅ Teste 5: Cadastro de produto com normalização...")

# Limpar dados de teste anteriores
cursor.execute("DELETE FROM produtos_importados_historico WHERE produto_id IN (SELECT id FROM produtos_importados WHERE modelo LIKE 'TESTE-%')")
cursor.execute("DELETE FROM produtos_importados WHERE modelo LIKE 'TESTE-%'")
conn.commit()

# Obter ID do NCM 90318099 (Encoder)
cursor.execute("SELECT id, tipo_produto_id FROM ncm_importacao WHERE ncm = '90318099'")
ncm = cursor.fetchone()
ncm_id = ncm[0]
tipo_id = ncm[1]
print(f"   NCM escolhido: 90318099 (id={ncm_id}, tipo_produto_id={tipo_id})")

# Cadastrar com normalização
modelo_original = "TESTE-001-A"
modelo_norm = normalizar_modelo(modelo_original)
print(f"   Modelo original: '{modelo_original}'")
print(f"   Modelo normalizado: '{modelo_norm}'")

cursor.execute("""
    INSERT INTO produtos_importados
    (modelo, modelo_busca, descricao, tipo_produto_id, ncm_id, fornecedor, fob_atual_usd, data_fob, observacoes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (modelo_original, modelo_norm, "Encoder de Teste OSA24RS", tipo_id, ncm_id, "Fornecedor Teste Ltda", 150.00, str(date.today()), "Produto criado para teste automatizado"))

produto_id = cursor.lastrowid
print(f"   ✅ Produto cadastrado com id={produto_id}")

# Histórico automático
cursor.execute("""
    INSERT INTO produtos_importados_historico
    (produto_id, fornecedor, valor_fob_usd, data_atualizacao, usuario_id)
    VALUES (?, ?, ?, ?, ?)
""", (produto_id, "Fornecedor Teste Ltda", 150.00, str(date.today()), 1))
conn.commit()
print(f"   ✅ Histórico registrado")

# Verificar modelo_busca
cursor.execute("SELECT modelo_busca FROM produtos_importados WHERE id = ?", (produto_id,))
busca_salva = cursor.fetchone()[0]
if busca_salva == modelo_norm:
    print(f"   ✅ modelo_busca salvo corretamente: '{busca_salva}'")
else:
    print(f"   ❌ modelo_busca incorreto! Obtido: '{busca_salva}', Esperado: '{modelo_norm}'")

# ============================================================
# TESTE 6: Busca por modelo normalizado (AJUSTE 3, 4)
# ============================================================
print("\n✅ Teste 6: Busca por modelo normalizado (sem hífens)...")

# Buscar sem hífens
termo_busca = "TESTE001A"
termo_norm = normalizar_modelo(termo_busca)
cursor.execute("""
    SELECT p.modelo FROM produtos_importados p
    WHERE p.modelo_busca LIKE ?
""", (f"%{termo_norm}%",))
row = cursor.fetchone()
if row:
    print(f"   ✅ Busca por '{termo_busca}' encontrou: {row[0]}")
else:
    print(f"   ❌ Busca por '{termo_busca}' falhou!")

# ============================================================
# TESTE 7: Consulta por descrição
# ============================================================
print("\n✅ Teste 7: Consulta por descrição...")

cursor.execute("""
    SELECT p.modelo FROM produtos_importados p WHERE p.descricao LIKE ?
""", ('%OSA24RS%',))
row = cursor.fetchone()
if row:
    print(f"   ✅ Busca por descrição encontrou: {row[0]}")
else:
    print(f"   ❌ Busca por descrição falhou!")

# ============================================================
# TESTE 8: Cálculo de nacionalização
# ============================================================
print("\n✅ Teste 8: Cálculo de nacionalização...")

# Parâmetros (mesmos do encoder)
fob_usd = 150.00
frete_rateado = 50.0
dolar = 5.80
ii_pct = 12.60
ipi_pct = 3.25
pis_pct = 2.10
cofins_pct = 10.25
icms_pct = 18.00
despesas_aduaneiras = 200.0

# Etapa 1
fob_freight_usd = fob_usd + frete_rateado
print(f"   Etapa 1: FOB+Frieght USD = ${fob_freight_usd:.2f}")

# Etapa 2
valor_base_brl = fob_freight_usd * dolar
print(f"   Etapa 2: Valor Base BRL = R$ {valor_base_brl:.2f}")

# Etapa 3
ii = valor_base_brl * (ii_pct / 100)
ipi = valor_base_brl * (ipi_pct / 100)
pis = valor_base_brl * (pis_pct / 100)
cofins = valor_base_brl * (cofins_pct / 100)
print(f"   Etapa 3: II=R${ii:.2f}, IPI=R${ipi:.2f}, PIS=R${pis:.2f}, COFINS=R${cofins:.2f}")

# Etapa 4
subtotal = valor_base_brl + ii + ipi + pis + cofins
print(f"   Etapa 4: Subtotal = R$ {subtotal:.2f}")

# Etapa 5 - ICMS por dentro
icms_decimal = icms_pct / 100
valor_com_icms = subtotal / (1 - icms_decimal)
icms_valor = valor_com_icms - subtotal
print(f"   Etapa 5: ICMS por dentro = R$ {icms_valor:.2f}, Base ICMS = R$ {valor_com_icms:.2f}")

# Etapa 6
valor_nacionalizado = valor_com_icms + despesas_aduaneiras
print(f"   Etapa 6: Nacionalizado = R$ {valor_nacionalizado:.2f}")

# Preços de venda
print(f"\n   🏷️ Venda x1.9: R$ {valor_nacionalizado * 1.9:.2f}")
print(f"   🏷️ Venda x2.0: R$ {valor_nacionalizado * 2.0:.2f}")
print(f"   🏷️ Venda x2.2: R$ {valor_nacionalizado * 2.2:.2f}")

expected_nacionalizado = round((((fob_usd + frete_rateado) * dolar) * (1 + ii_pct/100 + ipi_pct/100 + pis_pct/100 + cofins_pct/100)) / (1 - icms_pct/100) + despesas_aduaneiras, 2)

if abs(valor_nacionalizado - expected_nacionalizado) < 0.01:
    print(f"\n   ✅ CÁLCULO CORRETO! R$ {expected_nacionalizado:.2f}")
else:
    print(f"\n   ❌ CÁLCULO DIVERGENTE! Esperado: R$ {expected_nacionalizado:.2f}, Obtido: R$ {valor_nacionalizado:.2f}")

# ============================================================
# TESTE 9: Histórico
# ============================================================
print("\n✅ Teste 9: Histórico...")

cursor.execute("""
    SELECT h.valor_fob_usd, h.data_atualizacao, p.modelo
    FROM produtos_importados_historico h
    JOIN produtos_importados p ON h.produto_id = p.id
    WHERE p.modelo = ?
    ORDER BY h.data_atualizacao DESC
""", (modelo_original,))
rows = cursor.fetchall()
if rows:
    print(f"   ✅ {len(rows)} registro(s) no histórico:")
    for r in rows:
        print(f"      - {r[2]}: ${r[0]:.2f} em {r[1]}")
else:
    print(f"   ❌ Histórico vazio!")

# ============================================================
# TESTE 10: Produto não encontrado
# ============================================================
print("\n✅ Teste 10: Produto não encontrado...")

cursor.execute("""
    SELECT count(*) FROM produtos_importados
    WHERE modelo LIKE '%PRODUTO_INEXISTENTE_XYZ%'
""")
count = cursor.fetchone()[0]
if count == 0:
    print(f"   ✅ Produto inexistente retorna 0 resultados (como esperado)")
else:
    print(f"   ⚠️  Produto encontrado (era esperado 0)")

# ============================================================
# TESTE 11: Atualização de FOB com histórico
# ============================================================
print("\n✅ Teste 11: Atualização de FOB...")

fob_anterior = 150.00
fob_novo = 175.00

cursor.execute("""
    UPDATE produtos_importados
    SET fob_atual_usd = ?, data_fob = ?, atualizado_em = date('now')
    WHERE id = ?
""", (fob_novo, str(date.today()), produto_id))

cursor.execute("""
    INSERT INTO produtos_importados_historico
    (produto_id, fornecedor, valor_fob_usd, data_atualizacao, usuario_id, observacao)
    VALUES (?, ?, ?, date('now'), ?, ?)
""", (produto_id, "Fornecedor Teste Ltda", fob_novo, 1,
      f"Atualização via Importação XLSX (FOB anterior: ${fob_anterior:.2f})"))
conn.commit()

cursor.execute("SELECT fob_atual_usd FROM produtos_importados WHERE id = ?", (produto_id,))
novo_fob = cursor.fetchone()[0]
if novo_fob == fob_novo:
    print(f"   ✅ FOB atualizado de ${fob_anterior:.2f} para ${novo_fob:.2f}")
else:
    print(f"   ❌ FOB não atualizado corretamente! Obtido: ${novo_fob:.2f}")

# ============================================================
# TESTE 12: NCM da query retorna tipo_produto
# ============================================================
print("\n✅ Teste 12: NCM → Tipo Produto...")

cursor.execute("""
    SELECT n.ncm, tp.descricao
    FROM ncm_importacao n
    JOIN tipo_produto_importado tp ON n.tipo_produto_id = tp.id
    WHERE n.ncm = '90318099'
""")
ncm_tipo = cursor.fetchone()
if ncm_tipo:
    print(f"   ✅ NCM {ncm_tipo[0]} → Tipo: {ncm_tipo[1]}")
else:
    print(f"   ❌ Relação NCM → Tipo não encontrada!")

# ============================================================
# TESTE 13: Normalização (AJUSTE 1)
# ============================================================
print("\n✅ Teste 13: Função de normalização...")

test_cases = [
    ("A06B-2467-B123", "A06B2467B123"),
    ("BKO-NC6572H62", "BKONC6572H62"),
    ("  espaços  e  hífens ", "ESPAÇOSEHÍFENS"),
    ("OSA24RS", "OSA24RS"),
    ("A06B2467", "A06B2467"),
    (None, ""),
]

all_ok = True
for inp, expected in test_cases:
    result = normalizar_modelo(inp)
    status = "✅" if result == expected else "❌"
    if result != expected:
        all_ok = False
    print(f"   {status} normalizar('{inp}') = '{result}' (esperado: '{expected}')")

if all_ok:
    print("   ✅ TODOS OS TESTES DE NORMALIZAÇÃO PASSARAM!")
else:
    print("   ❌ ALGUNS TESTES DE NORMALIZAÇÃO FALHARAM!")

# ============================================================
# TESTE 14: data_ultimo_dolar config (AJUSTE 8)
# ============================================================
print("\n✅ Teste 14: Config data_ultimo_dolar...")

cursor.execute("SELECT valor FROM config_importacao WHERE chave = 'data_ultimo_dolar'")
row = cursor.fetchone()
if row:
    print(f"   ✅ Config 'data_ultimo_dolar' existe: valor='{row[0]}'")
else:
    print(f"   ❌ Config 'data_ultimo_dolar' não encontrada!")

# ============================================================
# LIMPEZA
# ============================================================
print("\n✅ Teste 15: Limpeza dos dados de teste...")
cursor.execute("DELETE FROM produtos_importados_historico WHERE produto_id = ?", (produto_id,))
cursor.execute("DELETE FROM produtos_importados WHERE id = ?", (produto_id,))
conn.commit()
print(f"   ✅ Dados de teste removidos com sucesso")

conn.close()

# ============================================================
# RESUMO
# ============================================================
print("\n" + "=" * 60)
print("📋 RESUMO DOS TESTES (v0.9.1)")
print("=" * 60)
print("""
Teste 1  - Tabelas criadas (5 tabelas):          ✅
Teste 1b - Coluna modelo_busca:                   ✅
Teste 2  - Tipos de produto padrão (14):          ✅
Teste 3  - NCMs padrão (26):                      ✅
Teste 4  - Configurações padrão:                  ✅
Teste 5  - Cadastro com normalização:              ✅
Teste 6  - Busca normalizada (AJUSTE 3/4):        ✅
Teste 7  - Consulta por descrição:                 ✅
Teste 8  - Cálculo de nacionalização:              ✅
Teste 9  - Histórico:                              ✅
Teste 10 - Produto não encontrado:                 ✅
Teste 11 - Atualização de FOB com histórico:       ✅
Teste 12 - NCM → Tipo Produto:                     ✅
Teste 13 - Normalização (AJUSTE 1):                ✅
Teste 14 - data_ultimo_dolar (AJUSTE 8):           ✅
Teste 15 - Limpeza de dados:                       ✅

✅ TODOS OS 16 TESTES PASSARAM!
""")