# Guia de Componentes UI — ULITEC CRM v2.3

## Visão Geral

Este guia documenta todos os componentes reutilizáveis da biblioteca `components/`.

**Objetivo:** Garantir que todo o CRM tenha a mesma aparência, comportamento e organização, eliminando código duplicado e acelerando o desenvolvimento de novos módulos.

---

## Como Importar

```python
from components import (
    # Headers
    titulo_pagina,
    subtitulo,
    cabecalho_modulo,
    secao_divisoria,

    # KPIs
    card_indicador,
    linha_indicadores,

    # Status
    badge_status,

    # Filtros
    linha_filtros,
    filtro_unidade_sidebar,
    filtro_periodo_sidebar,

    # Tabelas
    tabela_padrao,

    # Mensagens
    mensagem_sucesso,
    mensagem_erro,
    mensagem_atencao,
    mensagem_info,
    confirmacao,

    # Containers
    container_resultado,

    # Busca
    caixa_busca,

    # Gráficos
    config_grafico,
    grafico_barras,
)

# Constantes
from components import STATUS_PADRAO, CORES_STATUS
```

---

## 1. Headers

### `titulo_pagina(icone, titulo, descricao="")`

Título principal de qualquer página.

```python
titulo_pagina("📊", "Dashboard Comercial", "Visão geral dos indicadores da ULITEC")
```

### `subtitulo(texto)`

Subtítulo padronizado.

```python
subtitulo("Indicadores do Período")
```

### `cabecalho_modulo(icone, titulo, descricao="")`

Cabeçalho completo com título, descrição e divisor.

```python
cabecalho_modulo("📞", "Relacionamento Comercial",
                 "Registre interações, gerencie pendências e acompanhe visitas.")
```

### `secao_divisoria(texto="")`

Divisor visual entre seções, com texto opcional.

```python
secao_divisoria("Análise Detalhada")
```

---

## 2. KPIs (Indicadores)

### `card_indicador(rotulo, valor, delta=None, help_text=None, icone="")`

Card de indicador individual.

```python
card_indicador("Clientes Ativos", 150, delta="+12%",
               help_text="Total de clientes com faturamento nos últimos 12 meses",
               icone="🏢")
```

### `linha_indicadores(indicadores, cols=4)`

Linha completa de KPIs em colunas.

```python
linha_indicadores([
    {"rotulo": "Clientes", "valor": 250, "icone": "🏢"},
    {"rotulo": "Receita", "valor": "R$ 2.5M", "delta": "+15%", "help": "Faturamento total"},
    {"rotulo": "Ticket Médio", "valor": "R$ 10.000", "icone": "🎯"},
    {"rotulo": "OS Abertas", "valor": 45, "delta": "-5%", "icone": "📦"},
])
```

---

## 3. Status (Badges)

### `badge_status(status, tamanho="pequeno")`

Gera HTML de badge padronizado para qualquer status.

**Tamanhos disponíveis:** `"pequeno"`, `"medio"`, `"grande"`

```python
st.markdown(badge_status("APROVADO"), unsafe_allow_html=True)
st.markdown(badge_status("CANCELADO", tamanho="grande"), unsafe_allow_html=True)
```

### `STATUS_PADRAO`

Lista de status principais do CRM:

```python
["ENVIADO", "ORÇADO", "APROVADO", "RECEBIDO", "CANCELADO"]
```

### `CORES_STATUS`

Dicionário com cores padronizadas para cada status:

| Status      | Cor Texto | Fundo    |
|-------------|-----------|----------|
| ENVIADO     | Azul      | #dbeafe  |
| ORÇADO      | Amarelo   | #fef3c7  |
| APROVADO    | Verde     | #dcfce7  |
| RECEBIDO    | Índigo    | #e0e7ff  |
| CANCELADO   | Vermelho  | #fee2e2  |
| ABERTA      | Azul      | #dbeafe  |
| FECHADA     | Verde     | #dcfce7  |
| VENCIDA     | Vermelho  | #fee2e2  |
| PENDENTE    | Amarelo   | #fef3c7  |
| CONCLUIDA   | Verde     | #dcfce7  |
| PERDIDA     | Vermelho  | #fee2e2  |

