# Roadmap do CRM Inteligente — ULITEC CRM 2026/2027

## Visão Estratégica

Transformar o CRM de um sistema **transacional** (registrar o que aconteceu)
para um sistema **inteligente** (antecipar, recomendar e automatizar).

---

## 1. MAPA DE FUNCIONALIDADES ATUAIS

### 1.1 Comercial

| Funcionalidade | Módulo | Status |
|---------------|--------|--------|
| Score Comercial (ABCD + peso) | Central de Oportunidades | ✅ Implementado |
| Classificação ABCD (faturamento) | Central de Oportunidades | ✅ Implementado |
| Clientes Esfriando/Esquentando | Central de Oportunidades | ✅ Implementado |
| Fila Operacional Prioritária | Central de Oportunidades | ✅ Implementado |
| Top Faturamento 12m | Central de Oportunidades | ✅ Implementado |
| Prospecção Mitsubishi | Central de Oportunidades | ✅ Implementado |
| Preventivas Vencidas | Central de Oportunidades | ✅ Implementado |
| Gestão de Comissões | Gestão Comissões | ✅ Implementado |
| Dashboard de Comissões | Gestão Comissões | ✅ Implementado |

### 1.2 Relacionamento

| Funcionalidade | Módulo | Status |
|---------------|--------|--------|
| Registro de Interações | Relacionamento Comercial | ✅ Implementado |
| Pendências Comerciais | Relacionamento Comercial | ✅ Implementado |
| Agenda Comercial | Relacionamento Comercial | ✅ Implementado |
| Alertas de Relacionamento | Relacionamento Comercial | ✅ Implementado |
| Evoluções com Timeline | Relacionamento Comercial | ✅ Implementado |
| Oportunidades via Interação | Relacionamento Comercial | ✅ Implementado |
| Próximas Ações Consolidadas | Relacionamento + Central | ✅ Implementado |

### 1.3 Inteligência

| Funcionalidade | Módulo | Status |
|---------------|--------|--------|
| Score de Priorização Comercial | inteligencia_comercial | ✅ Implementado |
| Detecção de Esfriamento | inteligencia_comercial | ✅ Implementado |
| Anomalia de Faturamento | inteligencia_comercial | ✅ Implementado |
| Prevenção de Perda | inteligencia_comercial | ✅ Implementado |
| Carteira Recomendada | inteligencia_comercial | ✅ Implementado |
| Cálculo de Score Explicável | inteligencia_comercial | ✅ Implementado |

### 1.4 Cliente 360

| Funcionalidade | Módulo | Status |
|---------------|--------|--------|
| Visão Consolidada do Cliente | Cliente 360 | ✅ Implementado |
| Timeline Unificada | Cliente 360 | ✅ Implementado |
| Último Contato | Cliente 360 | ✅ Implementado |
| Pendências Abertas | Cliente 360 | ✅ Implementado |
| Indicadores de Relacionamento | Cliente 360 | ✅ Implementado |

### 1.5 Dashboard

| Funcionalidade | Módulo | Status |
|---------------|--------|--------|
| Indicadores Executivos | Dashboard | ✅ Implementado |
| Métricas de Faturamento | Dashboard | ✅ Implementado |
| Sazonalidade | Dashboard | ✅ Implementado |

### 1.6 Pipeline

| Funcionalidade | Módulo | Status |
|---------------|--------|--------|
| Pipeline por Estágio | Pipeline OS | ✅ Implementado |
| Follow-up Programado | Pipeline OS | ✅ Implementado |
| OS Aguardando Aprovação | Pipeline OS | ✅ Implementado |
| Gestão de Propostas | Pipeline OS | ✅ Implementado |

### 1.7 Administrativo

| Funcionalidade | Módulo | Status |
|---------------|--------|--------|
| Gestão de Usuários | Administração | ✅ Implementado |
| Backup e Restauração | Administração | ✅ Implementado |
| Configurações de Frequência | Administração | ✅ Implementado |
| Versionamento | Administração | ✅ Implementado |

