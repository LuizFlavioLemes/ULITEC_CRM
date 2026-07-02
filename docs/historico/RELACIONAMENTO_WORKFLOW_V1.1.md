# PROPOSTA TÉCNICA — Relacionamento Comercial v1.1
## De LOG de Eventos para WORKFLOW de Relacionamento

**Data:** 23/06/2026
**Versão:** 1.1 (Proposta Arquitetural)
**Status:** ⚠️ Documento de análise — NENHUMA alteração deve ser implementada ainda.

---

## 1. Diagnóstico da Arquitetura Atual

### 1.1 Problema Central

`pendencias_comerciais` é uma tabela **subordinada** a `interacoes`:

```sql
-- Estrutura atual
pendencias_comerciais (
    id            INTEGER PRIMARY KEY,
    cliente_id    INTEGER,       -- FK clientes
    interacao_id  INTEGER,       -- FK interacoes  ← dependência funcional
    descricao     TEXT,
    prioridade    TEXT DEFAULT 'MEDIA',
    responsavel   TEXT,
    data_limite   DATE,
    status        TEXT DEFAULT 'ABERTA',  -- só ABERTA / FECHADA
    criado_em     DATE DEFAULT (date('now'))
)
```

**Consequências:**
- Pendência só existe se vinculada a uma interação.
- Ciclo de vida binário (ABERTA / FECHADA) — sem evolução, sem reagendamento, sem reabertura.
- Toda interação vira um registro em `interacoes` mesmo quando o propósito real é gerenciar uma pendência.
- `interacoes` funciona como **log de eventos** misturado com **gestão de tarefas**.
- Não há campo `pendencia_id` em `interacoes`, portanto não é possível saber quais interações pertencem a qual pendência.

### 1.2 Outros Gaps Identificados

| Aspecto | Situação Atual | Impacto |
|---------|---------------|---------|
| Responsável | Apenas texto livre (`responsavel TEXT`) | Sem rastreabilidade de assunção |
| Evolução | Nenhum campo para registro de andamento | Perde-se histórico dentro da pendência |
| Reagendamento | Não existe | Pendência vira "eterna aberta" |
| Reabertura | Não existe | Se concluiu errado, precisa recriar |
| Timeline 360 | Interações e pendências separadas | Visão fragmentada do relacionamento |
| Tela dedicada | Cards simples com botão "Concluir" | Sem detalhes, sem histórico vinculado |

---

## 2. Arquitetura Proposta — WORKFLOW DE RELACIONAMENTO

### 2.1 Princípios

1. **`pendencias_comerciais` vira o objeto principal do fluxo.**  
   Pendência nasce, vive e morre com autonomia. Interações são apenas eventos no histórico.

2. **`interacoes` vira estritamente histórico de eventos.**  
   Cada interação registrada pode (ou não) estar vinculada a uma pendência.  
   Uma interação **nunca mais** cria pendência automaticamente.

3. **Fluxo de estados da pendência:**

```
                    ┌──────────┐
                    │  ABERTA  │
                    └────┬─────┘
                         │
                    ┌────▼─────┐
                    │ ANDAMENTO│  ← assumiu responsável, tem evolução
                    └────┬─────┘
                         │
              ┌──────────┼──────────┐
              │          │          │
         ┌────▼───┐ ┌───▼────┐ ┌───▼────┐
         │REAGENDA│ │CONCLUIDA│ │CANCELADA│
         │  DADA  │ └───┬────┘ └────────┘
         └────────┘     │
                   ┌────▼─────┐
                   │ REABERTA │  → volta para ANDAMENTO ou ABERTA
                   └──────────┘
```

### 2.2 Migração do Modelo de Dados

#### Tabela `pendencias_comerciais` (REFORMULADA)