---

## 4. Filtros

### `filtro_unidade_sidebar()`

Filtro de unidade (filial) no sidebar. Gerencia automaticamente `st.session_state["unidade_ativa"]`.

```python
unidade = filtro_unidade_sidebar()
# Retorna: "GRUPO", "ULITEC SP" ou "ULITEC RS"
```

### `filtro_periodo_sidebar(chave, label, opcoes, default)`

Filtro de período no sidebar.

```python
periodo = filtro_periodo_sidebar(
    chave="filtro_periodo",
    default="Últimos 30 dias"
)
```

### `linha_filtros(filtros)`

Linha de filtros padronizada em colunas. Retorna dicionário com valores.

```python
valores = linha_filtros([
    {"tipo": "selectbox", "rotulo": "Estado", "opcoes": ["SP", "RS"], "key": "f_estado"},
    {"tipo": "multiselect", "rotulo": "Status", "opcoes": ["ATIVO", "INATIVO"], "key": "f_status"},
    {"tipo": "text", "rotulo": "Cliente", "placeholder": "Digite o nome...", "key": "f_cliente"},
    {"tipo": "date", "rotulo": "Data Início", "key": "f_data_ini"},
    {"tipo": "number", "rotulo": "Mínimo Máquinas", "min": 0, "max": 100, "key": "f_maquinas"},
])
```

**Tipos disponíveis:** `selectbox`, `multiselect`, `text`, `date`, `number`

---

## 5. Formulários

### `campo_obrigatorio(rotulo, placeholder="", chave=None)`

Campo de texto obrigatório com asterisco visual.

```python
nome = campo_obrigatorio("Nome do Cliente", "Razão social", "form_nome")
```

### `campo_opcional(rotulo, placeholder="", chave=None)`

Campo de texto opcional.

```python
email = campo_opcional("E-mail", "contato@exemplo.com", "form_email")
```

### `campo_data(rotulo, valor_padrao=None, chave=None)`

Campo de data.

```python
data = campo_data("Data de Entrega", chave="form_data")
```

### `campo_valor(rotulo, valor_padrao=0.0, chave=None)`

Campo de valor monetário.

```python
valor = campo_valor("Valor do Orçamento", chave="form_valor")
```

### `campo_observacao(rotulo, altura=100, chave=None)`

Campo de observações (textarea).

```python
obs = campo_observacao("Observações Técnicas", altura=200, chave="form_obs")
```

### `botoes_form(salvar=True, cancelar=True, excluir=False)`

Botões padronizados para formulários.

```python
salvou, cancelou, excluiu = botoes_form(salvar=True, cancelar=True, excluir=True)

if salvou:
    # salvar dados
if cancelou:
    # cancelar
if excluiu:
    # confirmar exclusão
```

---

## 6. Tabelas

### `tabela_padrao(dados, height=400, uso_largura=True, ocultar_indice=True, coluna_config=None)`

Tabela padronizada via `st.dataframe`.

```python
tabela_padrao(df_clientes, height=500, coluna_config={
    "faturamento": st.column_config.NumberColumn("Faturamento", format="R$ %.2f"),
    "data": st.column_config.DateColumn("Data"),
})
```

### `aplicar_estilo_tabela(df, coluna_cor="status", mapa_cores=None)`

Aplica estilo condicional baseado em coluna.

```python
st.dataframe(aplicar_estilo_tabela(df, coluna_cor="classe", mapa_cores={
    "A": "background-color: #dcfce7; color: #166534",
    "B": "background-color: #dbeafe; color: #1e40af",
    "C": "background-color: #fef3c7; color: #92400e",
    "D": "background-color: #fee2e2; color: #991b1b",
}))
```

---

## 7. Mensagens

### `mensagem_sucesso(texto)`

```python
mensagem_sucesso("Dados salvos com sucesso!")
```

### `mensagem_erro(texto)`

```python
mensagem_erro("Erro ao conectar com o banco de dados.")
```

### `mensagem_atencao(texto)`

```python
mensagem_atencao("Preencha todos os campos obrigatórios.")
```

### `mensagem_info(texto)`

