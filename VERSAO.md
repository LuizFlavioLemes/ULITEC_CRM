# ULITEC CRM

**Versão 1.0.3**

---

## Módulos Concluídos

- ✅ **Login** — Autenticação com bcrypt e perfis de acesso
- ✅ **Multiunidade** — Segregação por filial (SP / RS / Grupo)
- ✅ **Dashboard** — Indicadores comerciais com classificação ABC e sazonalidade
- ✅ **Clientes** — Base mestre de clientes com busca e filtros
- ✅ **Cliente 360°** — Visão completa do cliente com interações, OS e propostas
- ✅ **Pipeline OS** — Pipeline de ordens de serviço por estágio
- ✅ **Importação OS** — Importação de OS a partir de planilhas Excel
- ✅ **Importação Faturamento** — Importação de faturamento de planilhas Excel
- ✅ **Central Oportunidades** — Gestão e acompanhamento de oportunidades comerciais
- ✅ **Mitsubishi Consolidado** — Parque de máquinas Mitsubishi + conciliação com clientes
- ✅ **Base Produtos Importados** — Cadastro, consulta, nacionalização e importação de produtos importados
- ✅ **Administração** — Backup do banco, gestão de usuários, alertas e configurações
- ✅ **Relacionamento Comercial** — Página principal do vendedor com agenda, registro de interações, histórico, pendências e alertas automáticos
- ✅ **Inteligência Comercial** — Score comercial, clientes esfriando/esquentando, análise de carteira

---

## Módulo Relacionamento Comercial (v1.0.3)

### Funcionalidades

- **Página exclusiva do vendedor** (`pages/06_Relacionamento_Comercial.py`) com 5 abas:
  - **Agenda** — Visão de Hoje, 7 dias, 30 dias com próximas ações, pendências e follow-ups
  - **Registrar Interação** — Formulário completo com 7 tipos de interação, assunto, resultado, campos industriais para Visita Presencial, pendências e oportunidades
  - **Histórico** — Consulta com filtros por cliente, tipo, responsável e período
  - **Pendências Comerciais** — Abertas, vencidas e concluídas com botão para concluir
  - **Alertas** — Automáticos baseados nas regras da Administração

### Regras de Negócio

- Toda interação exige **próxima ação** OU **status CONCLUIDA**
- Usuário ID é registrado em todas as interações para indicadores por vendedor
- Visita Presencial coleta dados industriais: máquinas, Mitsubishi, concorrentes, produção

### Integrações

- **Cliente 360°** — Aba "📞 Relacionamento" com histórico, pendências e próximas ações (somente leitura)
- **Central de Oportunidades** — Aba "📞 Relacionamento" com KPIs e alertas
- **Administração** — Configurações de frequência por classe (WhatsApp, E-mail, Ligação, Visita) salvas no banco

### Tabelas

- `interacoes` — 22 colunas (assunto, usuario_id, status_interacao, campos industriais)
- `pendencias_comerciais` — Pendências vinculadas a interações
- `configuracoes` — Parâmetros de frequência e alertas

---

**Data da versão:** 22 de junho de 2026

---

### Próximo Módulo (Em Desenvolvimento)

- 🚧 **Módulo Relatórios IA**