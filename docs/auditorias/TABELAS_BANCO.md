# Estrutura do Banco de Dados

Total de tabelas: 23

## alertas

| Coluna | Tipo | PK | Obrigatório | Default |
|--------|------|----|-------------|--------|
| id | INTEGER | SIM | NÃO |  |
| tipo | TEXT |  | NÃO |  |
| descricao | TEXT |  | NÃO |  |
| data_alerta | DATE |  | NÃO |  |
| resolvido | INTEGER |  | NÃO | 0 |

## clientes

| Coluna | Tipo | PK | Obrigatório | Default |
|--------|------|----|-------------|--------|
| id | INTEGER | SIM | NÃO |  |
| codigo_erp | TEXT |  | NÃO |  |
| razao_social | TEXT |  | NÃO |  |
| nome_fantasia | TEXT |  | NÃO |  |
| cnpj | TEXT |  | NÃO |  |
| cidade | TEXT |  | NÃO |  |
| estado | TEXT |  | NÃO |  |
| telefone | TEXT |  | NÃO |  |
| email | TEXT |  | NÃO |  |
| segmento | TEXT |  | NÃO |  |
| parque_maquinas | INTEGER |  | NÃO | 0 |
| maquinas_mitsubishi | INTEGER |  | NÃO | 0 |
| frequencia_visita | INTEGER |  | NÃO | 90 |
| tipo_conta | TEXT |  | NÃO | 'LEAD FRIO' |
| classe_abc | TEXT |  | NÃO | 'D' |
| faturamento_12m | REAL |  | NÃO | 0 |
| ultima_visita | DATE |  | NÃO |  |
| ultimo_faturamento | DATE |  | NÃO |  |
| origem_erp | TEXT |  | NÃO |  |
| observacoes | TEXT |  | NÃO |  |
| ultima_importacao | DATE |  | NÃO |  |
| status | TEXT |  | NÃO |  |
| data_cadastro | TEXT |  | NÃO |  |
| origem_cadastro | TEXT |  | NÃO |  |

## conciliacao_mitsubishi

| Coluna | Tipo | PK | Obrigatório | Default |
|--------|------|----|-------------|--------|
| id | INTEGER | SIM | NÃO |  |
| maquina_id | INTEGER |  | NÃO |  |
| cliente_sugerido_id | INTEGER |  | NÃO |  |
| customer | TEXT |  | NÃO |  |
| cliente_sugerido | TEXT |  | NÃO |  |
| score | REAL |  | NÃO |  |
| status | TEXT |  | NÃO | 'REVISAO' |

## config_ia

| Coluna | Tipo | PK | Obrigatório | Default |
|--------|------|----|-------------|--------|
| id | INTEGER | SIM | NÃO |  |
| api_key | TEXT |  | NÃO |  |
| modelo | TEXT |  | NÃO | 'gpt-4o-mini' |
| ativo | INTEGER |  | NÃO | 1 |
| criado_em | TEXT |  | NÃO | datetime('now', 'localtime') |
| atualizado_em | TEXT |  | NÃO | datetime('now', 'localtime') |

## config_importacao

| Coluna | Tipo | PK | Obrigatório | Default |
|--------|------|----|-------------|--------|
| id | INTEGER | SIM | NÃO |  |
| chave | TEXT |  |  |  |
| valor | REAL |  |  |  |
| descricao | TEXT |  | NÃO | '' |

## configuracoes

| Coluna | Tipo | PK | Obrigatório | Default |
|--------|------|----|-------------|--------|
| chave | TEXT | SIM | NÃO |  |
| valor | TEXT |  | NÃO |  |
| descricao | TEXT |  | NÃO |  |

## evolucao_pendencias

| Coluna | Tipo | PK | Obrigatório | Default |
|--------|------|----|-------------|--------|
| id | INTEGER | SIM | NÃO |  |
| pendencia_id | INTEGER |  |  |  |
| descricao | TEXT |  |  |  |
| tipo_evolucao | TEXT |  | NÃO | 'COMENTARIO' |
| usuario_id | INTEGER |  | NÃO |  |
| usuario_nome | TEXT |  | NÃO |  |
| criado_em | TEXT |  | NÃO | datetime('now', 'localtime') |

