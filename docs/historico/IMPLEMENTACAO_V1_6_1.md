# IMPLEMENTAÇÃO V1.6.1 — CORREÇÕES E CONSOLIDAÇÃO PRÉ-V1.7

**Data:** 24/06/2026  
**Versão:** 1.6.1  
**Base:** V1.6 (auditada e estável)

---

## 1. Arquivos Alterados

| Arquivo | Tipo de Alteração |
|---------|------------------|
| `_corrige_abcd.py` | Script único para popular classificação ABCD no banco |
| `pages/01_Base_Clientes.py` | + Bloqueio de acesso para perfil OPERADOR |
| `pages/00_Dashboard.py` | - Remoção do gráfico de sazonalidade e projeção |
| `pages/10_Central_Oportunidades.py` | Reescrevido com novas seções e limpeza visual |
| `_gen_snapshot.py` | Script temporário (pode ser removido) |

---

## 2. Correções Realizadas

### 2.1 Classificação ABCD (ETAPA 2)

**Problema:** Coluna `classe_abc` no banco nunca foi populada — todos os 839 clientes ativos estavam como "D".

**Correção:** Script `_corrige_abcd.py` que:
- Calcula faturamento 12m agregado da tabela `faturamento`
- Aplica regra A=10%, B=30%, C=60% sobre clientes com faturamento > 0
- Clientes sem faturamento → D
- Executa `UPDATE clientes SET classe_abc = ? WHERE id = ?` para todos os 839 registros

**Resultado pós-correção:**
- Classe A: 26 clientes
- Classe B: 79 clientes
- Classe C: 158 clientes
- Classe D: 576 clientes

**Nota:** O Dashboard ainda recalcula a classificação em runtime com sliders customizáveis. A coluna do banco agora está consistente com a função `classificar_abcd()` do módulo de inteligência comercial.

### 2.2 Base Clientes (ETAPA 3)

**Problema:** Página redundante (Base Mestre de Clientes) poluía o menu para todos os perfis.

**Correção:** Adicionado bloqueio de acesso no início do arquivo:
- Perfil OPERADOR → vê mensagem de acesso restrito e `st.stop()`
- Perfis MASTER, SOCIO, GESTOR → acesso normal

**Página não foi removida.** Permanece acessível internamente.

### 2.3 Dashboard (ETAPA 4)

**Problema:** Componentes identificados como descartáveis ou sem valor operacional:
- Gráfico "Faturamento Mensal — Projeção com Sazonalidade" (complexidade desnecessária)
- Seção "Análise de Sazonalidade e Tendência" com KPIs redundantes
- "Linha de Ritmo (2025 vs 2026)"

**Correção:** Removidas as 3 seções (aproximadamente 230 linhas). O Dashboard manteve:
- Cards de indicadores (Clientes, Ativos, Receita, Ticket, Classe A, Sem Fat.)
- Top Clientes (barras horizontais + treemap)
- Distribuição ABC
- Ranking Potencial Comercial
- Tabelas de Oportunidades e Ranking ABC

---

## 3. Melhorias de Usabilidade

### 3.1 Central de Oportunidades (ETAPAS 5, 6, 7)

#### Seção "O QUE FAZER HOJE" (NOVA)
- Lista consolidada de ações urgentes ordenadas por prioridade
- Mistura: pendências vencidas, pendências de hoje, OS aguardando aprovação, visitas atrasadas, clientes esfriando
- Cada linha mostra: cliente, descrição, responsável, vencimento
- Destaque por cor: vermelho (vencida), amarelo (vence hoje), laranja (esfriando)

#### Indicadores Simplificados
- Removidos tooltips excessivamente longos
- Nomes de KPIs mais enxutos

#### Limpeza Visual
- Removidos emojis excessivos dos títulos das seções
- Abas renomeadas para nomes mais diretos: "Grid" e "Detalhes" ao invés de "Grid Ranking" e "Cards Detalhados"
- Removidos termos técnicos desnecessários
- Títulos de seção simplificados (ex: "COMERCIAL" → "Listas Acionáveis")
- Reduced caption verbosity

#### Pendências com Detalhamento
- Agora exibe: Cliente, Descrição, Responsável, Prioridade, Vencimento formatado
- Mostra quem é o responsável pela pendência

#### Alertas Acionáveis
- Transformados de indicadores numéricos em listas com cliente e detalhes

#### Clientes Esfriando e Esquentando
- Agora mostram os clientes, não apenas quantidades

---

## 4. Ajustes na Central de Oportunidades

### Estrutura Final da Página

