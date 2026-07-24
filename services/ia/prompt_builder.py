"""
Construção de prompts para a IA.
O template de sistema é mantido separado do código para facilitar manutenção.
"""

# Template do prompt de sistema (instrução fixa para a IA)
PROMPT_SISTEMA = """
Você é um consultor comercial industrial especialista em manutenção CNC, automação industrial, retrofit, eletrônica industrial e relacionamento B2B.

Analise exclusivamente os dados fornecidos.

Não invente informações.

Caso não existam dados suficientes, informe claramente.

Seu objetivo é auxiliar a equipe comercial da ULITEC na tomada de decisão, identificação de riscos, oportunidades e próximos passos.

---

Formato obrigatório da resposta:

1. **Resumo Executivo**
   - Síntese geral do cliente em até 3 parágrafos.

2. **Situação Comercial**
   - Faturamento, ticket médio, tendência, sazonalidade.

3. **Histórico de Relacionamento**
   - Interações recentes, frequência de visitas, qualidade do relacionamento.

4. **Riscos Identificados**
   - Riscos comerciais, técnicos ou operacionais.

5. **Oportunidades Identificadas**
   - Upsell, cross-sell, máquinas sem contrato, segmentos não explorados.

6. **Próximas Ações Recomendadas**
   - Ações concretas e priorizadas para o comercial.
""".strip()

def montar_contexto_cliente(
    cliente: dict,
    faturamento: dict,
    os_data: dict,
    oportunidades: dict,
    mitsubishi: dict,
    interacoes: list,
) -> str:
    """
    Monta o prompt de usuário com todos os dados coletados.

    Args:
        cliente: dict com dados do cliente
        faturamento: dict com dados de faturamento
        os_data: dict com dados de OS
        oportunidades: dict com dados de oportunidades
        mitsubishi: dict com dados Mitsubishi
        interacoes: list de dicts com interações

    Returns:
        String formatada com o contexto completo
    """
    linhas = []

    # --- Cliente ---
    linhas.append("## DADOS DO CLIENTE")
    if cliente:
        linhas.append(f"- Razão Social: {cliente.get('razao_social', 'N/D')}")
        linhas.append(f"- Cidade/UF: {cliente.get('cidade', 'N/D')}/{cliente.get('estado', 'N/D')}")
        linhas.append(f"- Segmento: {cliente.get('segmento', 'N/D')}")
        linhas.append(f"- Status: {cliente.get('status', 'N/D')}")
        obs = cliente.get('observacoes')
        if obs:
            linhas.append(f"- Observações: {obs}")
    else:
        linhas.append("Sem dados cadastrais disponíveis.")

    # --- Faturamento ---
    linhas.append("\n## FATURAMENTO (últimos 12 meses)")
    if faturamento and faturamento.get("faturamento_12m", 0) > 0:
        linhas.append(f"- Faturamento 12M: R$ {faturamento['faturamento_12m']:,.2f}")
        linhas.append(f"- Último faturamento: {faturamento['ultimo_faturamento']}")
        linhas.append(f"- Meses com faturamento: {faturamento['meses_faturados']}")
        linhas.append(f"- Média mensal: R$ {faturamento['media_mensal']:,.2f}")
    else:
        linhas.append("Sem faturamento nos últimos 12 meses.")

    # --- OS ---
    linhas.append("\n## ORDENS DE SERVIÇO (últimos 24 meses)")
    if os_data and os_data.get("quantidade_total", 0) > 0:
        linhas.append(f"- Total de OS: {os_data['quantidade_total']}")
        linhas.append(f"- Última OS: {os_data['ultima_os']}")
        linhas.append(f"- Valor total estimado: R$ {os_data['valor_total']:,.2f}")
        if os_data.get("por_status"):
            linhas.append("- Distribuição por status:")
            for status, qtd in os_data["por_status"].items():
                linhas.append(f"  - {status}: {qtd}")
    else:
        linhas.append("Nenhuma ordem de serviço encontrada.")

    # --- Oportunidades ---
    linhas.append("\n## OPORTUNIDADES")
    if oportunidades and (oportunidades.get("abertas", 0) > 0 or oportunidades.get("ganhas", 0) > 0):
        linhas.append(f"- Abertas: {oportunidades['abertas']}")
        linhas.append(f"- Ganhas: {oportunidades['ganhas']}")
        linhas.append(f"- Perdidas: {oportunidades['perdidas']}")
        linhas.append(f"- Valor potencial: R$ {oportunidades['valor_potencial']:,.2f}")
    else:
        linhas.append("Nenhuma oportunidade registrada.")

    # --- Mitsubishi ---
    linhas.append("\n## PARQUE MITSUBISHI")
    if mitsubishi and mitsubishi.get("quantidade", 0) > 0:
        linhas.append(f"- Quantidade de máquinas: {mitsubishi['quantidade']}")
        if mitsubishi.get("principais_series_cnc"):
            linhas.append("- Principais séries CNC:")
            for s in mitsubishi["principais_series_cnc"]:
                linhas.append(f"  - {s}")
    else:
        linhas.append("Nenhuma máquina Mitsubishi vinculada.")

    # --- Interações ---
    linhas.append("\n## INTERAÇÕES RECENTES (últimas 10)")
    if interacoes:
        for i, interacao in enumerate(interacoes, 1):
            linhas.append(f"\n{i}. Data: {interacao.get('data_interacao', 'N/D')}")
            linhas.append(f"   Tipo: {interacao.get('tipo_interacao', 'N/D')}")
            linhas.append(f"   Responsável: {interacao.get('responsavel', 'N/D')}")
            resumo = interacao.get("resumo", "")
            if resumo:
                linhas.append(f"   Resumo: {resumo}")
            prox = interacao.get("proxima_acao", "")
            if prox:
                linhas.append(f"   Próxima ação: {prox}")
    else:
        linhas.append("Nenhuma interação registrada.")

    linhas.append("\n---")
    linhas.append("Com base APENAS nos dados acima, gere a análise completa conforme o formato solicitado.")

    return "\n".join(linhas)

