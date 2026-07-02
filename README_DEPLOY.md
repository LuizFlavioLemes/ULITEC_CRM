# 🚀 Deploy ULITEC CRM — cPanel Python Application

Guia completo para publicar, atualizar e manter o CRM ULITEC em ambiente Linux com cPanel + Python Application.

---

## 📦 Estrutura de Deploy

```
ULITEC_CRM/
├── app.py                  ← Entry point Streamlit
├── config.py               ← Configuração central (paths, secrets)
├── requirements.txt        ← Dependências pip
├── passenger_wsgi.py       ← WSGI wrapper para cPanel
├── .env.example            ← Template de variáveis de ambiente
├── .env                    ← Variáveis REAIS (NÃO versionar)
├── crm.db                  ← Banco SQLite (copiar ou recriar)
├── database.py             ← Criação/migração do banco
├── auth.py                 ← Autenticação
├── permissions.py          ← Matriz de permissões
├── components/             ← Componentes UI
├── pages/                  ← Telas do sistema
├── services/               ← Serviços de backend
├── logs/                   ← Logs (criado automaticamente)
├── uploads/                ← Uploads (criado automaticamente)
├── backups/                ← Backups (criado automaticamente)
└── docs/                   ← Documentação
```

---

## ⚙️ Pré-requisitos

- cPanel com **Python Application** habilitado
- Python 3.10+
- Acesso SSH (recomendado) ou File Manager

---

## 🔧 1. Primeiro Deploy (Publicação Inicial)

### 1.1 Criar Python Application no cPanel

1. Acesse cPanel → **Setup Python App**
2. Clique em **Create Application**
3. Configure:
   - **Python version:** 3.10 ou superior
   - **Application root:** `/home/usuario/ulitec_crm` (caminho sugerido)
   - **Application URL:** escolha o domínio/subdomínio
   - **Application startup file:** `passenger_wsgi.py`
   - **Application Entry point:** `application`
4. Clique em **Create**

### 1.2 Upload dos arquivos

Via File Manager ou SSH (rsync/scp):

```bash
# Subir todos os arquivos para a pasta da aplicação
rsync -avz --exclude '.git' --exclude '__pycache__' --exclude '*.pyc' \
      --exclude 'backups/*.db' --exclude 'backup/*' \
      --exclude 'relatórios para integração/*' \
      --exclude 'legacy/*' --exclude 'debug/*' \
      ./ usuario@host:/home/usuario/ulitec_crm/
```

### 1.3 Configurar .env

```bash
# Copiar template
cp .env.example .env

# Editar com as credenciais reais
nano .env
```

Preencher **obrigatoriamente:**

```env
ULITEC_AMBIENTE=CLOUD
MASTER_PASSWORD=sua_senha_segura
IA_PROVIDER=groq
GROQ_API_KEY=sua_chave_groq
GROQ_MODEL=llama-3.1-8b-instant
```

### 1.4 Instalar dependências

No cPanel, acesse a Python Application criada e use a interface **"Install packages from requirements.txt"**. Ou via SSH:

```bash
cd /home/usuario/ulitec_crm
source ~/virtualenv/ulitec_crm/3.10/bin/activate
pip install -r requirements.txt
```

### 1.5 Criar banco de dados (se necessário)

Se o banco `crm.db` foi copiado junto com os arquivos, pule esta etapa.

Caso precise criar um banco novo:

```bash
python database.py
```

Isso criará todas as tabelas, unidades padrão, NCMS e configurações iniciais.

### 1.6 Testar

Acesse a URL configurada. O login padrão é:

- **Usuário:** `admin`
- **Senha:** a definida em `MASTER_PASSWORD` no `.env`

Altere a senha imediatamente após o primeiro login.

---

## 🔄 2. Atualização (Deploy de Nova Versão)

### 2.1 Fazer backup

```bash
cp crm.db backups/pre_update_$(date +%Y%m%d_%H%M%S).db
```

### 2.2 Subir novos arquivos

```bash
rsync -avz --exclude 'crm.db' --exclude '.env' --exclude 'backups/' \
      --exclude 'uploads/' --exclude 'logs/' --exclude '__pycache__' \
      ./ usuario@host:/home/usuario/ulitec_crm/
```

**IMPORTANTE:** NUNCA sobrescrever `crm.db` ou `.env` durante atualização.

### 2.3 Atualizar dependências

```bash
source ~/virtualenv/ulitec_crm/3.10/bin/activate
pip install -r requirements.txt --upgrade
```

### 2.4 Reiniciar aplicação

No cPanel → **Setup Python App** → clique em **Restart** na aplicação.

---

## 💾 3. Backup e Restauração

### 3.1 Backup manual (SSH)

```bash
cp crm.db backups/crm_backup_$(date +%Y%m%d_%H%M%S).db
```

### 3.2 Backup pela interface

Acesse **Administração → Banco → Backup** no CRM.