1. **O QUE FAZER HOJE** — Lista de ações urgentes (NOVA)
2. **Indicadores** — 6 KPIs simplificados
3. **Prioridades Comerciais** — Top 20 com score (Grid + Detalhes)
4. **Listas Acionáveis** — Esfriando, Esquentando, Sem Visita, Sem Faturamento, ABCD
5. **Operacional** — Top Faturamento, OS Aprovação, Preventivas, Prospecção
6. **Relacionamento** — Alertas, Pendências, Próximas Ações

### Abas Renomeadas
- "🔴 Esfriando" → "Clientes Esfriando"
- "🟢 Esquentando" → "Clientes Esquentando"
- "💰 Top Faturamento 12m" → "Top Faturamento 12m"
- "📊 Classificação ABCD" → "Classificação ABCD"

---

## 5. Ajustes no Dashboard

### Remoções
- Gráfico de Faturamento Mensal com projeção sazonal (Plotly complexo)
- Seção de Análise de Sazonalidade e Tendência (3 KPIs)
- Linha de Ritmo 2025 vs 2026

### Mantido
- Cards de KPIs principais
- Top Clientes (barras + treemap)
- Distribuição ABC
- Ranking Potencial Comercial
- Tabelas de Oportunidades e Ranking ABC
- Tabela de Maiores Clientes

---

## 6. Ajustes no Menu

Nenhum arquivo de menu foi alterado. O Streamlit gera o menu automaticamente a partir dos arquivos em `pages/`. O bloqueio de acesso na Base Clientes para OPERADOR atinge o mesmo efeito de "ocultar" para usuários comuns, sem remover a página.

---

## 7. Riscos Identificados

| Risco | Severidade | Mitigação |
|-------|-----------|-----------|
| Dashboard recalcula classificação em runtime com sliders, divergindo do banco | Baixa | Banco agora está correto. Sliders são configuráveis para simulações |
| Script `_corrige_abcd.py` foi executado uma vez — se novos clientes forem importados, a coluna ficará desatualizada | Média | Necessário script periódico ou trigger na importação (pendente para V1.7) |
| `_corrige_abcd.py` e `_gen_snapshot.py` são scripts temporários no diretório raiz | Muito Baixa | Podem ser removidos ou movidos para `scripts/` |
| Central de Oportunidades removiu seção "ENGENHARIA MAIS COMERCIAL" e "🤝 RELACIONAMENTO" com emoji, mas manteve todo o conteúdo | Baixa | Apenas nomenclatura visual alterada |
| Seção "O QUE FAZER HOJE" depende de `get_pendencias()` que requer dados na tabela `pendencias_comerciais` | Baixa | Se não houver dados, exibe "Nenhuma ação urgente" |

---

## 8. Pendências para V1.7

- [ ] Popular `classe_abc` automaticamente na importação de clientes (trigger ou script periódico)
- [ ] Unificar a fonte de classificação ABCD (apenas banco ou apenas cálculo em tempo real — filtrar redundância)
- [ ] Remover sliders de percentual do Dashboard (ou unificar com a regra do banco)
- [ ] Padronizar nomenclatura: `classificacao` para score AAA/AA/A/B/C e `classe_abc` para ABCD
- [ ] Avaliar se a página Base Clientes pode ser substituída pela busca dentro do Cliente 360
- [ ] Criar diretório `scripts/` para utilitários e mover `_corrige_abcd.py` e `_gen_snapshot.py`
- [ ] Testar fluxo completo com usuário real na Central de Oportunidades
- [ ] Iniciar desenvolvimento da V1.7 com base neste relatório

---

## Resumo

| Etapa | Status |
|-------|--------|
| ETAPA 1 — Ponto de restauração | ✅ backup/pre_v1_6_1/ criado |
| ETAPA 2 — Classificação ABCD | ✅ Banco populado corretamente |
| ETAPA 3 — Base Clientes | ✅ Acesso restrito para OPERADOR |
| ETAPA 4 — Dashboard | ✅ Componentes descartáveis removidos |
| ETAPA 5 — Central de Oportunidades | ✅ Melhorias implementadas |
| ETAPA 6 — O QUE FAZER HOJE | ✅ Seção criada |
| ETAPA 7 — Limpeza visual | ✅ Títulos e abas revisados |
| ETAPA 8 — Validação | ✅ ast.parse() OK nos 3 arquivos |
| Relatório gerado | ✅ docs/IMPLEMENTACAO_V1_6_1.md |

**V1.6.1 concluída. Pronto para V1.7.**