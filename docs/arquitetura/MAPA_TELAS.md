# MAPA DE TELAS — ULITEC CRM v1.6.9

## 1. Dashboard
- **Objetivo:** Exibir visão executiva com indicadores comerciais, financeiros e operacionais em tempo real.
- **Usuário principal:** Diretoria, Gerência Comercial, Gerência Operacional.
- **Fonte de dados:** `crm.db` — tabelas: `oportunidades`, `os`, `clientes`, `faturamento`, `produtos_importados`.
- **Dependências:** Módulo `inteligencia_comercial.py` para cálculos de score e métricas.

---

## 2. Cliente 360
- **Objetivo:** Visão unificada do cliente com dados cadastrais, financeiros, OS, oportunidades e relacionamento.
- **Usuário principal:** Comercial, Pós-vendas, Administrativo.
- **Fonte de dados:** `crm.db` — tabelas: `clientes`, `os`, `oportunidades`, `faturamento`, `interacoes`.
- **Dependências:** `services/relacionamento.py`, `services/inteligencia_comercial.py`.

---

## 3. Relacionamento Comercial
- **Objetivo:** Gerenciar interações com clientes, agendamentos e histórico de contato.
- **Usuário principal:** Equipe Comercial.
- **Fonte de dados:** `crm.db` — tabelas: `interacoes`, `clientes`, `oportunidades`.
- **Dependências:** `services/relacionamento.py`.

---

## 4. Central de Oportunidades
- **Objetivo:** Consolidar oportunidades comerciais, indicar ações prioritárias e exibir métricas.
- **Usuário principal:** Comercial, Gerência.
- **Fonte de dados:** `crm.db` — tabelas: `oportunidades`, `clientes`, `faturamento`.
- **Dependências:** `services/inteligencia_comercial.py`.

---

## 5. Pipeline OS
- **Objetivo:** Acompanhar ordens de serviço em andamento por etapa/filial.
- **Usuário principal:** Operacional, Pós-vendas.
- **Fonte de dados:** `crm.db` — tabela: `os`.
- **Dependências:** Nenhuma específica (consulta direta ao banco).

---

## 6. Parque Mitsubishi
- **Objetivo:** Gestão de máquinas Mitsubishi registradas, garantia e manutenção.
- **Usuário principal:** Pós-vendas, Operacional.
- **Fonte de dados:** `crm.db` — tabela: `maquinas_mitsubishi`.
- **Dependências:** `services/mitsubishi.py`.

---

## 7. Base Produtos Importados
- **Objetivo:** Catálogo de produtos importados com preços, estoque e fornecedores.
- **Usuário principal:** Importação, Comercial.
- **Fonte de dados:** `crm.db` — tabelas: `produtos_importados`, `pedidos_importacao`.
- **Dependências:** Nenhuma específica.

---

## 8. Centro Importações
- **Objetivo:** Gerenciar pedidos de importação, desembaraço e logística.
- **Usuário principal:** Equipe de Importação.
- **Fonte de dados:** `crm.db` — tabelas: `pedidos_importacao`, `produtos_importados`, `fornecedores`.
- **Dependências:** Nenhuma específica.

---

## 9. Administração
- **Objetivo:** Configurações do sistema, gestão de usuários, logs e parametrizações.
- **Usuário principal:** Administrador do sistema.
- **Fonte de dados:** `crm.db` — tabelas: `usuarios`, `configuracoes`, `logs`.
- **Dependências:** `auth.py`, `database.py`.

---

> **Total de telas ativas:** 9
> **Telas removidas:** Base Clientes (movida para `legacy/`)