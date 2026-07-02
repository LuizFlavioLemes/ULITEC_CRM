# Relatório da Estrutura Atual — ULITEC CRM v0.9.1 (Feature IA em desenvolvimento)

Data: 22/06/2026

---

## 1. Páginas do Sistema

| # | Arquivo | Módulo | Perfil Mínimo |
|---|---------|--------|---------------|
| 00 | `app.py` | Home / Boas-Vindas | Autenticado |
| 01 | `pages/00_Dashboard.py` | Dashboard Comercial | MASTER, GESTOR |
| 02 | `pages/01_Base_Clientes.py` | Base Mestre de Clientes | Autenticado |
| 03 | `pages/02_Cliente_360.py` | Cliente 360° | Autenticado |
| 04 | `pages/10_Central_Oportunidades.py` | Central de Oportunidades | Autenticado |
| 05 | `pages/11_Pipeline_OS.py` | Pipeline de Ordens de Serviço | Autenticado |
| 06 | `pages/12_Acoes_Massa.py` | Ações em Massa | Autenticado |
| 07 | `pages/15_Parque_Mitsubishi.py` | Parque Mitsubishi | Autenticado |
| 08 | `pages/30_Importar_Clientes.py` | Importar Clientes | MASTER, GESTOR |
| 09 | `pages/31_Importar_Faturamento.py` | Importar Faturamento | MASTER, GESTOR |
| 10 | `pages/32_Importar_OS.py` | Importar OS | MASTER, GESTOR |
| 11 | `pages/36_Pendencias_Cadastro.py` | Pendências de Cadastro | Autenticado |
| 12 | `pages/90_Administracao.py` | Administração | MASTER |
| 13 | `pages/99_Debug_OS.py` | Debug OS | MASTER |
| 14 | `pages/16_Base_Produtos_Importados.py` | Base Produtos Importados | Autenticado |

**Total: 15 páginas** (incluindo app.py como homepage)

---

## 2. Tabelas do Banco de Dados

| # | Tabela | Descrição |
|---|--------|-----------|
| 01 | `unidades` | Unidades/filiais (ULITEC SP, ULITEC RS) |
| 02 | `usuarios` | Usuários do sistema com perfis e autenticação |
| 03 | `clientes` | Cadastro mestre de clientes |
| 04 | `faturamento` | Registro de faturamento por cliente |
| 05 | `faturamento_itens` | Itens detalhados de faturamento |
| 06 | `ordens_servico` | Pipeline de ordens de serviço |
| 07 | `propostas` | Propostas comerciais |
| 08 | `oportunidades` | Oportunidades comerciais |
| 09 | `interacoes` | Histórico de interações com clientes |
| 10 | `maquinas_mitsubishi` | Parque de máquinas Mitsubishi |
| 11 | `conciliacao_mitsubishi` | Conciliação de máquinas x clientes |
| 12 | `alertas` | Alertas do sistema |
| 13 | `configuracoes` | Configurações gerais (chave/valor) |
| 14 | `produtos_importados` | Cadastro de produtos importados |
| 15 | `produtos_importados_historico` | Histórico de preços FOB de produtos importados |
| 16 | `ncm_importacao` | Classificação NCM para importação |
| 17 | `tipo_produto_importado` | Tipos de produto com alíquotas (II, IPI, PIS, COFINS, ICMS) |
| 18 | `config_importacao` | Configurações do módulo de importação |
| 19 | `config_ia` | Configuração da API OpenAI (chave, modelo) |
| 20 | `relatorios_ia` | Log de execuções de relatórios IA |

**Total: 20 tabelas**

---

## 3. Serviços

| # | Arquivo | Funções Exportadas |
|---|---------|-------------------|
| 01 | `services/mitsubishi.py` | 15 funções do módulo Mitsubishi |
| 02 | `services/ia/openai_client.py` | `testar_conexao`, `gerar_relatorio` |
| 03 | `services/ia/data_collector.py` | `coletar_cliente`, `coletar_faturamento`, `coletar_os`, `coletar_oportunidades`, `coletar_mitsubishi`, `coletar_interacoes` |
| 04 | `services/ia/prompt_builder.py` | `montar_contexto_cliente`, `PROMPT_SISTEMA` |
| 05 | `services/ia/engine.py` | `gerar_analise_cliente` |