def montar_contexto_relatorio_tecnico(
    descricao_tecnica: str,
    cliente: str = "",
    numero_os: str = "",
    equipamento: str = "",
    marca: str = "",
    modelo: str = "",
    serial: str = "",
    componentes_substituidos: str = "",
    observacoes: str = "",
    modo_orcamento: bool = False,
) -> str:
    """
    Monta o prompt de usuário para geração de relatório técnico no padrão ULITEC.

    Args:
        descricao_tecnica: Descrição técnica livre (obrigatório)
        cliente: Nome do cliente (opcional)
        numero_os: Número da OS (opcional)
        equipamento: Nome do equipamento (opcional)
        marca: Marca do equipamento (opcional)
        modelo: Modelo do equipamento (opcional)
        serial: Número de série (opcional)
        componentes_substituidos: Componentes substituídos (opcional)
        observacoes: Observações adicionais (opcional)
        modo_orcamento: Se True, gera para orçamento (futuro)

    Returns:
        String formatada com o prompt completo
    """
    linhas = []

    linhas.append("# DADOS PARA RELATÓRIO TÉCNICO")
    linhas.append("")

    # Informações do equipamento/cadastro
    cabecalho = []
    if cliente:
        cabecalho.append(f"Cliente: {cliente}")
    if numero_os:
        cabecalho.append(f"OS: {numero_os}")
    if equipamento:
        cabecalho.append(f"Equipamento: {equipamento}")
    if marca:
        cabecalho.append(f"Marca: {marca}")
    if modelo:
        cabecalho.append(f"Modelo: {modelo}")
    if serial:
        cabecalho.append(f"Serial: {serial}")

    if cabecalho:
        linhas.append("## Informações")
        for info in cabecalho:
            linhas.append(f"- {info}")
        linhas.append("")

    # Descrição técnica (obrigatório)
    linhas.append("## Descrição Técnica")
    linhas.append("")
    linhas.append(descricao_tecnica)
    linhas.append("")

    # Componentes substituídos (se fornecido)
    if componentes_substituidos:
        linhas.append("## Componentes Substituídos")
        linhas.append("")
        linhas.append(componentes_substituidos)
        linhas.append("")

    # Observações adicionais (se fornecido)
    if observacoes:
        linhas.append("## Observações Adicionais")
        linhas.append("")
        linhas.append(observacoes)
        linhas.append("")

    # Modo
    if modo_orcamento:
        linhas.append("## Modo")
        linhas.append("")
        linhas.append("Gerar relatório para ORÇAMENTO (serviço futuro). Utilize 'Será realizada...' em SOLUÇÃO.")
        linhas.append("")

    linhas.append("---")
    linhas.append("")
    linhas.append("Com base APENAS nas informações acima, gere o relatório técnico completo no padrão ULITEC.")
    linhas.append("Siga rigorosamente a estrutura: SINTOMA, CAUSA, SOLUÇÃO, OBSERVAÇÕES.")

    return "\n".join(linhas)

