# AUDITORIA — CLASSIFICAÇÃO ABCD

**Data:** 24/06/2026
**Etapa:** 6 — Auditoria Classificação ABCD

---

## 1. Regras de Negócio (Documentadas)

| Classe | Critério |
|--------|----------|
| **A** | Top 10% clientes com faturamento > 0 |
| **B** | Próximos 30% (posição 10% a 40%) |
| **C** | Próximos 60% (posição 40% a 100%) |
| **D** | Sem faturamento (faturamento_12m = 0 ou NULL) |

---

## 2. Situação Real no Banco

### Coluna `classe_abc` na tabela `clientes`

| Valor | Quantidade |
|-------|-----------|
| A | 0 |
| B | 0 |
| C | 0 |
| D | 839 |
| NULL | 0 |
| VAZIO | 0 |

**Conclusão:** A coluna `classe_abc` no banco NUNCA foi populada corretamente. Todos os 839 clientes ativos estão marcados como "D". Isso indica que a importação de planilhas nunca preencheu este campo.

### Classificação Calculada (via `classificar_abcd()`)

| Classe | Quantidade | Faturamento Médio 12m |
|--------|-----------|----------------------|
| A | 26 | (top 10%) |
| B | 79 | (próximos 30%) |
| C | 158 | (próximos 60%) |
| D | 576 | R$ 0,00 |
| **Total** | **839** | |

**Conclusão:** A função `classificar_abcd()` no `services/inteligencia_comercial.py` funciona CORRETAMENTE. Ela recalcula a classificação em tempo real baseada no faturamento.

---

## 3. O Problema do "Filtro D Vazio"

### Investigações Realizadas

1. **Diagnóstico executado** (`debug/diagnostico_classificacao.py`):
   - `classificar_abcd(unidade=None)` → A=26, B=79, C=158, D=576 ✅
   - `classificar_abcd(unidade='ULITEC SP')` → A=15, B=46, C=93, D=685 ✅
   - `classificar_abcd(unidade='ULITEC RS')` → A=11, B=36, C=71, D=721 ✅

2. **Verificação da coluna no banco:**
   - Todos os 839 registros estão como "D" na tabela `clientes`

### Causa Raiz

**NÃO** é o filtro D que está vazio — é o **OPOSTO**.

O filtro da **Central de Oportunidades** usa `classificar_abcd()` (recálculo em tempo real) e funciona normalmente.

O problema relatado ("Filtro D aparece vazio") tem **duas causas possíveis**:

**Causa 1 — Mais provável:**
A página **Base de Clientes** (`01_Base_Clientes.py`) e o **Dashboard** (`00_Dashboard.py`) usam a coluna `classe_abc` do banco. Como TODOS os 839 registros estão como "D", filtros A, B e C aparecem VAZIOS nessas páginas. O usuário pode ter confundido qual filtro está vazio.

**Causa 2 — Possível:**
Se o filtro D está vazio em algum contexto, pode ser devido a um conflito de nomes entre:
- `classe_abc` (coluna no banco — sempre "D")
- `classificacao` (campo calculado no score — AAA, AA, A, B, C — NÃO usa D)

### Evidências

| Fonte | A | B | C | D | Método |
|-------|---|---|---|----|--------|
| Banco (coluna `classe_abc`) | 0 | 0 | 0 | 839 | Direto |
| `classificar_abcd()` GRUPO | 26 | 79 | 158 | 576 | Recálculo |
| `calcular_score_comercial()` | AAA/AA/A/B/C | — | — | — | Score |

---

## 4. Distribuição por Unidade

### ULITEC SP
| Classe | Quantidade |
|--------|-----------|
| A | 15 |
| B | 46 |
| C | 93 |
| D | 685 |

### ULITEC RS
| Classe | Quantidade |
|--------|-----------|
| A | 11 |
| B | 36 |
| C | 71 |
| D | 721 |

> **Nota:** O total por unidade + GRUPO = 839 porque o banco não separa filiais por registro de cliente — a segregação é por faturamento.

---

## 5. Verificação de Consistência

### Classe D — Clientes sem faturamento
- **Clientes com faturamento_12m = 0 ou NULL:** 576
- **Clientes classificados como D por `classificar_abcd()`:** 576
- ✅ **CONSISTENTE**

### Clientes com faturamento > 0 (263)
- A + B + C = 26 + 79 + 158 = **263**
- ✅ **CONSISTENTE (total = 100% dos clientes com faturamento)**

### Percentuais
- A = 26/263 = 9.9% ≈ 10% ✅
- B = 79/263 = 30.0% ✅
- C = 158/263 = 60.1% ≈ 60% ✅

---

## 6. Diagnóstico Final

| Item | Status |
|------|--------|
| Regra de negócio A=Top10% | ✅ Correta |
| Regra de negócio B=Próximos30% | ✅ Correta |
| Regra de negócio C=Próximos60% | ✅ Correta |
| Regra de negócio D=SemFaturamento | ✅ Correta |
| Distribuição percentual | ✅ Consistente |
| Função `classificar_abcd()` | ✅ Funcional |
| Coluna `classe_abc` no banco | ❌ NUNCA POPULADA (tudo "D") |

---

## 7. Problema Identificado (Objetivo e Evidente)

**Problema:** A coluna `classe_abc` na tabela `clientes` **nunca foi atualizada** com a classificação correta. Todos os 839 clientes estão como "D".

**Impacto:**
- Páginas que usam a coluna do banco (Base Clientes, Dashboard) mostram classificação incorreta
- A Central de Oportunidades NÃO é afetada porque usa `classificar_abcd()` em tempo real

**Causa:** A importação de planilhas nunca preencheu a coluna `classe_abc` — não há trigger ou rotina de atualização.

**Correção necessária (para V1.7):**
Executar `UPDATE clientes SET classe_abc = (classificação calculada)` via script único.

---

## 8. Recomendação para V1.7

- Unificar a fonte de classificação ABCD (apenas banco ou apenas cálculo em tempo real — não ambos)
- Criar script para popular a coluna `classe_abc` no banco
- Remover a lógica duplicada de classificação no Dashboard (sliders percentuais)
- Padronizar nomenclatura: usar "classificacao" para score e "classe_abc" para ABCD

---

*Nenhuma alteração foi feita. Apenas análise documental.*