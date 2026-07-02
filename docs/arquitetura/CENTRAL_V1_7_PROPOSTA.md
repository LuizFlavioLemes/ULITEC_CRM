# CENTRAL DE OPORTUNIDADES — Proposta para V1.7

## Análise da tela atual (v1.6.9)

---

### 1. O que DEVERIA ENTRAR na Central?

| Item | Justificativa |
|---|---|
| **Score Comercial (Top 20)** | Já está presente. É o núcleo da central. Manter. |
| **O QUE FAZER HOJE** | Priorização operacional. Essencial para o usuário. Manter. |
| **Próximas Ações (agenda)** | Essencial. Já está na aba Relacionamento. |
| **Alertas de Relacionamento** | Visitas vencidas, pendências vencidas. Já está presente. |
| **OS Aguardando Aprovação** | Operacional crítico. Já está presente. |
| **Preventivas Vencidas** | Manutenção preventiva. Já está presente. |
| **Prospecção Mitsubishi** | Potencial de novos negócios. Já está presente. |
| **Clientes Esfriando / Esquentando** | Tendências. Já estão presentes. |
| **Classificação ABCD** | Base para priorização. Já está presente. |

---

### 2. O que DEVERIA SAIR da Central?

| Item | Motivo |
|---|---|
| **Top Faturamento 12m** | É informação de BI/Dashboard, não uma lista acionável imediata. Não gera ação urgente. |
| **Detalhes por Cliente (expansões)** | Cada expander revela informações densas de score que poderiam ser acessadas pelo Cliente 360. |
| **Múltiplas abas operacionais redundantes** | As 4 abas em "Operacional" e "Listas Acionáveis" geram excesso de informação para um usuário comercial comum. |

---

### 3. Quais informações são OPERACIONAIS?

| Informação | Tipo |
|---|---|
| Pendências vencidas | Operacional |
| OS aguardando aprovação | Operacional |
| Visitas atrasadas | Operacional |
| Próximas ações (agenda) | Operacional |
| Preventivas vencidas | Operacional |
| Clientes sem visita | Operacional |
| Clientes sem faturamento | Operacional |
| Alertas de relacionamento | Operacional |

---

### 4. Quais informações são BI?

| Informação | Tipo |
|---|---|
| Top Faturamento 12m | BI |
| Classificação ABCD (percentis) | BI |
| Clientes Esfriando / Esquentando (tendência) | Misto (BI + alerta) |
| Score Comercial calculado | BI |
| Prospecção Mitsubishi (potencial) | BI + Operacional |

---

### 5. O que deveria aparecer na seção "O QUE FAZER HOJE"?

**Sugestão de novo layout:**

1. **🔴 Pendências vencidas** (hoje)
2. **🟡 Pendências vencem hoje**
3. **🔴 OS aguardando > 15 dias**
4. **📅 Visitas atrasadas > 90 dias**
5. **🔴 Clientes esfriando (variação < -50%)**

Esses são os 5 itens que geram ação IMEDIATA.

**Sugestão de remoção do "O QUE FAZER HOJE":**
- Pendências com vencimento > 3 dias (não são urgentes)
- Clientes esfriando com variação entre -30% e -50% (monitorar, não agir)

---

### Resumo da proposta

A Central atual tenta ser **tudo ao mesmo tempo**: operacional, BI, prospecção e relacionamento.

Para V1.7, sugere-se:

```
CENTRAL DE OPORTUNIDADES
├── O QUE FAZER HOJE (apenas urgências reais)
├── Score Comercial (Top 20)
├── Próximas Ações (agenda consolidada)
├── Alertas (relacionamento + preventivas)
└── Prospecção Mitsubishi
```

Mover para Dashboard:
- Top Faturamento 12m
- Classificação ABCD (visão geral)

Manter no Relacionamento:
- Detalhes de expansão de cliente
- Timeline de interações

> ⚠️ **Não implementar agora. Apenas documentar para V1.7.**