## faturamento

| Coluna | Tipo | PK | Obrigatório | Default |
|--------|------|----|-------------|--------|
| id | INTEGER | SIM | NÃO |  |
| cliente_id | INTEGER |  | NÃO |  |
| unidade | TEXT |  | NÃO |  |
| data_faturamento | DATE |  | NÃO |  |
| valor | REAL |  | NÃO |  |
| tipo | TEXT |  | NÃO |  |
| origem | TEXT |  | NÃO |  |

## faturamento_itens

| Coluna | Tipo | PK | Obrigatório | Default |
|--------|------|----|-------------|--------|
| id | INTEGER | SIM | NÃO |  |
| cliente_id | INTEGER |  | NÃO |  |
| unidade | TEXT |  | NÃO |  |
| descricao_item | TEXT |  | NÃO |  |
| tipo_item | TEXT |  | NÃO |  |
| data_venda | DATE |  | NÃO |  |
| valor_total | REAL |  | NÃO |  |
| origem | TEXT |  | NÃO |  |
| data_importacao | DATE |  | NÃO |  |

## interacoes

| Coluna | Tipo | PK | Obrigatório | Default |
|--------|------|----|-------------|--------|
| id | INTEGER | SIM | NÃO |  |
| cliente_id | INTEGER |  | NÃO |  |
| data_interacao | DATE |  | NÃO |  |
| tipo_interacao | TEXT |  | NÃO |  |
| responsavel | TEXT |  | NÃO |  |
| unidade | TEXT |  | NÃO |  |
| qtd_maquinas | INTEGER |  | NÃO |  |
| qtd_mitsubishi | INTEGER |  | NÃO |  |
| brinde_entregue | TEXT |  | NÃO |  |
| status_cliente | TEXT |  | NÃO |  |
| nivel_producao | TEXT |  | NÃO |  |
| perspectiva_6m | TEXT |  | NÃO |  |
| concorrentes | TEXT |  | NÃO |  |
| resumo | TEXT |  | NÃO |  |
| proxima_acao | TEXT |  | NÃO |  |
| data_proxima_acao | DATE |  | NÃO |  |
| assunto | TEXT |  | NÃO |  |
| resultado | TEXT |  | NÃO |  |
| usuario_id | INTEGER |  | NÃO |  |
| status_interacao | TEXT |  | NÃO | 'ABERTA' |
| resultado_comercial | TEXT |  | NÃO |  |
| contato_cargo | TEXT |  | NÃO |  |
| contato_telefone | TEXT |  | NÃO |  |
| contato_email | TEXT |  | NÃO |  |
| contato_nome | TEXT |  | NÃO |  |
| tipo_prox_acao | TEXT |  | NÃO |  |
| obs_prox_acao | TEXT |  | NÃO |  |

## maquinas_mitsubishi

| Coluna | Tipo | PK | Obrigatório | Default |
|--------|------|----|-------------|--------|
| id | INTEGER | SIM | NÃO |  |
| customer | TEXT |  | NÃO |  |
| address | TEXT |  | NÃO |  |
| city | TEXT |  | NÃO |  |
| uf | TEXT |  | NÃO |  |
| machine | TEXT |  | NÃO |  |
| serial_number | TEXT |  | NÃO |  |
| nc_series | TEXT |  | NÃO |  |
| nc_type | TEXT |  | NÃO |  |
| dealer | TEXT |  | NÃO |  |
| warranty_start | TEXT |  | NÃO |  |
| warranty_end | TEXT |  | NÃO |  |
| ano | INTEGER |  | NÃO |  |
| cliente_id | INTEGER |  | NÃO |  |
| score_match | REAL |  | NÃO |  |
| validado | INTEGER |  | NÃO | 0 |

## ncm_importacao

