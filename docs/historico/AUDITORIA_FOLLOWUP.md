# Auditoria de Follow-up — V1.6.10

## Parâmetros da Administração (aba "Operação")

### Definições na tela (pages/90_Administracao.py:246-267)

| Parâmetro | Chave | Valor Padrão | Salvo? |
|-----------|-------|--------------|--------|
| Prazo envio proposta | `envio_proposta` | 3 | ❌ |
| Primeiro follow-up | `followup_1` | 2 | ❌ |
| Segundo follow-up | `followup_2` | 7 | ❌ |
| Terceiro follow-up | `followup_3` | 15 | ❌ |
| Proposta esquecida | `proposta_esquecida` | 30 | ❌ |
| Prazo expedição | `expedicao` | 5 | ❌ |
| Feedback cliente | `feedback_cliente` | 7 | ❌ |

**Problema:** Os parâmetros da aba "Operação" (linhas 239-279) usam `st.number_input` com `key` mas NÃO são salvos no bloco `if st.button("Salvar Configurações")` (linhas 698-718). O bloco de salvamento só persiste configurações de relacionamento.

## Onde os parâmetros DEVERIAM ser lidos

### 1. Pipeline OS — Follow-up de Propostas (pages/11_Pipeline_OS.py)

**Local:** Linhas 703-708 (função de registrar follow-up)

```python
if followup_count == 0:
    nova_data_followup = date.today() + pd.Timedelta(days=2)  # hardcoded
elif followup_count == 1:
    nova_data_followup = date.today() + pd.Timedelta(days=7)  # hardcoded
else:
    nova_data_followup = date.today() + pd.Timedelta(days=15) # hardcoded
```

**Problema:** Valores hardcoded (2, 7, 15) em vez de consultar `get_config('followup_1')`, `get_config('followup_2')`, `get_config('followup_3')`.

### 2. Central de Oportunidades (pages/10_Central_Oportunidades.py)

**Local:** Linhas 122-125
Usa `get_config('dias_followup_proposta')` apenas para alerta de proposta sem retorno.

**Problema:** Não integra:
- Follow-ups vencidos de OS
- Propostas esquecidas (30+ dias)
- OS aguardando aprovação

### 3. services/relacionamento.py

**Local:** Linhas 62-71 (`CHAVES_CONFIG`)
**Problema:** Não inclui as chaves de follow-up operacional.

### 4. services/relacionamento.py — get_agenda() (linhas 341-408)

**Local:** Linhas 359-401
Consulta `os.proximo_followup` mas não usa os parâmetros configurados para calcular datas.

## Fluxo Atual vs Esperado

### Atual
```
Admin configura (mas não salva) → valores hardcoded no Pipeline
```

### Esperado
```
Admin configura → salva no banco → Pipeline consulta → respeita parâmetros
```

## Divergências Encontradas

| Item | Status | Severidade |
|------|--------|------------|
| Parâmetros não salvos na Admin | ❌ | CRÍTICA |
| Valores hardcoded no Pipeline | ❌ | CRÍTICA |
| CHAVES_CONFIG sem follow-up | ❌ | ALTA |
| Central sem follow-ups vencidos | ❌ | MÉDIA |
| Proposta esquecida não utilizada | ❌ | MÉDIA |

## Recomendações

1. Adicionar chaves `followup_1`, `followup_2`, `followup_3`, `proposta_esquecida` ao salvamento na Admin
2. Adicionar à `CHAVES_CONFIG` em services/relacionamento.py
3. Alterar Pipeline OS para consultar `get_config()`
4. Integrar follow-ups vencidos na Central de Oportunidades
5. Integrar proposta esquecida (30+ dias sem follow-up)
</write_to_file>