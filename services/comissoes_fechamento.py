"""
Motor de Fechamento Mensal — Gestao Comercial ULITEC CRM v1.0

Responsavel por:
  - Fechar competencia (gravar snapshot definitivo)
  - Registrar pagamento
  - Gerenciar comissoes avulsas

Regras de ouro:
  - Snapshot NUNCA e recalculado depois de FECHADO
  - NENHUMA alteracao em tabelas de faturamento ou clientes
"""

import json
from datetime import date

from services.comissoes_db import (
    get_conn,
    query_parceiros_ativos,
    query_carteira_parceiro,
    query_faturamento_periodo,
    query_faturamento_periodo_unidade,
)


def _get_usuario() -> str:
    """Retorna o nome do usuário logado."""
    try:
        import streamlit as st
        return st.session_state.get("usuario_nome", "Sistema")
    except Exception:
        return "Sistema"


def fechar_competencia(competencia: str) -> list:
    """
    Calcula e grava snapshot definitivo de uma competencia.
    Após fechado: NUNCA mais altera.
    Nao passa por PREVIEW — insere diretamente como FECHADO.

    competencia: formato 'YYYY-MM' (ex: '2026-07')
    Retorna: lista de ids criados.
    """
    ano, mes = competencia.split("-")
    ano = int(ano)
    mes = int(mes)

    data_inicio = f"{ano:04d}-{mes:02d}-01"
    if mes == 12:
        data_fim = f"{ano + 1:04d}-01-01"
    else:
        data_fim = f"{ano:04d}-{mes + 1:02d}-01"

    usuario = _get_usuario()
    conn = get_conn()
    cursor = conn.cursor()

    # Verificar se ja existe fechamento para esta competencia
    cursor.execute("SELECT 1 FROM fechamento_mensal WHERE competencia = ? AND status = 'FECHADO' LIMIT 1", (competencia,))
    if cursor.fetchone():
        conn.close()
        return []  # ja fechado — nao recalcula

    # 1. Buscar parceiros ativos
    parceiros = query_parceiros_ativos()
    if not parceiros:
        conn.close()
        return []

    # 2. Buscar faturamento (3 escopos)
    fat_grupo = {r[0]: r[1] for r in query_faturamento_periodo(data_inicio, data_fim)}
    fat_sp = {r[0]: r[1] for r in query_faturamento_periodo_unidade(data_inicio, data_fim, "ULITEC SP")}
    fat_rs = {r[0]: r[1] for r in query_faturamento_periodo_unidade(data_inicio, data_fim, "ULITEC RS")}
    mapa_fat = {"GRUPO": fat_grupo, "ULITEC SP": fat_sp, "ULITEC RS": fat_rs}

    # 3. Nomes dos clientes
    cursor.execute("SELECT id, razao_social FROM clientes")
    nomes = {r[0]: r[1] for r in cursor.fetchall()}

    ids_criados = []

    for p in parceiros:
        p_id, p_nome, percentual, base_calculo, aliquota, escopo, dias_pag = p

        carteira_ids = query_carteira_parceiro(p_id)
        if not carteira_ids:
            continue

        fat = mapa_fat.get(escopo, {})
        if not fat:
            continue

        clientes_calc = []
        total_bruto = 0.0
        total_impostos = 0.0
        total_liquido = 0.0
        total_comissao = 0.0

        for cid in carteira_ids:
            vbruto = fat.get(cid, 0)
            if vbruto <= 0:
                continue

            if base_calculo == "LIQUIDO":
                imp = round(vbruto * (aliquota / 100), 2)
                liq = round(vbruto - imp, 2)
                vbase = liq
            else:
                imp = 0.0
                liq = vbruto
                vbase = vbruto

            com = round(vbase * (percentual / 100), 2)
            clientes_calc.append({
                "cliente": nomes.get(cid, f"Cliente #{cid}"),
                "valor_bruto": round(vbruto, 2),
                "valor_liquido": round(liq, 2),
                "valor_comissao": com,
            })
            total_bruto += vbruto
            if base_calculo == "LIQUIDO":
                total_impostos += imp
            total_liquido += liq
            total_comissao += com

        if not clientes_calc:
            continue

        cursor.execute("""
            INSERT INTO fechamento_mensal
                (parceiro_id, competencia,
                 percentual, base_calculo, aliquota_impostos,
                 faturamento_considerado, clientes_json,
                 quantidade_clientes,
                 valor_bruto, valor_impostos, valor_liquido, valor_comissao,
                 status, fechado_em, fechado_por)
            VALUES (?, ?,
                    ?, ?, ?,
                    ?, ?,
                    ?,
                    ?, ?, ?, ?,
                    'FECHADO', date('now'), ?)
        """, (
            p_id, competencia,
            percentual, base_calculo, aliquota,
            escopo, json.dumps(clientes_calc, ensure_ascii=False),
            len(clientes_calc),
            round(total_bruto, 2), round(total_impostos, 2),
            round(total_liquido, 2), round(total_comissao, 2),
            usuario,
        ))
        ids_criados.append(cursor.lastrowid)

    conn.commit()
    conn.close()
    return ids_criados


