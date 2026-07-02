# Arquitetura — Módulo Relatórios Técnicos IA

## ULITEC CRM v0.9.0 → v1.0.0

---

## 1. Tabelas Necessárias

### 1.1 `relatorios_ia` (tabela principal)

Armazena todos os relatórios gerados, independente do provedor de IA.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | INTEGER PK AUTO | Identificador único |
| `cliente_id` | INTEGER FK→clientes | Cliente alvo (NULL se relatório global) |
| `unidade` | TEXT | Filial (SP/RS/GRUPO) |
| `tipo_relatorio` | TEXT | `analise_cliente`, `pipeline_os`, `oportunidades`, `faturamento`, `parque_maquinas`, `sazonalidade`, `personalizado` |
| `titulo` | TEXT | Título gerado ou definido pelo usuário |
| `parametros` | TEXT JSON | Parâmetros usados na geração (filtros, período, instruções) |
| `conteudo_md` | TEXT | Relatório completo em Markdown (pré-renderização) |
| `conteudo_html` | TEXT | Relatório em HTML formatado para PDF |
| `provedor_ia` | TEXT | `openai`, `gemini`, `ollama` |
| `modelo_ia` | TEXT | `gpt-4o`, `gemini-2.0`, `llama3`, etc. |
| `tokens_entrada` | INTEGER | Tokens de prompt consumidos |
| `tokens_saida` | INTEGER | Tokens de resposta consumidos |
| `custo_estimado` | REAL | Custo estimado em R$ da chamada |
| `status` | TEXT | `gerando`, `concluido`, `erro` |
| `erro` | TEXT | Mensagem de erro se houver |
| `criado_por` | INTEGER FK→usuarios | Usuário que solicitou |
| `data_criacao` | DATETIME | Timestamp de criação |
| `data_conclusao` | DATETIME | Timestamp de conclusão |

### 1.2 `relatorios_ia_pdf`

Histórico de PDFs gerados a partir de relatórios.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | INTEGER PK AUTO | Identificador único |
| `relatorio_id` | INTEGER FK→relatorios_ia | Relatório origem |
| `caminho_arquivo` | TEXT | Caminho relativo ao diretório de PDFs |
| `tamanho_bytes` | INTEGER | Tamanho do arquivo |
| `data_geracao` | DATETIME | Timestamp da geração |

### 1.3 `relatorios_ia_personalizados` (futuro, v2)

Modelos de prompt salvos pelo usuário para relatórios recorrentes.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | INTEGER PK AUTO | Identificador |
| `nome` | TEXT | Nome do template |
| `descricao` | TEXT | Descrição |
| `instrucoes_sistema` | TEXT | Prompt de sistema |
| `dados_incluir` | TEXT JSON | Quais fontes de dados incluir |
| `criado_por` | INTEGER FK→usuarios | |
| `data_criacao` | DATETIME | |

---

## 2. Campos Novos em Tabelas Existentes

### `clientes`

```sql
ALTER TABLE clientes ADD COLUMN ultimo_relatorio_ia_id INTEGER DEFAULT NULL;
ALTER TABLE clientes ADD COLUMN data_ultimo_relatorio_ia DATETIME DEFAULT NULL;
```

---

## 3. Estrutura de Arquivos

```
services/
├── __init__.py
├── mitsubishi.py                          # existente
├── ia/
│   ├── __init__.py
│   ├── provider.py                        # Factory pattern para provedores
│   ├── openai_client.py                   # Integração OpenAI
│   ├── gemini_client.py                   # (futuro) Integração Gemini
│   ├── ollama_client.py                   # (futuro) Integração Ollama
│   ├── prompt_builder.py                  # Montagem de prompts + contexto
│   └── token_counter.py                   # Estimativa de tokens antes da chamada
├── relatorios_ia/
│   ├── __init__.py
│   ├── engine.py                          # Orquestrador principal
│   ├── data_collector.py                  # Coleta dados do banco para o prompt
│   ├── pdf_generator.py                   # Geração de PDF (Markdown → HTML → PDF)
│   └── templates/
│       ├── cliente_360.md.j2              # Template prompt: análise de cliente
│       ├── pipeline_os.md.j2              # Template prompt: análise de pipeline
│       ├── faturamento.md.j2              # Template prompt: análise financeira
│       ├── oportunidades.md.j2            # Template prompt: análise oportunidades
│       └── parque_maquinas.md.j2          # Template prompt: análise máquinas

pages/
├── ...                                     # existentes
├── 40_Relatorios_IA.py                     # Página principal do módulo
├── 41_Relatorio_Visualizar.py              # Visualização de relatório individual
├── 42_Relatorio_Historico.py               # Histórico de relatórios gerados

database.py                                 # adicionar criação das novas tabelas
```

---

## 4. Serviços — Camada de IA

### 4.1 `services/ia/provider.py` — Factory de provedores