def montar_prompt_completo(
    cliente: dict,
    faturamento: dict,
    os_data: dict,
    oportunidades: dict,
    mitsubishi: dict,
    interacoes: list,
) -> str:
    """
    Monta um prompt completo e estruturado em Markdown para uso externo
    (ChatGPT, Gemini, Claude), sem necessidade de API.

    Args:
        cliente: dict com dados do cliente
        faturamento: dict com dados de faturamento
        os_data: dict com dados de OS
        oportunidades: dict com dados de oportunidades
        mitsubishi: dict com dados Mitsubishi
        interacoes: list de dicts com interações

    Returns:
        String formatada com o prompt completo em Markdown
    """
    linhas = []

    # --- Cabeçalho do prompt ---
    linhas.append("# CONTEXTO")
    linhas.append("")
    linhas.append("Você é um consultor comercial industrial especializado em manutenção CNC, automação industrial e venda de peças de reposição.")
    linhas.append("")
    linhas.append("Analise os dados abaixo e gere:")
    linhas.append("")
    linhas.append("1. Resumo executivo")
    linhas.append("2. Situação comercial")
    linhas.append("3. Tendência do cliente")
    linhas.append("4. Riscos identificados")
    linhas.append("5. Oportunidades comerciais")
    linhas.append("6. Plano de ação de curto prazo")
    linhas.append("7. Plano de ação de médio prazo")
    linhas.append("8. Próxima visita recomendada")
    linhas.append("9. Serviços preventivos sugeridos")
    linhas.append("10. Potencial de venda de peças")
    linhas.append("")

    # --- Dados do Cliente ---
    linhas.append("---")
    linhas.append("")
    linhas.append("## DADOS DO CLIENTE")
    if cliente:
        linhas.append(f"- Razão Social: {cliente.get('razao_social', 'N/D')}")
        linhas.append(f"- Cidade/UF: {cliente.get('cidade', 'N/D')}/{cliente.get('estado', 'N/D')}")
        linhas.append(f"- Segmento: {cliente.get('segmento', 'N/D')}")
        linhas.append(f"- Status: {cliente.get('status', 'N/D')}")
        obs = cliente.get('observacoes')
        if obs:
            linhas.append(f"- Observações: {obs}")
    else:
        linhas.append("Sem dados cadastrais disponíveis.")
    linhas.append("")

    # --- Faturamento ---
    linhas.append("---")
    linhas.append("")
    linhas.append("## FATURAMENTO 12M")
    if faturamento and faturamento.get("faturamento_12m", 0) > 0:
        linhas.append(f"- Faturamento 12M: R$ {faturamento['faturamento_12m']:,.2f}")
        linhas.append(f"- Último faturamento: {faturamento['ultimo_faturamento']}")
        linhas.append(f"- Meses com faturamento: {faturamento['meses_faturados']}")
        linhas.append(f"- Média mensal: R$ {faturamento['media_mensal']:,.2f}")
    else:
        linhas.append("Sem faturamento nos últimos 12 meses.")
    linhas.append("")

    # --- OS ---
    linhas.append("---")
    linhas.append("")
    linhas.append("## ORDENS DE SERVIÇO")
    if os_data and os_data.get("quantidade_total", 0) > 0:
        linhas.append(f"- Total de OS: {os_data['quantidade_total']}")
        linhas.append(f"- Última OS: {os_data['ultima_os']}")
        linhas.append(f"- Valor total estimado: R$ {os_data['valor_total']:,.2f}")
        if os_data.get("por_status"):
            linhas.append("- Distribuição por status:")
            for status, qtd in os_data["por_status"].items():
                linhas.append(f"  - {status}: {qtd}")
    else:
        linhas.append("Nenhuma ordem de serviço encontrada.")
    linhas.append("")

    # --- Oportunidades ---
    linhas.append("---")
    linhas.append("")
    linhas.append("## OPORTUNIDADES")
    if oportunidades and (oportunidades.get("abertas", 0) > 0 or oportunidades.get("ganhas", 0) > 0):
        linhas.append(f"- Abertas: {oportunidades['abertas']}")
        linhas.append(f"- Ganhas: {oportunidades['ganhas']}")
        linhas.append(f"- Perdidas: {oportunidades['perdidas']}")
        linhas.append(f"- Valor potencial: R$ {oportunidades['valor_potencial']:,.2f}")
    else:
        linhas.append("Nenhuma oportunidade registrada.")
    linhas.append("")

    # --- Mitsubishi ---
    linhas.append("---")
    linhas.append("")
    linhas.append("## PARQUE MITSUBISHI")
    if mitsubishi and mitsubishi.get("quantidade", 0) > 0:
        linhas.append(f"- Quantidade de máquinas: {mitsubishi['quantidade']}")
        if mitsubishi.get("principais_series_cnc"):
            linhas.append("- Principais séries CNC:")
            for s in mitsubishi["principais_series_cnc"]:
                linhas.append(f"  - {s}")
    else:
        linhas.append("Nenhuma máquina Mitsubishi vinculada.")
    linhas.append("")

    # --- Interações ---
    linhas.append("---")
    linhas.append("")
    linhas.append("## INTERAÇÕES")
    if interacoes:
        for i, interacao in enumerate(interacoes, 1):
            linhas.append(f"{i}. Data: {interacao.get('data_interacao', 'N/D')}")
            linhas.append(f"   Tipo: {interacao.get('tipo_interacao', 'N/D')}")
            linhas.append(f"   Responsável: {interacao.get('responsavel', 'N/D')}")
            resumo = interacao.get("resumo", "")
            if resumo:
                linhas.append(f"   Resumo: {resumo}")
            prox = interacao.get("proxima_acao", "")
            if prox:
                linhas.append(f"   Próxima ação: {prox}")
            linhas.append("")
    else:
        linhas.append("Nenhuma interação registrada.")
        linhas.append("")

    # --- Instrução final ---
    linhas.append("---")
    linhas.append("")
    linhas.append("IMPORTANTE:")
    linhas.append("")
    linhas.append("Utilize apenas os dados fornecidos.")
    linhas.append("Não invente informações.")
    linhas.append("Quando não houver dados suficientes, informe explicitamente.")

    return "\n".join(linhas)