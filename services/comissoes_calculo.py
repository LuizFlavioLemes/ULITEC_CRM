"""
Motor de Projeção Dinâmica — Gestão Comercial ULITEC CRM v1.0

Responsável exclusivamente por:
  - Calcular projeção de comissão em memória
  - NUNCA gravar dados no banco
  - NUNCA criar snapshot
  - NUNCA alterar histórico

Regras:
  - UMA única consulta de faturamento (processamento em memória)
  - Impostos aplicados apenas se base_calculo = 'LIQUIDO'
  - Escopo respeita faturamento_considerado (GRUPO, ULITEC SP, ULITEC RS)
  - Resultado usado APENAS para exibição no Dashboard
"""

from typing import Optional

from services.comissoes_db import (
    query_faturamento_periodo,
    query_faturamento_periodo_unidade,
    query_carteira_parceiro,
    query_parceiros_ativos,
    get_conn,
)

def _aplicar_impostos(valor_bruto: float, aliquota: float) -> tuple:
    """
    Aplica alíquota de impostos sobre o valor bruto.
    Retorna (valor_impostos, valor_liquido).
    """
    if aliquota <= 0:
        return 0.0, valor_bruto
    valor_impostos = valor_bruto * (aliquota / 100)
    valor_liquido = valor_bruto - valor_impostos
    return round(valor_impostos, 2), round(valor_liquido, 2)

def _calcular_comissao(valor_base: float, percentual: float) -> float:
    """Calcula o valor da comissão com base no percentual."""
    return round(valor_base * (percentual / 100), 2)

def projetar_comissao_mes(ano: int, mes: int) -> list:
    """
    Calcula a projeção de comissão para um mês específico.
    Processamento 100% em memória.

    Retorna lista de dicts:
    [
        {
            "parceiro_id": int,
            "parceiro_nome": str,
            "percentual": float,
            "base_calculo": str,
            "aliquota_impostos": float,
            "faturamento_considerado": str,
            "clientes": [
                {"cliente_id": int, "nome": str, "valor_bruto": float,
                 "valor_liquido": float, "valor_comissao": float}
            ],
            "total_clientes": int,
            "valor_bruto": float,
            "valor_impostos": float,
            "valor_liquido": float,
            "valor_comissao": float,
        }
    ]
    """
    data_inicio = f"{ano:04d}-{mes:02d}-01"
    # Último dia do mês
    if mes == 12:
        data_fim = f"{ano + 1:04d}-01-01"
    else:
        data_fim = f"{ano:04d}-{mes + 1:02d}-01"

    # 1. Buscar parceiros ativos
    parceiros = query_parceiros_ativos()
    if not parceiros:
        return []

    # 2. Buscar faturamento do período — UMA ÚNICA VEZ
    # Vamos buscar para cada escopo possível
    faturamento_grupo = {}
    faturamento_sp = {}
    faturamento_rs = {}

    # Mapeia cliente_id -> valor para GRUPO
    rows_grupo = query_faturamento_periodo(data_inicio, data_fim)
    for cid, total in rows_grupo:
        faturamento_grupo[cid] = total

    # Mapeia para SP
    rows_sp = query_faturamento_periodo_unidade(data_inicio, data_fim, "ULITEC SP")
    for cid, total in rows_sp:
        faturamento_sp[cid] = total

    # Mapeia para RS
    rows_rs = query_faturamento_periodo_unidade(data_inicio, data_fim, "ULITEC RS")
    for cid, total in rows_rs:
        faturamento_rs[cid] = total

    # 3. Mapa de faturamento por escopo
    mapa_faturamento = {
        "GRUPO": faturamento_grupo,
        "ULITEC SP": faturamento_sp,
        "ULITEC RS": faturamento_rs,
    }

    # 4. Nomes dos clientes (cache em memória)
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT id, razao_social FROM clientes")
    nomes_clientes = {r[0]: r[1] for r in cursor.fetchall()}
    conn.close()

    resultados = []

    for p in parceiros:
        p_id, p_nome, percentual, base_calculo, aliquota, escopo, dias_pag = p

        # 5. Buscar carteira do parceiro
        carteira_ids = query_carteira_parceiro(p_id)
        if not carteira_ids:
            continue

        # 6. Obter faturamento conforme escopo
        fat = mapa_faturamento.get(escopo, {})
        if not fat:
            continue

        # 7. Processar clientes da carteira
        clientes = []
        total_bruto = 0.0
        total_impostos = 0.0
        total_liquido = 0.0
        total_comissao = 0.0

        for cid in carteira_ids:
            valor_bruto = fat.get(cid, 0)
            if valor_bruto <= 0:
                continue

            if base_calculo == "LIQUIDO":
                imp, liq = _aplicar_impostos(valor_bruto, aliquota)
                valor_base = liq
            else:
                imp = 0.0
                liq = valor_bruto
                valor_base = valor_bruto

            comissao = _calcular_comissao(valor_base, percentual)

            clientes.append({
                "cliente_id": cid,
                "nome": nomes_clientes.get(cid, f"Cliente #{cid}"),
                "valor_bruto": round(valor_bruto, 2),
                "valor_liquido": round(liq, 2),
                "valor_comissao": comissao,
            })

            total_bruto += valor_bruto
            if base_calculo == "LIQUIDO":
                total_impostos += imp
            total_liquido += liq
            total_comissao += comissao

        if not clientes:
            continue

        resultados.append({
            "parceiro_id": p_id,
            "parceiro_nome": p_nome,
            "percentual": percentual,
            "base_calculo": base_calculo,
            "aliquota_impostos": aliquota,
            "faturamento_considerado": escopo,
            "clientes": clientes,
            "total_clientes": len(clientes),
            "valor_bruto": round(total_bruto, 2),
            "valor_impostos": round(total_impostos, 2),
            "valor_liquido": round(total_liquido, 2),
            "valor_comissao": round(total_comissao, 2),
        })

    return resultados

def projetar_por_periodo(ano_inicio: int, mes_inicio: int,
                         ano_fim: int, mes_fim: int,
                         parceiro_id: Optional[int] = None) -> list:
    """
    Calcula projeção para um período de meses.
    Retorna agregado mensal para gráficos de tendência.

    Cada elemento:
    {
        "competencia": "2026-07",
        "parceiro_id": int,
        "parceiro_nome": str,
        "valor_comissao": float,
    }
    """
    resultados = []
    ano, mes = ano_inicio, mes_inicio

    while (ano < ano_fim) or (ano == ano_fim and mes <= mes_fim):
        projecoes = projetar_comissao_mes(ano, mes)
        competencia = f"{ano:04d}-{mes:02d}"

        for proj in projecoes:
            if parceiro_id and proj["parceiro_id"] != parceiro_id:
                continue
            resultados.append({
                "competencia": competencia,
                "parceiro_id": proj["parceiro_id"],
                "parceiro_nome": proj["parceiro_nome"],
                "valor_comissao": proj["valor_comissao"],
            })

        mes += 1
        if mes > 12:
            mes = 1
            ano += 1

    return resultados