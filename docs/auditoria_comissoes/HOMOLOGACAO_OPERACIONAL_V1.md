# HOMOLOGACAO OPERACIONAL V1 — Gestao de Comissoes

## Checklist por Aba

---

## ABA 1 — DASHBOARD

### Pontos fortes
- KPIs claros e objetivos (8 indicadores em duas linhas)
- Projecao dinamica do mes calculada em tempo real
- Ranking de top parceiros e top clientes
- Sem necessidade de acao do usuario para carregar dados

### Pontos confusos
- O selectbox "Periodo de analise" nao filtra os indicadores — esta apenas decorativo. Isso pode gerar frustracao no usuario que selecionar "Ultimos 3 meses" e ver os mesmos numeros.
- A linha "Maior: {parceiro}" como rotulo de KPI quebra o padrao dos outros cards. O nome do parceiro dentro do rotulo parece estranho visualmente.
- "Comissao Pendente" e "Comissao Fechada" podem ser confundidas. Pendente = FECHADO (mas nao pago). Fechada = FECHADO + PAGO. Sem legenda, o usuario pode nao entender.

### Sugestoes de simplificacao
- [ ] **VINCULAR** o filtro "Periodo de analise" aos KPIs. Se usuario selecionar "Ultimos 3 meses", os indicadores devem refletir apenas esse periodo. (Usar `indicadores_por_periodo()`)
- [ ] Substituir rotulo "Maior: {nome}" por um card separado ou tooltip.

### Melhorias recomendadas para V1.1
- Grafico de barras com evolucao mensal da comissao
- Indicador de "Comissoes a vencer" (avulsas com data prevista nos proximos 7 dias)
- Tooltip explicativo em cada KPI

---

## ABA 2 — PARCEIROS

### Pontos fortes
- Formulario unico integrando parceiro + contrato + carteira
- Projecao individual por parceiro na listagem (receita mes, base, comissao projetada)
- Busca por nome
- Acoes de ativar/desativar/excluir disponiveis

### Pontos confusos
- O "Faturamento Considerado" na tabela mostra "GRUPO/ULITEC SP/ULITEC RS" mas o label original aprovado era "Faturamento considerado". Na listagem aparece exatamente como esta no banco — confuso para o usuario que nao sabe o que significa.
- Ao clicar "+ Novo Parceiro", o formulario abre SEM indicacao visual de que e para preencher. Uma mensagem "Preencha os dados do parceiro" seria bem-vinda.
- O campo "Observacoes" e "PIX" aparecem como campos obrigatorios visualmente mas sao opcionais.

### Sugestoes de simplificacao
- [ ] Adicionar texto informativo no topo do formulario: "Preencha os dados do parceiro, contrato e selecione os clientes da carteira"
- [ ] Indicar visualmente quais campos sao obrigatorios (ja tem o asterisco no nome, manter padrao)

### Melhorias recomendadas para V1.1
- Opcao de importar clientes por segmento/classe ABC para montar carteira rapida
- Historico de alteracoes do parceiro

---

## ABA 3 — FECHAMENTO

### Pontos fortes
- Fluxo linear: Conferir → Confirmar → Pagar
- Mensagens de estado claras (ja fechado, ja pago, disponivel para fechar)
- Nao permite fechar competencia ja fechada
- Botao "Confirmar Fechamento" grande e visivel

### Pontos confusos
- Ao selecionar mes/ano e ver a projecao, o usuario precisa rolar ate o final para encontrar o botao "Confirmar Fechamento". Se houver muitos parceiros, pode nao ver o botao sem rolar.
- Nao ha indicacao de quantos parceiros serao processados ANTES de clicar no botao. O usuario ve a tabela mas nao sabe se e todos ou apenas alguns.

### Sugestoes de simplificacao
- [ ] Exibir contador: "X parceiro(s) serao processados" acima do botao
- [ ] Adicionar um resumo fixo no topo: "Competencia X | Y parceiros | R$ Z total comissao"
- [ ] Manter o botao "Confirmar Fechamento" visivel sem necessidade de rolagem (usar st.columns no inicio)

### Melhorias recomendadas para V1.1
- Confirmacao com senha para fechar competencia (operacao critica)
- Notificacao por email para o parceiro quando o fechamento for confirmado

---

## ABA 4 — HISTORICO

### Pontos fortes
- Filtros por ano e parceiro
- Tabela completa com todas as informacoes do snapshot
- Totais no final (fechado, pago, pendente)
- Dados imutaveis (snapshot)

### Pontos confusos
- O filtro de parceiro carrega todos os parceiros, inclusive inativos. Se o parceiro foi desativado, ainda aparece no filtro.
- Nao ha opcao de exportacao (CSV/Excel) — mencionada na especificacao original mas nao implementada.

### Sugestoes de simplificacao
- [ ] Ordenar parceiros alfabeticamente no filtro (ja deve estar, mas confirmar)
- [ ] Filtrar apenas parceiros ativos + parceiros com fechamento no periodo

### Melhorias recomendadas para V1.1
- Exportacao para CSV
- Visualizacao do JSON de clientes (expandir detalhes por parceiro)

