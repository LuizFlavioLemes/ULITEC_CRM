# AUDITORIA V2.0 – SISTEMA DE PERMISSÕES

**Data:** 30/06/2026  
**Propósito:** Mapear todas as permissões atuais para reestruturar conforme novo modelo de perfis.  
**Status:** APENAS AUDITORIA — Nenhuma alteração foi implementada.

---

## 1. SITUAÇÃO ATUAL DO BANCO DE DADOS

### Tabela `usuarios` - colunas relevantes
| Coluna          | Tipo          | Observação                    |
|-----------------|---------------|-------------------------------|
| `perfil`        | TEXT          | Campo novo (migrado de `nivel_acesso`) |
| `nivel_acesso`  | TEXT          | Campo legado (ainda usado em cadastro) |
| `login`         | TEXT          | Usado para autenticação       |
| `senha`         | TEXT          | Senha em texto puro (legado)  |
| `senha_hash`    | TEXT          | Senha com bcrypt (novo)       |
| `ativo`         | INTEGER       | 1 = ativo, 0/Null = inativo   |
| `unidade_id`    | INTEGER       | FK para unidades (não utilizado) |

### Usuários cadastrados
| ID | Nome          | Login    | perfil    | nivel_acesso | Ativo |
|----|---------------|----------|-----------|--------------|-------|
| 1  | Flavio Lemes  | flavio   | OPERADOR  | SÓCIO        | 1     |
| 2  | admin         | admin    | MASTER    | NULL         | 1     |
| 3  | Ulisses       | ulisses  | OPERADOR  | SÓCIO        | 1     |

**PROBLEMA:** Perfil dos usuários reais (Flavio e Ulisses) está `OPERADOR` mas `nivel_acesso` está `SÓCIO`. Migração de `nivel_acesso` → `perfil` foi mal feita: mapeou `SÓCIO` → `MASTER` e `GERENTE` → `GESTOR`, mas não tratou corretamente. Ambos os sócios estão classificados como OPERADOR.

### Migração incorreta em `auth.py:41-46`
```python
SET perfil = CASE nivel_acesso
    WHEN 'SÓCIO' THEN 'MASTER'
    WHEN 'GERENTE' THEN 'GESTOR'
    WHEN 'OPERADOR SP' THEN 'OPERADOR'
    WHEN 'OPERADOR RS' THEN 'OPERADOR'
    ELSE 'OPERADOR'
END
```
**IMPACTO:** Sócios foram rebaixados para OPERADOR, sem acesso à Administração e outras telas restritas.

---

## 2. MAPA DE VERIFICAÇÕES DE ACESSO

### 2.1 Funções de verificação em `auth.py`

| Função                 | Localização | Uso atual                  |
|------------------------|-------------|----------------------------|
| `verificar_acesso()`   | auth.py:205 | Usada em TODAS as páginas  |
| `requer_login()`       | auth.py:227 | Decorator (NUNCA usado fora de auth) |
| `requer_perfil()`      | auth.py:242 | Decorator (NUNCA usado)    |
| `sidebar_usuario()`    | auth.py:304 | Usada em TODAS as páginas  |

### 2.2 Chamadas `verificar_acesso()` por página

#### Páginas ativas (pages/)
| Página | Proteção | Quem acessa |
|--------|----------|-------------|
| `00_Dashboard.py` | `perfis=["MASTER", "GESTOR"]` | MASTER, GESTOR |
| `02_Cliente_360.py` | `verificar_acesso()` (qualquer autenticado) | TODOS |
| `06_Relacionamento_Comercial.py` | `verificar_acesso()` | TODOS |
| `10_Central_Oportunidades.py` | `verificar_acesso()` | TODOS |
| `11_Pipeline_OS.py` | `verificar_acesso()` | TODOS |
| `15_Parque_Mitsubishi.py` | `perfis=["MASTER", "GESTOR"]` | MASTER, GESTOR |
| `16_Base_Produtos_Importados.py` | `verificar_acesso()` | TODOS |
| `20_Relatorio_IA.py` | `verificar_acesso()` | TODOS |
| `30_Centro_Importacoes.py` | `perfis=["MASTER", "GESTOR"]` | MASTER, GESTOR |
| `40_Gestao_Terceiros.py` | `verificar_acesso()` | TODOS |
| `90_Administracao.py` | `perfis=["MASTER"]` | SOMENTE MASTER |

