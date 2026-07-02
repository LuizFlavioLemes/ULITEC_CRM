# RELATÓRIO DE DIAGNÓSTICO OPERACIONAL
## Relacionamento Comercial v1.0.5

**Data:** 23/06/2026
**Objetivo:** Diagnosticar problemas operacionais identificados em uso real — SEM alterar arquitetura, SEM criar tabelas, SEM migrations.

---

## Problema 1 — CONTATOS NÃO SÃO REGISTRADOS

### Diagnóstico

O formulário de "Registrar Interação" (`pages/06_Relacionamento_Comercial.py`, aba2, linhas 164–563) não possui **nenhum campo** para registrar o contato humano com quem a interação ocorreu.

**Campos existentes no formulário:**
| Campo | Tipo |
|-------|------|
| Cliente | selectbox |
| Tipo de Interação | selectbox |
| Assunto | selectbox |
| Data da Interação | date_input |
| Resultado | selectbox |
| Responsável | text_input (disabled) |
| Unidade | selectbox |
| Status da Interação | selectbox |
| Descrição / Resumo | text_area |
| Campos Industriais | (condicional) |
| Próxima Ação | text_input |
| Data Próxima Ação | date_input |

**Campos de contato: inexistentes.**

### Estrutura da tabela `interacoes` (`database.py`, linhas 94–117)

```sql
CREATE TABLE interacoes (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id          INTEGER,
    data_interacao      DATE,
    tipo_interacao      TEXT,
    assunto             TEXT,
    responsavel         TEXT,
    usuario_id          INTEGER,
    unidade             TEXT,
    qtd_maquinas        INTEGER,
    qtd_mitsubishi      INTEGER,
    brinde_entregue     TEXT,
    status_cliente      TEXT,
    nivel_producao      TEXT,
    perspectiva_6m      TEXT,
    concorrentes        TEXT,
    resumo              TEXT,
    resultado           TEXT,
    proxima_acao        TEXT,
    data_proxima_acao   DATE,
    status_interacao    TEXT DEFAULT 'ABERTA'
);
```

**Não há colunas para:**
- `nome_contato` (quem atendeu)
- `cargo_contato` (cargo da pessoa)
- `telefone_contato` (telefone do contato)
- `email_contato` (e-mail do contato)

### Impacto

- Perda de rastreabilidade de quem é o interlocutor em cada cliente.
- Impossibilidade de gerar base de contatos por cliente.
- O usuário precisa descrever o contato manualmente no campo "Descrição", o que dificulta consultas e relatórios.

### Solução Recomendada

**Mínimo esforço — adicionar colunas + campos no formulário:**

1. **Adicionar à tabela `interacoes`:**
   ```sql
   ALTER TABLE interacoes ADD COLUMN nome_contato TEXT;
   ALTER TABLE interacoes ADD COLUMN cargo_contato TEXT;
   ALTER TABLE interacoes ADD COLUMN telefone_contato TEXT;
   ALTER TABLE interacoes ADD COLUMN email_contato TEXT;
   ```

2. **Adicionar campos no formulário** (após o `cliente_selecionado`):
   ```python
   with st.expander("👤 Dados do Contato", expanded=False):
       col_ct1, col_ct2 = st.columns(2)
       with col_ct1:
           nome_contato = st.text_input("Nome do contato", key="reg_nome_contato")
           cargo_contato = st.text_input("Cargo", key="reg_cargo_contato")
       with col_ct2:
           telefone_contato = st.text_input("Telefone", key="reg_tel_contato")
           email_contato = st.text_input("E-mail", key="reg_email_contato")
   ```

3. **Atualizar `registrar_interacao()`** para aceitar e persistir os 4 novos parâmetros.

4. **Exibir no Histórico** e no Cliente 360 as colunas de contato.

### Complexidade

| Item | Esforço |
|------|---------|
| ALTER TABLE (4 colunas) | 5 minutos |
| Atualizar `registrar_interacao()` | 10 minutos |
| Adicionar campos no formulário | 15 minutos |
| Exibir nas telas de histórico | 10 minutos |
| **Total** | **~40 minutos** |