```python
class AIProvider(ABC):
    @abstractmethod
    def gerar_relatorio(self, prompt_sistema, prompt_usuario, modelo) -> dict:
        """Retorna {"conteudo": str, "tokens_in": int, "tokens_out": int}"""

class AIProviderFactory:
    @staticmethod
    def criar(provedor: str) -> AIProvider:
        # openai → OpenAIProvider
        # gemini → GeminiProvider
        # ollama → OllamaProvider
```

### 4.2 `services/ia/openai_client.py` — Integração OpenAI

- API: `chat/completions`
- Modelo principal: `gpt-4o` (melhor custo-benefício)
- Fallback: `gpt-4o-mini` (relatórios simples)
- Timeout: 120s com retry (3 tentativas, backoff exponencial)
- Streaming: opcional para exibir progresso

Configuração via tabela `configuracoes`:

| Chave | Valor Padrão | Descrição |
|-------|-------------|-----------|
| `ai_provedor_padrao` | `openai` | Provedor ativo |
| `ai_modelo_padrao` | `gpt-4o` | Modelo ativo |
| `openai_api_key` | - | Chave da API |
| `ai_max_tokens` | `4000` | Limite por relatório |

### 4.3 `services/ia/gemini_client.py` — (Futuro)

- API Google Generative AI
- Modelo: `gemini-2.0-pro-exp`
- Quando: após validação da Fase 1

### 4.4 `services/ia/ollama_client.py` — (Futuro)

- API local: `http://localhost:11434/api/generate`
- Modelo: `llama3` ou `mistral`
- Vantagem: sem custo, dados não saem da rede

### 4.5 `services/ia/prompt_builder.py`

Funções:
- `montar_prompt_sistema(tipo_relatorio) → str` — carrega template + instruções de formatação
- `montar_contexto_cliente(cliente_id) → dict` — faturamento, OS, máquinas, visitas
- `montar_contexto_pipeline(unidade, periodo) → dict` — OS por status, taxas de conversão
- `montar_contexto_oportunidades(unidade) → dict` — oportunidades abertas por estágio

### 4.6 `services/ia/token_counter.py`

- `estimar_tokens(texto) → int`: ~4 chars por token
- `validar_limites(prompt, modelo) → bool`
- `calcular_custo(tokens_in, tokens_out, modelo) → float`

---

## 5. Fluxo Completo

```
Usuário na página 40_Relatorios_IA.py
  │
  ├─ 1. Seleciona TIPO de relatório
  │    • Análise de Cliente (seleciona cliente)
  │    • Análise de Pipeline OS (filtro unidade/período)
  │    • Análise de Oportunidades (filtro unidade)
  │    • Análise de Faturamento (filtro unidade/período)
  │    • Análise do Parque Mitsubishi (filtro estado)
  │    • Relatório Personalizado (instruções livres)
  │
  ├─ 2. Configura parâmetros
  │    • Período (mês/ano ou YTD)
  │    • Instruções adicionais (opcional)
  │    • Provedor IA (OpenAI / futuro Gemini/Ollama)
  │    • Modelo (gpt-4o / gpt-4o-mini)
  │
  ├─ 3. Clica "GERAR RELATÓRIO"
  │
  ├─ 4. Sistema executa:
  │    a. Coleta dados do banco (data_collector.py)
  │    b. Monta prompt (prompt_builder.py)
  │    c. Estima tokens e custo (token_counter.py)
  │    d. Exibe estimativa de custo + confirmação
  │    e. Chama provedor IA com streaming
  │    f. Salva resultado na tabela relatorios_ia
  │    g. Renderiza Markdown na tela
  │
  ├─ 5. Relatório exibido com opções:
  │    • 📄 Exportar PDF
  │    • 📋 Copiar texto
  │    • 🔄 Regenerar com mesmos parâmetros
  │    • 📝 Editar prompt e gerar novamente
  │
  └─ 6. Navegação para histórico ou novo relatório
```

---

## 6. Fluxo de Geração PDF

```
Usuário clica "Exportar PDF"
  │
  ├─ 1. Conteúdo Markdown → HTML (biblioteca markdown)
  │    • Template HTML com CSS impressão (logo, cabeçalho, rodapé)
  │    • Tabelas, gráficos (Plotly como PNG base64)
  │
  ├─ 2. HTML → PDF (weasyprint)
  │    • Formato A4, margens 2cm, numeração de páginas
  │
  ├─ 3. Salva em: backups/relatorios_pdf/relatorio_{id}_{data}.pdf
  │
  ├─ 4. Registra em relatorios_ia_pdf
  │
  └─ 5. Download automático
```

---

## 7. Fluxo de Histórico

```
Página 42_Relatorio_Historico.py
  │
  ├─ Grid com filtros: tipo, período, unidade, provedor, cliente
  │
  ├─ Cada relatório exibe:
  │    • Título, tipo, data, usuário, custo, status
  │    • Ações: Visualizar | Download PDF | Regenerar | Excluir
  │
  └─ Visualização (página 41): mesmo layout da geração, modo leitura
```

---

## 8. Integração com Pipeline OS

1. **Botão "Gerar Relatório IA"** na página `11_Pipeline_OS.py` → chama `40_Relatorios_IA.py` com parâmetros pré-preenchidos

