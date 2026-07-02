# Implementação v1.5.1 — Correção da Inteligência Comercial

**Data:** 23/06/2026  
**Versão:** 1.5.1  
**Status:** ✅ Implementado e validado

---

## Arquivos Alterados

| Arquivo | Tipo | Descrição |
|---------|------|-----------|
| `services/inteligencia_comercial.py` | Refatoração completa | Novo score, classificação ABCD corrigida, motivos e ações sugeridas |
| `pages/10_Central_Oportunidades.py` | Refatoração seletiva | Prioridades baseadas em score, tooltips, classificação via módulo |

---

## Regras Implementadas

### 1. Classificação ABCD Corrigida

**Problema original:** Clientes com faturamento = R$ 0,00 apareciam como classes A, B ou C.

**Solução implementada na função `classificar_abcd()`:**

- **Filtro obrigatório:** `faturamento_12m > 0`
- Somente clientes com faturamento participam da classificação A/B/C
- Todos os demais (faturamento = 0) recebem **Classe D**
- Percentuais fixos:
  - **Classe A:** top 10% dos clientes com faturamento
  - **Classe B:** próximos 30% (total acumulado 10%-30%)
  - **Classe C:** próximos 60% (total acumulado 30%-90%)
  - **Classe D:** faturamento = 0 ou sem relevância comercial

### 2. Score Comercial Real

**Função:** `calcular_score_comercial()` — completamente reescrita.

#### Fórmula Final

| Componente | Peso | Tipo | Detalhamento |
|------------|------|------|-------------|
| Máquinas Mitsubishi | **35 pts** | Muito Alto | Normalizado pelo máximo (`qtd / max_qtd * 35`) |
| Faturamento 12 meses | **25 pts** | Alto | Normalizado pelo máximo |
| Classe ABC | **15 pts** | Alto | A=15, B=10, C=5, D=0 |
| Dias sem contato | **10 pts** | Médio | Quanto mais dias, menor score (linear até 365d) |
| Dias sem visita | **10 pts** | Médio | Quanto mais dias, menor score (linear até 365d) |
| Queda faturamento | **3 pts** | Complementar | Quanto maior a queda, menos pontos |
| Preventivas vencidas | **1 pt** | Complementar | Muitos dias sem manutenção = menos pontos |
| Oportunidades abertas | **1 pt** | Complementar | Normalizado pelo máximo |

**Total máximo: 100 pontos**

#### Motivo da Prioridade

Gerado automaticamente para cada cliente com base em:
- Classe A → "Cliente estratégico"
- Muitas máquinas Mitsubishi → contagem
- Dias sem contato prolongado → alerta
- Dias sem visita prolongada → alerta
- Queda de faturamento significativa
- Preventivas vencidas
- Oportunidades em aberto

#### Próxima Ação Sugerida

Lógica determinística:
1. Se sem contato ≥ 60d ou sem visita ≥ 90d → "Agendar visita ou contato"
2. Se classe A e sem contato ≥ 30d → "Manter relacionamento estratégico"
3. Se oportunidades abertas → "Acompanhar oportunidades"
4. Se muitas máquinas → "Propor preventivas"
5. Padrão → "Analisar carteira e planejar ação"

### 3. Prioridades Comerciais Refatoradas

**Antes:** Fila baseada em pendências + esfriando (clientes irrelevantes no topo).

**Agora:** Fila baseada em **Score Comercial** (Top 20):
- Cliente
- Classe (ABCD com badge colorido)
- Faturamento 12 meses (R$)
- Máquinas Mitsubishi (quantidade)
- Dias sem contato
- Dias sem visita
- Score numérico
- Motivo da prioridade
- Ação sugerida

Design visual com cards HTML, borda colorida por classe, ícone por faixa de score.

### 4. Tooltips nos Indicadores

| Indicador | Tooltip |
|-----------|---------|
| 🔧 Preventivas Vencidas | Clientes com mais de 730 dias sem manutenção registrada (OS Faturada/Expedida) |
| 🎯 Prospecção Mitsubishi | Empresas com máquinas Mitsubishi mapeadas mas que nunca compraram da ULITEC |
| 🔴 Esfriando | Clientes com queda de faturamento superior a 30% (90d vs 90d anteriores) ou sem visita há mais de 120 dias |
| 🟢 Esquentando | Clientes com crescimento de faturamento superior a 20% nos últimos 90 dias vs período anterior |
| 📅 Sem Visita | Clientes sem visita registrada há mais de 90 dias ou nunca visitados |
| 🏭 Score Comercial | Pontuação baseada em: máquinas Mitsubishi (35pts), faturamento 12m (25pts), classificação ABC (15pts), dias sem contato (10pts), dias sem visita (10pts), queda faturamento (3pts), preventivas (1pt), oportunidades (1pt) |

---

## Validação

Ambos os arquivos foram validados com `ast.parse()` (Python AST parser):

```
OK: services/inteligencia_comercial.py
OK: pages/10_Central_Oportunidades.py
```

---

## Módulos NÃO Alterados

Conforme especificado, os seguintes módulos permanecem intactos:
- Relacionamento Comercial (`services/relacionamento.py`, `pages/06_Relacionamento_Comercial.py`)
- Cliente 360 (`pages/02_Cliente_360.py`)
- Pendências
- Timeline
- Evolução de Pendências

---

## Pendências Futuras

- [ ] Dashboard (`pages/00_Dashboard.py`) ainda possui lógica própria de classificação ABCD — deve ser unificada com `classificar_abcd()` do módulo
- [ ] `pages/90_Administracao.py` faz referência a classes A/B/C/D — verificar se precisa de adaptação
- [ ] Testar integração com dados reais em produção
- [ ] Validar se o score precisa de ajustes nos pesos conforme feedback dos vendedores