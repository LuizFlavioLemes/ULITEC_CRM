# INVENTÁRIO DO BANCO DE DADOS — ULITEC CRM v1.6.9

## Resumo Executivo

| Item | Valor |
|---|---|
| **SGBD** | SQLite 3 |
| **Arquivo** | `crm.db` |
| **Total de tabelas** | 23 (incluindo `sqlite_sequence`) |
| **Total de registros** | ~10.000+ |

---

## Tabelas e finalidades

| Tabela | Registros | Finalidade |
|---|---|---|
| `clientes` | 840 | Cadastro de clientes — base principal do CRM |
| `faturamento` | 551 | Histórico de faturamento por cliente |
| `faturamento_itens` | 675 | Itens detalhados do faturamento |
| `ordens_servico` | 98 | Ordens de serviço em andamento e histórico |
| `maquinas_mitsubishi` | 6.829 | Máquinas Mitsubishi registradas — Parque Mitsubishi |
| `conciliacao_mitsubishi` | 1.094 | Dados de conciliação de máquinas |
| `interacoes` | 11 | Registro de interações comerciais (visitas, WhatsApp, etc.) |
| `pendencias_comerciais` | 8 | Pendências comerciais abertas |
| `evolucao_pendencias` | 4 | Evoluções e comentários em pendências |
| `oportunidades` | 2 | Oportunidades comerciais registradas |
| `produtos_importados` | 135 | Catálogo de produtos importados |
| `produtos_importados_historico` | 136 | Histórico de alterações em produtos importados |
| `ncm_importacao` | 28 | Códigos NCM para importação |
| `tipo_produto_importado` | 14 | Tipos/categorias de produtos importados |
| `config_importacao` | 5 | Configurações do módulo de importação |
| `configuracoes` | 0 | Configurações do sistema (relacionamento, frequências) |
| `config_ia` | 0 | Configurações do módulo de IA |
| `relatorios_ia` | 2 | Relatórios gerados por IA |
| `alertas` | 0 | Alertas do sistema |
| `propostas` | 0 | Propostas comerciais |
| `unidades` | 2 | Filiais/unidades (ULITEC SP, ULITEC RS) |
| `usuarios` | 2 | Usuários do sistema |
| `sqlite_sequence` | 18 | Controle interno de auto-increment |

---

## Observações

- **`configuracoes` com 0 registros** pode indicar que as configurações de relacionamento estão sendo gravadas em outra estrutura ou não foram persistidas.
- **`oportunidades` com apenas 2 registros** sugere subutilização do módulo de oportunidades.
- **`interacoes` com 11 registros** indica que o relacionamento comercial está em estágio inicial de adoção.
- **`maquinas_mitsubishi` (6.829 registros)** é a maior tabela — núcleo do Parque Mitsubishi.
- **Tabelas vazias**: `alertas`, `config_ia`, `configuracoes`, `propostas` — podem ser candidatas a revisão/limpeza.

> ⚠️ **Não alterar banco. Apenas documentação.**