# ANÁLISE DE ARQUIVOS OBSOLETOS

**Data:** 24/06/2026

## Arquivos de Diagnóstico (Raiz)

| Arquivo | Tipo | Status | Observação |
|--------|------|--------|------------|
| `_check_db.py` | Diagnóstico | CANDIDATO A REMOÇÃO | Script de verificação pontual, já executado |
| `_create_evolucao.py` | Migração | CANDIDATO A REMOÇÃO | Script de evolução de schema, já executado |
| `_inspect_db.py` | Diagnóstico | CANDIDATO A REMOÇÃO | Inspeção de banco, uso único |
| `_inspect_schema.py` | Diagnóstico | CANDIDATO A REMOÇÃO | Inspeção de schema, uso único |
| `_temp_auditoria_geral.py` | Temp | DESCARTÁVEL | Gerado durante auditoria atual |
| `_temp_deps.py` | Temp | DESCARTÁVEL | Gerado durante auditoria atual |
| `_temp_estrutura.py` | Temp | DESCARTÁVEL | Gerado durante auditoria atual |
| `_temp_obsoletos.py` | Temp | DESCARTÁVEL | Este arquivo |
| `_temp_schema_export.py` | Temp | DESCARTÁVEL | Gerado durante auditoria atual |

## Arquivos de Debug

| Arquivo | Status | Observação |
|--------|--------|------------|
| `debug/99_Debug_OS.py` | CANDIDATO A REMOÇÃO | Script de diagnóstico não utilizado pelo app |
| `debug/diagnostico_classificacao.py` | CANDIDATO A REMOÇÃO | Script de diagnóstico não utilizado pelo app |
| `debug/valida_v151.py` | CANDIDATO A REMOÇÃO | Script de diagnóstico não utilizado pelo app |

## Arquivos Legacy

| Arquivo | Status | Observação |
|--------|--------|------------|
| `legacy/12_Acoes_Massa.py` | LEGACY | Páginas antigas desativadas |
| `legacy/30_Importar_Clientes.py` | LEGACY | Páginas antigas desativadas |
| `legacy/31_Importar_Faturamento.py` | LEGACY | Páginas antigas desativadas |
| `legacy/32_Importar_OS.py` | LEGACY | Páginas antigas desativadas |
| `legacy/36_Pendencias_Cadastro.py` | LEGACY | Páginas antigas desativadas |

## Documentos Duplicados/Redundantes

| Arquivo | Status | Observação |
|--------|--------|------------|
| `AUDITORIA_V1_0_4.md` | DOCUMENTO HISTÓRICO | Auditoria anterior, manter como referência |
| `RELATORIO_ESTABILIZACAO_V2.md` | DOCUMENTO HISTÓRICO | Relatório de estabilização, manter |
| `RELATORIO_ESTRUTURA.md` | DOCUMENTO HISTÓRICO | Relatório de estrutura, manter |

## Resumo

- **Diagnóstico na raiz:** 4 candidatos à remoção
- **Temporários desta auditoria:** 5 (serão removidos ao final)
- **Debug:** 3 candidatos à remoção
- **Legacy:** 5 arquivos inativos
- **Documentos históricos:** 3 (manter)

**Total removível com segurança:** ~12 arquivos
**Total legacy (manter parado):** 5 arquivos

*Nenhum arquivo foi removido. Apenas análise documental.*