#### Páginas legado (legacy/)
| Página | Proteção | Quem acessa |
|--------|----------|-------------|
| `01_Base_Clientes.py` | `verificar_acesso()` | TODOS |
| `12_Acoes_Massa.py` | `verificar_acesso()` | TODOS |
| `30_Importar_Clientes.py` | `perfis=["MASTER", "GESTOR"]` | MASTER, GESTOR |
| `31_Importar_Faturamento.py` | `perfis=["MASTER", "GESTOR"]` | MASTER, GESTOR |
| `32_Importar_OS.py` | `perfis=["MASTER", "GESTOR"]` | MASTER, GESTOR |
| `36_Pendencias_Cadastro.py` | `perfis=["MASTER", "GESTOR"]` | MASTER, GESTOR |

#### Debug
| Página | Proteção |
|--------|----------|
| `99_Debug_OS.py` | `verificar_acesso()` (qualquer autenticado) |

---

## 3. VERIFICAÇÕES NÃO PADRONIZADAS (ESPALHADAS PELO CÓDIGO)

### 3.1 `app.py` - Seletor de unidade por perfil
```python
# Linha 43: Verificação direta (NÃO usa função centralizada)
if st.session_state["perfil"] in ("MASTER", "SOCIO", "GESTOR"):
```
**PROBLEMA:** SÓCIO não está mapeado. Apenas SOCIO (sem acento) é verificado. OPERADOR cai no else e não pode selecionar unidade.

### 3.2 `pages/06_Relacionamento_Comercial.py:271-278`
```python
perfis_editaveis = ["MASTER", "SOCIO", "SÓCIO"]
disabled=st.session_state.get("perfil", "").upper() not in [p.upper() for p in perfis_editaveis]
```
**PROBLEMA:** Duplicidade SOCIO/SÓCIO. Verificação case-insensitive, mas comparação manual duplicada.

### 3.3 `pages/10_Central_Oportunidades.py:41-57`
```python
if "perfil" not in st.session_state:
    st.session_state["perfil"] = "SOCIO"
# ...
if st.session_state["perfil"] == "SOCIO":
    escolha = st.sidebar.selectbox(...)
else:
    st.session_state["unidade_ativa"] = st.session_state["unidade_usuario"]
```
**PROBLEMA:** Redundante com `app.py`. Só verifica SOCIO sem considerar MASTER/GESTOR.

### 3.4 `pages/11_Pipeline_OS.py:22-38`
```python
if "perfil" not in st.session_state:
    st.session_state["perfil"] = "SOCIO"
# ...
if st.session_state["perfil"] in ("MASTER", "SOCIO", "GESTOR"):
    escolha = st.sidebar.selectbox(...)
else:
    st.session_state["unidade_ativa"] = st.session_state["unidade_usuario"]
```
**PROBLEMA:** Redundante. Mesma lógica replicada em 3 arquivos diferentes.

### 3.5 `pages/90_Administracao.py:56`
```python
return resultado is not None and resultado["perfil"] in ("MASTER",)
```
**PROBLEMA:** Verificação direta ao invés de usar função. SÓCIO/GESTOR não podem acessar mesmo que faça sentido (ex: config de relacionamento).

### 3.6 `legacy/01_Base_Clientes.py:12-13`
```python
perfil = st.session_state.get("perfil", "OPERADOR")
if perfil == "OPERADOR":
```
**PROBLEMA:** Verificação direta espalhada. Só bloqueia OPERADOR, mas permite MASTER, GESTOR e SOCIO.

---

## 4. PERFIS ATUAIS VS PERFIS NOVOS

### Perfis atualmente existentes no sistema
| Perfil no BD | Ocorrências | Equivalente no novo modelo |
|--------------|-------------|---------------------------|
| MASTER       | admin       | MASTER                    |
| OPERADOR     | flavio, ulisses (deveriam ser SÓCIO) | OPERADOR (ou SÓCIO com correção) |
| (faltam)     | -           | SÓCIO, GERENTE (GESTOR)   |

