# DASHBOARD EXECUTIVO — Análise v1.6.9

## Classificação dos blocos atuais

---

### Bloco 1 — KPIs (6 cards)
| Card | Classificação | Justificativa |
|---|---|---|
| 🏢 Clientes (total) | **Manter** | Visão geral essencial |
| 💰 Ativos (com faturamento) | **Manter** | Indicador de base comercial |
| 📈 Receita total | **Manter** | Métrica principal |
| 🎯 Ticket Médio | **Manter** | Indicador de valor médio |
| ⭐ Classe A | **Manter** | Mostra concentração |
| ⚠️ Sem Faturamento | **Revisar** | Categórico demais. Seria melhor mostrar "clientes inativos" com tendência |

---

### Bloco 2 — Top Clientes (gráfico de barras + treemap)
| Classificação | Justificativa |
|---|---|
| **Manter** | Visualização útil. Mas o treemap é redundante com a barra. Sugere-se manter apenas a barra (mais legível). |

---

### Bloco 3 — Distribuição Receita por Classe (barras)
| Classificação | Justificativa |
|---|---|
| **Manter** | Essencial para ver concentração de receita. Mas está posicionado antes da tabela de ranking, o que quebra o fluxo. |

---

### Bloco 4 — Ranking Potencial Comercial (barras)
| Classificação | Justificativa |
|---|---|
| **Revisar** | Usa score próprio (simplificado) diferente do score da Central. Causa inconsistência. Deveria usar o mesmo score de `inteligencia_comercial.py`. |

---

### Bloco 5 — Top Oportunidades Comerciais (tabela)
| Classificação | Justificativa |
|---|---|
| **Remover** | Duplicado com o Ranking Potencial Comercial (bloco 4). Ambos usam o mesmo score. A tabela é redundante. |

---

### Bloco 6 — Ranking ABC (tabela)
| Classificação | Justificativa |
|---|---|
| **Revisar** | Mostra 50 linhas com informação densa demais para um dashboard executivo. Sugere-se limitar a 20 linhas ou transformar em gráfico. |

---

### Bloco 7 — Maiores Clientes (tabela)
| Classificação | Justificativa |
|---|---|
| **Manter** | Útil para visão executiva. Mas colunas como "codigo_erp" e "segmento" são operacionais, não executivas. Sugere-se simplificar. |

---

## Resumo da classificação

| Bloco | Decisão |
|---|---|
| KPIs (6 cards) | Manter |
| Top Clientes (barra + treemap) | Manter (apenas barra) |
| Distribuição ABC | Manter |
| Ranking Potencial | Revisar (usar score unificado) |
| Top Oportunidades (tabela) | Remover (redundante) |
| Ranking ABC (tabela) | Revisar (limitar ou graficar) |
| Maiores Clientes (tabela) | Manter (simplificar) |

---

## Problemas identificados

1. **Score divergente**: Dashboard calcula `score = faturamento * 0.5 + parque * 500 + mitsubishi * 1000 + frequencia * 200`. Central usa `inteligencia_comercial.calcular_score_comercial()` que é mais sofisticado. Os rankings podem divergir.

2. **Classificação ABC duplicada**: Dashboard refaz a classificação com percentis configuráveis. Central usa `classificar_abcd()`. Resultados podem ser diferentes.

3. **Falta indicadores operacionais no Dashboard**: Não tem OS, preventivas, visitas. Seria útil um painel de alertas executivos.

4. **Filtro de unidade limitado**: Só filtra faturamento. Não filtra clientes (mostra todos clientes mesmo quando filtra por unidade).

---

## Sugestão de novo layout para Dashboard Executivo (V1.7)

```
LINHA 1: KPIs (6 cards) — Clientes, Ativos, Receita, Ticket, Classe A, Inativos
LINHA 2: Top 15 Clientes (barra horizontal) + Distribuição ABC (pizza ou barras)
LINHA 3: Ranking Potencial Comercial (score unificado com Central) — top 20
LINHA 4: Alertas Executivos (cards: OS pendentes, preventivas vencidas, visitas atrasadas)
LINHA 5: Maiores Clientes (tabela simplificada — top 15)
```

> ⚠️ **Não implementar agora. Apenas documentar para V1.7.**