# MAPA DE SERVIÇOS — ULITEC CRM v1.6.9

## `services/__init__.py`
| Campo | Descrição |
|---|---|
| **Função** | Utilitário de formatação de dados de clientes |
| **`formatar_clientes_para_select(df)`** | Formata DataFrame de clientes em lista de rótulos "Razão Social - Cidade/UF" com dicionários de mapeamento |
| **Dependências** | pandas |
| **Consumido por** | Telas que usam selectbox de clientes |

---

## `services/relacionamento.py`
| Campo | Descrição |
|---|---|
| **Função** | Pilar de Relacionamento Comercial |
| **Principais funcionalidades** | Registro de interações, pendências, oportunidades, alertas, agenda, evoluções, timeline |
| **Tabelas BD** | `interacoes`, `pendencias_comerciais`, `evolucao_pendencias`, `oportunidades`, `clientes`, `configuracoes`, `ordens_servico` |
| **Funções públicas** | `registrar_interacao`, `get_historico_interacoes`, `get_agenda`, `criar_pendencia`, `get_pendencias`, `concluir_pendencia`, `atualizar_pendencia`, `reabrir_pendencia`, `get_pendencia_by_id`, `criar_oportunidade`, `get_alertas_relacionamento`, `get_indicadores_relacionamento`, `criar_evolucao_pendencia`, `get_evolucoes_pendencia`, `concluir_pendencia_com_evolucao`, `reabrir_pendencia_com_evolucao`, `get_proximas_acoes_consolidadas`, `get_contagem_proximas_acoes`, `get_ultimo_contato`, `get_pendencias_abertas_cliente`, `get_proximas_acoes_cliente`, `get_ultimos_eventos_cliente`, `get_timeline_unificada`, `get_contatos_conhecidos`, `get_config`, `set_config`, `salvar_configs_relacionamento`, `carregar_configs_relacionamento` |
| **Dependências** | sqlite3, pandas, datetime |
| **Consumido por** | `pages/02_Cliente_360.py`, `pages/06_Relacionamento_Comercial.py`, `pages/10_Central_Oportunidades.py`, `pages/00_Dashboard.py` |

---

## `services/inteligencia_comercial.py`
| Campo | Descrição |
|---|---|
| **Função** | Motor de inteligência comercial: scores, classificações ABC, métricas |
| **Principais funcionalidades** | Cálculo de score comercial, classificação ABCD, indicadores de desempenho |
| **Tabelas BD** | `clientes`, `faturamento`, `oportunidades`, `os`, `interacoes` |
| **Dependências** | sqlite3, pandas, numpy |
| **Consumido por** | `pages/00_Dashboard.py`, `pages/10_Central_Oportunidades.py`, `pages/02_Cliente_360.py` |

---

## `services/mitsubishi.py`
| Campo | Descrição |
|---|---|
| **Função** | Gestão do Parque Mitsubishi |
| **Principais funcionalidades** | CRUD de máquinas Mitsubishi, consultas, relatórios |
| **Tabelas BD** | `maquinas_mitsubishi` |
| **Dependências** | sqlite3, pandas |
| **Consumido por** | `pages/15_Parque_Mitsubishi.py` |

---

## `services/ia/` (pipeline de IA)

### `services/ia/__init__.py`
| Campo | Descrição |
|---|---|
| **Função** | Inicialização do módulo de IA |
| **Conteúdo** | Pacote vazio / inits |

### `services/ia/engine.py`
| Campo | Descrição |
|---|---|
| **Função** | Motor principal de IA para análise de clientes e oportunidades |
| **Dependências** | openai_client, prompt_builder, data_collector |
| **Consumido por** | `pages/02_Cliente_360.py` |

### `services/ia/prompt_builder.py`
| Campo | Descrição |
|---|---|
| **Função** | Montagem de prompts estruturados para OpenAI |
| **Dependências** | Nenhuma externa |

### `services/ia/openai_client.py`
| Campo | Descrição |
|---|---|
| **Função** | Cliente de comunicação com API OpenAI |
| **Dependências** | openai |

### `services/ia/data_collector.py`
| Campo | Descrição |
|---|---|
| **Função** | Coleta e preparação de dados contextuais para análise de IA |
| **Tabelas BD** | `clientes`, `faturamento`, `os`, `oportunidades`, `interacoes` |
| **Dependências** | sqlite3, pandas |

---

## Mapa de dependências entre serviços

```
pages/00_Dashboard.py ──────────────────────────────► inteligencia_comercial, relacionamento
pages/02_Cliente_360.py ──────► relacionamento, inteligencia_comercial, ia/engine
pages/06_Relacionamento_Comercial.py ──► relacionamento
pages/10_Central_Oportunidades.py ──► inteligencia_comercial, relacionamento
pages/11_Pipeline_OS.py ──► database.py (consulta direta)
pages/15_Parque_Mitsubishi.py ──► mitsubishi
pages/16_Base_Produtos_Importados.py ──► database.py (consulta direta)
pages/30_Centro_Importacoes.py ──► database.py (consulta direta)
pages/90_Administracao.py ──► auth.py, database.py
```

> **Total de módulos de serviço:** 5 principais + 4 submódulos de IA