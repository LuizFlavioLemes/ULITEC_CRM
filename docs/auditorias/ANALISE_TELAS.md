# ANÁLISE DE TELAS — ULITEC CRM V1.6

**Data:** 24/06/2026
**Etapa:** 3 — Revisão de Telas

---

## Classificação

| Categoria | Significado |
|-----------|-------------|
| **ESSENCIAL** | Núcleo do sistema, uso frequente, remove = quebra funcionalidade principal |
| **ÚTIL** | Agrega valor, mas não crítica para operação |
| **REDUNDANTE** | Sobreposição com outra tela |
| **OBSOLETA** | Sem uso ou substituída |

---

## 1. Dashboard (`00_Dashboard.py`) — **ESSENCIAL**

**Função:** Painel executivo com indicadores de desempenho, faturamento, sazonalidade, classificação ABC, tendências.

**Por que é essencial:** É a página inicial do CRM. Consolidado de métricas para tomada de decisão.

**Dependências:** `database.py`, `auth.py`

**Riscos:** Nenhum. Estável.

---

## 2. Base Clientes (`01_Base_Clientes.py`) — **ESSENCIAL**

**Função:** Cadastro mestre de clientes com busca por razão social, nome fantasia ou CNPJ. Filtro por unidade (filial).

**Funcionalidades exclusivas:**
- Consulta pública de clientes cadastrados
- Busca textual com filtro OR
- Separação por origem ERP (SP/RS)

**Dependências:** `database.py`, `auth.py`

**Sobreposição com Cliente 360:** NÃO. Base Clientes é uma listagem master. Cliente 360 é detalhamento individual. Não há redundância — são complementares.

**Riscos:** Nenhum. Página leve, 59 linhas.

---

## 3. Cliente 360 (`02_Cliente_360.py`) — **ESSENCIAL**

**Função:** Visão completa do cliente com faturamento, OS, oportunidades, interações, timeline unificada, e análise por IA.

**Funcionalidades exclusivas:**
- Seleção de cliente + visão 360°
- Dashboard de faturamento histórico
- Timeline de eventos
- Análise com IA integrada
- Relacionamento comercial embutido

**Dependências:** `database.py`, `auth.py`, `services/relacionamento.py`, `services/ia/*`

**Observação:** Página mais complexa (740 linhas). Integra múltiplos serviços.

**Riscos:** Depende de OpenAI para IA — se API falhar, análise trava.

---

## 4. Relacionamento Comercial (`06_Relacionamento_Comercial.py`) — **ESSENCIAL**

**Função:** Página principal do vendedor. Agenda, registro de interações, histórico, pendências, alertas.

**Funcionalidades exclusivas:**
- Agenda de ações (7/30 dias)
- Registro de interações com 7 tipos
- Gestão de pendências comerciais
- Alertas automáticos

**Dependências:** `database.py`, `auth.py`, `services/relacionamento.py`

**Observação:** Página mais extensa (972 linhas). Módulo mais recente e mais usado no dia-a-dia.

**Riscos:** Página densa. Complexidade alta de manutenção.

---

## 5. Central Oportunidades (`10_Central_Oportunidades.py`) — **ESSENCIAL**

**Função:** Gestão de oportunidades comerciais com múltiplas fontes de dados.

**Funcionalidades exclusivas:**
- Consolidação de oportunidades
- Pipeline visual
- Alertas e follow-up
- Classificação ABCD

**Dependências:** `database.py`, `auth.py`, `services/relacionamento.py`

**Riscos:** Integra múltiplas fontes — qualquer falha em fonte externa impacta.

---

## 6. Pipeline OS (`11_Pipeline_OS.py`) — **ÚTIL**

**Função:** Pipeline de ordens de serviço por estágio.

**Funcionalidades exclusivas:**
- Visualização de OS por estágio
- Filtros por cliente/período

**Observação:** Dados vêm de importação de planilhas. Valor operacional, mas não crítico para comercial.

**Riscos:** Baixo.

---

## 7. Parque Mitsubishi (`15_Parque_Mitsubishi.py`) — **ÚTIL**

**Função:** Parque de máquinas Mitsubishi + conciliação com clientes.

**Dependências:** `database.py`, `auth.py`, `services/mitsubishi.py`

**Observação:** Dado específico (clientes com máquinas Mitsubishi). Útil para prospecção industrial.

**Riscos:** Baixo.

---

## 8. Base Produtos Importados (`16_Base_Produtos_Importados.py`) — **ÚTIL**

**Função:** Cadastro, consulta e nacionalização de produtos importados.

**Dependências:** `database.py`, `auth.py`

**Observação:** Tabela separada no banco. Funcionalidade específica para operações de importação.

**Riscos:** Baixo.

---

## 9. Centro Importações (`30_Centro_Importacoes.py`) — **REDUNDANTE (parcial)**

**Função:** Centro de importações (comercial).

**Observação:** Possível sobreposição com `16_Base_Produtos_Importados.py`. Ambas tratam de importação, mas com ênfases diferentes (operacional vs cadastro). Vale avaliar consolidação futura.

**Riscos:** Baixo. Pode confundir usuários sobre onde registrar dados de importação.

---

## 10. Administração (`90_Administracao.py`) — **ESSENCIAL**

**Função:** Backup do banco, gestão de usuários, alertas e configurações.

**Funcionalidades exclusivas:**
- Gestão de usuários (CRUD)
- Backup manual do banco
- Configurações de frequência por classe
- Regras de alertas

**Dependências:** `database.py`, `auth.py`

**Riscos:** Crítico para segurança do sistema (gestão de usuários). Backup depende de permissões de escrita.

---

## Resumo Final

| Tela | Classificação | Complexidade | Risco |
|------|---------------|-------------|-------|
| Dashboard | ESSENCIAL | Média | Baixo |
| Base Clientes | ESSENCIAL | Baixa | Baixo |
| Cliente 360 | ESSENCIAL | Alta | Médio (IA) |
| Relacionamento Comercial | ESSENCIAL | Alta | Médio |
| Central Oportunidades | ESSENCIAL | Alta | Médio |
| Pipeline OS | ÚTIL | Média | Baixo |
| Parque Mitsubishi | ÚTIL | Baixa | Baixo |
| Base Produtos Importados | ÚTIL | Baixa | Baixo |
| Centro Importações | **REDUNDANTE (parcial)** | Baixa | Baixo |
| Administração | ESSENCIAL | Média | Alto (segurança) |

**Telas ESSENCIAIS:** 6
**Telas ÚTEIS:** 3
**Telas REDUNDANTES:** 1 (parcial)

---

## Atenção Especial: Base Clientes

**Funcionalidades exclusivas:**
- Listagem mestre com busca textual
- Filtro por unidade ERP

**Dependências:**
- Nenhuma página depende dela (é consulta apenas)
- Cliente 360 consome a mesma tabela `clientes`, mas não depende desta página

**Uso real:** Alta — é a porta de entrada para consulta de clientes.

**Sobreposição:** NENHUMA. Base Clientes é listagem; Cliente 360 é detalhe. Complementares.

**Recomendação:** MANTER.

---

*Nenhuma alteração foi feita. Apenas análise documental.*