# ANÁLISE DO DASHBOARD — ULITEC CRM V1.6

**Data:** 24/06/2026
**Etapa:** 4 — Revisão do Dashboard

---

## 1. Blocos do Dashboard

| Bloco | Descrição | Classificação |
|-------|-----------|---------------|
| 1. Cards KPI | 6 indicadores: Total Clientes, Ativos, Receita, Ticket Médio, Classe A, Sem Faturamento | **ESSENCIAL** |
| 2. Faturamento Mensal + Tendência | Gráfico de barras com linha de tendência linear e projeção 3M com sazonalidade | **ESSENCIAL** |
| 3. Análise Sazonalidade YTD | Comparação Jan-Jun 2025 vs 2026, Projeção 2026, Status de Tendência | **ÚTIL** |
| 4. Linha de Ritmo | Faturamento mensal 2025 vs 2026 (linha) | **ÚTIL** |
| 5. Top Clientes | Barra horizontal + treemap dos top 15 | **ESSENCIAL** |
| 6. Distribuição ABC | Barras de receita por classe | **ESSENCIAL** |
| 7. Ranking Potencial Comercial | Score potencial dos top 20 | **ÚTIL** |
| 8. Tabelas (Oportunidades + Ranking) | Listas com formatação por classe | **ÚTIL** |
| 9. Maiores Clientes | Tabela detalhada dos top 15 | **ÚTIL** |

---

## 2. Classificação Final

| Bloco | Classificação |
|-------|---------------|
| Cards KPI | ESSENCIAL |
| Faturamento Mensal + Tendência | ESSENCIAL |
| Análise Sazonalidade YTD | ÚTIL |
| Linha de Ritmo | ÚTIL |
| Top Clientes | ESSENCIAL |
| Distribuição ABC | ESSENCIAL |
| Ranking Potencial Comercial | ÚTIL |
| Tabelas (Oportunidades + Ranking) | ÚTIL |
| Maiores Clientes | ÚTIL |

**ESSENCIAIS:** 4 blocos
**ÚTEIS:** 5 blocos
**DESCARTÁVEIS:** 0

---

## 3. Avaliação da Base Histórica

### Sazonalidade

- Dados disponíveis: **2025 (completo)** e **2026 (parcial, até junho)**
- Total de meses históricos: ~18 meses
- Base **suficiente** para sazonalidade YTD (comparação Jan-Jun entre anos)
- Base **limitada** para sazonalidade mensal robusta — apenas 1 ciclo anual completo

### Tendências

- Regressão linear utilizada sobre 18 pontos
- Projeção de 3 meses (jul-set 2026)
- A projeção é **razoável**, mas tem baixa confiabilidade estatística com apenas ~18 meses de dados

### Risco de Projeção

- O modelo usa tendência linear + índice sazonal
- Apenas 1 ano completo de dados sazonais → fator sazonal pode não representar o padrão real
- Dados YTD 2026 positivos sugerem crescimento, mas insuficientes para validar ciclo completo

### Recomendação

- A base histórica é **suficiente** para indicadores essenciais (cards KPI, top clientes, distribuição ABC)
- Para sazonalidade e projeção, aguardar mais 6-12 meses de dados para maior confiabilidade
- Manter os blocos de sazonalidade como referência, mas com ressalva de que são preliminares

---

## 4. Problemas Identificados

1. **Duplicidade de leitura do banco:** O Dashboard faz `SELECT * FROM faturamento` 3 vezes (linhas 45, 276, 409), sobrecarregando o banco
2. **Classificação ABC inconsistente:** O Dashboard recalcula a classificação ABC com sliders de percentual, MAS a tabela `clientes` já tem `classe_abc` — há duas fontes de verdade
3. **Score potencial com pesos fixos:** `faturamento_real * 0.50 + parque_maquinas * 500 + maquinas_mitsubishi * 1000` — pesos arbitrários sem validação empírica
4. **Nenhum bloco é DESCARTÁVEL** — todos têm utilidade, mas os blocos de sazonalidade/projeção são os mais frágeis

---

## 5. Resumo

- Dashboard está **estável e funcional**
- Base histórica: **suficiente para indicadores essenciais**, **limitada para sazonalidade**
- Nenhum bloco deve ser removido
- Otimização de queries poderia reduzir 3 leituras de banco para 1
- Consistência da classificação ABC entre Dashboard e tabela precisa ser endereçada no futuro

---

*Nenhuma alteração foi feita. Apenas análise documental.*