2. **Dados enviados no prompt**:
   - Total de OS por status
   - Taxa de conversão por estágio
   - Ticket médio por estágio
   - OS com follow-up vencido
   - Top equipamentos com demanda
   - Lead time médio (recebimento → aprovação → faturamento)

3. **Futuro (v2)**: Sugestão de priorização baseada em valor, cliente, tempo parado

---

## 9. Dependências Necessárias

### Produção

| Pacote | Versão Mínima | Motivo |
|--------|--------------|--------|
| `openai` | >=1.0 | API OpenAI |
| `markdown` | >=3.5 | Markdown → HTML |
| `weasyprint` | >=60 | HTML → PDF |
| `jinja2` | >=3.0 | Templates de prompt |
| `tiktoken` | >=0.5 | Contagem precisa de tokens |

### Futuro (instalação condicional)

| Pacote | Módulo | Motivo |
|--------|--------|--------|
| `google-generativeai` | Gemini | API Google |
| `ollama` (HTTP) | Ollama | LLM local |

---

## 10. Riscos Técnicos

| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| **Custo OpenAI imprevisível** | Financeiro | Exibir estimativa antes de confirmar; limitar tokens; fallback gpt-4o-mini |
| **Latência** | UX | Streaming; timeout 120s; retry 3x; cache |
| **Alucinação** | Qualidade | Prompt engineering com contexto real; "não invente dados"; regeneração |
| **PDF com gráficos** | Técnico | Plotly → PNG base64 → HTML; testar weasyprint no Windows |
| **API externa indisponível** | Disponibilidade | Fallback entre provedores; mensagem de erro clara |
| **Dados sensíveis no prompt** | Segurança | Não incluir CNPJ/telefone sem autorização; Ollama local como alternativa |
| **Contexto excessivo** | Qualidade | Resumir dados consolidados; dividir relatórios longos em seções |

---

## 11. Estimativa de Implementação

| Fase | Atividade | Estimativa |
|------|-----------|------------|
| **1** | Estrutura de banco (SQL + database.py) | 2h |
| **2** | Provider factory + OpenAI client | 4h |
| **3** | Prompt builder + templates (5 templates) | 6h |
| **4** | Data collector (coleta dados do banco) | 4h |
| **5** | Página principal (40_Relatorios_IA.py) | 8h |
| **6** | Geração PDF (markdown → HTML → PDF) | 6h |
| **7** | Página de visualização (41_Relatorio_Visualizar.py) | 4h |
| **8** | Página de histórico (42_Relatorio_Historico.py) | 4h |
| **9** | Integração Pipeline OS (botão + parâmetros) | 3h |
| **10** | Testes + ajustes | 6h |
| **11** | Gemini client (futuro) | Após validação |
| **12** | Ollama client (futuro) | Após validação |
| | **Total Fases 1-10** | **~47h (~6 dias úteis)** |

---

## 12. Diagrama de Fluxo

```
┌─────────────────────────────────────────────────────────────┐
│                   Página 40_Relatorios_IA                   │
│  ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌─────────────┐  │
│  │ Cliente │  │ Pipeline │  │Faturamento│  │Personalizado │  │
│  │  360    │  │    OS    │  │          │  │             │  │
│  └────┬────┘  └────┬─────┘  └────┬─────┘  └──────┬──────┘  │
│       └────────────┼──────────────┼────────────────┘         │
│                    ▼              ▼                          │
│              ┌──────────────────────────────┐                │
│              │    services/ia/provider.py   │                │
│              │    Factory Pattern           │                │
│              └──────┬───────────────────────┘                │
│                     │                                       │
│          ┌──────────┼──────────┐                            │
│          ▼          ▼          ▼                             │
│  ┌───────────┐ ┌────────┐ ┌──────────┐                     │
│  │  OpenAI   │ │ Gemini │ │  Ollama  │                     │
│  │  (ativo)  │ │(futuro)│ │ (futuro) │                     │
│  └─────┬─────┘ └────────┘ └──────────┘                     │
│        │                                                   │
│        ▼                                                   │
│  ┌──────────────────────────────────────────┐               │
│  │         prompt_builder.py                │               │
│  │  Template + dados_reais → prompt final   │               │
│  └──────────────────┬───────────────────────┘               │
│                     │                                       │
│                     ▼                                       │
│  ┌──────────────────────────────────────────┐               │
│  │         engine.py (orquestrador)          │               │
│  │  1. Coleta dados (data_collector.py)     │               │
│  │  2. Estima tokens (token_counter.py)     │               │
│  │  3. Chama IA                             │               │
│  │  4. Salva em relatorios_ia               │               │
│  │  5. Renderiza resultado                  │               │
│  └──────────────────┬───────────────────────┘               │
│                     │                                       │
│                     ▼                                       │
│  ┌──────────────────────────────────────────┐               │
│  │    Resultado exibido na tela (Markdown)   │               │
│  │  Ações: Exportar PDF │ Copiar │ Regenerar │               │
│  └──────────────────────────────────────────┘               │
└─────────────────────────────────────────────────────────────┘