### Perfis que o sistema usa em verificações
| String usada | Onde |
|--------------|------|
| `"MASTER"`   | app.py, auth.py, 7 verificações em pages |
| `"SOCIO"`    | app.py, pages/06, 10, 11 |
| `"SÓCIO"`    | pages/06 (duplicado), pages/90 (cadastro) |
| `"GESTOR"`   | app.py, 7 verificações em pages (migrado de GERENTE) |
| `"OPERADOR"` | auth.py (default), legacy/01 |

---

## 5. PROBLEMAS IDENTIFICADOS

### 5.1 CRÍTICOS
1. **Perfil SÓCIO corrompido no banco:** Flavio e Ulisses (sócios reais) estão como OPERADOR devido a migração incorreta.
2. **SOCIO vs SÓCIO:** Sistema usa ambas as grafias. Perfil no banco pode ser um ou outro.
3. **Nível de Acesso legado:** Tela de Administração ainda cadastra usuários com `nivel_acesso` (texto puro) ao invés de `perfil` com `senha_hash`.
4. **Administração exclusiva MASTER:** SÓCIO não pode acessar Administração, o que impede gerenciamento de usuários.

### 5.2 REDUNDÂNCIAS
1. **Seletor de unidade replicado** em `app.py`, `pages/10_Central_Oportunidades.py` e `pages/11_Pipeline_OS.py` — mesmas 30 linhas copiadas.
2. **`perfil` default "SOCIO"** declarado em 4 arquivos diferentes.
3. **`unidade_ativa` default "GRUPO"** declarado em 3 arquivos.
4. **`unidade_usuario` default "ULITEC SP"** declarado em 4 arquivos.

### 5.3 FUNÇÕES NÃO UTILIZADAS
- `requer_perfil()` decorator — criado mas NUNCA usado em nenhuma página.
- `requer_login()` decorator — criado mas NUNCA usado (só como wrapper interno).

### 5.4 SEGREGAÇÃO DE UNIDADE INCORRETA
- OPERADOR não pode selecionar unidade (correto), mas herda `unidade_usuario` sem verificar se unidade está associada ao usuário no banco.
- `unidade_id` na tabela `usuarios` nunca é preenchido/verificado.

---

## 6. MAPA DE MÓDULOS E PERMISSÕES SUGERIDAS (NOVO MODELO)

### Legenda
- ✅ = Pode visualizar/acessar
- ➕ = Pode cadastrar/criar
- ✏️ = Pode editar
- ❌ = Pode excluir (com restrição)
- ⚙️ = Pode configurar/administrar
- 🚫 = Não pode
- 🛠️ = Dev (diagnóstico, debug, migração)

### Páginas Operacionais (acesso geral)

| Página | MASTER | SÓCIO | GERENTE | OPERADOR | CONSULTA |
|--------|--------|-------|---------|----------|----------|
| Dashboard | ✅ | ✅ | ✅ | ✅ | ✅ |
| Cliente 360 | ✅ | ✅ | ✅ | ✅ | ✅ |
| Relacionamento Comercial | ✅ | ✅ | ✅ | ✅➕✏️ | ✅ |
| Central Oportunidades | ✅ | ✅ | ✅ | ✅ | ✅ |
| Pipeline OS | ✅ | ✅ | ✅ | ✅ | ✅ |
| Base Produtos Importados | ✅ | ✅ | ✅ | ✅ | ✅ |
| Relatório IA | ✅ | ✅ | ✅ | ✅ | ✅ |
| Gestão Terceiros | ✅ | ✅ | ✅ | ✅➕✏️ | ✅ |
| Parque Mitsubishi | ✅ | ✅ | ✅ | ✅ | ✅ |

### Páginas Restritas

| Página | MASTER | SÓCIO | GERENTE | OPERADOR | CONSULTA |
|--------|--------|-------|---------|----------|----------|
| Centro Importações | ✅ | ✅ | ✅➕✏️ | ➕✏️ | 🚫 |
| Administração | ✅🛠️ | ✅⚙️ | 🚫 (parcial) | 🚫 | 🚫 |