---

## Problema 2 — PENDÊNCIA NÃO FUNCIONA COMO LEMBRETE

### Diagnóstico do Fluxo Completo

Rastreamento do caminho percorrido desde a criação até a exibição:

#### Etapa 1 — Criação (Código funciona corretamente)

O fluxo de criação está em `pages/06_Relacionamento_Comercial.py`, aba2:

1. Usuário marca checkbox `☐ Criar pendência comercial` (linha 384)
2. Preenche descrição, prioridade e data limite (linhas 388-408)
3. Clica em "💾 Salvar Interação" (linha 455)
4. `if submitted:` → chama `registrar_interacao()` (linha 498)
5. Se `criar_pend` True → chama `criar_pendencia()` (linha 522–529)

**O INSERT na tabela `pendencias_comerciais` só ocorre dentro do `if submitted:` — está correto.**

```python
# Linhas 522-529 — criação da pendência
if criar_pend:
    criar_pendencia(
        cliente_id=cliente_id,
        interacao_id=interacao_id,
        descricao=pend_descricao,
        prioridade=pend_prioridade,
        responsavel=responsavel,
        data_limite=pend_data_limite.strftime("%Y-%m-%d"),
    )
```

**Problema identificado:** A pendência só pode ser criada **como acoplada a uma interação**. Não existe um botão/fluxo para "Criar Pendência" independente. Isso força o usuário a registrar uma interação mesmo quando o único objetivo é criar um lembrete.

#### Etapa 2 — Exibição na AGENDA (Funciona)

`get_agenda()` em `services/relacionamento.py`, linhas 305–381:
- Faz UNION ALL entre interações com próxima ação, pendências e follow-ups.
- Pendências são consultadas com `WHERE p.status = 'ABERTA' AND p.data_limite <= ?`
- ✅ **Aparece na Agenda corretamente.**

#### Etapa 3 — Exibição no CLIENTE 360 (Funciona)

`get_indicadores_relacionamento()` em `services/relacionamento.py`, linhas 644–716:
- Conta `pendencias_abertas` e `pendencias_vencidas` por cliente_id
- ✅ **Aparece nos indicadores.**

`get_pendencias(cliente_id=...)` na aba "📞 Relacionamento" → sub-aba "📌 Pendências":
- ✅ **Aparece na lista.**

#### Etapa 4 — Exibição nos ALERTAS (Funciona)

`get_alertas_relacionamento()` em `services/relacionamento.py`, linhas 607–632:
- Consulta pendências com `WHERE p.status = 'ABERTA' AND p.data_limite < date('now')`
- ✅ **Aparece nos alertas se vencida.**

### Causa Raiz do Problema Relatado

O problema **não é técnico** (o código funciona), mas **de UX e flow**:

| Problema | Explicação |
|----------|------------|
| Pendência só nasce de interação | O usuário precisa registrar uma interação mesmo quando quer só criar um lembrete. Isso gera "ruído" no histórico. |
| Sem botão "Nova Pendência" | Não há atalho direto para criar pendência na aba 4 (Pendências). |
| Sem edição | Após criar, não é possível ajustar descrição, data ou prioridade (ver Problema 4). |
| Responsável fixo | O responsável da pendência vem do campo `responsavel` da interação (que é bloqueado / automático). Se outro usuário precisar assumir, não consegue. |

### Respostas às Perguntas

1. **A pendência está sendo criada corretamente?** ✅ Sim, o INSERT ocorre no momento certo, dentro do `if submitted:`.

2. **Está aparecendo na agenda?** ✅ Sim, via `get_agenda()` com UNION ALL.

3. **Está aparecendo no Cliente 360?** ✅ Sim, nos indicadores e na sub-aba de pendências.

4. **Está aparecendo nos alertas?** ✅ Sim, se vencida.