### 1.8 IA

| Funcionalidade | Módulo | Status |
|---------------|--------|--------|
| Relatório Gerencial via IA | Relatório IA | ✅ Implementado |
| Cliente 360 via IA | Relatório IA | ✅ Implementado |
| Integração Groq/Gemini/OpenAI | IA | ✅ Implementado |
| Prompt Builder | IA | ✅ Implementado |

---

## 2. OPORTUNIDADES DE AUTOMAÇÃO E INTELIGÊNCIA

### 2.1 Automação de Classificação e Recomendação

| # | Oportunidade | Problema Atual | Solução Proposta | Impacto | Dificuldade |
|---|-------------|----------------|------------------|---------|-------------|
| 1 | **Classificação automática de interações** | Vendedor precisa selecionar assunto/resultado manualmente | IA classifica automaticamente o resumo da interação em assunto, sentimento e resultado | Médio | Baixa |
| 2 | **Sugestão de próxima ação** | Vendedor decide próxima ação sem critério objetivo | Sistema sugere próxima ação baseada em regras (classe, histórico, pendências abertas) | Alto | Baixa |
| 3 | **Recomendação de cliente a visitar** | Vendedor escolhe cliente baseado em intuição | Score + pendências + últimas interações geram ranking diário de visitas | Alto | Média |

### 2.2 Alertas Inteligentes

| # | Oportunidade | Problema Atual | Solução Proposta | Impacto | Dificuldade |
|---|-------------|----------------|------------------|---------|-------------|
| 4 | **Alerta de mudança de classe** | Cliente A→B é detectado só no fechamento do mês | Monitoramento contínuo dispara alerta quando faturamento cai abaixo do limiar da classe | Alto | Média |
| 5 | **Alerta de oportunidade perdida** | Cliente compra da concorrência sem ação preventiva | Sistema detecta queda de pedidos + aumento de OS de concorrentes (via campos industriais) e alerta | Alto | Alta |
| 6 | **Alerta de inatividade do vendedor** | Vendedor "esquece" cliente sem visita há 90+ dias | Notificação proativa no login com lista de clientes abandonados | Médio | Baixa |

### 2.3 IA Generativa

| # | Oportunidade | Problema Atual | Solução Proposta | Impacto | Dificuldade |
|---|-------------|----------------|------------------|---------|-------------|
| 7 | **Resumo automático do cliente** | Vendedor gasta 5min lendo histórico antes de ligar | IA gera resumo executivo de 3 linhas do cliente ao abrir o perfil | Alto | Média |
| 8 | **Roteiro de visita inteligente** | Vendedor não sabe o que abordar na visita | IA gera roteiro personalizado: pendências, oportunidades, histórico, sugestão de abordagem | Alto | Alta |
| 9 | **E-mail/WhatsApp automático** | Vendedor gasta tempo digitando mensagens | IA gera minuta de e-mail ou WhatsApp baseada no contexto | Médio | Alta |
| 10 | **Análise de sentimento de interações** | Resultado é escolha manual (Positivo/Neutro/Negativo) | IA analisa o texto da interação e sugere classificação de sentimento | Baixo | Média |

### 2.4 Automação Operacional

| # | Oportunidade | Problema Atual | Solução Proposta | Impacto | Dificuldade |
|---|-------------|----------------|------------------|---------|-------------|
| 11 | **Criação automática de pendência** | Vendedor precisa marcar checkbox + preencher | Pendência criada automaticamente baseada em regras (ex: visita sem resultado positivo gera follow-up) | Alto | Média |
| 12 | **Follow-up automático para OS** | Gerente precisa lembrar vendedor de follow-up | Sistema envia notificação automática para o responsável quando follow-up vence | Alto | Baixa |
| 13 | **Sugestão de horário de visita** | Vendedor perde tempo agendando visita | Baseado em histórico, sugere melhor dia/horário para visitar cada cliente | Médio | Alta |
| 14 | **Atualização automática de cadastro** | Cadastro fica desatualizado (telefone, endereço) | Ao registrar interação com contato diferente, pergunta se deseja atualizar | Baixo | Baixa |