| Coluna | Tipo | PK | Obrigatório | Default |
|--------|------|----|-------------|--------|
| id | INTEGER | SIM | NÃO |  |
| ncm | TEXT |  |  |  |
| descricao | TEXT |  | NÃO | '' |
| tipo_produto_id | INTEGER |  | NÃO |  |
| ativo | INTEGER |  | NÃO | 1 |
| criado_em | DATE |  | NÃO | date('now') |
| atualizado_em | DATE |  | NÃO | date('now') |

## oportunidades

| Coluna | Tipo | PK | Obrigatório | Default |
|--------|------|----|-------------|--------|
| id | INTEGER | SIM | NÃO |  |
| cliente_id | INTEGER |  | NÃO |  |
| unidade | TEXT |  | NÃO |  |
| data_abertura | DATE |  | NÃO |  |
| origem | TEXT |  | NÃO |  |
| descricao | TEXT |  | NÃO |  |
| valor_estimado | REAL |  | NÃO |  |
| status | TEXT |  | NÃO |  |

## ordens_servico

| Coluna | Tipo | PK | Obrigatório | Default |
|--------|------|----|-------------|--------|
| id | INTEGER | SIM | NÃO |  |
| numero_os | TEXT |  | NÃO |  |
| cliente_id | INTEGER |  | NÃO |  |
| unidade | TEXT |  | NÃO |  |
| responsavel | TEXT |  | NÃO |  |
| equipamento | TEXT |  | NÃO |  |
| marca | TEXT |  | NÃO |  |
| modelo | TEXT |  | NÃO |  |
| serial_number | TEXT |  | NÃO |  |
| data_recebimento | DATE |  | NÃO |  |
| data_envio_proposta | DATE |  | NÃO |  |
| data_aprovacao | DATE |  | NÃO |  |
| data_faturamento | DATE |  | NÃO |  |
| data_expedicao | DATE |  | NÃO |  |
| data_perda | DATE |  | NÃO |  |
| valor_estimado | REAL |  | NÃO | 0 |
| valor_proposta | REAL |  | NÃO | 0 |
| status | TEXT |  | NÃO | 'RECEBIDA' |
| motivo_perda | TEXT |  | NÃO |  |
| proximo_followup | DATE |  | NÃO |  |
| observacoes | TEXT |  | NÃO |  |
| origem | TEXT |  | NÃO | 'MANUAL' |
| data_criacao | DATE |  | NÃO |  |
| data_atualizacao | DATE |  | NÃO |  |
| desconto_valor | REAL |  | NÃO | 0 |
| desconto_percentual | REAL |  | NÃO | 0 |
| valor_faturado | REAL |  | NÃO | 0 |
| tecnico | TEXT |  | NÃO |  |
| followup_count | INTEGER |  | NÃO | 0 |

## pendencias_comerciais

| Coluna | Tipo | PK | Obrigatório | Default |
|--------|------|----|-------------|--------|
| id | INTEGER | SIM | NÃO |  |
| cliente_id | INTEGER |  | NÃO |  |
| interacao_id | INTEGER |  | NÃO |  |
| descricao | TEXT |  | NÃO |  |
| prioridade | TEXT |  | NÃO | 'MEDIA' |
| responsavel | TEXT |  | NÃO |  |
| data_limite | DATE |  | NÃO |  |
| status | TEXT |  | NÃO | 'ABERTA' |
| criado_em | DATE |  | NÃO | date('now') |

## produtos_importados

| Coluna | Tipo | PK | Obrigatório | Default |
|--------|------|----|-------------|--------|
| id | INTEGER | SIM | NÃO |  |
| modelo | TEXT |  |  |  |
| descricao | TEXT |  | NÃO | '' |
| tipo_produto_id | INTEGER |  | NÃO |  |
| ncm_id | INTEGER |  | NÃO |  |
| fornecedor | TEXT |  | NÃO | '' |
| fob_atual_usd | REAL |  | NÃO | 0 |
| data_fob | DATE |  | NÃO |  |
| observacoes | TEXT |  | NÃO | '' |
| ativo | INTEGER |  | NÃO | 1 |
| ultimo_preco_venda | REAL |  | NÃO | NULL |
| criado_em | DATE |  | NÃO | date('now') |
| atualizado_em | DATE |  | NÃO | date('now') |
| modelo_busca | TEXT |  | NÃO | '' |

