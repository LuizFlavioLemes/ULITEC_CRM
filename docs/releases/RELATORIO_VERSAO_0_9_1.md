# Relatório de Versão — ULITEC CRM v0.9.1

**Data:** 19/06/2026

---

## Resumo

Esta versão conclui o **Módulo Base Produtos Importados**, consolidando o cadastro, consulta, nacionalização e importação de produtos importados via arquivos XLSX.

---

## Novidades da v0.9.1

### 1. Nova Página

| Arquivo | Módulo | Perfil |
|---------|--------|--------|
| `pages/16_Base_Produtos_Importados.py` | Base Produtos Importados | Autenticado |

Funcionalidades da página:
- Cadastro completo de produtos importados (modelo, descrição, tipo, NCM, fornecedor, FOB USD)
- Consulta e edição de produtos cadastrados
- Cálculo de nacionalização com alíquotas (II, IPI, PIS, COFINS, ICMS)
- Histórico de preços FOB por produto
- Importação em lote via upload de arquivo XLSX
- Normalização automática de modelos (busca por palavras-chave)

### 2. Novas Tabelas no Banco de Dados

| # | Tabela | Descrição |
|---|--------|-----------|
| 01 | `produtos_importados` | Cadastro de produtos importados |
| 02 | `produtos_importados_historico` | Histórico de preços FOB de produtos importados |
| 03 | `ncm_importacao` | Classificação NCM para importação |
| 04 | `tipo_produto_importado` | Tipos de produto com alíquotas (II, IPI, PIS, COFINS, ICMS) |
| 05 | `config_importacao` | Configurações do módulo de importação |

### 3. Alterações no Banco Existente

- Banco `crm.db` atualizado com as 5 novas tabelas
- Backup da versão criado: `backups/crm_v0_9_1.db`

---

## Estrutura Atualizada

- **Páginas:** 15 (era 14 na v0.9.0)
- **Tabelas:** 18 (era 13 na v0.9.0)
- **Serviços:** 1 (inalterado)
- **Módulos concluídos:** 12 (era 11 na v0.9.0)

---

## Arquivos da Versão

### Criados
- `pages/16_Base_Produtos_Importados.py` — Página do módulo
- `test_produtos_importados.py` — Testes automatizados do módulo
- `backups/crm_v0_9_1.db` — Backup do banco nesta versão

### Modificados
- `crm.db` — Adicionadas 5 novas tabelas
- `VERSAO.md` — Atualizado para v0.9.1 com módulo concluído
- `RELATORIO_ESTRUTURA.md` — Atualizado para refletir v0.9.1

---

## Testes

O módulo foi testado com sucesso via `test_produtos_importados.py`, cobrindo:
- Criação de produto
- Consulta de produto
- Edição de produto
- Exclusão de produto
- Cálculo de nacionalização
- Histórico de preços
- Importação XLSX
- Normalização de modelos

---

## Próximos Passos

- 🚧 **Módulo Relatórios IA** (em desenvolvimento)

---

**ULITEC CRM v0.9.1** — 19 de junho de 2026