```python
mensagem_info("Nenhum cliente encontrado com o filtro selecionado.")
```

### `confirmacao(texto, ao_confirmar, *args, **kwargs)`

Caixa de confirmação com callback.

```python
confirmacao("Tem certeza que deseja excluir este registro?", excluir_registro, id=123)
```

---

## 8. Containers

### `container_resultado(titulo="", expandido=True)`

Container padronizado. Com título vira `st.expander`, sem título vira `st.container(border=True)`.

```python
with container_resultado("Detalhes do Cliente"):
    st.write("Conteúdo aqui...")

with container_resultado():
    st.write("Container com borda")
```

---

## 9. Busca

### `caixa_busca(placeholder="🔍 Buscar...", chave="caixa_busca", help_text=None, label=None, valor_padrao="")`

Caixa de busca padronizada.

```python
termo = caixa_busca("Buscar cliente por nome...", chave="busca_cliente")
```

Com label visível:

```python
termo = caixa_busca("Buscar Produto", chave="busca_produto",
                     placeholder="Digite modelo ou descrição",
                     label="🔍 Buscar Produto")
```

---

## 10. Gráficos

### `config_grafico(altura=400, titulo=None)`

Retorna configuração padrão para gráficos Plotly.

```python
fig.update_layout(**config_grafico(altura=500, titulo="Vendas por Mês"))
```

### `grafico_barras(dados, x, y, titulo="", cor=None, altura=400, horizontal=False, color_coluna=None)`

Gráfico de barras padronizado com Plotly.

```python
# Barras verticais
grafico_barras(df_vendas, x="mes", y="valor", titulo="Vendas por Mês")

# Barras horizontais com cores por categoria
grafico_barras(df_top, x="faturamento", y="cliente",
               titulo="Top Clientes", horizontal=True,
               color_coluna="classe_abc")
```

---

## 11. Helpers

### `espacamento(altura=1)`

Adiciona linhas de espaçamento vertical.

```python
espacamento(2)  # 2 linhas em branco
```

### `linha_separadora()`

Adiciona linha separadora (`st.divider()`).

```python
linha_separadora()
```

---

## Boas Práticas

1. **Sempre importe da biblioteca `components`**, nunca crie componentes manuais duplicados.

2. **Use `linha_indicadores`** em vez de criar `st.columns()` + `st.metric()` manualmente.

3. **Use `badge_status`** para todos os status do sistema — garante cores consistentes.

4. **Use `linha_filtros`** para qualquer conjunto de filtros — garante alinhamento e largura padronizados.

5. **Use `tabela_padrao`** com `aplicar_estilo_tabela` para evitar coloração manual.

6. **Use `cabecalho_modulo`** no início de cada página de módulo.

7. **Nunca crie funções de estilo inline.** Use `aplicar_estilo_tabela` com o dicionário `CORES_STATUS`.

---

## Exemplo Completo

```python
from components import (
    cabecalho_modulo,
    linha_indicadores,
    linha_filtros,
    tabela_padrao,
    badge_status,
    grafico_barras,
)

# Cabeçalho
cabecalho_modulo("📊", "Meu Módulo", "Descrição do módulo")

# KPIs
linha_indicadores([
    {"rotulo": "Total", "valor": 100, "icone": "🏢"},
    {"rotulo": "Ativos", "valor": 80, "delta": "+5%", "icone": "✅"},
])

# Filtros
linha_filtros([
    {"tipo": "selectbox", "rotulo": "Estado", "opcoes": ["SP", "RS"], "key": "f_estado"},
])

# Tabela com status
for _, row in df.iterrows():
    st.markdown(f"{row['nome']} {badge_status(row['status'])}", unsafe_allow_html=True)

# Gráfico
grafico_barras(df, x="mes", y="vendas", titulo="Vendas")
```

---

## Arquivos

| Arquivo | Descrição |
|---------|-----------|
| `__init__.py` | Re-exporta todos os componentes |
| `ui.py` | Implementação de todos os componentes |

## Próximos Passos

Na próxima sprint, migraremos módulo por módulo para utilizar esta biblioteca, removendo aproximadamente **70-80% do código de interface duplicado** (~2000+ linhas economizadas).