### 2.5 Inteligência de Negócio

| # | Oportunidade | Problema Atual | Solução Proposta | Impacto | Dificuldade |
|---|-------------|----------------|------------------|---------|-------------|
| 15 | **Previsão de faturamento** | Diretor não sabe quanto vai faturar no mês | ML prediz faturamento baseado em histórico, pipeline e score | Alto | Alta |
| 16 | **Detecção automática de padrão de compra** | Equipe descobre sazonalidade manualmente | Algoritmo detecta ciclos de compra de cada cliente e recomenda abordagem no momento ideal | Alto | Alta |
| 17 | **Segmentação dinâmica** | Classes ABCD são estáticas (base faturamento) | Clusterização dinâmica considera faturamento, frequência, recência, maquinário | Médio | Alta |
| 18 | **Churn Prediction** | Cliente só é identificado como "perdido" quando deixa de comprar | Modelo ML aponta clientes com >70% de risco de perda nos próximos 60 dias | Alto | Alta |

---

## 3. MATRIZ IMPACTO vs ESFORÇO

```
                    ALTO IMPACTO
                        │
                        │
    2. Sugestão próx.   │  3. Recomendação visita
       ação (B)         │  4. Alerta mudança classe (M)
    6. Inatividade v.   │  7. Resumo automático (M)
       (B)              │ 11. Pendência automática (M)
    12. Follow-up auto  │ 15. Previsão faturamento (A)
       (B)              │ 18. Churn Prediction (A)
    14. Atualização      │
       cadastro (B)      │
                        │
   ─────────────────────┼──────────────────────────
     BAIXO ESFORÇO      │         ALTO ESFORÇO
                        │
    1. Classificação    │  5. Oportunidade perdida (A)
       automática (B)   │  8. Roteiro visita (A)
   10. Sentimento (M)   │  9. E-mail automático (A)
                        │ 13. Sugestão horário (A)
                        │ 16. Padrão compra (A)
                        │ 17. Segmentação dinâmica (A)
                        │
                        │
                    BAIXO IMPACTO
```

**Legenda:** B = Baixa dificuldade | M = Média | A = Alta

---

## 4. ROADMAP POR FASES

### Fase 3.1 — Quick Wins (Mês 1-2)

**Foco:** Máximo impacto com mínimo esforço.

| # | Oportunidade | Prioridade | Esforço | Ganho Esperado |
|---|-------------|------------|---------|----------------|
| 12 | Follow-up automático para OS | 🔴 Alta | Baixo | Redução de 40% de follow-ups perdidos |
| 6 | Alerta de inatividade do vendedor | 🔴 Alta | Baixo | Redução de clientes abandonados |
| 2 | Sugestão de próxima ação | 🔴 Alta | Baixo | Aumento de produtividade comercial |
| 14 | Atualização automática de cadastro | 🟡 Média | Baixo | Base mais limpa sem esforço extra |
| 11 | Criação automática de pendência | 🔴 Alta | Médio | 60% das pendências criadas automaticamente |

**Entregas da Fase 3.1:**
- Notificações push para follow-ups vencidos
- Painel de inatividade por vendedor (login)
- Próxima ação sugerida baseada em regras
- Botão "Atualizar cadastro" ao detectar contato diferente
- Regras de negócio para pendência automática

**Ganhos esperados para equipe comercial:**
- 2h/semana economizadas por vendedor com sugestão de próxima ação
- Redução de 30% de follow-ups perdidos
- Aumento de 15% na taxa de contato com clientes inativos

---

### Fase 3.2 — Inteligência Operacional (Mês 3-4)

**Foco:** Automação de processos operacionais com regras de negócio.

