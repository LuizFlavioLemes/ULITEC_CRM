# FONTES DE DADOS DA CENTRAL DE OPORTUNIDADES

**Data:** 24/06/2026
**Etapa:** 5 — Central de Oportunidades

---

## 1. Arquitetura Atual

A Central de Oportunidades (`pages/10_Central_Oportunidades.py` — 1152 linhas) consome dados de duas fontes principais:

```
Central de Oportunidades
├── services/inteligencia_comercial.py (1116 linhas)
│   ├── get_clientes_esfriando()
│   ├── get_clientes_esquentando()
│   ├── get_clientes_sem_visita()
│   ├── get_clientes_sem_faturamento()
│   ├── get_clientes_muitas_os()
│   ├── get_clientes_parque_relevante()
│   ├── calcular_score_comercial()
│   ├── classificar_abcd()
│   └── get_resumo_executivo()
│
└── services/relacionamento.py
    ├── get_alertas_relacionamento()
    ├── get_pendencias()
    ├── carregar_configs_relacionamento()
    ├── get_proximas_acoes_consolidadas()
    └── get_contagem_proximas_acoes()
```

---

## 2. Mapeamento de Fontes

### Pendências
- **Origem:** Tabela `pendencias_comerciais` via `services/relacionamento.py`
- **Critério:** Pendências abertas e vencidas
- **Filtro:** Por unidade (filial)

### Alertas
- **Origem:** Tabela `configuracoes` + regras de `services/relacionamento.py`
- **Critério:** Clientes com frequência de contato abaixo do configurado por classe ABCD
- **Filtro:** Por unidade

### Follow-up / Próximas Ações
- **Origem:** Tabela `interacoes` via `services/relacionamento.py`
- **Critério:** Interações com próxima ação agendada e não concluída
- **Agregação:** Consolidado por cliente

### Pipeline OS
- **Origem:** Tabela `ordens_servico` (importada de planilhas)
- **Critério:** OS em aberto ou em andamento
- **Filtro:** Por cliente/unidade

### Parque Mitsubishi
- **Origem:** Tabela `clientes` (colunas `parque_maquinas`, `maquinas_mitsubishi`) + tabela `mitsubishi_maquinas`
- **Critério:** Clientes com máquinas Mitsubishi cadastradas

### Inteligência Comercial
- **Origem:** Tabela `clientes` + `faturamento` + `interacoes`
- **Funções:**
  - `get_clientes_esfriando()` — faturamento caiu no período atual vs anterior (90 dias)
  - `get_clientes_esquentando()` — faturamento cresceu
  - `get_clientes_sem_visita()` — sem interação de visita nos últimos 90 dias
  - `get_clientes_sem_faturamento()` — sem faturamento nos últimos 12 meses
  - `get_clientes_muitas_os()` — alta quantidade de OS abertas
  - `get_clientes_parque_relevante()` — parque Mitsubishi significativo

### Classificação ABCD
- **Origem:** Tabela `clientes` (coluna `classe_abc`) OU recálculo via `classificar_abcd()`
- **Critério:**
  - A = Top 10% faturamento
  - B = Próximos 30% (10-40%)
  - C = Próximos 60% (40-100%)
  - D = Sem faturamento

---

## 3. Tabelas Utilizadas

| Tabela | Origem | Frequência de Atualização |
|--------|--------|---------------------------|
| `clientes` | ERP (importação planilha) | Manual |
| `faturamento` | ERP (importação planilha) | Manual |
| `ordens_servico` | Planilha OS | Manual |
| `interacoes` | Relacionamento Comercial | Em tempo real |
| `pendencias_comerciais` | Relacionamento Comercial | Em tempo real |
| `configuracoes` | Administração | Manual |
| `mitsubishi_maquinas` | Mitsubishi Service | Manual |

---

## 4. O que ALIMENTA a Central Hoje

1. **Dados ERP (via importação de planilhas):**
   - Clientes (cadastro)
   - Faturamento (histórico)
   - OS (ordens de serviço)

2. **Dados do Relacionamento Comercial:**
   - Interações (visitas, ligações, e-mails, etc.)
   - Pendências comerciais
   - Alertas automáticos

3. **Dados Mitsubishi:**
   - Máquinas por cliente (parque)

4. **Dados calculados:**
   - Score comercial (pesos fixos)
   - Classificação ABCD
   - Status esfriando/esquentando

---

## 5. O que DEVERIA Alimentar no Futuro

| Fonte Potencial | Benefício | Prioridade |
|----------------|-----------|------------|
| **ERP em tempo real (via API)** | Eliminar importação manual de planilhas | ALTA |
| **CRM de vendas externo** | Integrar leads e propostas | MÉDIA |
| **E-mail corporativo** | Rastrear interações automáticas | MÉDIA |
| **WhatsApp Business API** | Registrar mensagens como interações | ALTA |
| **Sistema de OS (API)** | Pipeline em tempo real | ALTA |
| **Satisfação do cliente (NPS)** | Score de relacionamento | BAIXA |
| **Indicadores financeiros** | Risco de crédito, inadimplência | MÉDIA |
| **Histórico de compras por SKU** | Recomendação de produtos | BAIXA |

---

## 6. Observações

- Todas as fontes atuais dependem de **importação manual de planilhas** (legado)
- O Relacionamento Comercial é a única fonte em tempo real
- A Central tem lógica redundante de classificação ABCD (pode conflitar com a coluna no banco)
- O Score comercial é calculado com pesos fixos — não há aprendizado de máquina real, apenas regras determinísticas

---

*Documento gerado automaticamente — auditoria V1.6*