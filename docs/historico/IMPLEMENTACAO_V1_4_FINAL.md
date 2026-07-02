# Implementação V1.4 — Pendência Viva

## Arquivos Alterados

| Arquivo | Alterações |
|---------|------------|
| `services/relacionamento.py` | - Removido parâmetro `tipo_evolucao` da função `criar_evolucao_pendencia`<br>- Adicionado parâmetro `proximo_contato` (opcional)<br>- Quando `proximo_contato` é fornecido, atualiza automaticamente `data_limite` da pendência<br>- Descrição da evolução inclui automaticamente "Próximo contato definido para DD/MM/YYYY"<br>- Query `get_pendencias` agora retorna `ultima_atualizacao` (data da evolução mais recente) |
| `pages/06_Relacionamento_Comercial.py` | - Removido import de `TIPOS_EVOLUCAO` (não usado)<br>- Formulário de evolução: campo "Tipo" substituído por "Próximo Contato" (date_input)<br>- Label do botão alterado para "Registrar Atualização"<br>- Chamada a `criar_evolucao_pendencia` ajustada (sem `tipo_evolucao`, com `proximo_contato`) |

## Funcionalidades Implementadas

### 1. Tipo da Evolução Removido
O campo "Tipo da Evolução" foi completamente removido da interface. Toda evolução registrada via formulário é salva como `COMENTARIO` no banco.

### 2. Próximo Contato Adicionado
Um campo `date_input` "Próximo Contato" foi adicionado ao formulário de evolução, logo abaixo do campo de comentário.

### 3. Atualização Automática da data_limite
Quando o campo "Próximo Contato" é preenchido ao registrar uma evolução:
- A `data_limite` da pendência é automaticamente atualizada para a nova data
- A agenda e os alertas passam a considerar a nova data imediatamente

### 4. Timeline Aprimorada
Cada evolução registra automaticamente na descrição:
- O comentário do usuário
- "Próximo contato definido para DD/MM/YYYY" (se preenchido)

### 5. Última Atualização na Listagem
A query `get_pendencias` agora inclui a coluna `ultima_atualizacao` obtida da evolução mais recente de cada pendência.

### 6. Agenda
A função `get_agenda` já utilizava `data_limite` diretamente da tabela `pendencias_comerciais`, portanto qualquer alteração na `data_limite` (via evolução) é automaticamente refletida na agenda — sem necessidade de alteração.

### 7. Alertas
Os alertas já utilizavam `data_limite` para determinar:
- `data_limite < hoje` → Pendência vencida
- `data_limite = hoje` → Contato previsto para hoje (a query da agenda já trata este caso)

Nenhuma alteração foi necessária nos alertas.

## Testes Executados

- `py_compile services/relacionamento.py` → **OK**
- `py_compile pages/06_Relacionamento_Comercial.py` → **OK**

## Pendências Futuras

- Considerar exibir `ultima_atualizacao` explicitamente nos cards de pendência na interface
- Adicionar indicador visual de "pendência viva" (com evoluções recentes) na listagem
- Notificar responsável quando `data_limite` for alterada por outro usuário