| # | Oportunidade | Prioridade | Esforço | Ganho Esperado |
|---|-------------|------------|---------|----------------|
| 1 | Classificação automática de interações | 🟡 Média | Baixo | 30s economizados por interação |
| 3 | Recomendação de cliente a visitar | 🔴 Alta | Médio | Aumento de visitas produtivas |
| 4 | Alerta de mudança de classe | 🔴 Alta | Médio | Ação preventiva antes da perda |
| 7 | Resumo automático do cliente | 🔴 Alta | Médio | 3min economizados por consulta |

**Entregas da Fase 3.2:**
- Classificador de interações (assunto + sentimento baseado em regras)
- Ranking diário de visitas (Score + Pendências + Última Interação)
- Monitor contínuo de faturamento por classe
- Resumo executivo do cliente na página inicial do Cliente 360

**Ganhos esperados para equipe comercial:**
- 3h/semana economizadas por vendedor (classificação + resumo)
- Aumento de 20% na efetividade de visitas
- Retenção de clientes em mudança de classe (A→B)

---

### Fase 3.3 — IA Generativa (Mês 5-7)

**Foco:** Assistência inteligente com Large Language Models.

| # | Oportunidade | Prioridade | Esforço | Ganho Esperado |
|---|-------------|------------|---------|----------------|
| 8 | Roteiro de visita inteligente | 🔴 Alta | Alto | Visitas mais produtivas e preparadas |
| 9 | E-mail/WhatsApp automático | 🟡 Média | Alto | 5h/semana economizadas em comunicação |
| 10 | Análise de sentimento de interações | 🟡 Média | Médio | Dados mais precisos sem esforço manual |
| 5 | Alerta de oportunidade perdida | 🔴 Alta | Alto | Recuperação de clientes em risco |

**Entregas da Fase 3.3:**
- Bot "Assistente de Visita" que gera roteiro personalizado
- Geração de minuta de e-mail/WhatsApp no registro de interação
- Sentiment analysis automático nas interações
- Alerta de concorrência ativa

**Ganhos esperados para equipe comercial:**
- 5h/semana economizadas por vendedor (comunicação + preparação)
- Aumento de 25% na taxa de conversão de visitas
- Mais dados de concorrência sem esforço extra

---

### Fase 4 — Machine Learning (Mês 8-12)

**Foco:** Modelos preditivos e segmentação avançada.

| # | Oportunidade | Prioridade | Esforço | Ganho Esperado |
|---|-------------|------------|---------|----------------|
| 15 | Previsão de faturamento | 🔴 Alta | Alto | Planejamento financeiro mais preciso |
| 18 | Churn Prediction | 🔴 Alta | Alto | Redução de perda de clientes |
| 16 | Detecção de padrão de compra | 🟡 Média | Alto | Abordagem no momento ideal |
| 17 | Segmentação dinâmica | 🟡 Média | Alto | Segmentação mais precisa que ABCD |

**Entregas da Fase 4:**
- Modelo de previsão de faturamento mensal
- Score de Risco de Perda (Churn) atualizado semanalmente
- Algoritmo de ciclo de compra por cliente
- Segmentação por cluster (ML) disponível no Dashboard

**Ganhos esperados para a empresa:**
- Previsão de faturamento com margem de erro <10%
- Redução de 15% na taxa de churn
- Aumento de 30% no upsell com timing correto

---

## 5. OPORTUNIDADES DE IA DETALHADAS

### 5.1 Classificação Automática (Fase 3.2)

**Problema:** Vendedor gasta 30s por interação selecionando assunto, resultado e tipo.

**Solução:**
- Modelo de classificação (regras + ML leve) baseado no texto da interação
- Assuntos mapeados: Preventiva, Retrofit, Follow-up, Proposta, etc.
- Resultado inferido: Positivo/Neutro/Negativo baseado em palavras-chave

**Tecnologia:** Regras + sklearn (TF-IDF + LogisticRegression) → roda localmente, sem API

**Dados necessários:** ~500 interações já classificadas manualmente (supervisionado)

### 5.2 Resumo Executivo do Cliente (Fase 3.2)

