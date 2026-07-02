# ROADMAP CLOUD — ULITEC CRM v1.6.9

## Análise de preparação para migração para cloud

---

### Situação atual

| Componente | Atual | Para Cloud |
|---|---|---|
| **Banco de Dados** | SQLite (`crm.db` — arquivo local) | PostgreSQL (VPS Linux) |
| **Servidor** | Localhost (Streamlit) | VPS Linux (Ubuntu/Debian) |
| **Domínio** | Sem domínio | Com domínio + HTTPS |
| **Backup** | Manual (backups/ no projeto) | Automático (cron + S3/Drive) |
| **Usuários** | 2 usuários locais | Múltiplos usuários remotos |
| **Segurança** | Autenticação simples (Streamlit) | HTTPS + autenticação reforçada |

---

### Passos necessários para Cloud

#### 1. Banco de Dados — SQLite → PostgreSQL

| Item | Descrição |
|---|---|
| **Migração de dados** | Exportar SQLite → SQL → importar no PostgreSQL |
| **Driver** | `psycopg2` ou `pg8000` |
| **Adaptação de queries** | `datetime('now')` → `NOW()`, `julianday()` → `EXTRACT(DAY FROM ...)`, `||` (concat) funciona igual |
| **Transações** | PostgreSQL requer gerenciamento mais rigoroso de conexões |
| **Pool de conexões** | Implementar `psycopg2.pool` ou `SQLAlchemy` |

**Complexidade:** MÉDIA-ALTA (muitas queries com funções SQLite proprietárias)

---

#### 2. Servidor — VPS Linux

| Item | Especificação sugerida |
|---|---|
| **OS** | Ubuntu 22.04 LTS |
| **Hardware mínimo** | 2 vCPUs, 4GB RAM, 40GB SSD |
| **Runtime** | Python 3.10+ |
| **Gerenciamento** | systemd (serviço Streamlit) |
| **Proxy reverso** | Nginx |
| **HTTPS** | Let's Encrypt / Certbot |

**Custo estimado:** ~R$ 50-80/mês (Hetzner, DigitalOcean, ou AWS Lightsail)

---

#### 3. Domínio e HTTPS

| Item | Descrição |
|---|---|
| **Domínio** | Comprar domínio (.com.br) ~R$ 40/ano |
| **SSL** | Let's Encrypt (gratuito, renovação automática) |
| **Configuração** | Nginx como proxy reverso com SSL termination |

---

#### 4. Backup Automático

| Item | Descrição |
|---|---|
| **Frequência** | Diário (cron) |
| **Destino** | Google Drive API + local |
| **Retenção** | 7 dias local, 30 dias cloud |
| **Ferramenta** | Script Python + `cron` + `gdrive` ou `rclone` |

---

#### 5. Deploy Contínuo

| Item | Descrição |
|---|---|
| **Git** | Manter GitHub como central |
| **Pull** | Script `git pull && systemctl restart streamlit` |
| **Rollback** | Manter versão anterior no VPS |

---

### Desafios identificados

1. **SQLite → PostgreSQL**: Funções de data `julianday()`, `datetime()` e `strftime()` são específicas do SQLite. Será necessário revisar ~30+ queries no código.
2. **Conexões concorrentes**: SQLite não lida bem com múltiplos usuários simultâneos. PostgreSQL resolve, mas exige pool de conexões.
3. **Streamlit em produção**: Streamlit não é ideal para produção multi-usuário. Alternativas: FastAPI + React, ou manter Streamlit atrás de Nginx.
4. **Segurança**: Atual autenticação é básica. Será necessário JWT ou OAuth para cloud.

---

### Recomendação

| Fase | Ação | Prioridade |
|---|---|---|
| **Fase 1 (curto prazo)** | Substituir SQLite por PostgreSQL mantendo Streamlit | Alta |
| **Fase 2 (médio prazo)** | Contratar VPS + domínio + HTTPS | Alta |
| **Fase 3 (longo prazo)** | Migrar de Streamlit para web app tradicional (FastAPI + React) | Média |
| **Contínuo** | Backup automático diário | Alta |

---

### Pronto para Cloud?

**AVALIAÇÃO: NÃO**

Motivos:
1. SQLite não suporta concorrência multi-usuário
2. Código possui queries SQLite-dependentes (julianday, datetime)
3. Backup manual (não automatizado)
4. Sem HTTPS
5. Streamlit em produção tem limitações de segurança e performance

> ⚠️ **Não implementar agora. Apenas planejamento para V1.7.**