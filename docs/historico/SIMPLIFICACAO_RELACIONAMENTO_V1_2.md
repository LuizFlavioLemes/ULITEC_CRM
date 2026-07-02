# Simplificação do Módulo Relacionamento Comercial — v1.2

## Objetivo

Eliminar a duplicidade entre "Próxima Ação" e "Pendência Comercial", unificando o fluxo para que toda ação futura seja representada exclusivamente como pendência.

## Mudanças Realizadas

### 1. Remoção do bloco "Próxima Ação" na aba Registrar Interação

**Arquivo:** `pages/06_Relacionamento_Comercial.py`

- Removidos os campos:
  - `tipo_prox_acao` (selectbox com tipos: Ligar, WhatsApp, E-mail, etc.)
  - `data_proxima_acao` (date_input)
  - `obs_prox_acao` (text_input)
- Removida a validação que exigia preencher próxima ação OU marcar como CONCLUIDA
- Removida a regra de negócio que impedia salvar interação sem próximo passo
- O formulário agora contém apenas:
  - Dados da interação
  - Resultado comercial (para visitas presenciais)
  - Criar pendência comercial (opcional)
  - Criar oportunidade (opcional)

### 2. Criação de pendência vinculada à interação

Quando o usuário marca "Criar Pendência Comercial", os campos exibidos são:
- Descrição
- Data Limite (default: +7 dias)
- Prioridade (ALTA, MÉDIA, BAIXA)

Ao salvar, a operação cria:
1. **Interação** — com os dados preenchidos
2. **Pendência** — vinculada à interação via `interacao_id`

Ambos são criados na mesma transação (try/except com rollback implícito).

### 3. Reformulação da Agenda Comercial

**Arquivo:** `services/relacionamento.py` — função `get_agenda()`

A agenda agora exibe exclusivamente:

| Categoria | Origem | Filtro |
|-----------|--------|--------|
| Pendências Abertas | `pendencias_comerciais` | status = ABERTA E data_limite <= período |
| Follow-up de Propostas | `ordens_servico` | proximo_followup <= período |

**Removido** da agenda:
- ~~Interações com data_proxima_acao~~ (substituído por pendências)

### 4. Reformulação dos Alertas

**Arquivo:** `services/relacionamento.py` — função `get_alertas_relacionamento()`

**Removido** o alerta:
- ~~ACAO_VENCIDA~~ (próximas ações vencidas de interações)

**Mantidos:**
- VISITA_PROXIMA_VENCIMENTO — clientes próximos de perder frequência de visita
- PENDENCIA_VENCIDA — pendências comerciais com data limite vencida

### 5. Reformulação dos Indicadores (Cliente 360)

**Arquivo:** `services/relacionamento.py` — função `get_indicadores_relacionamento()`

**Removido** do retorno:
- ~~proxima_acao~~
- ~~data_proxima_acao~~

**Mantidos:**
- ultima_interacao_data, tipo, resultado
- pendencias_abertas
- pendencias_vencidas
- total_interacoes
- oportunidades_relacionamento

### 6. Atualização do Cliente 360

**Arquivo:** `pages/02_Cliente_360.py`

- **Bloco 3 substituído**: de "Próximas Ações" (que consultava `get_proximas_acoes_cliente()` baseado em `data_proxima_acao` das interações) para **"Oportunidades com Follow-up Pendente"** (que consulta `proximo_followup` da tabela `ordens_servico`)
- Pendências abertas do cliente continuam sendo exibidas no Bloco 2 com destaque visual por prioridade

### 7. Compatibilidade com banco de dados

As colunas abaixo foram **mantidas na tabela `interacoes`** para compatibilidade, mas **não são mais utilizadas na interface**:
- `tipo_prox_acao`
- `data_proxima_acao`
- `obs_prox_acao`
- `proxima_acao`

Nenhuma nova tabela foi criada. Nenhuma estrutura de banco foi alterada.

## Arquivos Modificados

| Arquivo | Alterações |
|---------|------------|
| `services/relacionamento.py` | Agenda, alertas, indicadores, funções de consulta |
| `pages/06_Relacionamento_Comercial.py` | Formulário de interação, validação, alertas |
| `pages/02_Cliente_360.py` | Substituição do bloco de próximas ações |

## Funcionalidades Preservadas

- ✅ Registro de interação com dados de contato
- ✅ Campos industriais (visita presencial)
- ✅ Criação de pendência vinculada à interação
- ✅ Criação de oportunidade vinculada à interação
- ✅ Gestão completa de pendências (editar, concluir, reabrir)
- ✅ Nova pendência independente (sem interação)
- ✅ Alertas de visita vencida
- ✅ Alertas de pendência vencida
- ✅ Cliente 360 com resumo executivo
- ✅ Central de Oportunidades (páginas separadas)

## Fluxo Novo (simplificado)

```
Interação com cliente
  → Se houver ação futura: criar pendência
  → Se houver oportunidade: criar oportunidade
  → Pendência alimenta a agenda automaticamente
  → Pendência vencida gera alerta
```

## Testes de Validação

### Cenário 1: Criar interação simples
1. Acessar Relacionamento Comercial > Registrar Interação
2. Preencher cliente, tipo, descrição, status CONCLUIDA
3. ✅ Interação salva sem exigir próxima ação

### Cenário 2: Criar interação com pendência
1. Acessar Relacionamento Comercial > Registrar Interação
2. Preencher cliente, tipo, descrição
3. Marcar "Criar pendência comercial"
4. Preencher descrição, data limite, prioridade
5. Salvar
6. ✅ Interação criada
7. ✅ Pendência criada e visível na aba Pendências > Abertas

### Cenário 3: Verificar agenda
1. Acessar Relacionamento Comercial > Agenda
2. ✅ Pendências abertas aparecem na agenda
3. ✅ Follow-ups de propostas aparecem na agenda
4. ❌ Próximas ações de interações NÃO aparecem mais

### Cenário 4: Verificar Cliente 360
1. Acessar Cliente 360 > selecionar cliente
2. ✅ Pendências abertas visíveis nos indicadores
3. ✅ Pendências em destaque na aba Relacionamento
4. ✅ Follow-ups pendentes de OS visíveis

### Cenário 5: Verificar aba Pendências
1. Acessar Relacionamento Comercial > Pendências
2. ✅ Todas as pendências (inclusive as criadas via interação) aparecem
3. ✅ É possível editar, concluir e reabrir

---

**Versão:** 1.2  
**Data:** 23/06/2026  
**Autor:** Simplificação do módulo Relacionamento Comercial