### Funcionalidades dentro da Administração

| Funcionalidade | MASTER | SÓCIO | GERENTE |
|----------------|--------|-------|---------|
| Gestão de Usuários | ✅ | ✅✏️ | 🚫 |
| Config. Relacionamento | ✅ | ✅ | ✅✏️ |
| Config. BI/Indicadores | ✅ | ✅ | ✅ |
| Backup Banco | ✅ | ✅ | 🚫 |
| Manutenção Técnica | ✅🛠️ | 🚫 | 🚫 |
| Parâmetros Gerais | ✅ | ✅ | ✅✏️ |
| Classificação ABC | ✅ | ✅ | ✅ |
| Config. Operacionais | ✅ | ✅ | ✅ |

---

## 7. PLANO DE MIGRAÇÃO PARA V2.0

### Fase 1: Correção da Base
- [ ] Corrigir `auth.py:init_auth()` para mapear `SÓCIO` → `SÓCIO` (não MASTER)
- [ ] Corrigir `GERENTE` → `GERENTE` (não GESTOR)
- [ ] Garantir que `nivel_acesso` não seja mais usado para cadastro
- [ ] Script de correção dos usuários existentes

### Fase 2: Funções Centralizadas em `auth.py`
- [ ] Criar `tem_acesso(perfis_autorizados: list) -> bool`
- [ ] Criar `pode_editar() -> bool` (MASTER, SÓCIO, GERENTE = True)
- [ ] Criar `pode_excluir() -> bool` (MASTER, SÓCIO = True; GERENTE = True com restrições)
- [ ] Criar `pode_administrar() -> bool` (MASTER, SÓCIO = True)
- [ ] Manter `verificar_acesso()` usando as funções acima internamente
- [ ] Remover `requer_perfil()` e `requer_login()` se não forem utilizados

### Fase 3: Padronização das Páginas
- [ ] Substituir TODAS as verificações `st.session_state["perfil"] == "SOCIO"` por `tem_acesso()`
- [ ] Substituir TODAS as verificações `perfis in ("MASTER", "SOCIO", "GESTOR")` por `tem_acesso()`
- [ ] Eliminar defaults duplicados de perfil/unidade em cada página
- [ ] Centralizar seletor de unidade em `app.py` (sidebar global)

### Fase 4: Atualizar Proteções das Páginas

| Página | Nova proteção |
|--------|---------------|
| 00_Dashboard | `tem_acesso(["MASTER", "SOCIO", "GERENTE", "OPERADOR"])` → geral |
| 15_Parque_Mitsubishi | `tem_acesso(["MASTER", "SOCIO", "GERENTE", "OPERADOR"])` → geral |
| 30_Centro_Importacoes | `tem_acesso(["MASTER", "SOCIO", "GERENTE"])` |
| 90_Administracao | `tem_acesso(["MASTER", "SOCIO"])` + controles internos por aba |

### Fase 5: Tela de Administração
- [ ] Criar abas com proteção granular:
  - Usuários: MASTER + SÓCIO
  - Config Relacionamento: MASTER + SÓCIO + GERENTE
  - Backup: MASTER + SÓCIO
  - Manutenção Técnica: SOMENTE MASTER
  - BI/Parâmetros: MASTER + SÓCIO + GERENTE

### Fase 6: Limpeza de Código
- [ ] Remover verificações redundantes de `perfil` em Central Oportunidades e Pipeline OS
- [ ] Unificar strings de perfil (SOCIO → SÓCIO em todo lugar)
- [ ] Mover iniciação da session_state para app.py (evitar repetição)

---

## 8. ARQUIVOS QUE PRECISAM SER ALTERADOS

### Prioridade ALTA (correção de dados)
| Arquivo | O que alterar |
|---------|--------------|
| `auth.py` | Migração de nivel_acesso para perfil |
| `_migrar_perfis.py` (novo script) | Corrigir perfis dos usuários existentes |