def registrar_pagamento(fechamento_id: int, observacao: str = ""):
    """
    Registra pagamento de um fechamento.
    Altera status para PAGO.
    """
    usuario = _get_usuario()

    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE fechamento_mensal
        SET status = 'PAGO',
            data_pagamento = date('now'),
            usuario_pagamento = ?,
            observacao_pagamento = ?
        WHERE id = ?
          AND status = 'FECHADO'
    """, (usuario, observacao, fechamento_id))
    conn.commit()
    conn.close()


# ═══════════════════════════════════════════════════════════
# COMISSOES AVULSAS
# ═══════════════════════════════════════════════════════════

def criar_comissao_avulsa(dados: dict) -> int:
    """Cria uma nova comissão avulsa."""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO comissoes_avulsas
            (parceiro_id, cliente_id, os_id, descricao,
             valor_faturado, percentual, valor_comissao,
             data_prevista, observacoes)
        VALUES (?, ?, ?, ?,
                ?, ?, ?,
                ?, ?)
    """, (
        dados.get("parceiro_id"),
        dados.get("cliente_id"),
        dados.get("os_id"),
        dados.get("descricao", ""),
        float(dados.get("valor_faturado", 0)),
        float(dados.get("percentual", 0)),
        float(dados.get("valor_comissao", 0)),
        dados.get("data_prevista"),
        dados.get("observacoes", ""),
    ))
    avulsa_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return avulsa_id


def atualizar_comissao_avulsa(avulsa_id: int, dados: dict):
    """Atualiza dados de uma comissão avulsa."""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE comissoes_avulsas SET
            cliente_id = ?,
            os_id = ?,
            descricao = ?,
            valor_faturado = ?,
            percentual = ?,
            valor_comissao = ?,
            data_prevista = ?,
            observacoes = ?,
            atualizado_em = date('now')
        WHERE id = ?
    """, (
        dados.get("cliente_id"),
        dados.get("os_id"),
        dados.get("descricao", ""),
        float(dados.get("valor_faturado", 0)),
        float(dados.get("percentual", 0)),
        float(dados.get("valor_comissao", 0)),
        dados.get("data_prevista"),
        dados.get("observacoes", ""),
        avulsa_id,
    ))
    conn.commit()
    conn.close()


def alterar_status_avulsa(avulsa_id: int, novo_status: str):
    """Altera o status de uma comissão avulsa."""
    conn = get_conn()
    cursor = conn.cursor()
    if novo_status == "PAGO":
        cursor.execute("""
            UPDATE comissoes_avulsas
            SET status = ?, data_pagamento = date('now'), atualizado_em = date('now')
            WHERE id = ?
        """, (novo_status, avulsa_id))
    else:
        cursor.execute("""
            UPDATE comissoes_avulsas
            SET status = ?, atualizado_em = date('now')
            WHERE id = ?
        """, (novo_status, avulsa_id))
    conn.commit()
    conn.close()


def excluir_comissao_avulsa(avulsa_id: int):
    """Exclui uma comissão avulsa pelo ID."""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM comissoes_avulsas WHERE id = ?", (avulsa_id,))
    conn.commit()
    conn.close()



