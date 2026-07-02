# CORREÇÃO PENDÊNCIAS V1.6.12

## 1. Arquivos alterados
- `services/relacionamento.py` — função `get_alertas_relacionamento()`
- `pages/10_Central_Oportunidades.py` — bloco "O QUE FAZER HOJE"

## 2. Linhas alteradas
- `services/relacionamento.py`: linhas 700-725 (filtro `<` → `<=` + classificação VENCIDA/VENCE HOJE)
- `pages/10_Central_Oportunidades.py`: linhas 316-430 (inserção de 2 novos blocos: pendências vencidas + pendências hoje; renumeração de 1-5 para 1-7)

## 3. Causa raiz
- Alerta usava `data_limite < hoje` em vez de `data_limite <= hoje`, excluindo pendências com vencimento igual ao dia atual
- Bloco "O QUE FAZER HOJE" não consultava `pendencias_comerciais`

## 4. Correções realizadas
- `get_alertas_relacionamento()`: `<=` e classificação: PENDENCIA_VENCIDA (se < hoje) / PENDENCIA_VENCE_HOJE (se == hoje)
- "O QUE FAZER HOJE": novas fontes #1 (pendências vencidas) e #2 (pendências hoje), prioridades renumeradas (1-7)
- caption e coloração ajustados

## 5. Validação da pendência "ligar PC"
| Local | Antes | Depois |
|-------|-------|--------|
| Pendências | ✅ Aparecia | ✅ Aparece |
| Alertas | ❌ Não aparecia | ✅ Aparece (VENCE HOJE) |
| O QUE FAZER HOJE | ❌ Não aparecia | ✅ Aparece (🟠 PENDÊNCIA HOJE) |

## 6. Pendências remanescentes
Nenhuma. Todas as 7 pendências abertas estão cobertas (1 vence hoje, 6 futuras).