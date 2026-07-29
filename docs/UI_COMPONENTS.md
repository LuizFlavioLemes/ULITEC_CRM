# Catálogo de Componentes Comuns (UI Framework)

## Visão Geral

A biblioteca `components/common/` fornece componentes Streamlit reutilizáveis,
genéricos e desacoplados de qualquer regra de negócio.

**Princípios:**
- Nenhum componente acessa banco de dados
- Nenhum componente importa Services
- Nenhum componente contém regra de negócio
- Todos os componentes aceitam parâmetros para personalização

---

## 1. page_header

**Arquivo:** `components/common/page_header.py`

| Função | Descrição |
|--------|-----------|
| `page_header(icone, titulo, descricao="")` | Cabeçalho completo de página (título + descrição) |
| `section_header(titulo, descricao="")` | Cabeçalho de seção (subheader + caption) |
| `page_subtitle(texto)` | Subtítulo padronizado (subheader) |

**Exemplo:**
```python
from components.common import page_header

page_header("📊", "Dashboard Comercial", "Indicadores do período")
section_header("Clientes Ativos", "Total: 150 clientes")
```

---

## 2. metric_grid

**Arquivo:** `components/common/metric_grid.py`

| Função | Descrição |
|--------|-----------|
| `metric_grid(indicadores, cols=4)` | Grid de KPIs em linha |
| `metric_card(rotulo, valor, delta, help_text, icone)` | Card de métrica individual |

**Parâmetros de `metric_grid`:**
- `indicadores`: Lista de dicts com chaves:
  - `"rotulo"` (str, obrigatório)
  - `"valor"` (qualquer, obrigatório)
  - `"delta"` (str, opcional — ex: "+15%")
  - `"help"` (str, opcional — tooltip)
  - `"icone"` (str, opcional — emoji)
- `cols`: Número de colunas (default=4)

**Exemplo:**
```python
from components.common import metric_grid

metric_grid([
    {"rotulo": "Clientes", "valor": 150, "icone": "🏢", "help": "Total de clientes ativos"},
    {"rotulo": "Receita", "valor": "R$ 1.2M", "delta": "+12%"},
    {"rotulo": "OS Abertas", "valor": 45, "icone": "🔧"},
], cols=3)
```

---

## 3. panel

**Arquivo:** `components/common/panel.py`

| Função | Descrição |
|--------|-----------|
| `panel(content, titulo="", icone="")` | Painel genérico com borda |
| `info_panel(mensagem, titulo="")` | Painel informativo |
| `warning_panel(mensagem, titulo="")` | Painel de alerta |

**Parâmetros de `panel`:**
- `content`: Pode ser `str` (renderiza com markdown) ou `callable` (executa dentro do container)
- `titulo`: Título opcional do painel
- `icone`: Emoji opcional

**Exemplo:**
```python
from components.common import panel

# String simples
panel("Conteúdo em texto", titulo="Informações", icone="ℹ️")

# Conteúdo complexo com callable
panel(None, titulo="Relatório", icone="📊"):
    st.write("Dados aqui")
    st.dataframe(df)
```

---

## 4. section

**Arquivo:** `components/common/section.py`

| Função | Descrição |
|--------|-----------|
| `section(titulo, descricao="")` | Seção completa (h3 + caption + divider) |
| `subsection(titulo)` | Subseção (subheader) |
| `divider()` | Divisor visual |

**Exemplo:**
```python
from components.common import section

section("Indicadores", "KPIs do período")
subsection("Clientes Prioritários")
```

---

## 5. toolbar

**Arquivo:** `components/common/toolbar.py`

| Função | Descrição |
|--------|-----------|
| `toolbar(botoes, cols=None)` | Barra de botões em linha |
| `action_button(rotulo, tipo, key, largura)` | Botão individual |

**Parâmetros de `toolbar`:**
- `botoes`: Lista de dicts com:
  - `"rotulo"` (str, obrigatório)
  - `"tipo"` ("primary" | "secondary", default="secondary")
  - `"key"` (str, opcional)
- `cols`: Número de colunas (calculado automaticamente se None)

**Retorno:** Rótulo do botão clicado ou None.

**Exemplo:**
```python
from components.common import toolbar

acao = toolbar([
    {"rotulo": "💾 Salvar", "tipo": "primary", "key": "save"},
    {"rotulo": "🗑 Excluir", "key": "delete"},
])
if acao == "💾 Salvar":
    salvar_dados()
```

---

## 6. empty_state

**Arquivo:** `components/common/empty_state.py`

| Função | Descrição |
|--------|-----------|
| `empty_state(mensagem, icone)` | Estado vazio (st.success) |
| `no_results(mensagem)` | Busca sem resultados (st.info) |

**Exemplo:**
```python
from components.common import empty_state

empty_state("Nenhuma pendência para hoje", icone="📌")
no_results("Nenhum cliente encontrado com este filtro")
```

---

## 7. loading

**Arquivo:** `components/common/loading.py`

| Função | Descrição |
|--------|-----------|
| `loading_wrapper(func, *args, mensagem, **kwargs)` | Executa função com spinner |
| `spinner_context(mensagem)` | Context manager para blocos com spinner |

**Exemplo:**
```python
from components.common import loading

# Wrapper para função única
df = loading_wrapper(
    pd.read_sql_query,
    "SELECT * FROM clientes", conn,
    mensagem="Buscando clientes..."
)

# Context manager para múltiplas operações
with spinner_context("Processando..."):
    df1 = carregar_vendas()
    df2 = carregar_clientes()
```

---

## Resumo de Importação

```python
# Importar todos os componentes
from components.common import (
    page_header, section_header, page_subtitle,   # page_header.py
    metric_grid, metric_card,                     # metric_grid.py
    panel, info_panel, warning_panel,             # panel.py
    section, subsection, divider,                 # section.py
    toolbar, action_button,                       # toolbar.py
    empty_state, no_results,                      # empty_state.py
    loading_wrapper, spinner_context,             # loading.py
)
```

## Compatibilidade

A biblioteca foi projetada para ser **totalmente compatível** com o UI framework
legado em `components/ui.py`. Ambos podem coexistir sem conflitos.

Nenhuma página existente foi alterada durante a criação desta biblioteca.
A migração para os novos componentes é opcional e pode ser feita gradualmente.