**Problema:** Vendedor precisa ler 3-5 interações para entender situação do cliente.

**Solução:**
- Prompt template + LLM (Groq/Gemini) gera resumo de 3 linhas
- Contexto: últimas 5 interações, pendências abertas, score, classe, último faturamento
- Exibido no topo da página Cliente 360

**Tecnologia:** API Groq (já integrada) + Prompt Engineering

**Dados necessários:** Já disponíveis no Cliente 360

### 5.3 Roteiro de Visita (Fase 3.3)

**Problema:** Vendedor chega na visita sem preparação, perde oportunidades de cross-sell.

**Solução:**
- LLM gera roteiro personalizado com:
  - Pendências abertas do cliente
  - Oportunidades identificadas
  - Máquinas com preventiva vencida
  - Sugestão de abordagem comercial
  - Produtos/serviços para oferecer

**Tecnologia:** API Groq/Gemini + Template de prompt estruturado

**Dados necessários:** Pendências, interações, parque de máquinas, faturamento — já disponíveis

### 5.4 Churn Prediction (Fase 4)

**Problema:** Cliente é identificado como perdido apenas quando para de comprar (muitas vezes já é tarde).

**Solução:**
- Modelo ML (XGBoost/LightGBM) treinado com features:
  - Dias sem visita
  - Variação de faturamento (3m, 6m, 12m)
  - Número de interações no período
  - Pendências abertas
  - Classe ABCD
  - Presença de concorrentes (campo industrial)
  - Resultado médio das interações

**Tecnologia:** XGBoost + MLflow para experiment tracking

**Métrica alvo:** Precision@80% recall (identificar 80% dos churners com precisão >70%)

---

## 6. BACKLOG PRIORIZADO

| Prioridade | Item | Fase | Impacto | Esforço | ROI Estimado |
|-----------|------|------|---------|---------|--------------|
| P0 | Follow-up automático para OS | 3.1 | Alto | Baixo | 🔥 Imediato |
| P0 | Sugestão de próxima ação | 3.1 | Alto | Baixo | 🔥 Imediato |
| P0 | Alerta de inatividade | 3.1 | Médio | Baixo | 🔥 Imediato |
| P0 | Recomendação de visita | 3.2 | Alto | Médio | 1 mês |
| P0 | Alerta de mudança de classe | 3.2 | Alto | Médio | 1 mês |
| P1 | Resumo automático do cliente | 3.2 | Alto | Médio | 2 meses |
| P1 | Pendência automática | 3.1 | Alto | Médio | 2 meses |
| P1 | Classificação automática | 3.2 | Médio | Baixo | 2 meses |
| P2 | Roteiro de visita IA | 3.3 | Alto | Alto | 4 meses |
| P2 | Oportunidade perdida | 3.3 | Alto | Alto | 4 meses |
| P2 | Atualização de cadastro | 3.1 | Baixo | Baixo | 4 meses |
| P3 | Churn Prediction | 4 | Alto | Alto | 6 meses |
| P3 | Previsão de faturamento | 4 | Alto | Alto | 6 meses |
| P3 | E-mail automático | 3.3 | Médio | Alto | 6 meses |
| P4 | Padrão de compra | 4 | Médio | Alto | 9 meses |
| P4 | Segmentação dinâmica | 4 | Médio | Alto | 12 meses |
| P4 | Sentimento de interações | 3.3 | Baixo | Médio | 12 meses |
| P4 | Sugestão de horário | 3.3 | Médio | Alta | 12 meses |

---

## 7. GANHOS ESPERADOS PARA EQUIPE COMERCIAL

### 7.1 Economia de Tempo

| Atividade | Tempo atual (semana) | Tempo com CRM Inteligente | Economia |
|-----------|---------------------|--------------------------|----------|
| Classificar interação | 3h | 0h (automático) | 3h |
| Escolher próxima ação | 2h | 0h (sugerido) | 2h |
| Preparar visita | 4h | 1h (roteiro gerado) | 3h |
| Escrever e-mails | 3h | 1h (minuta gerada) | 2h |
| Consultar histórico | 2h | 0.5h (resumo automático) | 1.5h |
| **Total por vendedor** | **14h** | **2.5h** | **11.5h/semana** |

