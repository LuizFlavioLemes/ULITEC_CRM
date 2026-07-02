# AUDITORIA GERAL — ULITEC CRM V1.6

**Data:** 24/06/2026

## 1. Visão Geral

- Total de arquivos .py: **41**
- Páginas (Streamlit): **10**
- Serviços: **9**
- Debug/Diagnóstico: **3**
- Testes: **3**
- Documentos .md: **20**
- Arquivos Legacy: **5**
- Backups: **14**
- Scripts temporários/inspect: **8**
- Banco SQLite (crm.db): **EXISTE**

## 2. Estrutura do Sistema

### Páginas (9 pages)
- `00_Dashboard.py` — Dashboard executivo com indicadores
- `01_Base_Clientes.py` — Cadastro mestre de clientes
- `02_Cliente_360.py` — Visão completa do cliente
- `06_Relacionamento_Comercial.py` — Página do vendedor
- `10_Central_Oportunidades.py` — Gestão de oportunidades
- `11_Pipeline_OS.py` — Pipeline de ordens de serviço
- `15_Parque_Mitsubishi.py` — Parque de máquinas
- `16_Base_Produtos_Importados.py` — Produtos importados
- `30_Centro_Importacoes.py` — Centro de importações
- `90_Administracao.py` — Administração do sistema

### Serviços (4)
- `services/relacionamento.py` — Regras de relacionamento comercial
- `services/mitsubishi.py` — Lógica do parque Mitsubishi
- `services/inteligencia_comercial.py` — Score e análise de carteira
- `services/ia/` — Módulo de IA (engine, openai_client, prompt_builder, data_collector)

### Infraestrutura
- `app.py` — Entry point Streamlit
- `auth.py` — Autenticação
- `database.py` — Conexão com banco
- `crm.db` — Banco SQLite

## 3. Versão Atual

- Tag: **V1.0.3** (conforme VERSAO.md)
- Módulos instalados: 13 módulos concluídos
- Último módulo: Inteligência Comercial
- Próximo módulo (planejado): Relatórios IA

## 4. Backups Disponíveis

- Total de backups: 14
- Backups históricos e automáticos disponíveis
- Pasta `backups/` com snapshots anteriores

## 5. Arquivos Temporários/Diagnóstico

- `_check_db.py`
- `_create_evolucao.py`
- `_inspect_db.py`
- `_inspect_schema.py`
- `_temp_auditoria_geral.py`
- `_temp_deps.py`
- `_temp_estrutura.py`
- `_temp_schema_export.py`
---

*Documento gerado automaticamente — auditoria V1.6*