```sql
CREATE TABLE pendencias_comerciais (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id      INTEGER NOT NULL,
    -- Metadados da pendência
    titulo          TEXT NOT NULL,              -- ← NOVO: título curto
    descricao       TEXT,                       -- descrição detalhada
    prioridade      TEXT DEFAULT 'MEDIA',       -- ALTA / MEDIA / BAIXA
    -- Responsabilidade
    responsavel_atual TEXT,                     -- ← NOVO: atual responsável
    responsavel_abertura TEXT,                  -- ← NOVO: quem abriu
    data_abertura   DATE DEFAULT (date('now')),
    data_limite     DATE,
    -- Ciclo de vida
    status          TEXT DEFAULT 'ABERTA',
    -- ABERTA, ANDAMENTO, CONCLUIDA, CANCELADA, REAGENDADA, REABERTA
    motivo_cancelamento TEXT,                   -- ← NOVO
    concluida_em    DATE,                       -- ← NOVO
    concluida_por   TEXT,                       -- ← NOVO
    -- Auditoria
    criado_em       DATE DEFAULT (date('now')),
    atualizado_em   DATE DEFAULT (date('now')),
    criado_por      TEXT,                       -- ← NOVO
    -- FK
    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
);
```

**Justificativa das mudanças:**
- `interacao_id` removido — pendência não precisa mais nascer de interação.
- `titulo` adicionado — para exibição em cards e listas.
- `responsavel_atual` separado de `responsavel_abertura`.
- `concluida_em` / `concluida_por` para auditoria.
- `motivo_cancelamento` para encerramento com causa.
- `criado_por` para saber quem originou.

#### Tabela `evolucao_pendencias` (NOVA)

```sql
CREATE TABLE evolucao_pendencias (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    pendencia_id    INTEGER NOT NULL,
    tipo            TEXT NOT NULL,
    -- ABERTURA, ASSUNCAO, EVOLUCAO, REAGENDAMENTO,
    -- CANCELAMENTO, CONCLUSAO, REABERTURA, COMENTARIO
    descricao       TEXT NOT NULL,
    responsavel     TEXT NOT NULL,
    data_evolucao   DATE DEFAULT (date('now')),
    -- Dados contextuais
    nova_data_limite DATE,                      -- preenchido em REAGENDAMENTO
    novo_responsavel TEXT,                      -- preenchido em ASSUNCAO
    interacao_id    INTEGER,                    -- opcional: vincula a interação
    FOREIGN KEY (pendencia_id) REFERENCES pendencias_comerciais(id),
    FOREIGN KEY (interacao_id) REFERENCES interacoes(id)
);
```

**Finalidade:** Cada evolução vira um registro imutável. É a **timeline** da pendência.

#### Tabela `interacoes` (ADIÇÃO DE CAMPO)

```sql
-- Adicionar à tabela existente:
-- ALTER TABLE interacoes ADD COLUMN pendencia_id INTEGER;
```

Isso permite que uma interação seja **opcionalmente** vinculada a uma pendência como "evento histórico".  
O campo será opcional (NULL para interações avulsas).

---

## 3. Fluxo de Operações

### 3.1 Abrir Pendência (NOVO — independente de interação)

**Trigger:** Botão "Nova Pendência" na página de Relacionamento ou no Cliente 360.

```python
def abrir_pendencia(
    cliente_id: int,
    titulo: str,
    descricao: str,
    prioridade: str = "MEDIA",
    responsavel: str = "",
    data_limite: Optional[str] = None,
    usuario: str = "",
) -> int:
    # 1. INSERT em pendencias_comerciais (status='ABERTA')
    # 2. INSERT em evolucao_pendencias (tipo='ABERTURA')
    # 3. Retorna pendencia_id
```

**Regras:**
- `responsavel` pode ficar vazio — pendência sem dono.
- Se `responsavel` preenchido, já cria evolução de ASSUNCAO também.

### 3.2 Assumir Responsável

**Trigger:** Botão "Assumir" na tela de detalhes da pendência.

```python
def assumir_pendencia(
    pendencia_id: int,
    novo_responsavel: str,
    usuario: str,
) -> None:
    # 1. UPDATE responsavel_atual em pendencias_comerciais
    # 2. Se status == 'ABERTA', alterar para 'ANDAMENTO'
    # 3. INSERT em evolucao_pendencias (tipo='ASSUNCAO', novo_responsavel=...)
```

### 3.3 Registrar Evolução

**Trigger:** Botão "Registrar Evolução" na tela de detalhes.

```python
def registrar_evolucao(
    pendencia_id: int,
    descricao: str,
    responsavel: str,
    interacao_id: Optional[int] = None,
) -> None:
    # 1. Se status == 'ABERTA' e já tem responsavel, alterar para 'ANDAMENTO'
    # 2. INSERT em evolucao_pendencias (tipo='EVOLUCAO')
```

