"""
Biblioteca de frases padronizadas ULITEC para relatórios técnicos.
V1.6.11 — Padrão de redação técnica industrial.
"""

# ── Frases de abertura para CAUSA ──
ABERTURA_CAUSA = [
    "Em análise técnica realizada em laboratório...",
    "Durante análise técnica realizada em laboratório...",
]

# ── Frases de diagnóstico ──
FRASES_DIAGNOSTICO = [
    "Foi isolada a falha no circuito de {circuito}, onde constatou-se {condicao}.",
    "Identificou-se componente(s) avariado(s) e/ou fora de especificação no setor de {circuito}.",
    "Verificou-se {condicao} no barramento de {circuito}, comprometendo o funcionamento do equipamento.",
    "Observou-se {condicao} na interface de comunicação {protocolo}, impossibilitando a troca de dados entre os módulos.",
    "Constatou-se {condicao} na fonte chaveada, resultando em tensões fora da faixa nominal de operação.",
    "Identificou-se falha no estágio de potência ({circuito}), com {condicao} nos semicondutores de saída.",
    "Verificou-se {condicao} no circuito de monitoramento de corrente, causando disparo indevido do sistema de proteção.",
]

# ── Circuitos comuns ──
CIRCUITOS = [
    "PWM",
    "barramento DC",
    "comunicação serial",
    "encoder",
    "fonte chaveada",
    "acionamento de potência",
    "monitoramento de corrente",
    "interface de controle",
    "driver de gate",
    "retificação",
    "inversor",
]

# ── Protocolos de comunicação ──
PROTOCOLOS = [
    "RS232",
    "RS422",
    "RS485",
    "Modbus RTU",
    "Modbus TCP",
    "PROFIBUS",
    "PROFINET",
    "EtherCAT",
    "CANbus",
    "DeviceNet",
    "CC-Link",
]

# ── Condições de falha ──
CONDICOES_FALHA = [
    "curto-circuito entre fases",
    "componente com fuga térmica",
    "capacitores eletrolíticos com ESR elevado",
    "trilha danificada por sobrecorrente",
    "componente com deriva térmica",
    "solda fria em junção crítica",
    "isolamento rompido por sobretensão",
    "contato intermitente por oxidação",
    "componente operando fora da faixa de tolerância",
    "circuito de proteção atuado indevidamente",
]

# ── Frases de SOLUÇÃO (passado - serviço realizado) ──
FRASES_SOLUCAO_PASSADO = [
    "Foi realizada a substituição de {componentes}.",
    "Foi executada a higienização da placa eletrônica em máquina ultrassônica.",
    "Foi realizada a secagem em estufa com temperatura controlada.",
    "Foi efetuada a substituição de componentes fora de especificação.",
    "Foi realizada a substituição da pasta térmica dos semicondutores de potência.",
    "Foram executados testes funcionais completos em simulador dedicado.",
    "Foi refeita a solda dos componentes do circuito de {circuito}.",
    "Foi reconstituída a trilha danificada do circuito de {circuito}.",
    "Foi realizado o reparo eletrônico especializado no módulo de {circuito}.",
    "Foram substituídos todos os capacitores eletrolíticos do conjunto por apresentarem ESR elevado.",
    "Foi realizada a calibração dos parâmetros de {circuito} conforme especificação do fabricante.",
    "Foi executada a limpeza dos conectores e bornes de comunicação com solvente dielétrico.",
    "Foi realizada a intervenção eletrônica especializada com substituição dos componentes críticos.",
    "Foi efetuada a substituição do conector de {protocolo} por apresentar oxidação nos terminais.",
]

# ── Frases de SOLUÇÃO (futuro - orçamento) ──
FRASES_SOLUCAO_FUTURO = [
    "Será realizada a substituição de {componentes}.",
    "Será executada a higienização da placa eletrônica em máquina ultrassônica.",
    "Será realizada a secagem em estufa com temperatura controlada.",
    "Será efetuada a substituição de componentes fora de especificação.",
    "Serão executados testes funcionais completos em simulador dedicado.",
]

# ── Frases de agregação de valor (para equipamentos eletrônicos) ──
AGREGACAO_VALOR = [
    "higienização em máquina ultrassônica",
    "secagem em estufa com temperatura controlada",
    "substituição de componentes fora de especificação",
    "substituição de pasta térmica",
    "testes funcionais completos em simulador dedicado",
    "testes em simulador dedicado",
]

# ── Frases de encerramento / validação ──
FRASES_VALIDACAO = [
    "Após os reparos, o equipamento apresentou funcionamento normal e estável durante os testes funcionais.",
    "O equipamento foi submetido a bancada de testes, apresentando funcionamento normal e estável.",
    "Testes funcionais completos em simulador dedicado realizados com sucesso.",
    "Equipamento testado e aprovado em bancada, com todos os parâmetros dentro da especificação do fabricante.",
]