### Prioridade ALTA (funções centralizadas)
| Arquivo | O que alterar |
|---------|--------------|
| `auth.py` | Adicionar `tem_acesso()`, `pode_editar()`, `pode_excluir()`, `pode_administrar()` |

### Prioridade MÉDIA (padronização das páginas)
| Arquivo | O que alterar |
|---------|--------------|
| `app.py` | Centralizar defaults e seletor de unidade |
| `pages/00_Dashboard.py` | Trocar `verificar_acesso(perfis=[...])` por função padronizada |
| `pages/02_Cliente_360.py` | Nenhuma (já usa `verificar_acesso()`) |
| `pages/06_Relacionamento_Comercial.py` | Substituir verificação inline de perfil |
| `pages/10_Central_Oportunidades.py` | Remover defaults duplicados + substituir SOCIO |
| `pages/11_Pipeline_OS.py` | Remover defaults duplicados + substituir SOCIO |
| `pages/15_Parque_Mitsubishi.py` | Trocar proteção para acesso geral |
| `pages/30_Centro_Importacoes.py` | Adicionar GERENTE |
| `pages/90_Administracao.py` | Adicionar SÓCIO + abas granulares |
| `pages/40_Gestao_Terceiros.py` | Nenhuma (já usa `verificar_acesso()`) |
| `pages/20_Relatorio_IA.py` | Nenhuma (já usa `verificar_acesso()`) |

### Prioridade BAIXA (legado - manter apenas se ainda usados)
| Arquivo | O que alterar |
|---------|--------------|
| `legacy/01_Base_Clientes.py` | Substituir verificação OPERADOR |
| `legacy/12_Acoes_Massa.py` | Nenhuma alteração necessária |

---

## 9. NÃO IMPLEMENTAR AGORA (PREVISÃO FUTURA)

- Perfil CONSULTA (somente leitura) — previsto para vendedores, clientes internos, TV, diretoria
- Controle de permissão por registro (criado_por) — OPERADOR só edita próprios registros
- Auditoria de ações (log de quem fez o quê)

---

## 10. IMPACTO POR MÓDULO

| Módulo | Impacto | Complexidade |
|--------|---------|--------------|
| Autenticação | ⚠️ Correção de migração + novas funções | Média |
| Dashboard | 🔄 Trocar protetores de acesso | Baixa |
| Cliente 360 | ✅ Nenhuma | Nula |
| Relacionamento | 🔄 Verificação inline de perfil | Baixa |
| Central Oportunidades | 🔄 Remover redundâncias | Baixa |
| Pipeline OS | 🔄 Remover redundâncias | Baixa |
| Parque Mitsubishi | 🔄 Liberar acesso geral | Baixa |
| Produtos Importados | ✅ Nenhuma | Nula |
| Relatório IA | ✅ Nenhuma | Nula |
| Centro Importações | 🔄 Adicionar GERENTE | Baixa |
| Gestão Terceiros | ✅ Nenhuma | Nula |
| Administração | 🔄 Adicionar SÓCIO + abas granulares | Média |
| Legado | 🔄 Substituições mínimas | Baixa |

---

## R E S U M O   E X E C U T I V O

1. **Sistema atual tem 4 perfis** (MASTER, GESTOR, SOCIO, OPERADOR) mas com migração incorreta — sócios estão como OPERADOR.
2. **22 verificações de perfil** espalhadas em 15 arquivos — sem padronização.
3. **3 padrões diferentes** de verificação: `verificar_acesso()`, comparação inline de `session_state`, e comparação em legados.
4. **SOCIO vs SÓCIO:** grafia inconsistente em todo o sistema.
5. **Funções decoradoras não utilizadas:** `requer_perfil()` e `requer_login()` existem mas nunca foram aplicadas.
6. **Nova estrutura proposta:** MASTER → SÓCIO → GERENTE → OPERADOR → CONSULTA (futuro).
7. **Centralização:** Criar `tem_acesso()`, `pode_editar()`, `pode_excluir()`, `pode_administrar()` em auth.py.
8. **Redução estimada:** De 22 verificações espalhadas para ~12 chamadas centralizadas.

---
*Fim do relatório de auditoria. Nenhuma alteração foi implementada.*