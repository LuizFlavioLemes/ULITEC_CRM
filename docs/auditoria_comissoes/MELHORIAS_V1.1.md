# MELHORIAS V1.1 — Gestao de Comissoes

> Ideias futuras que NAO serao implementadas agora.
> Preservando o escopo da V1 e evitando complexidade desnecessaria.

---

## GRAFICOS E VISUALIZACAO

### 🔵 Grafico de evolucao mensal
Exibir grafico de linhas/barras com a comissao dos ultimos 12 meses, com tendencia e projecao.
- Fonte: `fechamento_mensal` (historico) + `projetar_por_periodo()` (projecao)
- Reutilizar padrao de tendencia ja implementado no Dashboard Comercial

### 🔵 Heatmap Parceiro x Mes
Matriz onde cada celula representa a comissao de um parceiro em um mes, colorida por valor.
- Fonte: `SELECT parceiro_id, competencia, SUM(valor_comissao) FROM fechamento_mensal GROUP BY ...`
- Ja preparado no banco, so falta a UI

### 🔵 Sazonalidade
Melhores e piores meses do ano para comissao.
- Reutilizar logica de sazonalidade do Dashboard Comercial

---

## FUNCIONALIDADES

### 🔵 Exportacao CSV no Historico
Botao para baixar a tabela de historico como CSV.
- Usar `st.download_button` com `df.to_csv()`
- Implementacao simples (< 10 linhas)

### 🔵 Alerta de comissoes a vencer
No Dashboard, exibir alerta: "X comissoes avulsas com pagamento previsto para esta semana".
- `query_comissoes_avulsas_abertas()` ja implementada
- So falta incorporar no componente de dashboard

### 🔵 Confirmacao com senha para fechamento
Exigir senha do usuario logado para confirmar o fechamento da competencia.
- Operacao critica que gera snapshot definitivo
- Prevenir fechamento acidental

---

## MELHORIAS NA EXPERIENCIA

### 🔵 Tooltips nos KPIs do Dashboard
Adicionar `help_text` em cada KPI explicando o que significa.
- "Comissao Fechada" = FECHADO + PAGO
- "Comissao Pendente" = FECHADO (nao pago)
- "Comissao Paga" = PAGO

### 🔵 Vinculacao real do filtro "Periodo de analise"
Hoje o filtro esta decorativo. Vincular aos KPIs usando `indicadores_por_periodo()`.

### 🔵 Detalhamento do JSON de clientes no Historico
Expandir linha na tabela de historico para mostrar detalhes de cada cliente processado.
- Ler `clientes_json` e exibir em `st.expander`

---

## INTEGRACOES FUTURAS

### 🔵 Cliente 360
No futuro, o Cliente 360 podera exibir:
> "Este cliente gerou R$ X em comissoes para Y parceiros nos ultimos 12 meses"

Ja preparado: `fechamento_mensal.clientes_json` contem todos os dados por cliente.

### 🔵 Notificacao para o parceiro
Quando o fechamento for confirmado, enviar um resumo por email ou WhatsApp.
- Fora do escopo do CRM — depende de integracao externa

---

## NAO IMPLEMENTAR (DECISAO CONSCIENTE)

| Funcionalidade | Motivo |
|---------------|--------|
| Comissao por produto | Nao faz parte da operacao ULITEC |
| Comissao por margem | Complexidade desnecessaria para V1 |
| Comissao escalonada | Nao existe hoje |
| Multiplos contratos ativos | Um parceiro = um contrato |
| Metas e campanhas | Fora do escopo |
| Simuladores | Nao resolve problema real |
| Comissao por equipamento | Nao se aplica |
| Pagamento parcelado | Nao existe necessidade |

---

## OBSERVACAO

Todas as melhorias listadas aqui sao **desejaveis mas nao urgentes**.
O modulo V1 ja entrega o valor principal:
- Controle de parceiros e carteiras
- Projecao dinamica
- Fechamento mensal com snapshot
- Comissoes avulsas
- Dashboard com indicadores

**Proximo passo:** Utilizar o modulo por pelo menos 1 ciclo de fechamento completo (1 mes) antes de planejar a V1.1.