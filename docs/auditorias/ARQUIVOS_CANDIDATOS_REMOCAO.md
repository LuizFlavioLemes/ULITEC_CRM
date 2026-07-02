# ARQUIVOS CANDIDATOS À REMOÇÃO

**Data:** 24/06/2026
**Etapa:** 2 — Limpeza Controlada

---

## 1. Critérios de Classificação

| Categoria | Descrição |
|-----------|-----------|
| **UTILIZADO** | Referenciado por app.py ou services/pages em uso |
| **OBSOLETO** | Script de diagnóstico pontual, já executado |
| **LEGACY** | Página/substituída por versão mais recente |
| **TEMP** | Gerado durante esta auditoria |

---

## 2. Scripts de Diagnóstico na Raiz

| Arquivo | Classificação | Motivo |
|---------|---------------|--------|
| `_check_db.py` | OBSOLETO | Verificação de banco já realizada |
| `_create_evolucao.py` | OBSOLETO | Migração de schema já executada |
| `_inspect_db.py` | OBSOLETO | Inspeção pontual de banco |
| `_inspect_schema.py` | OBSOLETO | Inspeção de schema já realizada |

---

## 3. Scripts Temporários (desta auditoria)

| Arquivo | Classificação | Motivo |
|---------|---------------|--------|
| `_temp_schema_export.py` | TEMP | Gerado para exportar schema |
| `_temp_estrutura.py` | TEMP | Gerado para listar estrutura |
| `_temp_deps.py` | TEMP | Gerado para mapear dependências |
| `_temp_auditoria_geral.py` | TEMP | Gerado para auditoria geral |
| `_temp_obsoletos.py` | TEMP | Gerado para análise de obsoletos |
| `_temp_backup.py` | TEMP | Gerado para backup lógico |

---

## 4. Arquivos de Debug

| Arquivo | Classificação | Motivo |
|---------|---------------|--------|
| `debug/99_Debug_OS.py` | OBSOLETO | Debug de OS, não referenciado pelo app |
| `debug/diagnostico_classificacao.py` | OBSOLETO | Diagnóstico de classificação ABCD |
| `debug/valida_v151.py` | OBSOLETO | Validação da V1.5.1 |

---

## 5. Arquivos Legacy

| Arquivo | Classificação | Motivo |
|---------|---------------|--------|
| `legacy/12_Acoes_Massa.py` | LEGACY | Funcionalidade substituída |
| `legacy/30_Importar_Clientes.py` | LEGACY | Substituída por importação integrada |
| `legacy/31_Importar_Faturamento.py` | LEGACY | Substituída por importação integrada |
| `legacy/32_Importar_OS.py` | LEGACY | Substituída por importação integrada |
| `legacy/36_Pendencias_Cadastro.py` | LEGACY | Substituída por pendências comerciais |

---

## 6. Resumo Final

| Categoria | Quantidade | Ação Recomendada |
|-----------|------------|------------------|
| OBSOLETO (raiz) | 4 | Remover |
| TEMP (auditoria) | 6 | Remover ao final |
| OBSOLETO (debug) | 3 | Remover |
| LEGACY | 5 | Manter congelado |
| **Total** | **18** | |

---

## 7. Observações

- Nenhum arquivo foi removido durante esta auditoria.
- A remoção deve ser feita apenas após validação de que nenhum import referência estes arquivos.
- Os arquivos `_temp_*` podem ser removidos imediatamente após esta auditoria.
- Os arquivos `legacy/` podem ser mantidos como referência histórica.

---

*Documento gerado automaticamente — auditoria V1.6*