### Soluções Recomendadas (sem alterar arquitetura)

| Prioridade | Solução | Esforço |
|:----------:|---------|:-------:|
| 🔴 | **Botão "Nova Pendência" na aba 4** — permitir criar pendência independente sem precisar de interação (chamar `criar_pendencia` com `interacao_id=None`) | 30 min |
| 🟡 | **Exibir na aba 4 um campo "Responsável" editável** — hoje o responsável é copiado da interação; na criação independente, o usuário deve poder escolher | 15 min |
| 🟢 | **Permitir criar pendência com data futura e responsável diferente** — basta expor o campo `responsavel` no formulário de pendência | 10 min |

---

## Problema 3 — FORMULÁRIO SALVANDO INTERAÇÕES INDEVIDAMENTE

### Auditoria Completa do Fluxo de Gravação

#### 1. Onde o INSERT é disparado?

**Único local:** `pages/06_Relacionamento_Comercial.py`, linhas 496–543, dentro do bloco:

```python
if submitted:  # ← linha 461 — st.form_submit_button retorna True
    # ... validações ...
    interacao_id = registrar_interacao(...)    # ← INSERT único
    if criar_pend:
        criar_pendencia(...)                    # ← INSERT único
    if criar_opp:
        criar_oportunidade(...)                 # ← INSERT único
```

`st.form_submit_button` do Streamlit **SÓ RETORNA TRUE QUANDO O BOTÃO É EXPLICITAMENTE CLICADO**. Durante qualquer re-run (troca de aba, alteração de widget, `st.rerun()` externo), ele retorna False.

**✅ Conclusão: O mecanismo de formulário do Streamlit está correto. Não há INSERT indevido por callback ou evento automático.**

#### 2. Existem callbacks indevidos?

**Não.** Nenhum widget utiliza o parâmetro `on_change` ou `on_click`. Todos os campos estão dentro do `st.form()` e usam `key=` apenas para session_state.

#### 3. Existe rerun salvando registros?

**Identificado:** Sim, em **dois locais** na aba de Pendências (aba4):

```python
# Linha 689
if c4.button("✅ Concluir", key=f"conc_{row['id']}"):
    concluir_pendencia(row["id"])
    st.rerun()              # ← rerun após concluir

# Linha 710
if c4.button("✅ Concluir", key=f"conc_venc_{row['id']}"):
    concluir_pendencia(row["id"])
    st.rerun()              # ← rerun após concluir
```

**Análise:** Esses `st.rerun()` NÃO causam duplicação de interações, pois ocorrem em uma aba diferente (aba4 - Pendências) e chamam `concluir_pendencia()` que é um UPDATE, não INSERT. O formulário de interação está na aba2 e o `st.form_submit_button` retorna False durante re-runs.

#### 4. Há duplicação por session_state?

**Análise:** As chaves `key=` nos widgets do formulário (ex: `"reg_cliente"`, `"reg_tipo"`, `"reg_descricao"`) persistem no `st.session_state` entre re-runs. Mas **isso não causa INSERT** porque o INSERT só ocorre dentro de `if submitted:`.

#### 5. Possível causa da duplicação observada pelo usuário

Mesmo sem encontrar um bug no código, **há um cenário que pode explicar o comportamento:**

**Cenário suspeito: Checkbox de pendência/oportunidade + submit**

```python
# Linhas 384-417
criar_pend = st.checkbox("☐ Criar pendência comercial", key="reg_criar_pendencia")

with st.container():
    if criar_pend:
        # mostra campos de pendência...
    else:
        pend_descricao = ""
        pend_prioridade = "MEDIA"
        pend_data_limite = date.today() + timedelta(days=7)
```

O bloco acima está **DENTRO do formulário**. No Streamlit, quando um checkbox dentro de um form muda, ele **não causa submit automático** — mas ele **dispara re-run**. Durante o re-run, os campos condicionais (linhas 388–408) podem resetar valores se a lógica de `else:` (linhas 409–412) for executada com o checkbox ainda False.