# ── Observações padrão ──
OBSERVACOES_PADRAO = {
    "aterramento": "Verificar aterramento do equipamento antes da reinstalação.",
    "cablagem": "Verificar cablagem e conectores do equipamento no campo.",
    "isolação": "Verificar isolação dos motores e cabos de potência.",
    "obsoleto": "Equipamento obsoleto. Recomenda-se plano de substituição.",
    "descontinuado": "Peça/subconjunto descontinuado pelo fabricante. Avaliar alternativa compatível.",
    "rede": "Verificar qualidade da rede elétrica de alimentação.",
    "ventilação": "Verificar condições de ventilação do painel elétrico.",
    "preventiva": "Recomenda-se incluir este equipamento no plano de manutenção preventiva.",
}

# ── Tom: proibições ──
PALAVRAS_PROIBIDAS = [
    "achamos",
    "acreditamos",
    "parece",
    "talvez",
    "possivelmente",
    "provavelmente",
]

# ── Tom: palavras obrigatórias ──
PALAVRAS_PREFERENCIAIS = [
    "constatou-se",
    "verificou-se",
    "identificou-se",
    "observou-se",
    "foi constatado",
    "foi verificado",
    "foi identificado",
    "foi observado",
]

# ── Prompt de sistema para relatório técnico ULITEC ──
PROMPT_SISTEMA_ULITEC = """
Você é um engenheiro eletrônico especializado em manutenção industrial, automação CNC,
eletrônica de potência, serviços de campo e retrofit da empresa ULITEC.

Você deve gerar relatórios técnicos EXCLUSIVAMENTE no padrão ULITEC descrito abaixo.

## ESTRUTURA OBRIGATÓRIA (nesta ordem)

SINTOMA

CAUSA

SOLUÇÃO

OBSERVAÇÕES

## TOM

- Técnico
- Formal
- Engenharia industrial

NUNCA utilizar: achamos, acreditamos, parece, talvez, possivelmente, provavelmente.

SEMPRE que possível utilizar: constatou-se, verificou-se, identificou-se, observou-se,
foi constatado, foi verificado, foi identificado, foi observado.

## REGRAS POR SEÇÃO

### SINTOMA
- Descrever APENAS a falha observada em campo.
- NÃO explicar a causa.
- 1 a 3 parágrafos curtos.
- Exemplos:
  * "Equipamento apresentando alarme Z55."
  * "Falha de comunicação RS422."
  * "Servo motor com vibração excessiva."
  * "Acionamento sem habilitação."

### CAUSA
- SEMPRE iniciar com:
  * "Em análise técnica realizada em laboratório..."
  * ou "Durante análise técnica realizada em laboratório..."
- Explicar:
  * circuito analisado
  * falha encontrada
  * componentes avariados
  * mecanismo da falha
- Utilizar linguagem técnica como:
  * circuito PWM, barramento DC, monitoramento de corrente,
    comunicação serial, encoder, fonte chaveada
- 2 a 6 parágrafos.

### SOLUÇÃO
- Descrever EXATAMENTE o que foi realizado.
- Utilizar frases como:
  * "Foi realizada..."
  * "Foi executada..."
  * "Foi substituído..."
  * "Foi efetuada..."
- Para orçamento (serviço futuro):
  * "Será realizada..."
  * "Será executada..."
- DEVE citar:
  * componentes substituídos
  * reparos efetuados
  * ajustes realizados
  * testes executados

### AGREGAÇÃO DE VALOR (para equipamentos eletrônicos)
Quando fizer sentido, acrescentar AUTOMATICAMENTE:
- Higienização em máquina ultrassônica
- Secagem em estufa com temperatura controlada
- Substituição de componentes fora de especificação
- Substituição de pasta térmica
- Testes funcionais completos em simulador dedicado
- Testes em simulador dedicado

### OBSERVAÇÕES
- Formato numerado: I -, II -, III -, IV -, etc.
- Sugestões técnicas como:
  * Verificar aterramento do equipamento
  * Verificar cablagem e conectores
  * Verificar isolação dos motores
  * Equipamento obsoleto
  * Peça descontinuada

## EXEMPLO DE ENTRADA DO OPERADOR

"alarme z55 servomotor sem comunicacao rs422"

## EXEMPLO DE SAÍDA ESPERADA

SINTOMA

Equipamento apresentando alarme Z55.
Servomotor sem comunicação RS422 com a CNC.

CAUSA

Em análise técnica realizada em laboratório, foi identificada falha no circuito de
comunicação serial RS422. Constatou-se o driver de comunicação avariado, impossibilitando
a troca de dados entre o servomotor e a unidade de controle.

Verificou-se componente com fuga térmica no estágio de saída do driver,
comprometendo o nível de tensão diferencial da linha de comunicação.

Observou-se ainda capacitores eletrolíticos da fonte local do circuito de comunicação
com ESR elevado, fora da especificação original do fabricante.

SOLUÇÃO

Foi realizada a substituição do driver de comunicação serial RS422.
Foi efetuada a substituição dos capacitores eletrolíticos da fonte local por
apresentarem ESR elevado.
Foi executada a higienização da placa eletrônica em máquina ultrassônica e secagem
em estufa com temperatura controlada.
Foram executados testes funcionais completos em simulador dedicado, com
funcionamento normal e estável.

OBSERVAÇÕES

I - Verificar cablagem e conectores do servomotor no campo.
II - Verificar aterramento do painel elétrico.
""".strip()