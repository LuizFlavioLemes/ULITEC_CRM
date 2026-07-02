# 🔍 Auditoria Pré-Deploy Cloud — ULITEC CRM

**Data:** 01/07/2026  
**Versão do CRM:** 1.0.3 (constante em admin_sistema.py)  
**Ambiente alvo:** Linux (cPanel) + Python Application  
**Banco:** SQLite (`crm.db`)  
**Framework:** Streamlit  

---

## 📋 1 — CAMINHOS ABSOLUTOS

### ✔️ Status: NENHUMA ocorrência de `C:\` encontrada

Nenhum arquivo `.py` contém caminho absoluto no formato `C:\`, `C:\\`, `C:/ULITEC`, ou similar. Todos os caminhos para `crm.db` são relativos no formato `"crm.db"` (string simples, sem path).

| Arquivo | Linha | Ocorrência | Crítica |
|---------|-------|------------|---------|
| `auth.py` | 8 | `DB_PATH = "crm.db"` | BAIXO |
| `database.py` | 6 | `sqlite3.connect("crm.db")` | BAIXO |
| `services/ia/engine.py` | 21 | `DB_PATH = "crm.db"` | BAIXO |
| `services/ia/data_collector.py` | 11 | `DB_PATH = "crm.db"` | BAIXO |
| `services/inteligencia_comercial.py` | 59 | `sqlite3.connect("crm.db")` | BAIXO |
| `services/relacionamento.py` | 83 | `sqlite3.connect("crm.db")` | BAIXO |
| `services/mitsubishi.py` | 6 | `DB_PATH = "crm.db"` | BAIXO |
| `services/admin_sistema.py` | 29 | `DB_PATH = Path("crm.db")` | BAIXO |

### ⚠️ Problema detectado em `services/ia/ia_client.py`:

| Linha | Código | Problema |
|-------|--------|----------|
| 28 | `os.getcwd()` | `print()` de diagnóstico que revela diretório atual. Deve ser removido em produção. |

**Recomendação:** O uso de `"crm.db"` como caminho relativo funciona em Linux desde que o working directory seja a raiz do projeto. No cPanel, a Python Application define o diretório de trabalho corretamente. **BAIXO risco.**

---

## 📋 2 — BANCO DE DADOS

### Localização do banco

O arquivo `crm.db` é localizado por **caminho relativo** em TODOS os 8 pontos de acesso. Não há resolução absoluta, o que é compatível com Linux.

### Quem abre conexão

| Módulo | Função | Arquivo | Linha |
|--------|--------|---------|-------|
| `database.py` | `criar_banco()` | `database.py` | 6 |
| `auth.py` | `get_conn()` | `auth.py` | 12 |
| `auth.py` | `init_auth()` | `auth.py` | 17, 184 |
| `services/ia/engine.py` | `_salvar_log()` | `engine.py` | 33 |
| `services/ia/data_collector.py` | `_get_conn()` | `data_collector.py` | 15 |
| `services/inteligencia_comercial.py` | `_get_conn()` | `inteligencia_comercial.py` | 59 |
| `services/relacionamento.py` | `_get_conn()` | `relacionamento.py` | 83 |
| `services/mitsubishi.py` | `_get_conn()` | `mitsubishi.py` | 10 |
| `services/admin_sistema.py` | `obter_status_sistema()` | `admin_sistema.py` | 169 |
| `services/admin_sistema.py` | `_obter_conn()` | `admin_sistema.py` | 794 |
| `pages/00_Dashboard.py` | `sqlite3.connect(` | `00_Dashboard.py` | ~3 |

### Quem cria o arquivo

| Arquivo | Função | Descrição |
|---------|--------|-----------|
| `database.py` | `criar_banco()` | Cria TODAS as tabelas via `CREATE TABLE IF NOT EXISTS` |

**OBS:** `criar_banco()` só é executada se `database.py` for chamado diretamente (`__name__ == "__main__"`). O banco **já existe** no repositório. Em cloud novo, o `init_auth()` em `auth.py` adiciona colunas, mas não cria tabelas. É necessário garantir que `criar_banco()` seja chamado ou que o banco seja copiado.

### ⚠️ Crítico: Falta modo WAL

**NENHUM arquivo configura `PRAGMA journal_mode=WAL`.**  
SQLite em modo padrão (DELETE/journal) no Linux pode sofrer com concorrência entre múltiplas threads do Streamlit.

| Arquivo | Problema |
|---------|----------|
| TODOS | Nenhum `conn.execute("PRAGMA journal_mode=WAL")` |

**Recomendação:** Adicionar `PRAGMA journal_mode=WAL` em todas as funções `_get_conn()`.

---

## 📋 3 — PASTAS UTILIZADAS PELO SISTEMA

| Pasta | Caminho | Quem Cria | Uso | Auto-Cria? |
|-------|---------|-----------|-----|------------|
| `backups/` | `Path("backups")` | `admin_sistema.py:268` | Backup do banco | ✅ `mkdir(exist_ok=True)` |
| `backups/export/` | `Path("backups/export")` | `admin_sistema.py:342` | Exportação .zip | ✅ `mkdir(exist_ok=True)` |
| `backups/manifestos/` | `Path("backups/manifestos")` | `admin_sistema.py:269` | Manifestos JSON | ✅ `mkdir(exist_ok=True)` |
| `logs/` | — | ❌ NÃO criada | Diretório vazio no repositório | ❌ Não criada automaticamente |
| `backup/` | — | ❌ Manual | Backups antigos (legado) | ❌ Não criada |

**Pastas que DEPENDEM de existir previamente:** NENHUMA. As 3 pastas essenciais (`backups/`, `backups/export/`, `backups/manifestos/`) são criadas automaticamente.

**Pasta `logs/`:** Existe no repositório mas está vazia. Nenhum código escreve nela. **BAIXO risco.**

**Pasta `relatórios para integração/`:** Pasta com arquivos `.xlsx` de dados. Não é criada/gerida por código. **Fora do escopo do deploy.**

**Pasta `tests/`:** Testes unitários. Não são executados automaticamente. **Sem impacto no deploy.**

**Pasta `debug/`:** Scripts de diagnóstico. **Sem impacto no deploy.**

**Pasta `legacy/`:** Código obsoleto. **Sem impacto no deploy.**

---

## 📋 4 — ARQUIVOS GRAVADOS EM DISCO

| Arquivo | Função | Tipo | Destino |
|---------|--------|------|---------|
| `admin_sistema.py:276` | `gerar_backup_completo()` | `shutil.copy2` | `backups/crm_backup_*.db` |
| `admin_sistema.py:300` | `gerar_backup_completo()` | `open(...,"w")` | `backups/manifestos/manifesto_*.json` |
| `admin_sistema.py:378` | `exportar_backup_compactado()` | `zipfile.ZipFile` | `backups/export/ULITEC_CRM_BACKUP_*.zip` |
| `admin_sistema.py:385` | `exportar_backup_compactado()` | `zf.writestr` | Manifesto dentro do .zip |
| `admin_sistema.py:391` | `exportar_backup_compactado()` | `zf.writestr` | Versionamento dentro do .zip |
| `admin_sistema.py:408` | `exportar_backup_compactado()` | `zf.writestr` | `RESTAURAR.txt` dentro do .zip |

**TOTAL: 6 pontos de escrita em disco.** Todos estão centralizados em `services/admin_sistema.py`. Nenhum outro arquivo escreve em disco (apenas leitura do SQLite).

---

## 📋 5 — DEPENDÊNCIAS

### ⚠️ CRÍTICO: `requirements.txt` NÃO EXISTE

O projeto **não possui arquivo `requirements.txt`**. O cPanel Python Application exige este arquivo para instalar dependências. É o item mais crítico para o deploy.

### Bibliotecas realmente utilizadas (por import nos .py):

| Biblioteca | Usada por | Categoria |
|------------|-----------|-----------|
| `streamlit` | `app.py`, `auth.py`, `permissions.py`, `pages/*`, `components/*` | Core |
| `sqlite3` | `database.py`, `auth.py`, `services/*`, `pages/*` | Core (builtin) |
| `pandas` | `services/*`, `pages/*` | Core |
| `bcrypt` | `auth.py` | Core |
| `python-dotenv` | `app.py`, `services/ia/ia_client.py` | Core |
| `google-generativeai` | `services/ia/gemini_client.py` | IA |
| `openai` | `services/ia/openai_client.py` | IA |
| `rapidfuzz` | `services/mitsubishi.py` | Mitsubishi |
| `openpyxl` (implícito) | `services/mitsubishi.py` (`pd.read_excel`) | Importação |
| `plotly` | `pages/00_Dashboard.py` | Dashboard |
| `numpy` | `services/inteligencia_comercial.py` | Inteligência |
| `groq` (implícito) | `services/ia/groq_client.py` (referenciado mas não lido) | IA |

### Biblioteca referenciada mas arquivo NÃO encontrado:

| Biblioteca | Arquivo esperado | Status |
|------------|-----------------|--------|
| `groq` | `services/ia/groq_client.py` | ❌ Arquivo NÃO existe no disco |

`ia_client.py` linha 117 faz `from services.ia.groq_client import gerar_relatorio` — mas `services/ia/groq_client.py` **NÃO EXISTE**. O `.env` define `IA_PROVIDER=GROQ`. Isso quebrará em runtime.

### Resumo:

| Situação | Qtd |
|----------|-----|
| Utilizadas e AUSENTES do requirements.txt | TODAS (arquivo não existe) |
| Instaladas mas não utilizadas | — |
| Duplicadas | — |
| **requirements.txt** | ❌ **NÃO EXISTE** |

---

## 📋 6 — VARIÁVEIS SENSÍVEIS

### 🔴 ALTO — Credenciais hardcoded

| Arquivo | Linha | Valor | Problema |
|---------|-------|-------|----------|
| `auth.py` | 134 | `"Ulitec2026@"` | Senha do admin MASTER hardcoded no código |
| `.env` | 24 | `GROQ_API_KEY=gsk_i7JSyrb...` | Chave de API Groq exposta no .env |

### 🟡 MÉDIO — Deveriam virar configuração

| Arquivo | Linha | Constante | Recomendação |
|---------|-------|-----------|--------------|
| `app.py` | 29 | `st.session_state["perfil"] = "SÓCIO"` | Perfil padrão hardcoded |
| `app.py` | 26-29 | `st.session_state["unidade_ativa"]` etc. | Valores padrão fixos |
| `auth.py` | 8 | `DB_PATH = "crm.db"` | Caminho do banco (relativo, ok, mas ideal como config) |
| `database.py` | — | Todos os INSERTs de seed | Dados iniciais (unidades, NCMS, tipos de produto) |
| `services/admin_sistema.py` | 29-34 | `DB_PATH`, `BACKUP_DIR`, `EXPORT_DIR`, etc. | Caminhos de diretórios |
| `services/ia/ia_client.py` | 28 | `print(f"[ia_client] ...")` | Debug print com `os.getcwd()` — vazar em produção |
| `.env` | 25 | `GROQ_MODEL=llama-3.1-8b-instant` | Modelo padrão hardcoded |

### Resumo de sensíveis:

- 🔴 **2 credenciais hardcoded** (senha admin + API key)
- 🟡 **7 constantes que deveriam ser configuráveis**
- ❌ **NENHUM mecanismo de secrets/cofre** (sem `.env.example`, sem `config.py`, sem variáveis de ambiente validadas)

---

## 📋 7 — COMPATIBILIDADE LINUX

### ✔️ Barras invertidas: ZERO ocorrências

Nenhum arquivo `.py` usa `\` como separador de path. Todos usam `/` ou `Path()`.

### ✔️ Case sensitivity: OK

Nomes de arquivos são consistentes (ex: `crm.db`, `app.py`). Nenhum import faz distinção de case.

### ✔️ Encoding: OK

| Arquivo | Linha | Uso |
|---------|-------|-----|
| `admin_sistema.py` | 300 | `encoding="utf-8"` |

Apenas um ponto usa encoding explícito. Demais usam default do Python, que é UTF-8.

### ✔️ Permissões: NÃO gerenciadas

Nenhum código faz `chmod`, `os.chown`, ou manipula permissões. Não há necessidade no escopo atual.

### ✔️ `tempfile`: NÃO utilizado

Nenhum uso de `tempfile.gettempdir()` — não depende de `/tmp` do Linux.

### ✔️ `shutil`: Apenas 1 uso

| Arquivo | Linha | Uso |
|---------|-------|-----|
| `admin_sistema.py` | 276 | `shutil.copy2` para backup |

Uso compatível com Linux.

### ✔️ `subprocess` / `os.system`: ZERO usos

Nenhum comando shell é executado. Totalmente portável.

### ⚠️ `os.getcwd()`: 1 ocorrência de debug

| Arquivo | Linha | Código | Ação |
|---------|-------|--------|------|
| `services/ia/ia_client.py` | 28 | `print(f"[ia_client] Diretório atual: {os.getcwd()}")` | Remover em produção |

### ⚠️ Case sensitivity em dados

| Arquivo | Linha | Padrão | Risco |
|---------|-------|--------|-------|
| `services/ia/ia_client.py` | 86-87 | `MODELOS_GEMINI`, `MODELOS_OPENAI` | Sets case-sensitive |
| Vários `.py` | — | `status = 'ATIVO'`, `'ABERTA'`, etc. | Dados em maiúsculo — consistente |

**Conclusão:** Compatibilidade Linux BOA. Apenas remover o `print()` de debug.

---

## 📋 8 — ESCRITA CONCORRENTE (SQLite)

### 🔴 ALTO — Ausência de WAL mode

O SQLite em modo padrão (sem WAL) usa locking de arquivo. Com Streamlit, múltiplas threads podem tentar escrever simultaneamente.

| Ponto de conflito | Arquivo | Descrição |
|-------------------|---------|-----------|
| Backup durante uso | `admin_sistema.py:276` | `shutil.copy2` do banco enquanto outras páginas leem/escrevem |
| Reset durante uso | `admin_sistema.py:697` | `DELETE FROM` em TODAS tabelas operacionais |
| Limpeza de módulo | `admin_sistema.py:954` | `DELETE FROM` em tabelas de um módulo |
| Importação Mitsubishi | `services/mitsubishi.py:188` | `DELETE FROM maquinas_mitsubishi` + INSERT em lote |
| Conciliação | `services/mitsubishi.py:273` | `DELETE FROM conciliacao_mitsubishi` + múltiplos UPDATEs |
| Registro de interação | `services/relacionamento.py:206` | INSERT + UPDATE simultâneo |
| Múltiplos usuários | Qualquer página | Duas abas abertas escrevendo no mesmo banco |

### Cenários de risco:

1. **Usuário A fazendo backup** enquanto **Usuário B registra interação** → arquivo copiado com transação pela metade
2. **Reset do sistema** enquanto outro usuário navega → `DELETE` em massa com leituras concorrentes
3. **Conciliação Mitsubishi** (DELETE + UPDATE em lote) enquanto Dashboard consulta → locks

### Recomendação:
- Ativar `PRAGMA journal_mode=WAL` em TODAS as conexões
- Adicionar timeout de busy_handler: `conn.execute("PRAGMA busy_timeout=5000")`
- Backup usar `sqlite3.backup` API em vez de `shutil.copy2` (cópia atômica)

---

## 📋 9 — STREAMLIT

### ✔️ `st.cache_data` / `st.cache_resource`: NÃO utilizado

Nenhuma ocorrência de `@st.cache` nos arquivos principais. OK.

### ⚠️ `st.session_state`: Uso extensivo

| Arquivo | Uso | Compatível? |
|---------|-----|-------------|
| `app.py` | `usuario_logado`, `perfil`, `unidade_ativa`, `unidade_usuario` | ✅ |
| `auth.py` | `usuario_id`, `usuario_nome`, `perfil`, etc. | ✅ |
| `permissions.py` | Leitura de `perfil` | ✅ |

Session state é compatível com deploy cloud. Cada usuário tem sua própria sessão.

### ✔️ Uploads / Downloads

| Arquivo | Componente | Compatível? |
|---------|-----------|-------------|
| `services/mitsubishi.py:175` | `pd.read_excel(arquivo_bytes)` | ✅ Via `st.file_uploader` |
| `pages/90_Administracao.py` | Download de backup | ✅ Via `st.download_button` |

Streamlit gerencia arquivos temporários automaticamente. Compatível com cloud.

### ⚠️ `st.switch_page`: Uso OK

Usado em `app.py` e `auth.py`. Compatível com Streamlit Cloud/cPanel.

### ✔️ Widgets: Todos padrão

`st.button`, `st.form`, `st.selectbox`, `st.columns`, `st.sidebar`, `st.text_input`, `st.dataframe`, `plotly` — todos compatíveis.

**Conclusão:** Streamlit está **pronto para deploy cloud**. Nenhum recurso incompatível detectado.

---

## 📋 10 — DEPLOY: O QUE FALTA

### 🔴 CRÍTICO — Bloqueadores de deploy

| # | Item | Situação | Ação necessária |
|---|------|----------|-----------------|
| 1 | **`requirements.txt`** | ❌ Não existe | Criar com todas as dependências |
| 2 | **`services/ia/groq_client.py`** | ❌ Não existe | Criar ou alterar `.env` para `IA_PROVIDER=gemini` |
| 3 | **config.py central** | ❌ Não existe | Criar arquivo de configuração unificado |
| 4 | **`.env.example`** | ❌ Não existe | Template sem secrets |

### 🟡 ALTO — Itens essenciais

| # | Item | Situação | Ação necessária |
|---|------|----------|-----------------|
| 5 | SQLite WAL mode | ❌ Não configurado | Adicionar em todas as conexões |
| 6 | Senha MASTER hardcoded | `auth.py:134` | Mover para `.env` |
| 7 | API key Groq no `.env` | `.env:24` | Confirmar se deve ir para produção |
| 8 | `print()` de debug | `ia_client.py:26-28` | Remover ou usar `logging` |
| 9 | `os.getcwd()` debug | `ia_client.py:28` | Remover |

### 🟡 MÉDIO — Melhorias recomendadas

| # | Item | Ação |
|---|------|------|
| 10 | Pasta `logs/` | Criar automaticamente ou documentar |
| 11 | `backup/` vs `backups/` | Padronizar nome da pasta |
| 12 | `.env` no `.gitignore` | Verificar se está ignorado |
| 13 | `database.py:662` | Garantir que `criar_banco()` seja chamado no startup |
| 14 | Timezone | `datetime.now()` usa timezone local. Verificar se servidor Linux terá `America/Sao_Paulo` |
| 15 | `crm.db` no repositório | Considerar se o banco será copiado ou recriado |

### 🟢 BAIXO — Opcionais

| # | Item | Ação |
|---|------|------|
| 16 | `pytest` para testes | Rodar antes do deploy |
| 17 | Arquivos `.xlsx` em `relatórios para integração/` | Avaliar se devem subir |
| 18 | Pasta `legacy/` | Avaliar remoção |
| 19 | Pasta `debug/` | Avaliar remoção |

---

## 📊 RESUMO EXECUTIVO

### Status geral: ⚠️ 65% PRONTO para deploy

O projeto está **funcionalmente pronto** — código compatível com Linux, sem paths absolutos, sem comandos shell, sem dependências de Windows. Os problemas são de **configuração e segurança**, não de arquitetura.

### Bloqueadores (não pode deploy sem resolver):

| # | Item | Criticidade |
|---|------|-------------|
| 1 | Criar `requirements.txt` | 🔴 CRÍTICO |
| 2 | Criar ou corrigir `groq_client.py` (ou trocar provider) | 🔴 CRÍTICO |
| 3 | Criar `config.py` + `.env.example` | 🟡 ALTO |

### Ordem ideal de correção:

1. **Criar `requirements.txt`** com todas as dependências
2. **Resolver `groq_client.py`** (criar o arquivo ou alterar `IA_PROVIDER` para `gemini`)
3. **Criar `config.py`** centralizando `DB_PATH`, diretórios, e defaults
4. **Adicionar WAL mode** no SQLite em todas as conexões
5. **Mover senha MASTER** para `.env` (nunca hardcoded)
6. **Criar `.env.example`** como template
7. **Remover `print()` de debug** do `ia_client.py`
8. **Verificar timezone** no servidor Linux
9. **Testar `criar_banco()`** — garantir que banco novo é criado se não existir
10. **Opcional:** Rodar testes unitários

### Total de ocorrências por criticidade:

| Criticidade | Qtd |
|-------------|-----|
| 🔴 CRÍTICO | 3 |
| 🟡 ALTO | 5 |
| 🟡 MÉDIO | 6 |
| 🟢 BAIXO | 4 |

---

**Relatório gerado por auditoria manual de código.**  
**Versão do relatório:** 1.0  
**Nenhum arquivo foi modificado.**