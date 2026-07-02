# INVENTÁRIO DE ARQUIVOS TEMPORÁRIOS — ULITEC CRM v1.6.9

## Critérios de classificação

| Categoria | Critério |
|---|---|
| **A) Pode remover** | Arquivos de diagnóstico/inspect/check que não são importados por nenhum módulo do sistema |
| **B) Deve manter** | Arquivos de debug que ainda podem ser úteis para troubleshooting |
| **C) Arquivo de apoio** | Scripts auxiliares utilizados em validações manuais |

---

## Inventário

### Raiz do projeto

| Arquivo | Categoria | Motivo |
|---|---|---|
| `_check_db.py` | **A) Pode remover** | Script de verificação de banco. Não é importado por nenhum módulo. |
| `_create_evolucao.py` | **A) Pode remover** | Script de criação de evolução. Não é importado por nenhum módulo. |
| `_inspect_db.py` | **A) Pode remover** | Script de inspeção de banco. Não é importado por nenhum módulo. |
| `_inspect_schema.py` | **A) Pode remover** | Script de inspeção de schema. Não é importado por nenhum módulo. |

### debug/

| Arquivo | Categoria | Motivo |
|---|---|---|
| `debug/99_Debug_OS.py` | **C) Arquivo de apoio** | Página Streamlit auxiliar para debug de OS. Pode ser útil. |
| `debug/diagnostico_classificacao.py` | **A) Pode remover** | Script de diagnóstico de classificação. Não é importado. |
| `debug/valida_v151.py` | **C) Arquivo de apoio** | Script de validação V1.5.1. Pode ser útil como referência. |

### legacy/

| Arquivo | Categoria | Motivo |
|---|---|---|
| `legacy/01_Base_Clientes.py` | **B) Deve manter** | Página removida da navegação. Mantida como referência. |
| `legacy/12_Acoes_Massa.py` | **B) Deve manter** | Funcionalidade descontinuada. Mantida como referência. |
| `legacy/30_Importar_Clientes.py` | **B) Deve manter** | Funcionalidade de importação descontinuada. |
| `legacy/31_Importar_Faturamento.py` | **B) Deve manter** | Funcionalidade de importação descontinuada. |
| `legacy/32_Importar_OS.py` | **B) Deve manter** | Funcionalidade de importação descontinuada. |
| `legacy/36_Pendencias_Cadastro.py` | **B) Deve manter** | Funcionalidade descontinuada. |

### services/ e tests/

Nenhum arquivo temporário encontrado nestes diretórios.

---

## Resumo

| Categoria | Quantidade |
|---|---|
| **A) Pode remover** | 5 arquivos |
| **B) Deve manter** | 6 arquivos |
| **C) Arquivo de apoio** | 2 arquivos |

> **Recomendação:** Os 5 arquivos categoria A podem ser removidos com segurança na V1.7.