---

## ABA 5 — COMISSOES AVULSAS

### Pontos fortes
- Cadastro simples com campos minimos necessarios
- Transicao de status progressiva (AGUARDANDO_FATURAMENTO → AGUARDANDO_COMPENSACAO → PAGO)
- Filtro por parceiro
- Acoes de avancar status e excluir

### Pontos confusos
- O campo "OS" (ordem de servico) nao esta no formulario — foi listado na especificacao como opcional
- A descricao aparece truncada na tabela (50 caracteres + "..."). Se o usuario digitar uma descricao longa, nao vera completa.
- Nao ha alerta visual de "pagamento proximo" — a especificacao pedia que o sistema avisasse quando existirem pagamentos previstos para os proximos dias.

### Sugestoes de simplificacao
- [ ] Adicionar campo "OS" (opcional) no formulario
- [ ] Mostrar descricao completa em um expander ou tooltip
- [ ] Adicionar alerta no Dashboard: "X comissoes avulsas com pagamento previsto para esta semana"

### Melhorias recomendadas para V1.1
- Lembrete automatico na pagina inicial do CRM
- Historico de alteracoes (timeline)

---

## AUDITORIA VISUAL

| Item | Status | Observacao |
|------|--------|------------|
| Paleta de cores consistente com o CRM | ✅ | Mesmo padrao do Dashboard Comercial |
| Fonte e tamanhos padronizados | ✅ | Usa componentes globais |
| Badges de status | ✅ | Reusa `badge_status()` |
| Cards de KPI | ✅ | Reusa `card_indicador()` e `linha_indicadores()` |
| Tabelas padronizadas | ✅ | Reusa `tabela_padrao()` |
| Margens e espacamento | ✅ | `st.divider()` nos lugares corretos |
| Labels vazios | ✅ | Nenhum label vazio encontrado |
| Responsividade | ✅ | Uso de `st.columns()` e `width="stretch"` |

---

## AUDITORIA DE NOMENCLATURA

| Local | Encontrado | Sugerido | Prioridade |
|-------|-----------|----------|------------|
| Pagina | "Gestao de Comissoes" | "Gestao Comercial" | **Media** — conforme especificacao original |
| Aba 1 | "Dashboard" | OK | - |
| Aba 2 | "Parceiros" | OK | - |
| Aba 3 | "Fechamento" | ✅ "Conferir Fechamento" foi usado como titulo interno, OK |
| Aba 4 | "Historico" | OK | - |
| Aba 5 | "Comissoes Avulsas" | OK | - |
| Botao | "Salvar" | OK | - |
| Botao | "Confirmar Fechamento" | ✅ Exato conforme aprovado |
| Botao | "Confirmar Pagamento" | OK | - |

---

## AUDITORIA DE FLUXO OPERACIONAL

### Fluxo: Criar parceiro
**Cliques atuais:** 4
1. Clicar "+ Novo Parceiro"
2. Preencher formulario
3. Clicar "Salvar"
4. Visualizar na listagem

**Avaliacao:** ✅ Otimo. Nao ha como reduzir sem perder dados essenciais.

### Fluxo: Fechar competencia
**Cliques atuais:** 3
1. Selecionar mes/ano
2. Conferir valores
3. Clicar "Confirmar Fechamento"

**Avaliacao:** ✅ Excelente. Direto ao ponto.

### Fluxo: Registrar pagamento
**Cliques atuais:** 3
1. Selecionar competencia ja fechada
2. Selecionar parceiro
3. Clicar "Confirmar Pagamento"

**Avaliacao:** ✅ Simples e rapido.

---

## TESTES BASICOS DE PERFORMANCE

| Operacao | Complexidade | Observacao |
|----------|-------------|------------|
| Abertura do Dashboard | 3 queries | Parceiros, carteiras, fechamentos. Aceitavel. |
| Projecao do mes | 3 queries (fat grupo/sp/rs) + 1 query (clientes) | **Potencial gargalo** se houver muitos parceiros com carteiras grandes. Otimizacao futura: cache de session_state. |
| Listagem de parceiros | 1 query com LEFT JOIN | ✅ Otimo |
| Fechamento de competencia | 3 queries (fat) + 1 INSERT por parceiro | Aceitavel para operacao unica por mes. |
| Cadastro de parceiro | 1 INSERT + N INSERTs (carteira) | ✅ Esperado |
| Listagem de historico | 1 query com JOIN | ✅ Otimo |

---

## RESUMO EXECUTIVO

### Itens criticos para corrigir antes do uso em producao:
1. **Filtro "Periodo de analise" decorativo** — nao filtra os KPIs. Falsa expectativa para o usuario.
2. **Alerta de avulsas proximas** — nao implementado. Especificacao pedia.
3. **Campo "OS" faltando** no formulario de comissoes avulsas.

### Itens importantes para V1.1:
1. Exportacao CSV no Historico
2. Grafico de tendencia no Dashboard
3. Confirmacao com senha para fechamento
4. Tooltips explicativos nos KPIs

---

*Documento gerado em 15/07/2026 — Homologacao Operacional V1*