O sistema gera:
- `backups/crm_backup_*.db` — cópia do banco
- `backups/manifestos/manifesto_*.json` — metadados

### 3.3 Restauração

Acesse **Administração → Banco → Restauração** no CRM.

Selecione um arquivo `.db` ou `.zip` para restaurar.

**O sistema cria um backup automático ANTES de restaurar.**

---

## 🌐 4. Configuração de Ambiente

### Variáveis obrigatórias (.env)

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `ULITEC_AMBIENTE` | `DEV` ou `CLOUD` | `CLOUD` |
| `MASTER_PASSWORD` | Senha inicial do admin | `Senha@123` |
| `IA_PROVIDER` | `groq`, `gemini` ou `openai` | `groq` |
| `GROQ_API_KEY` | Chave da API Groq | `gsk_...` |

### Variáveis opcionais

| Variável | Padrão |
|----------|--------|
| `GROQ_MODEL` | `llama-3.1-8b-instant` |
| `GEMINI_API_KEY` | (vazio) |
| `GEMINI_MODEL` | `gemini-2.0-flash` |
| `OPENAI_API_KEY` | (vazio) |
| `OPENAI_MODEL` | `gpt-4o-mini` |

---

## 🏗️ 5. Arquivos Específicos do cPanel

### passenger_wsgi.py

O cPanel Python Application usa Passenger + WSGI.

Como o Streamlit não é WSGI nativamente, o `passenger_wsgi.py`:
1. Importa o `app.py` do Streamlit
2. Cria um objeto `application` compatível com WSGI
3. O Passenger gerencia o processo

### Arquivos NÃO necessários para cPanel

| Arquivo | Necessário? | Motivo |
|---------|-------------|--------|
| `Procfile` | ❌ | Usado apenas por Heroku |
| `runtime.txt` | ❌ | cPanel seleciona Python na interface |
| `startup.sh` | ❌ | cPanel usa Passenger, não script shell |
| `Dockerfile` | ❌ | Não usa containers |
| `nginx.conf` | ❌ | cPanel gerencia o servidor web |

---

## 🧪 6. Verificação Pós-Deploy

### 6.1 Testar acesso

```bash
# Verificar se a aplicação responde
curl -I https://seu-dominio.com/
```

### 6.2 Logs

Logs do Passenger ficam em:

```
/home/usuario/ulitec_crm/passenger.log
/home/usuario/logs/ulitec_crm.error.log
```

### 6.3 Verificar permissões

```bash
# Garantir que o cPanel consiga ler/escrever
chmod 755 /home/usuario/ulitec_crm
chmod 664 /home/usuario/ulitec_crm/crm.db
chmod -R 755 /home/usuario/ulitec_crm/backups
```

---

## 🔒 7. Segurança

- ❌ **NUNCA** comitar `.env` no repositório
- ❌ **NUNCA** expor `crm.db` publicamente
- ✅ Manter `crm.db` fora do `public_html`
- ✅ Usar HTTPS (cPanel oferece AutoSSL gratuito)
- ✅ Rotacionar `MASTER_PASSWORD` periodicamente
- ✅ Fazer backup antes de qualquer atualização

---

## 📊 8. Monitoramento

### Tamanho do banco

```bash
ls -lh crm.db
```

### Logs de acesso

Os logs de acesso do Apache ficam em:

```
/home/usuario/logs/domínio-ssl_log
```

### Health check

Acessar `/healthz` (não implementado ainda — retorna 200 se a aplicação estiver rodando).

---

## 🆘 9. Troubleshooting

### Aplicação não inicia

1. Verificar logs: `/home/usuario/logs/`
2. Verificar se `passenger_wsgi.py` existe na raiz
3. Verificar se `requirements.txt` foi instalado
4. Verificar se `python` no path do cPanel é 3.10+

### Erro 500

1. Rodar manualmente para ver erros:
   ```bash
   source ~/virtualenv/ulitec_crm/3.10/bin/activate
   streamlit run app.py --server.port 8501
   ```
2. Verificar dependências: `pip list`

### Banco de dados corrompido

```bash
sqlite3 crm.db "PRAGMA integrity_check;"
```

Se falhar, restaurar do último backup.

### Módulo não encontrado

```bash
source ~/virtualenv/ulitec_crm/3.10/bin/activate
pip install -r requirements.txt
```

---

## 📋 Checklist de Deploy

- [ ] Python Application criada no cPanel
- [ ] Arquivos copiados para o servidor
- [ ] `.env` configurado com credenciais reais
- [ ] `requirements.txt` instalado
- [ ] `crm.db` existe e está íntegro
- [ ] `passenger_wsgi.py` configurado
- [ ] Permissões de arquivos verificadas
- [ ] Backup inicial feito
- [ ] Login testado com `admin` / `MASTER_PASSWORD`
- [ ] HTTPS ativo (AutoSSL)
- [ ] Logs monitorados por 24h

---

**Versão do Deploy Guide:** 1.0  
**Última atualização:** 01/07/2026