**Total: 5 serviços** — 1 existente (Mitsubishi) + 4 novos do módulo IA.

---

## 4. Autenticação

- **Arquivo:** `auth.py`
- **Método:** `bcrypt` (hash de senhas)
- **Usuário padrão:** admin / Ulitec2026@ (MASTER)
- **Fluxo:** login → session_state → proteção via `verificar_acesso()`

### Perfis de Acesso

| Perfil | Nível |
|--------|-------|
| `MASTER` | Acesso total (administração, debug, importações) |
| `GESTOR` | Dashboard comercial, importações |
| `SOCIO` | Visão consolidada multiunidade |
| `OPERADOR` | Acesso operacional (clientes, OS, oportunidades) |

### Funções de Segurança

- `verificar_acesso(requer_login, perfis)` — Proteção de páginas
- `requer_login` — Decorator de autenticação
- `requer_perfil(*perfis)` — Decorator de perfil específico
- `sidebar_usuario()` — Exibição de usuário + logout

---

## 5. Permissões por Página

| Página | MASTER | GESTOR | SOCIO | OPERADOR |
|--------|--------|--------|-------|----------|
| Home (app.py) | ✅ | ✅ | ✅ | ✅ |
| Dashboard | ✅ | ✅ | ❌ | ❌ |
| Base Clientes | ✅ | ✅ | ✅ | ✅ |
| Cliente 360° | ✅ | ✅ | ✅ | ✅ |
| Central Oportunidades | ✅ | ✅ | ✅ | ✅ |
| Pipeline OS | ✅ | ✅ | ✅ | ✅ |
| Ações em Massa | ✅ | ✅ | ✅ | ✅ |
| Parque Mitsubishi | ✅ | ✅ | ✅ | ✅ |
| Importar Clientes | ✅ | ✅ | ❌ | ❌ |
| Importar Faturamento | ✅ | ✅ | ❌ | ❌ |
| Importar OS | ✅ | ✅ | ❌ | ❌ |
| Base Produtos Importados | ✅ | ✅ | ✅ | ✅ |
| Pendências Cadastro | ✅ | ✅ | ✅ | ✅ |
| Administração | ✅ | ❌ | ❌ | ❌ |
| Debug OS | ✅ | ❌ | ❌ | ❌ |

---

## 6. Módulos Concluídos

1. **Login** — Autenticação com bcrypt, perfis de acesso
2. **Multiunidade** — Segregação por filial (SP / RS / Grupo)
3. **Dashboard** — Indicadores comerciais, classificação ABC, sazonalidade
4. **Clientes** — Base mestre de clientes com busca e filtros
5. **Cliente 360°** — Visão completa do cliente com interações
6. **Pipeline OS** — Pipeline de ordens de serviço com estágios
7. **Importação OS** — Importação de OS a partir de planilhas
8. **Importação Faturamento** — Importação de faturamento de planilhas
9. **Central Oportunidades** — Gestão de oportunidades comerciais
10. **Mitsubishi Consolidado** — Parque Mitsubishi + conciliação
11. **Administração** — Backup, usuários, alertas, configurações
12. **Base Produtos Importados** — Cadastro, consulta, nacionalização e importação XLSX de produtos importados

13. **Relatórios IA (v1.0.0)** — Análise de cliente com IA integrada ao Cliente 360°

**Total: 13 módulos concluídos**

---

## 7. Tecnologias

- **Frontend:** Streamlit
- **Banco:** SQLite3
- **Gráficos:** Plotly, Plotly Express
- **Autenticação:** bcrypt
- **Fuzzy Matching:** rapidfuzz (conciliação Mitsubishi)
- **Análise:** Pandas, NumPy
- **IA:** OpenAI API (gpt-4o, gpt-4o-mini)
