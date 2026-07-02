# Changelog

Todas as mudanças notáveis deste projeto serão documentadas neste arquivo.

O formato segue [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

---

## [1.0.3] — 2026-07-02

### Added
- Módulo Central de Versionamento (`services/version.py`) — fonte única oficial da versão do sistema
- CHANGELOG.md seguindo padrão Keep a Changelog
- Aba "Informações da Instalação" na Administração (versão, build, ambiente, banco, python, data da release)
- Rodapé padronizado reutilizável em `components/ui.py` com versão e ambiente
- Infraestrutura preparada para futuras releases automáticas (tuplas de versão, check de versão mínima)

### Changed
- `config.py`: delega versão ao módulo central (`services/version.py`)
- `app.py`: utiliza rodapé padronizado do `components/ui.py`
- `VERSAO.md`: mantido como changelog narrativo/detalhado, sem duplicação de versão

### Fixed
- Eliminada duplicidade de versão — toda consulta passa exclusivamente por `services/version.py`

### Known Issues
- BUILD ainda é incrementado manualmente (CI/CD pipeline futuro automatizará)
- `VERSAO.md` e `CHANGELOG.md` coexistem — avaliar consolidação futura

---

## [1.0.2] — 2026-06-22

### Added
- Relacionamento Comercial: página exclusiva do vendedor com 5 abas (Agenda, Registrar Interação, Histórico, Pendências, Alertas)
- Inteligência Comercial: Score comercial, clientes esfriando/esquentando, análise de carteira
- Integração com Cliente 360° (aba Relacionamento, somente leitura)
- Integração com Central de Oportunidades (aba Relacionamento com KPIs e alertas)
- Configurações de frequência por classe (WhatsApp, E-mail, Ligação, Visita) na Administração
- Tabelas: `interacoes` (22 colunas), `pendencias_comerciais`

---

## [1.0.1] — 2026-06-01

### Added
- Mitsubishi Consolidado: Parque de máquinas + conciliação com clientes
- Base Produtos Importados: Cadastro, consulta, nacionalização, importação Excel
- Relatório IA (Groq / Gemini / OpenAI)
- Central de Oportunidades
- Gestão de Terceiros

---

## [1.0.0] — 2026-05-01

### Added
- Lançamento inicial do CRM Industrial ULITEC
- Autenticação com bcrypt e perfis de acesso (MASTER, SÓCIO, GERENTE, VENDEDOR)
- Multiunidade: segregação por filial (SP, RS, Grupo)
- Dashboard Executivo com indicadores ABC e sazonalidade
- Base Mestre de Clientes com busca e filtros
- Cliente 360° com interações, OS e propostas
- Pipeline de Ordens de Serviço por estágio
- Importação de OS via Excel
- Importação de Faturamento via Excel
- Importação de Clientes via Excel
- Pendências de Cadastro
- Administração: Backup do banco, gestão de usuários, alertas e configurações
- Ações em Massa