### 7.2 Ganhos de Receita

| Indicador | Atual | Projetado | Fonte |
|-----------|-------|-----------|-------|
| Visitas produtivas | 40% | 65% | Roteiro de visita |
| Follow-ups realizados | 60% | 90% | Follow-up automático |
| Retenção de clientes A | 90% | 97% | Alerta de mudança de classe |
| Churn anual | 15% | 8% | Churn Prediction |
| Upsell por visita | 1 a cada 10 | 2 a cada 10 | Recomendação de visita |

---

## 8. RECOMENDAÇÕES ESTRATÉGICAS

### 8.1 Começar pelo operacional, depois inteligência

A Fase 3.1 (Quick Wins) não requer ML nem IA. São regras de negócio bem definidas
que geram valor imediato. Isso constrói confiança na equipe para as fases seguintes.

### 8.2 Manter o humano no loop

Todas as funcionalidades de IA propostas são **assistivas**, não substitutivas.
O vendedor sempre aprova/rejeita antes da ação ser executada.

### 8.3 Estratégia de dados para ML

Para viabilizar a Fase 4, iniciar coleta de dados estruturados já na Fase 3.1:
- Log de recomendações aceitas/rejeitadas
- Feedback do vendedor sobre sugestões
- Resultado real de visitas com roteiro vs sem roteiro

### 8.4 Arquitetura de IA

```
[Regras de Negócio]  → Fase 3.1 (rápido, deterministico)
[ML Leve (sklearn)]  → Fase 3.2 (classificação, recomendação)
[LLM (Groq/Gemini)]  → Fase 3.3 (geração de texto, análise)
[ML Avançado (XGB)]  → Fase 4 (predição, churn)
```

Cada camada é incremental e não substitui a anterior.

### 8.5 Métricas de sucesso

| Fase | Métrica | Meta |
|------|---------|------|
| 3.1 | Follow-ups realizados / total | >85% |
| 3.2 | Taxa de aceitação de sugestão de visita | >60% |
| 3.3 | Tempo economizado por vendedor (auto-reportado) | >8h/semana |
| 4 | Precisão do Churn Prediction | >75% |

### 8.6 Riscos e Mitigações

| Risco | Probabilidade | Mitigação |
|-------|--------------|-----------|
| Vendedores ignorarem sugestões automáticas | Média | Design não intrusivo + gamificação (meta de usar sugestões) |
| Modelo de churn com dados insuficientes | Alta | Iniciar coleta agora, modelo só em 6 meses |
| LLM gerar conteúdo inadequado | Baixa | Revisão humana obrigatória antes de envio |
| Resistência a mudança | Média | Treinamento presencial + onboarding gradual (1 feature por semana) |

---

## 9. RESUMO EXECUTIVO

O CRM ULITEC tem hoje uma base sólida de dados e processos digitalizados.
O próximo passo é transformar esses dados em **inteligência acionável**.

**Em 3 meses** (Fase 3.1 + 3.2):
- Vendedor economiza 6h/semana com automações operacionais
- Follow-ups passam de 60% para 90% de realização
- Visitas são priorizadas por score + pendências

**Em 6 meses** (Fase 3.3):
- Vendedor economiza 11h/semana com IA generativa
- Cada visita tem roteiro personalizado
- Clientes em risco são identificados precocemente

**Em 12 meses** (Fase 4):
- CRM prevê faturamento, detecta churn e recomenda ações
- Segmentação dinâmica substitui ABCD estático
- Sistema opera de forma preditiva, não apenas reativa

---

> **Documento gerado em:** 29/07/2026
> **Responsável:** Planejamento Estratégico CRM
> **Próxima revisão:** Após conclusão da Fase 3.1