**Mas isso ainda não causa INSERT.** O INSERT só acontece com `submitted = True`.

**Diagnóstico final:** Com base exclusivamente no código-fonte analisado, **não há evidência de bug que cause INSERT indevido**. O mecanismo de `st.form` com `st.form_submit_button` do Streamlit é seguro por design.

**Hipótese mais provável para o problema reportado:**

| Hipótese | Probabilidade |
|----------|:------------:|
| Usuário clicou em "Salvar Interação" sem perceber (duplo clique no botão) | Alta |
| Usuário preencheu, salvou, e ao navegar para outra aba e voltar, o formulário reexibiu dados anteriores (session_state persistiu) e o usuário salvou novamente achando que era rascunho | Média |
| Refresh da página (F5) com dados de formulário persistentes no session_state — mas submit continua bloqueado | Média |
| Bug específico do Streamlit em versões mais antigas | Baixa |

### Solução Recomendada (Preventiva)

Mesmo sem confirmação de bug no código, para prevenir duplicação:

1. **Adicionar flag de salvamento no session_state:**
   ```python
   if submitted:
       # ... salvar ...
       st.session_state["interacao_salva"] = True
       st.rerun()
   ```
   E no topo da aba, verificar:
   ```python
   if st.session_state.get("interacao_salva", False):
       st.success("✅ Interação já registrada. Preencha novamente para nova interação.")
       st.stop()
   ```

2. **Resetar formulário após salvar:** Limpar as chaves do session_state relacionadas ao formulário após o submit bem-sucedido.

3. **Bloquear duplo clique:** Desabilitar o botão imediatamente após o clique (não trivial no Streamlit puro, mas possível com JavaScript).

### Complexidade

| Medida | Esforço |
|--------|---------|
| Flag de salvamento + rerun | 15 min |
| Reset de session_state | 10 min |
| **Total** | **~25 min** |

---

## Problema 4 — EDIÇÃO DE PENDÊNCIAS

### 1. O que já está implementado?

**Camada de dados (`services/relacionamento.py`):**

| Função | O que faz | Implementada? |
|--------|-----------|:-------------:|
| `criar_pendencia()` | INSERT com cliente_id, interacao_id, descricao, prioridade, responsavel, data_limite | ✅ |
| `get_pendencias()` | SELECT com filtros (status, responsavel, cliente_id) | ✅ |
| `concluir_pendencia()` | UPDATE status = 'FECHADA' | ✅ |

**Camada de interface (`pages/06_Relacionamento_Comercial.py`, aba4):**

| Funcionalidade | Implementada? | Detalhes |
|----------------|:-------------:|----------|
| Listar pendências abertas | ✅ | Cards com cliente, descrição, prioridade, data |
| Listar pendências vencidas | ✅ | Cards com destaque vermelho |
| Listar pendências concluídas | ✅ | Dataframe simples |
| Concluir pendência | ✅ | Botão por card |
| Visualizar detalhes | ❌ | Só mostra resumo no card |
| Editar descrição | ❌ | Não existe |
| Editar vencimento | ❌ | Não existe |
| Editar prioridade | ❌ | Não existe |
| Reabrir pendência | ❌ | Não existe |
| Criar pendência independente | ❌ | Só via formulário de interação |
| Filtro por responsável | ❌ | Não na interface (mas `get_pendencias` aceita o parâmetro) |

### 2. O que falta?

**Funcionalidades críticas ausentes:**

1. **Visualizar detalhes** — não há tela de detalhes; o card na aba 4 só mostra 1 linha
2. **Editar** — nenhum campo de pendência pode ser alterado após criação
3. **Reabrir** — uma vez concluída, não há como reverter
4. **Criar independente** — não há botão "Nova Pendência" desacoplado de interação

### 3. Qual o menor esforço para disponibilizar essas operações?

#### Proposta 1 — Expansão dos Cards na Aba 4 (menor esforço)

Sem criar nova página, expandir os cards existentes na aba4:

```python
# Pseudocódigo — expandir card atual
with st.expander(f"📌 {row['cliente']} — {row['descricao']}"):
    st.write(f"**Prioridade:** {row['prioridade']}")
    st.write(f"**Data Limite:** {row['data_limite']}")
    st.write(f"**Responsável:** {row['responsavel']}")
    
    nova_desc = st.text_area("Descrição", value=row['descricao'],
                             key=f"edit_desc_{row['id']}")
    nova_prio = st.selectbox("Prioridade", PRIORIDADES,
                              index=PRIORIDADES.index(row['prioridade']),
                              key=f"edit_prio_{row['id']}")
    nova_data = st.date_input("Data Limite",
                               value=datetime.strptime(row['data_limite'], "%Y-%m-%d").date(),
                               key=f"edit_data_{row['id']}")
    
    col_a1, col_a2, col_a3 = st.columns(3)
    col_a1.button("💾 Salvar", key=f"salvar_{row['id']}")
    col_a2.button("✅ Concluir", key=f"conc_exp_{row['id']}")
    col_a3.button("🔄 Reabrir", key=f"reabrir_{row['id']}")
```

Para isso, seria necessário implementar no backend:

```python
# Funções novas em services/relacionamento.py
def atualizar_pendencia(pendencia_id, descricao=None, prioridade=None, data_limite=None):
    # UPDATE dinâmico — só altera campos fornecidos
    ...

def reabrir_pendencia(pendencia_id):
    # UPDATE status = 'ABERTA'
    ...
```

#### Esforço Estimado

| Funcionalidade | Arquivos | Esforço |
|----------------|----------|:-------:|
| `atualizar_pendencia()` | `services/relacionamento.py` | 20 min |
| `reabrir_pendencia()` | `services/relacionamento.py` | 10 min |
| Expandir cards na aba4 | `pages/06_Relacionamento_Comercial.py` | 45 min |
| **Total** | | **~75 min** |

#### Proposta 2 — Modal/Dialog (melhor UX)

Usar `st.dialog()` do Streamlit (disponível a partir de versões recentes) para abrir uma janela modal ao clicar no card da pendência:

```python
@st.dialog("📌 Detalhes da Pendência")
def modal_pendencia(pendencia_id):
    # Carregar dados da pendência
    # Exibir formulário completo
    # Botões de ação
```

**Esforço adicional:** +20 minutos em relação à Proposta 1.

---

## RESUMO — ORDEM DE IMPLEMENTAÇÃO RECOMENDADA

Priorizada por impacto operacional imediato vs. esforço:

| Ordem | Problema | Solução | Esforço | Impacto |
|:-----:|----------|---------|:-------:|:-------:|
| 1️⃣ | **Problema 4 — Edição** | `atualizar_pendencia()` + `reabrir_pendencia()` + expandir cards | 75 min | 🔴 Alto |
| 2️⃣ | **Problema 1 — Contatos** | 4 colunas + campos no formulário | 40 min | 🔴 Alto |
| 3️⃣ | **Problema 2 — Pendência independente** | Botão "Nova Pendência" na aba 4 + responsável editável | 30 min | 🟡 Médio |
| 4️⃣ | **Problema 3 — Prevenção duplicação** | Flag de salvamento + reset session_state | 25 min | 🟡 Médio |
| | **Total** | | **~170 min (2h50)** | |

### Observações Importantes

1. **Nenhuma das soluções acima requer criação de novas tabelas ou alteração de arquitetura.**
2. **Nenhuma das soluções conflita com a evolução v1.1 (Workflow).**
3. As colunas adicionadas no Problema 1 (`nome_contato`, `cargo_contato`, etc.) serão utilizadas pela timeline v1.1.
4. A função `atualizar_pendencia()` do Problema 4 será base para as novas funções `reagendar_pendencia()` e `registrar_evolucao()` do v1.1.

---

*Diagnóstico gerado por análise do código-fonte do ULITEC CRM v1.0.4*