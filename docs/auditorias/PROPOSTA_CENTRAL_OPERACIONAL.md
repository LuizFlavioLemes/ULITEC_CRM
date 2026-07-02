# PROPOSTA — CENTRAL DE OPORTUNIDADES OPERACIONAL

**Data:** 24/06/2026
**Etapa:** 5 (parte 2) — Proposta de Evolução

---

## 1. Situação Atual

A Central de Oportunidades (1152 linhas) tenta fazer **tudo ao mesmo tempo**:

- Inteligência comercial (score, classificação, tendências)
- Gestão de pendências (relacionamento)
- Alertas de relacionamento
- Pipeline OS
- Parque Mitsubishi
- Classificação ABCD
- Filtros por estado/cidade/unidade

**Problema identificado:** A página é sobrecarregada. Funcionalidades de relacionamento comercial deveriam estar na página de Relacionamento, e inteligência pura deveria ser serviço de fundo.

---

## 2. Proposta de Redesign

### Separar em 3 camadas:

```
Central de Oportunidades V2
├── [CAMADA 1] Painel Executivo (visão geral)
│   ├── KPIs consolidados
│   ├── Distribuição ABCD
│   └── Score comercial
│
├── [CAMADA 2] Inteligência Ativa (alertas + ações)
│   ├── Clientes esfriando
│   ├── Clientes esquentando
│   ├── Clientes sem visita
│   └── Clientes sem faturamento
│
└── [CAMADA 3] Operacional (aprofundamento)
    ├── Pendências (link para Relacionamento)
    ├── Próximas ações (link para Relacionamento)
    ├── Pipeline OS (link para Pipeline OS)
    └── Parque Mitsubishi (link para Parque Mitsubishi)
```

---

## 3. Benefícios

- **Redução de complexidade:** A página atual tem 1152 linhas. A V2 teria ~400-500 linhas
- **Separação de responsabilidades:** Cada página cuida do seu domínio
- **Performance:** Menos queries simultâneas
- **Usabilidade:** Usuário não precisa filtrar em múltiplos lugares

---

## 4. Riscos da Abordagem Atual

| Risco | Impacto | Probabilidade |
|-------|---------|---------------|
| Timeout em queries pesadas | Alto | Média |
| Conflito de classificação ABCD com banco | Médio | Alta |
| Duplicidade de lógica com outras páginas | Médio | Alta |
| Manutenção difícil (1152 linhas) | Alto | Certa |

---

## 5. Recomendação para V1.7

- Reduzir escopo da Central para **inteligência pura** (esfriando, esquentando, score)
- Mover pendências/alertas/próximas ações para **Relacionamento Comercial**
- Mover Pipeline OS para sua própria página (já existe)
- Unificar fonte de classificação ABCD (apenas banco, sem recálculo local)

---

*Nenhuma alteração foi feita. Apenas análise documental.*