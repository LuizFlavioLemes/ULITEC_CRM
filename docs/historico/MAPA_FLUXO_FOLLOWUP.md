# Mapa do Fluxo de Follow-up — V1.6.10

## Fluxo Completo do Pipeline OS

```
OS Criada (RECEBIDA)
  │
  ▼
Proposta Enviada (PROPOSTA ENVIADA)
  │
  ├── 1º Follow-up (after followup_1 dias) ──┐
  │                                           │
  ├── 2º Follow-up (after followup_2 dias) ──┤
  │                                           │
  ├── 3º Follow-up (after followup_3 dias) ──┤
  │                                           │
  └── Proposta Esquecida (after proposta_esquecida dias)
                                              │
                                              ▼
                                        APROVADA / PERDIDA / CANCELADA
```

## Estado Atual (V1.6.9)

### Onde o follow-up é registrado
- **pages/11_Pipeline_OS.py** — aba 4 "Follow-up de Propostas" (linhas 647-728)
  - Usa `followup_count` da tabela `ordens_servico`
  - Calcula próxima data com valores hardcoded:
    - 1º follow-up: +2 dias
    - 2º follow-up: +7 dias
    - 3º follow-up: +15 dias

### Onde os parâmetros são configurados
- **pages/90_Administracao.py** — aba "Operação" (linhas 239-267)
  - Inputs para: followup_1 (2), followup_2 (7), followup_3 (15), proposta_esquecida (30)
  - **Não são salvos no banco** (bloco salvar só persiste relacionamento)

### Onde os parâmetros são lidos
- **Em lugar nenhum.** Os valores na Admin não são salvos, e o Pipeline usa hardcoded.

## Problemas Encontrados

### 1. Quebra no Ciclo Salvar → Ler
```
Admin (st.number_input) → session_state (não persiste) → Pipeline (hardcoded)
```

### 2. Campos com key não salvos
Os seguintes campos na Admin têm key definida mas não são coletados no salvamento:
- `envio_proposta`, `followup_1`, `followup_2`, `followup_3`
- `proposta_esquecida`, `expedicao`, `feedback_cliente`

### 3. CHAVES_CONFIG desatualizado
O array `CHAVES_CONFIG` em `services/relacionamento.py` não inclui as chaves operacionais.

### 4. get_agenda() não usa parâmetros
A função `get_agenda()` em `services/relacionamento.py` consulta `os.proximo_followup` mas não usa os parâmetros configurados para alertas de proposta esquecida.

## Fluxo Correto (pós-correção)

```
Admin configura → salvar_configs_operacionais() → tabela configuracoes
                                                      │
                                                      ▼
Pipeline OS consulta → get_config('followup_1') → calcula data correta
                                                      │
                                                      ▼
Central de Oportunidades consulta → follow-ups vencidos / hoje / propostas esquecidas
```

## Tabela de Mapeamento

| Etapa | Admin Key | Config Chave | Pipeline (atual) | Pipeline (corrigido) |
|-------|-----------|-------------|-------------------|---------------------|
| 1º follow-up | `followup_1` | `followup_1` | +2 dias hardcoded | get_config('followup_1') |
| 2º follow-up | `followup_2` | `followup_2` | +7 dias hardcoded | get_config('followup_2') |
| 3º follow-up | `followup_3` | `followup_3` | +15 dias hardcoded | get_config('followup_3') |
| Proposta esquecida | `proposta_esquecida` | `proposta_esquecida` | não utilizado | get_config('proposta_esquecida') |
| Prazo proposta | `envio_proposta` | `envio_proposta` | não utilizado | get_config('envio_proposta') |
| Prazo expedição | `expedicao` | `expedicao` | não utilizado | get_config('expedicao') |
| Feedback | `feedback_cliente` | `feedback_cliente` | não utilizado | get_config('feedback_cliente') |
</write_to_file>