**Na interface:** campo de texto + opção de vincular a uma interação existente.  
**No Cliente 360:** evolucao_pendencias aparece na timeline como "📌 Pendência X — Evolução: ..."

### 3.4 Reagendar

**Trigger:** Botão "Reagendar" com novo date picker de data limite.

```python
def reagendar_pendencia(
    pendencia_id: int,
    nova_data_limite: str,
    motivo: str,
    responsavel: str,
) -> None:
    # 1. UPDATE data_limite em pendencias_comerciais
    # 2. Status mantém (ou muda para REAGENDADA se estava CONCLUIDA? Não. Só pendências abertas)
    # 3. INSERT em evolucao_pendencias (tipo='REAGENDAMENTO', nova_data_limite=...)
```

**Regra:** Só pode reagendar pendência com status ABERTA ou ANDAMENTO.

### 3.5 Concluir

```python
def concluir_pendencia(
    pendencia_id: int,
    descricao: str,
    responsavel: str,
) -> None:
    # 1. UPDATE status='CONCLUIDA', concluida_em=today, concluida_por=...
    # 2. INSERT em evolucao_pendencias (tipo='CONCLUSAO')
```

### 3.6 Reabrir

```python
def reabrir_pendencia(
    pendencia_id: int,
    motivo: str,
    responsavel: str,
    nova_data_limite: Optional[str] = None,
) -> None:
    # 1. UPDATE status='REABERTA', depois update para 'ANDAMENTO' ou 'ABERTA'
    # 2. Se nova_data_limite, atualizar e registrar REAGENDAMENTO
    # 3. INSERT em evolucao_pendencias (tipo='REABERTURA')
```

---

## 4. Timeline Unificada no Cliente 360

### 4.1 Nova aba "📌 Relacionamento" com Timeline

Em vez de três sub-abas separadas (Últimas Interações, Pendências, Próximas Ações), **uma única timeline consolidada**:

```sql
-- Query unificada para timeline
SELECT
    data_evento,
    tipo_evento,        -- INTERACAO / EVOLUCAO_PENDENCIA / ABERTURA_PENDENCIA
    titulo,
    descricao,
    responsavel,
    entidade_id,        -- interacao_id ou pendencia_id
    entidade_tipo       -- 'interacao' ou 'pendencia'
FROM (
    -- Interações
    SELECT
        i.data_interacao AS data_evento,
        'INTERACAO' AS tipo_evento,
        i.tipo_interacao AS titulo,
        i.resumo AS descricao,
        i.responsavel,
        i.id AS entidade_id,
        'interacao' AS entidade_tipo
    FROM interacoes i
    WHERE i.cliente_id = ?

    UNION ALL

    -- Evoluções de pendências (inclusive abertura e conclusão)
    SELECT
        ep.data_evolucao AS data_evento,
        CASE ep.tipo
            WHEN 'ABERTURA' THEN 'ABERTURA_PENDENCIA'
            WHEN 'CONCLUSAO' THEN 'CONCLUSÃO_PENDENCIA'
            WHEN 'EVOLUCAO' THEN 'EVOLUCAO_PENDENCIA'
            WHEN 'ASSUNCAO' THEN 'ASSUNÇÃO_PENDENCIA'
            WHEN 'REAGENDAMENTO' THEN 'REAGENDAMENTO_PENDENCIA'
            WHEN 'REABERTURA' THEN 'REABERTURA_PENDENCIA'
            WHEN 'CANCELAMENTO' THEN 'CANCELAMENTO_PENDENCIA'
            ELSE ep.tipo
        END AS tipo_evento,
        pc.titulo AS titulo,
        ep.descricao AS descricao,
        ep.responsavel,
        ep.pendencia_id AS entidade_id,
        'pendencia' AS entidade_tipo
    FROM evolucao_pendencias ep
    JOIN pendencias_comerciais pc ON ep.pendencia_id = pc.id
    WHERE pc.cliente_id = ?
)
ORDER BY data_evento DESC, entidade_id DESC
```

**Renderização no frontend:** cada evento vira um card colorido por tipo:
- 🔵 Interação
- 🟡 Abertura de pendência
- 🟢 Conclusão de pendência
- 🟠 Evolução de pendência
- 🔴 Reabertura / Cancelamento