## produtos_importados_historico

| Coluna | Tipo | PK | Obrigatório | Default |
|--------|------|----|-------------|--------|
| id | INTEGER | SIM | NÃO |  |
| produto_id | INTEGER |  | NÃO |  |
| fornecedor | TEXT |  | NÃO | '' |
| valor_fob_usd | REAL |  | NÃO | 0 |
| data_atualizacao | DATE |  | NÃO |  |
| usuario_id | INTEGER |  | NÃO |  |
| observacao | TEXT |  | NÃO | '' |
| criado_em | DATE |  | NÃO | date('now') |
| fornecedor_busca | TEXT |  | NÃO | '' |

## propostas

| Coluna | Tipo | PK | Obrigatório | Default |
|--------|------|----|-------------|--------|
| id | INTEGER | SIM | NÃO |  |
| numero_os | TEXT |  | NÃO |  |
| cliente_id | INTEGER |  | NÃO |  |
| unidade | TEXT |  | NÃO |  |
| data_recebimento | DATE |  | NÃO |  |
| data_envio_proposta | DATE |  | NÃO |  |
| data_aprovacao | DATE |  | NÃO |  |
| data_faturamento | DATE |  | NÃO |  |
| data_expedicao | DATE |  | NÃO |  |
| valor_proposta | REAL |  | NÃO |  |
| status | TEXT |  | NÃO |  |
| observacoes | TEXT |  | NÃO |  |

## relatorios_ia

| Coluna | Tipo | PK | Obrigatório | Default |
|--------|------|----|-------------|--------|
| id | INTEGER | SIM | NÃO |  |
| cliente_id | INTEGER |  | NÃO |  |
| modelo | TEXT |  | NÃO |  |
| prompt_tokens | INTEGER |  | NÃO | 0 |
| completion_tokens | INTEGER |  | NÃO | 0 |
| tempo_execucao | REAL |  | NÃO | 0 |
| custo_estimado | REAL |  | NÃO | 0 |
| criado_em | TEXT |  | NÃO | datetime('now', 'localtime') |

## sqlite_sequence

| Coluna | Tipo | PK | Obrigatório | Default |
|--------|------|----|-------------|--------|
| name |  |  | NÃO |  |
| seq |  |  | NÃO |  |

## tipo_produto_importado

| Coluna | Tipo | PK | Obrigatório | Default |
|--------|------|----|-------------|--------|
| id | INTEGER | SIM | NÃO |  |
| descricao | TEXT |  |  |  |
| ii | REAL |  | NÃO | 0 |
| ipi | REAL |  | NÃO | 0 |
| pis | REAL |  | NÃO | 0 |
| cofins | REAL |  | NÃO | 0 |
| icms | REAL |  | NÃO | 0 |
| ativo | INTEGER |  | NÃO | 1 |

## unidades

| Coluna | Tipo | PK | Obrigatório | Default |
|--------|------|----|-------------|--------|
| id | INTEGER | SIM | NÃO |  |
| nome | TEXT |  |  |  |
| sigla | TEXT |  | NÃO |  |
| cidade | TEXT |  | NÃO |  |
| estado | TEXT |  | NÃO |  |

## usuarios

| Coluna | Tipo | PK | Obrigatório | Default |
|--------|------|----|-------------|--------|
| id | INTEGER | SIM | NÃO |  |
| login | TEXT |  | NÃO |  |
| senha | TEXT |  | NÃO |  |
| nome | TEXT |  | NÃO |  |
| email | TEXT |  | NÃO |  |
| nivel_acesso | TEXT |  | NÃO |  |
| senha_hash | TEXT |  | NÃO |  |
| ultimo_login | TEXT |  | NÃO |  |
| perfil | TEXT |  | NÃO | 'OPERADOR' |
| unidade_id | INTEGER |  | NÃO |  |
| ativo | INTEGER |  | NÃO | 1 |

