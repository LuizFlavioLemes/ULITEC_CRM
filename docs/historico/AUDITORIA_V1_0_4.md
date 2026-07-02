# Auditoria de Estabilização — ULITEC CRM v1.0.4

> **Data:** 22 de Junho de 2026  
> **Propósito:** Auditar estrutura, identificar código morto, arquivos órfãos, imports quebrados, tabelas não utilizadas e propor plano de limpeza antes de executar exclusões.

---

## Sumário

1. [Snapshot de Segurança](#1-snapshot-de-segurança)
2. [Estrutura de Arquivos](#2-estrutura-de-arquivos)
3. [Imports e Dependências](#3-imports-e-dependências)
4. [Navegação e Páginas Acessíveis](#4-navegação-e-páginas-acessíveis)
5. [Tabelas e Colunas do Banco](#5-tabelas-e-colunas-do-banco)
6. [Scripts Temporários e Código Morto](#6-scripts-temporários-e-código-morto)
7. [Funcionalidades Não Implementadas / Pendentes](#7-funcionalidades-não-implementadas--pendentes)
8. [Plano de Limpeza Proposto](#8-plano-de-limpeza-proposto)

---

## 1. Snapshot de Segurança

### Criado em 22/06/2026 15:25
| Recurso | Arquivo |
|---------|---------|
| Banco de dados | `backups/crm_backup_v1.0.3_audit_20260622_152555.db` |
| Código fonte | `backups/source_snapshot_20260622_152555.tar.gz` |

---

## 2. Estrutura de Arquivos

### 2.1 Arquivos .py (31 arquivos)

| Categoria | Arquivos |
|-----------|----------|
| **Raiz** (6) | `app.py`, `auth.py`, `database.py`, `diagnostico_ic.py` |
| **Páginas** (15) | `00_Dashboard` a `99_Debug_OS` |
| **Services** (8) | `__init__.py`, `inteligencia_comercial.py`, `mitsubishi.py`, `relacionamento.py`, `ia/__init__.py`, `ia/data_collector.py`, `ia/engine.py`, `ia/openai_client.py`, `ia/prompt_builder.py` |
| **Testes** (3) | `test_cliente360_ia.py`, `test_inteligencia_comercial.py`, `test_produtos_importados.py` |
| **Auditoria** (2) | `audit_banco.py` ⚠️, `audit_completo.py` ⚠️ (criados durante esta auditoria) |

### 2.2 Documentação (5 arquivos)
- `VERSAO.md` — Versão atual do projeto
- `RELATORIO_ESTRUTURA.md` — Relatório de estrutura
- `RELATORIO_VERSAO_0_9_1.md`, `RELATORIO_VERSAO_1_0_0.md`, `RELATORIO_VERSAO_1_0_3.md` — Histórico de versões
- `docs/ARQUITETURA_RELATORIOS_IA.md` — Documentação do módulo IA (não implementado)

### 2.3 Planilhas (6 arquivos)
- `relatórios para integração/` — 6 arquivos `.xlsx` (base clientes, máquinas Mitsubishi, OS RS/SP, vendas RS/SP)

---

## 3. Imports e Dependências

### ✅ Todos os imports internos estão resolvidos
Nenhum import quebrado encontrado entre os módulos do projeto.

### 📦 Bibliotecas externas utilizadas
| Biblioteca | Uso |
|------------|-----|
| `streamlit` | Framework web |
| `pandas` | DataFrames |
| `sqlite3` | Banco de dados |
| `bcrypt` | Hash de senhas |
| `plotly` | Gráficos |
| `numpy` | Cálculos de tendência/sazonalidade |
| `openpyxl` | Leitura de planilhas |
| `rapidfuzz` | Fuzzy matching (conciliação Mitsubishi) |
| `openai` | API OpenAI (módulo IA) |

### ⚠️ Observações
- `py_compile` importado em `test_inteligencia_comercial.py` — biblioteca padrão Python
- `audit_completo.py` importa `ast` — biblioteca padrão Python (script temporário)

---

## 4. Navegação e Páginas Acessíveis

### ✅ Todas as 15 páginas são acessíveis via navegação automática do Streamlit

| # | Página | Acessível | Observação |
|---|--------|-----------|------------|
| 1 | `00_Dashboard.py` | ✅ | Apenas MASTER/GESTOR |
| 2 | `01_Base_Clientes.py` | ✅ | Todos os perfis |
| 3 | `02_Cliente_360.py` | ✅ | Todos os perfis |
| 4 | `06_Relacionamento_Comercial.py` | ✅ | Todos os perfis |
| 5 | `10_Central_Oportunidades.py` | ✅ | Todos os perfis |
| 6 | `11_Pipeline_OS.py` | ✅ | Todos os perfis |
| 7 | `12_Acoes_Massa.py` | ✅ | Todos os perfis |
| 8 | `15_Parque_Mitsubishi.py` | ✅ | Todos os perfis |
| 9 | `16_Base_Produtos_Importados.py` | ✅ | Todos os perfis |
| 10 | `30_Importar_Clientes.py` | ✅ | Apenas MASTER |
| 11 | `31_Importar_Faturamento.py` | ✅ | Apenas MASTER |
| 12 | `32_Importar_OS.py` | ✅ | Apenas MASTER |
| 13 | `36_Pendencias_Cadastro.py` | ✅ | Apenas MASTER/GESTOR |
| 14 | `90_Administracao.py` | ✅ | Apenas MASTER |
| 15 | `99_Debug_OS.py` | ✅ | Todos os perfis (⚠️ página de debug) |

### ⚠️ Página 99_Debug_OS.py
Página de debug que exibe dados brutos de OS. **Deve ser removida ou restrita em produção.**

---

## 5. Tabelas e Colunas do Banco

### 5.1 Todas as 21 tabelas têm referência no código ✅

| Tabela | Registros | Referências | Status |
|--------|-----------|-------------|--------|
| `alertas` | **0** | 6 arquivos | ⚠️ **Órfã** — tabela criada mas nunca populada |
| `clientes` | — | 23 arquivos | ✅ Ativa |
| `conciliacao_mitsubishi` | — | 3 arquivos | ✅ Ativa |
| `config_ia` | — | 3 arquivos | ✅ Ativa |
| `config_importacao` | — | 3 arquivos | ✅ Ativa |
| `configuracoes` | — | 3 arquivos | ✅ Ativa |
| `faturamento` | — | 18 arquivos | ✅ Ativa |
| `faturamento_itens` | **675** | 4 arquivos | ⚠️ **Possível redundância** com `faturamento` |
| `interacoes` | — | 10 arquivos | ✅ Ativa |
| `maquinas_mitsubishi` | — | 10 arquivos | ✅ Ativa |
| `ncm_importacao` | — | 3 arquivos | ✅ Ativa |
| `oportunidades` | — | 12 arquivos | ✅ Ativa |
| `ordens_servico` | — | 11 arquivos | ✅ Ativa |
| `pendencias_comerciais` | — | 2 arquivos | ✅ Ativa |
| `produtos_importados` | — | 3 arquivos | ✅ Ativa |
| `produtos_importados_historico` | — | 3 arquivos | ✅ Ativa |
| `propostas` | **0** | 6 arquivos | ⚠️ **Redundante** — `ordens_servico` já cobre propostas |
| `relatorios_ia` | — | 3 arquivos | ✅ Ativa |
| `tipo_produto_importado` | — | 3 arquivos | ✅ Ativa |
| `unidades` | — | 13 arquivos | ✅ Ativa |
| `usuarios` | — | 4 arquivos | ✅ Ativa |

### 5.2 Tabelas Candidatas à Remoção

#### 🟡 `alertas` (0 registros)
- Criada mas **nunca populada**
- A funcionalidade de alertas foi implementada via `get_alertas_relacionamento()` que usa consultas dinâmicas, não esta tabela
- **Ação proposta:** Remover tabela

#### 🟡 `propostas` (0 registros)
- Parece ser uma tabela legada do v0.9.1
- Toda a gestão de propostas está centralizada em `ordens_servico` (colunas: `valor_proposta`, `data_envio_proposta`, `data_aprovacao`, `status`)
- **Ação proposta:** Remover tabela

#### 🟡 `faturamento_itens` (675 registros)
- Contém dados de faturamento em nível de item
- Apenas 4 arquivos referenciam (vs 18 para `faturamento`)
- Pode ser que nenhuma página atual acesse ativamente (apenas importação)
- **Ação proposta:** Investigar antes de remover

### 5.3 Colunas Potencialmente Não Utilizadas em `clientes`
Nenhuma coluna encontrada com zero referências (varredura textual).

---

## 6. Scripts Temporários e Código Morto

### 🟢 Pode Remover Imediatamente
| Arquivo | Motivo |
|---------|--------|
| `audit_banco.py` | **Criado durante esta auditoria** — temporário |
| `audit_completo.py` | **Criado durante esta auditoria** — temporário |

### 🟡 Investigar Antes de Remover
| Arquivo | Motivo |
|---------|--------|
| `diagnostico_ic.py` | Script de diagnóstico da inteligência comercial. Não é página nem service. **Provavelmente temporário** |
| `test_cliente360_ia.py` | Testes unitários do módulo IA |
| `test_inteligencia_comercial.py` | Testes unitários da inteligência comercial |
| `test_produtos_importados.py` | Teste de normalização de modelos |
| `pages/99_Debug_OS.py` | Página de debug exposta no menu — **risco em produção** |

### 🔴 Manter (Documentação)
| Arquivo | Motivo |
|---------|--------|
| `docs/ARQUITETURA_RELATORIOS_IA.md` | Especificação do próximo módulo (Relatórios IA) |
| `relatórios para integração/*.xlsx` | Dados de entrada para importação |

### 🔴 Manter (Relatórios de Versão)
| Arquivo | Motivo |
|---------|--------|
| `RELATORIO_ESTRUTURA.md` | Documentação histórica |
| `RELATORIO_VERSAO_0_9_1.md` | Histórico de versões |
| `RELATORIO_VERSAO_1_0_0.md` | Histórico de versões |
| `RELATORIO_VERSAO_1_0_3.md` | Histórico de versões |
| `VERSAO.md` | Versão atual |

---

## 7. Funcionalidades Não Implementadas / Pendentes

### 🚧 Módulo Relatórios IA (mencionado em VERSAO.md)
- Estrutura de diretórios criada: `services/ia/`
- Models criados: `data_collector.py`, `engine.py`, `openai_client.py`, `prompt_builder.py`
- Testes criados: `test_cliente360_ia.py`
- Documentação: `docs/ARQUITETURA_RELATORIOS_IA.md`
- **Não integrado em nenhuma página como funcionalidade independente** (apenas embutido no Cliente 360°)
- **Status:** Parcialmente implementado, aguardando conclusão

### ⚠️ Módulo Inteligência Comercial
- `diagnostico_ic.py` parece ser um script de diagnóstico avulso
- `test_inteligencia_comercial.py` contém testes mas o módulo `services/inteligencia_comercial.py` está ativo e integrado

---

## 8. Plano de Limpeza Proposto

### Fase 1 — Segurança (JÁ EXECUTADO ✅)
- [x] Snapshot do banco de dados
- [x] Snapshot do código fonte

### Fase 2 — Remoção Segura (AUTORIZAÇÃO NECESSÁRIA)
- [ ] **Remover** `audit_banco.py` — Script temporário criado durante auditoria
- [ ] **Remover** `audit_completo.py` — Script temporário criado durante auditoria
- [ ] **Remover** `pages/99_Debug_OS.py` — Página de debug exposta em produção
- [ ] **Remover** `diagnostico_ic.py` — Script de diagnóstico avulso

### Fase 3 — Limpeza de Banco (AUTORIZAÇÃO NECESSÁRIA)
- [ ] **DROP TABLE `alertas`** — Tabela nunca populada (0 registros)
- [ ] **DROP TABLE `propostas`** — Tabela redundante com `ordens_servico` (0 registros)
- [ ] **Avaliar `faturamento_itens`** — Verificar se é acessada por alguma página atualmente

### Fase 4 — Manutenção de Testes (AUTORIZAÇÃO NECESSÁRIA)
- [ ] **Avaliar** `test_cliente360_ia.py` — Manter se o módulo IA for prioridade, remover se cancelado
- [ ] **Avaliar** `test_inteligencia_comercial.py` — Testes unitários válidos, recomendado manter
- [ ] **Avaliar** `test_produtos_importados.py` — Apenas 1 função de teste, pode ser integrado

### Fase 5 — Gestão de Dados (AUTORIZAÇÃO NECESSÁRIA)
- [ ] **Avaliar** `relatórios para integração/*.xlsx` — Mover para storage externo se não forem mais necessários como input recorrente

---

## Resumo Final

| Categoria | Qtde | Ação Recomendada |
|-----------|------|------------------|
| Scripts temporários da auditoria | **2** | **Remover imediatamente** |
| Scripts de debug/diagnóstico | **2** | **Remover** (diagnostico_ic.py, 99_Debug_OS.py) |
| Tabelas órfãs (0 registros) | **2** | **DROP** (alertas, propostas) |
| Tabela sob avaliação | **1** | Investigar (faturamento_itens) |
| Testes unitários | **3** | Manter ou integrar |
| Documentação | **5** | Manter |
| Planilhas de integração | **6** | Avaliar necessidade contínua |

---

**Próximo passo:** Aguardar autorização para executar as exclusões propostas na Fase 2 em diante.