### 4.2 Indicadores Atualizados

`get_indicadores_relacionamento()` deve retornar também:
- Pendências em ANDAMENTO
- Pendências REAGENDADAS
- Pendências REABERTAS no período
- Tempo médio de conclusão

---

## 5. Tela "Detalhes da Pendência" (NOVA Página)

### 5.1 Acesso

A partir de:
- Card de pendência na página de Relacionamento (aba 4)
- Card de pendência na Cliente 360
- Link em notificações/alertas

### 5.2 Layout Proposto

```
┌─────────────────────────────────────────────────────────┐
│ 📌 DETALHES DA PENDÊNCIA                    [Voltar]   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─ CABEÇALHO ───────────────────────────────────────┐  │
│  │  Título: [título da pendência]                     │  │
│  │  Cliente: [nome] → link para 360                  │  │
│  │  Status: 🟡 ANDAMENTO  |  Prioridade: 🔴 ALTA     │  │
│  │  Responsável: João Silva  |  Aberta em: 15/06     │  │
│  │  Data Limite: 30/06/2026  |  [Reagendar]           │  │
│  │  Descrição: [texto completo...]                    │  │
│  └────────────────────────────────────────────────────┘  │
│                                                         │
│  ┌─ AÇÕES ────────────────────────────────────────────┐  │
│  │  [Registrar Evolução] [Concluir] [Reabrir]         │  │
│  │  [Cancelar]  [Assumir Responsável]                  │  │
│  └────────────────────────────────────────────────────┘  │
│                                                         │
│  ┌─ TIMELINE ─────────────────────────────────────────┐  │
│  │  23/06 - João: Reagendado para 30/06 📅            │  │
│  │  20/06 - Maria: Cliente solicitou novo orçamento   │  │
│  │  18/06 - João: Assumiu responsabilidade 👤         │  │
│  │  15/06 - Maria: Pendência criada 📌                │  │
│  └────────────────────────────────────────────────────┘  │
│                                                         │
│  ┌─ INTERAÇÕES VINCULADAS ───────────────────────────┐  │
│  │  📞 22/06 - WhatsApp - Maria: "Enviei orçamento"   │  │
│  │  📞 18/06 - Ligação - João: "Cliente confirmou"    │  │
│  └────────────────────────────────────────────────────┘  │
│                                                         │
│  ┌─ PRÓXIMAS AÇÕES ──────────────────────────────────┐  │
│  │  📅 30/06 - Ligação de cobrança - João            │  │
│  └────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 5.3 Funcionalidades da Tela

| Componente | Funcionalidade |
|------------|---------------|
| Cabeçalho | Exibe todos os metadados da pendência |
| Botão Reagendar | Abre modal com date picker + campo motivo |
| Registrar Evolução | Abre modal com textarea (obrigatório) + checkbox "Vincular interação" |
| Concluir | Confirmação com textarea de resultado |
| Reabrir | Só aparece se status = CONCLUIDA ou CANCELADA |
| Cancelar | Abre modal com campo motivo_cancelamento |
| Assumir Responsável | Só aparece se responsavel_atual estiver vazio ou for outro usuário |
| Timeline | Lista todas as evoluções em ordem cronológica reversa |
| Interações Vinculadas | Interações com `pendencia_id = X` |
| Próximas Ações | Próximas ações das interações vinculadas (data_proxima_acao) |

---

## 6. Impacto nos Alertas

### 6.1 Alertas de Pendência (Atualizar)

O alerta de "PENDENCIA_VENCIDA" em `get_alertas_relacionamento()` deve considerar **apenas** pendências com status ABERTA ou ANDAMENTO (não REAGENDADA, que já tem nova data).

### 6.2 Novo Alerta: Pendência sem Dono

```python
# Pendências que estão ABERTAS há mais de 3 dias sem responsavel_atual
```

### 6.3 Novo Alerta: Pendência sem Evolução

```python
# Pendências em ANDAMENTO sem evolução há mais de 7 dias
```

---

## 7. Plano de Migração (Fases)

### ⚠️ NENHUMA ALTERAÇÃO DEVE SER FEITA ANTES DA APROVAÇÃO DESTE DOCUMENTO

### Fase 1 — Modelo de Dados

1. Criar tabela `evolucao_pendencias`
2. Adicionar colunas à `pendencias_comerciais` (ver seção 2.2)
3. Adicionar `pendencia_id` à `interacoes`
4. Migrar dados existentes:
   - Pendências abertas → manter, com `responsavel_atual = responsavel`, `responsavel_abertura = responsavel`, `status = ABERTA`
   - Pendências fechadas → migrar com `status = CONCLUIDA`
   - Para cada pendência existente, criar registro em `evolucao_pendencias` (tipo='ABERTURA') com data = `criado_em`
5. Remover coluna `interacao_id` de `pendencias_comerciais` (após confirmação)

### Fase 2 — Serviços (services/relacionamento.py)

1. Implementar funções: `abrir_pendencia`, `assumir_pendencia`, `registrar_evolucao_pendencia`, `reagendar_pendencia`, `concluir_pendencia`, `reabrir_pendencia`, `cancelar_pendencia`
2. Refatorar `criar_pendencia` existente para usar as novas funções
3. Atualizar `get_pendencias` para novos status
4. Implementar `get_timeline_cliente(cliente_id)` (query unificada)
5. Implementar `get_detalhes_pendencia(pendencia_id)`
6. Atualizar `get_indicadores_relacionamento`

### Fase 3 — Interface (pages/06_Relacionamento_Comercial.py)

1. Substituir aba "Pendências" por versão com cards clicáveis que levam aos detalhes
2. Adicionar botão "Nova Pendência" na aba de Pendências (cria pendência independente)
3. Remover checkbox "Criar pendência comercial" do formulário de interação
4. Adicionar campo opcional "Vincular a pendência existente" no formulário de interação

### Fase 4 — Nova Tela

1. Criar `pages/07_Detalhes_Pendencia.py`
2. Implementar layout completo da seção 5
3. Testar fluxo completo: abrir → assumir → evoluir → reagendar → concluir → reabrir

### Fase 5 — Cliente 360

1. Substituir sub-abas atuais pela timeline unificada
2. Adicionar indicadores de pendências em ANDAMENTO e REAGENDADAS

---

## 8. Matriz de Riscos

| Risco | Probabilidade | Impacto | Mitigação |
|-------|:------------:|:-------:|-----------|
| Perda do vínculo pendência ↔ interação original | Baixa | Alto | Manter `pendencia_id` em `interacoes` |
| Dados órfãos na migração | Média | Médio | Script de migração com validação (pendências sem interação devem ser mantidas) |
| Quebra de relatórios existentes | Média | Alto | Atualizar `get_pendencias` para manter compatibilidade com campo `status_exibicao` |
| Performance da timeline com muitos registros | Baixa | Médio | Índices em `cliente_id` + `data_evolucao` + paginação (limite 100 eventos) |
| Usuários acostumados com fluxo atual resistirem | Alta | Baixo | Manter interface familiar + treinamento |

---

## 9. Resumo das Mudanças

| Arquivo | Tipo de Mudança | Descrição |
|---------|:--------------:|-----------|
| `database.py` | 📝 | Nova tabela `evolucao_pendencias` + alter table `pendencias_comerciais` + alter table `interacoes` |
| `services/relacionamento.py` | 🔄 | 7 novas funções + refatoração de existentes |
| `pages/06_Relacionamento_Comercial.py` | 🔄 | Aba de Pendências reformulada + formulário sem checkbox |
| `pages/02_Cliente_360.py` | 🔄 | Timeline unificada no lugar de sub-abas |
| `pages/07_Detalhes_Pendencia.py` | 🆕 | Nova página de detalhes |

---

## 10. Próximos Passos

1. ✅ Revisar e aprovar este documento
2. 🔲 Implementar Fase 1 (modelo de dados — `database.py`)
3. 🔲 Executar script de migração de dados
4. 🔲 Implementar Fase 2 (serviços)
5. 🔲 Implementar Fase 3 (interface existente)
6. 🔲 Implementar Fase 4 (nova tela)
7. 🔲 Implementar Fase 5 (Cliente 360)
8. 🔲 Testes integrados de todo o fluxo
9. 🔲 Homologação com usuários
10. 🔲 Deploy em produção

---

*Documento gerado por análise do código-fonte do ULITEC CRM v1.0.4*