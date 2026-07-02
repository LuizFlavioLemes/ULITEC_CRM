# Correção — KeyError: 'tipo'

## Arquivo
`pages/10_Central_Oportunidades.py`

## Erro Original

```
KeyError: 'tipo'

Linha 437:
    val = str(row["tipo"])

Linha 461:
    df_exib_hoje.style.apply(colorir_fila, axis=1)
```

## Causa Raiz

A função `colorir_fila()` acessava a coluna `"tipo"` do DataFrame `row`, mas o DataFrame passado para `style.apply()` era `df_exib_hoje`, que já havia passado por um `rename(columns=rename_map)` onde `"tipo"` foi renomeado para `"Prioridade"`.

**Fluxo que gerava o erro:**

1. `df_hoje` possuía a coluna `"tipo"` (criada nos dicionários de `lista_prioridades`)
2. `df_exib_hoje = df_hoje[colunas_exib].rename(columns=rename_map)` renomeava `"tipo"` → `"Prioridade"`
3. `df_exib_hoje.style.apply(colorir_fila, axis=1)` chamava a função com cada linha de `df_exib_hoje`
4. Dentro de `colorir_fila`, `row["tipo"]` falhava porque a coluna agora se chama `"Prioridade"`

## Correção Aplicada

### 1. Troca do nome da coluna

```python
# Antes (linha 437):
val = str(row["tipo"])

# Depois:
val = str(row["Prioridade"])
```

### 2. Proteção defensiva

Adicionada verificação no início da função para evitar crash caso a coluna esperada não exista:

```python
if "Prioridade" not in row.index:
    return [""] * len(row)
```

## Validação

```
python -m py_compile pages/10_Central_Oportunidades.py
→ Sem erros de compilação.
```

## Escopo

- Nenhuma regra de negócio foi alterada.
- Nenhuma alteração de layout foi feita.
- Apenas a função `colorir_fila()` foi modificada.
- As demais 1080+ linhas do arquivo permanecem intactas.