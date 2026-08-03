"""
Módulo de Relacionamento Comercial — ULITEC CRM v1.0.3

Serviço central do pilar de relacionamento:
- Registrar interações (visitas, WhatsApp, e-mail, ligação, reunião)
- Criar pendências comerciais
- Criar oportunidades vinculadas
- Gerenciar configurações de frequência por classe
- Gerar alertas automáticos
"""

from datetime import datetime, date, timedelta
from typing import Optional, List

import pandas as pd

from config import DB_PATH

from database import get_connection

# ──────────────────────────────────────────────
# CONSTANTES
# ──────────────────────────────────────────────

TIPOS_INTERACAO = [
    "Visita Presencial",
    "WhatsApp",
    "E-mail",
    "Ligação",
    "Teams",
    "Reunião Técnica",
    "Reunião Comercial",
]

ASSUNTOS_PADRAO = [
    "Preventiva",
    "Retrofit",
    "Servo",
    "Follow-up",
    "Proposta",
    "Reclamação",
    "Oportunidade",
    "Orçamento",
    "Pós-venda",
    "Outros",
]

RESULTADOS = ["Positivo", "Neutro", "Negativo"]

PRIORIDADES = ["ALTA", "MEDIA", "BAIXA"]

TIPOS_PENDENCIA = [
    "Visita",
    "Follow-up",
    "Proposta",
    "Venda",
    "Cobrança",
    "Preventiva",
    "Assistência Técnica",
    "Outro",
]

TIPOS_PROXIMA_ACAO = [
    "Ligar",
    "WhatsApp",
    "E-mail",
    "Visita",
    "Cobrar Pedido",
    "Cobrar Retorno",
    "Enviar Proposta",
    "Reunião",
    "Outro",
]

CHAVES_CONFIG = [
    "whats_A", "whats_B", "whats_C", "whats_D",
    "email_A", "email_B", "email_C", "email_D",
    "ligacao_A", "ligacao_B", "ligacao_C", "ligacao_D",
    "visita_A", "visita_B", "visita_C", "visita_D",
    "alerta_visita", "alerta_contato",
    "fat_A", "fat_B", "fat_C",
    "os_A", "os_B", "os_C",
    "fat_qtd_A", "fat_qtd_B", "fat_qtd_C",
    # v1.6.10 — parâmetros operacionais
    "followup_1", "followup_2", "followup_3",
    "proposta_esquecida", "envio_proposta",
    "expedicao", "feedback_cliente",
]

# ──────────────────────────────────────────────
# CONEXÃO
# ──────────────────────────────────────────────

def _get_conn():
    return get_connection()

# ──────────────────────────────────────────────
# CONFIGURAÇÕES
# ──────────────────────────────────────────────

def get_config(chave: str, valor_padrao: str = "30") -> str:
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT valor FROM configuracoes WHERE chave = ?", (chave,)
        ).fetchone()
        return row[0] if row else valor_padrao
    finally:
        conn.close()

def set_config(chave: str, valor: str, descricao: str = "") -> None:
    conn = _get_conn()
    try:
        conn.execute(
            """
            INSERT INTO configuracoes (chave, valor, descricao)
            VALUES (?, ?, ?)
            ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor
            """,
            (chave, str(valor), descricao),
        )
        conn.commit()
    finally:
        conn.close()

def salvar_configs_relacionamento(params: dict) -> None:
    descricoes = {
        "whats_A": "Frequência WhatsApp Classe A (dias)",
        "whats_B": "Frequência WhatsApp Classe B (dias)",
        "whats_C": "Frequência WhatsApp Classe C (dias)",
        "whats_D": "Frequência WhatsApp Classe D (dias)",
        "email_A": "Frequência E-mail Classe A (dias)",
        "email_B": "Frequência E-mail Classe B (dias)",
        "email_C": "Frequência E-mail Classe C (dias)",
        "email_D": "Frequência E-mail Classe D (dias)",
        "ligacao_A": "Frequência Ligação Classe A (dias)",
        "ligacao_B": "Frequência Ligação Classe B (dias)",
        "ligacao_C": "Frequência Ligação Classe C (dias)",
        "ligacao_D": "Frequência Ligação Classe D (dias)",
        "visita_A": "Frequência Visita Presencial Classe A (dias)",
        "visita_B": "Frequência Visita Presencial Classe B (dias)",
        "visita_C": "Frequência Visita Presencial Classe C (dias)",
        "visita_D": "Frequência Visita Presencial Classe D (dias)",
        "alerta_visita": "Antecedência alerta de visita (dias)",
        "alerta_contato": "Antecedência alerta de contato (dias)",
        "fat_A": "Faturamento mínimo Classe A (R$)",
        "fat_B": "Faturamento mínimo Classe B (R$)",
        "fat_C": "Faturamento mínimo Classe C (R$)",
        "os_A": "Qtd mínima OS Classe A",
        "os_B": "Qtd mínima OS Classe B",
        "os_C": "Qtd mínima OS Classe C",
        "fat_qtd_A": "Qtd mínima faturamentos Classe A",
        "fat_qtd_B": "Qtd mínima faturamentos Classe B",
        "fat_qtd_C": "Qtd mínima faturamentos Classe C",
    }
    for chave, valor in params.items():
        desc = descricoes.get(chave, "")
        set_config(chave, str(valor), desc)

def carregar_configs_relacionamento() -> dict:
    configs = {}
    for chave in CHAVES_CONFIG:
        configs[chave] = get_config(chave, "30")
    return configs

# ──────────────────────────────────────────────
# INTERAÇÕES
# ──────────────────────────────────────────────

def registrar_interacao(
    cliente_id: int,
    tipo_interacao: str,
    assunto: str = "",
    descricao: str = "",
    resultado: str = "Neutro",
    responsavel: str = "",
    usuario_id: Optional[int] = None,
    unidade: str = "",
    proxima_acao: str = "",
    data_proxima_acao: Optional[str] = None,
    data_interacao: Optional[str] = None,
    qtd_maquinas: Optional[int] = None,
    qtd_mitsubishi: Optional[int] = None,
    brinde_entregue: Optional[str] = None,
    status_cliente: Optional[str] = None,
    nivel_producao: Optional[str] = None,
    perspectiva_6m: Optional[str] = None,
    concorrentes: Optional[str] = None,
    status_interacao: str = "ABERTA",
    resultado_comercial: Optional[str] = None,
    # v1.0.5 — campos de contato
    contato_nome: Optional[str] = None,
    contato_cargo: Optional[str] = None,
    contato_telefone: Optional[str] = None,
    contato_email: Optional[str] = None,
    # v1.0.5 — próxima ação estruturada
    tipo_prox_acao: Optional[str] = None,
    obs_prox_acao: Optional[str] = None,
    entregou_brinde: Optional[str] = None,
    descricao_brinde: Optional[str] = None,
    data_brinde: Optional[str] = None,
) -> int:
    """
    Registra uma interação e atualiza clientes.ultima_visita.
    Se o tipo for 'Visita Presencial', aceita campos industriais opcionais.
    v1.0.5: adicionados campos de contato e próxima ação estruturada.
    Retorna o ID da interação criada.
    """
    if data_interacao is None:
        data_interacao = date.today().strftime("%Y-%m-%d")

    conn = _get_conn()
    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO interacoes
                (cliente_id, data_interacao, tipo_interacao, assunto,
                 responsavel, usuario_id, unidade, resumo, resultado,
                 proxima_acao, data_proxima_acao, status_interacao,
                 qtd_maquinas, qtd_mitsubishi, brinde_entregue,
                 status_cliente, nivel_producao, perspectiva_6m, concorrentes,
                 resultado_comercial,
                 contato_nome, contato_cargo, contato_telefone, contato_email,
                 tipo_prox_acao, obs_prox_acao,
                 entregou_brinde, descricao_brinde, data_brinde)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?)
            """,
            (
                cliente_id,
                data_interacao,
                tipo_interacao,
                assunto,
                responsavel,
                usuario_id,
                unidade,
                descricao,
                resultado,
                proxima_acao,
                data_proxima_acao,
                status_interacao,
                qtd_maquinas,
                qtd_mitsubishi,
                brinde_entregue,
                status_cliente,
                nivel_producao,
                perspectiva_6m,
                concorrentes,
                resultado_comercial,
                contato_nome,
                contato_cargo,
                contato_telefone,
                contato_email,
                tipo_prox_acao,
                obs_prox_acao,
                entregou_brinde,
                descricao_brinde,
                data_brinde,
            ),
        )
        interacao_id = cursor.lastrowid

        # Atualizar ultima_visita do cliente
        cursor.execute(
            "UPDATE clientes SET ultima_visita = ? WHERE id = ?",
            (data_interacao, cliente_id),
        )

        conn.commit()
        return interacao_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_historico_interacoes(
    cliente_id: Optional[int] = None,
    responsavel: Optional[str] = None,
    tipo: Optional[str] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    limite: int = 100,
) -> pd.DataFrame:
    conn = _get_conn()
    try:
        conditions = []
        params = []

        if cliente_id is not None:
            conditions.append("i.cliente_id = ?")
            params.append(cliente_id)
        if responsavel:
            conditions.append("i.responsavel = ?")
            params.append(responsavel)
        if tipo:
            conditions.append("i.tipo_interacao = ?")
            params.append(tipo)
        if data_inicio:
            conditions.append("i.data_interacao >= ?")
            params.append(data_inicio)
        if data_fim:
            conditions.append("i.data_interacao <= ?")
            params.append(data_fim)

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

        query = f"""
        SELECT
            i.id,
            i.data_interacao,
            i.tipo_interacao,
            i.assunto,
            c.razao_social AS cliente,
            i.responsavel,
            i.usuario_id,
            i.resumo AS descricao,
            i.resultado,
            i.proxima_acao,
            i.data_proxima_acao,
            i.status_interacao,
            i.qtd_maquinas,
            i.qtd_mitsubishi,
            i.brinde_entregue,
            i.status_cliente,
            i.nivel_producao,
            i.perspectiva_6m,
            i.concorrentes,
            i.contato_nome,
            i.contato_cargo,
            i.contato_telefone,
            i.contato_email,
            i.tipo_prox_acao,
            i.obs_prox_acao,
            CASE
                WHEN i.data_proxima_acao IS NOT NULL
                     AND i.data_proxima_acao < date('now')
                     AND i.status_interacao = 'ABERTA'
                THEN 'VENCIDA'
                ELSE i.status_interacao
            END AS status_exibicao
        FROM interacoes i
        LEFT JOIN clientes c ON i.cliente_id = c.id
        {where}
        ORDER BY i.data_interacao DESC, i.id DESC
        LIMIT ?
        """
        params.append(limite)

        df = pd.read_sql_query(query, conn, params=params)
        return df
    finally:
        conn.close()

def get_agenda(
    dias_frente: int = 30,
    responsavel: Optional[str] = None,
) -> pd.DataFrame:
    """Retorna agenda consolidada: pendências abertas + oportunidades com follow-up pendente."""
    conn = _get_conn()
    try:
        data_limite = (date.today() + timedelta(days=dias_frente)).strftime("%Y-%m-%d")
        hoje = date.today().strftime("%Y-%m-%d")

        # --- Pendências ---
        conditions_pend = ["p.status = 'ABERTA'", "p.data_limite <= ?"]
        params_pend = [data_limite]
        if responsavel:
            conditions_pend.append("p.responsavel = ?")
            params_pend.append(responsavel)
        where_pend = " AND ".join(conditions_pend)

        # --- Follow-ups OS ---
        conditions_os = ["os.proximo_followup IS NOT NULL", "os.proximo_followup <= ?"]
        params_os = [data_limite]
        if responsavel:
            conditions_os.append("os.responsavel = ?")
            params_os.append(responsavel)
        where_os = " AND ".join(conditions_os)

        query = f"""
        SELECT
            p.data_limite AS data_prevista,
            '' AS tipo_interacao,
            p.prioridade AS assunto,
            c.razao_social AS cliente,
            p.responsavel,
            p.descricao,
            'PENDÊNCIA' AS tipo_agenda,
            CASE
                WHEN p.data_limite < ? THEN 'VENCIDA'
                WHEN p.data_limite = ? THEN 'HOJE'
                ELSE 'PENDENTE'
            END AS status
        FROM pendencias_comerciais p
        LEFT JOIN clientes c ON p.cliente_id = c.id
        WHERE {where_pend}
        UNION ALL
        SELECT
            os.proximo_followup AS data_prevista,
            '' AS tipo_interacao,
            'Follow-up' AS assunto,
            c.razao_social AS cliente,
            os.responsavel,
            'Follow-up de proposta' AS descricao,
            'FOLLOW-UP' AS tipo_agenda,
            CASE
                WHEN os.proximo_followup < ? THEN 'VENCIDA'
                WHEN os.proximo_followup = ? THEN 'HOJE'
                ELSE 'PENDENTE'
            END AS status
        FROM ordens_servico os
        LEFT JOIN clientes c ON os.cliente_id = c.id
        WHERE {where_os}
        ORDER BY data_prevista ASC
        """
        params_final = [hoje, hoje] + params_pend + [hoje, hoje] + params_os

        df = pd.read_sql_query(query, conn, params=params_final)
        return df
    finally:
        conn.close()

# ──────────────────────────────────────────────
# PENDÊNCIAS COMERCIAIS
# ──────────────────────────────────────────────

def criar_pendencia(
    cliente_id: int,
    descricao: str,
    prioridade: str = "MEDIA",
    responsavel: str = "",
    data_limite: Optional[str] = None,
    interacao_id: Optional[int] = None,
    tipo_pendencia: Optional[str] = None,
) -> int:
    """
    Cria uma pendência comercial.
    interacao_id é opcional — permite criar pendência independente (v1.0.5).
    """
    if data_limite is None:
        data_limite = (date.today() + timedelta(days=7)).strftime("%Y-%m-%d")

    conn = _get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO pendencias_comerciais
                (cliente_id, interacao_id, descricao, prioridade,
                 responsavel, data_limite, status, tipo_pendencia)
            VALUES (?, ?, ?, ?, ?, ?, 'ABERTA', ?)
            """,
            (cliente_id, interacao_id, descricao, prioridade,
             responsavel, data_limite, tipo_pendencia),
        )
        pendencia_id = cursor.lastrowid
        conn.commit()
        return pendencia_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_pendencias(
    status: Optional[str] = None,
    responsavel: Optional[str] = None,
    cliente_id: Optional[int] = None,
) -> pd.DataFrame:
    conn = _get_conn()
    try:
        conditions = []
        params = []

        if status:
            conditions.append("p.status = ?")
            params.append(status)
        if responsavel:
            conditions.append("p.responsavel = ?")
            params.append(responsavel)
        if cliente_id is not None:
            conditions.append("p.cliente_id = ?")
            params.append(cliente_id)

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

        # v1.4: incluir ultima_atualizacao da evolução mais recente
        query = f"""
        SELECT
            p.id,
            c.razao_social AS cliente,
            p.descricao,
            p.prioridade,
            p.responsavel,
            p.data_limite,
            p.status,
            p.criado_em,
            CASE
                WHEN p.data_limite < date('now') AND p.status = 'ABERTA'
                THEN 'VENCIDA'
                ELSE p.status
            END AS status_exibicao,
            (SELECT criado_em FROM evolucao_pendencias
             WHERE pendencia_id = p.id
             ORDER BY id DESC LIMIT 1) AS ultima_atualizacao
        FROM pendencias_comerciais p
        LEFT JOIN clientes c ON p.cliente_id = c.id
        {where}
        ORDER BY
            CASE WHEN p.prioridade = 'ALTA' THEN 0 WHEN p.prioridade = 'MEDIA' THEN 1 ELSE 2 END,
            p.data_limite ASC
        """
        df = pd.read_sql_query(query, conn, params=params)
        return df
    finally:
        conn.close()

def concluir_pendencia(pendencia_id: int) -> None:
    conn = _get_conn()
    try:
        conn.execute(
            "UPDATE pendencias_comerciais SET status = 'FECHADA' WHERE id = ?",
            (pendencia_id,),
        )
        conn.commit()
    finally:
        conn.close()

# ── v1.0.5: NOVAS FUNÇÕES DE GESTÃO DE PENDÊNCIAS ──

def atualizar_pendencia(
    pendencia_id: int,
    descricao: Optional[str] = None,
    prioridade: Optional[str] = None,
    data_limite: Optional[str] = None,
    responsavel: Optional[str] = None,
) -> None:
    """
    Atualiza campos de uma pendência. Só altera campos fornecidos (não-None).
    """
    updates = []
    params = []
    if descricao is not None:
        updates.append("descricao = ?")
        params.append(descricao)
    if prioridade is not None:
        updates.append("prioridade = ?")
        params.append(prioridade)
    if data_limite is not None:
        updates.append("data_limite = ?")
        params.append(data_limite)
    if responsavel is not None:
        updates.append("responsavel = ?")
        params.append(responsavel)

    if not updates:
        return  # nada a atualizar

    params.append(pendencia_id)
    conn = _get_conn()
    try:
        conn.execute(
            f"UPDATE pendencias_comerciais SET {', '.join(updates)} WHERE id = ?",
            params,
        )
        conn.commit()
    finally:
        conn.close()

def reabrir_pendencia(pendencia_id: int) -> None:
    """Reabre uma pendência concluída, voltando status para ABERTA."""
    conn = _get_conn()
    try:
        conn.execute(
            "UPDATE pendencias_comerciais SET status = 'ABERTA' WHERE id = ?",
            (pendencia_id,),
        )
        conn.commit()
    finally:
        conn.close()

def get_pendencia_by_id(pendencia_id: int) -> Optional[dict]:
    """Retorna dados completos de uma pendência pelo ID."""
    conn = _get_conn()
    try:
        conn.row_factory = dict
        row = conn.execute(
            """
            SELECT p.id, p.cliente_id, c.razao_social AS cliente,
                   p.descricao, p.prioridade, p.responsavel,
                   p.data_limite, p.status, p.criado_em,
                   CASE
                       WHEN p.data_limite < date('now') AND p.status = 'ABERTA'
                       THEN 'VENCIDA'
                       ELSE p.status
                   END AS status_exibicao
            FROM pendencias_comerciais p
            LEFT JOIN clientes c ON p.cliente_id = c.id
            WHERE p.id = ?
            """,
            (pendencia_id,),
        ).fetchone()
        if row:
            return dict(row)
        return None
    finally:
        conn.close()

# ──────────────────────────────────────────────
# OPORTUNIDADES
# ──────────────────────────────────────────────

def criar_oportunidade(
    cliente_id: int,
    titulo: str,
    valor_estimado: float = 0.0,
    probabilidade: str = "MEDIA",
    observacao: str = "",
    responsavel: str = "",
    unidade: str = "",
) -> int:
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO oportunidades
                (cliente_id, unidade, data_abertura, origem,
                 descricao, valor_estimado, status)
            VALUES (?, ?, ?, 'RELACIONAMENTO', ?, ?, 'ABERTA')
            """,
            (
                cliente_id,
                unidade,
                date.today().strftime("%Y-%m-%d"),
                f"[{probabilidade}] {titulo}\n{observacao}".strip(),
                valor_estimado,
            ),
        )
        oportunidade_id = cursor.lastrowid
        conn.commit()
        return oportunidade_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

# ──────────────────────────────────────────────
# ALERTAS
# ──────────────────────────────────────────────

def get_alertas_relacionamento(unidade: Optional[str] = None) -> list:
    configs = carregar_configs_relacionamento()
    alertas = []
    hoje = date.today()

    conn = _get_conn()
    try:
        # 1. VISITAS PRÓXIMAS DO VENCIMENTO
        for classe in ["A", "B", "C", "D"]:
            freq_visita = int(configs.get(f"visita_{classe}", "90"))
            alerta_dias = int(configs.get("alerta_visita", "15"))
            dias_limite = freq_visita - alerta_dias

            params = [classe, hoje.strftime("%Y-%m-%d")]
            query_unidade = ""
            if unidade:
                query_unidade = " AND EXISTS (SELECT 1 FROM faturamento f WHERE f.cliente_id = c.id AND f.unidade = ?)"
                params.append(unidade)

            df = pd.read_sql_query(
                f"""
                SELECT c.id, c.razao_social,
                       julianday('{hoje}') - julianday(c.ultima_visita) AS dias_ultima_visita
                FROM clientes c
                WHERE c.classe_abc = ?
                  AND c.ultima_visita IS NOT NULL
                  AND julianday('{hoje}') - julianday(c.ultima_visita) >= ?
                  AND c.status = 'ATIVO'
                  {query_unidade}
                ORDER BY dias_ultima_visita DESC
                """,
                conn,
                params=params,
            )

            for _, row in df.iterrows():
                dias = int(row["dias_ultima_visita"])
                alertas.append({
                    "tipo": "VISITA_PROXIMA_VENCIMENTO",
                    "cliente": row["razao_social"],
                    "cliente_id": row["id"],
                    "descricao": (
                        f"Classe {classe}: {row['razao_social']} — "
                        f"{dias} dias sem visita (limite: {freq_visita} dias)"
                    ),
                    "severidade": "ALTA" if classe in ("A", "B") else "MEDIA",
                })

        # 2. PENDÊNCIAS VENCIDAS E VENCENDO HOJE
        df_pend = pd.read_sql_query(
            """
            SELECT p.id, p.cliente_id, c.razao_social,
                   p.descricao, p.data_limite
            FROM pendencias_comerciais p
            LEFT JOIN clientes c ON p.cliente_id = c.id
            WHERE p.status = 'ABERTA'
              AND p.data_limite <= date('now')
            ORDER BY p.data_limite ASC
            LIMIT 30
            """,
            conn,
        )

        for _, row in df_pend.iterrows():
            data_limite = datetime.strptime(row["data_limite"], "%Y-%m-%d").date()
            if data_limite < hoje:
                dias_atraso = (hoje - data_limite).days
                alertas.append({
                    "tipo": "PENDENCIA_VENCIDA",
                    "cliente": row["razao_social"],
                    "cliente_id": row["cliente_id"],
                    "descricao": (
                        f"Pendência vencida: '{row['descricao']}' — "
                        f"{row['razao_social']} ({dias_atraso} dias)"
                    ),
                    "severidade": "ALTA" if dias_atraso > 7 else "MEDIA",
                })
            else:
                # data_limite == hoje
                alertas.append({
                    "tipo": "PENDENCIA_VENCE_HOJE",
                    "cliente": row["razao_social"],
                    "cliente_id": row["cliente_id"],
                    "descricao": (
                        f"Pendência vence hoje: '{row['descricao']}' — "
                        f"{row['razao_social']}"
                    ),
                    "severidade": "ALTA",
                })

        return alertas

    finally:
        conn.close()

# ──────────────────────────────────────────────
# INDICADORES PARA CLIENTE 360
# ──────────────────────────────────────────────

def get_indicadores_relacionamento(cliente_id: int) -> dict:
    conn = _get_conn()
    try:
        ultima = conn.execute(
            """
            SELECT data_interacao, tipo_interacao, resultado
            FROM interacoes
            WHERE cliente_id = ?
            ORDER BY data_interacao DESC
            LIMIT 1
            """,
            (cliente_id,),
        ).fetchone()

        pend_abertas = conn.execute(
            """
            SELECT COUNT(*)
            FROM pendencias_comerciais
            WHERE cliente_id = ? AND status = 'ABERTA'
            """,
            (cliente_id,),
        ).fetchone()[0]

        pend_vencidas = conn.execute(
            """
            SELECT COUNT(*)
            FROM pendencias_comerciais
            WHERE cliente_id = ?
              AND status = 'ABERTA'
              AND data_limite < date('now')
            """,
            (cliente_id,),
        ).fetchone()[0]

        total_interacoes = conn.execute(
            "SELECT COUNT(*) FROM interacoes WHERE cliente_id = ?",
            (cliente_id,),
        ).fetchone()[0]

        opp_relac = conn.execute(
            """
            SELECT COUNT(*)
            FROM oportunidades
            WHERE cliente_id = ? AND origem = 'RELACIONAMENTO'
            """,
            (cliente_id,),
        ).fetchone()[0]

        return {
            "ultima_interacao_data": ultima[0] if ultima else None,
            "ultima_interacao_tipo": ultima[1] if ultima else None,
            "ultima_interacao_resultado": ultima[2] if ultima else None,
            "pendencias_abertas": pend_abertas,
            "pendencias_vencidas": pend_vencidas,
            "total_interacoes": total_interacoes,
            "oportunidades_relacionamento": opp_relac,
        }
    finally:
        conn.close()

# ──────────────────────────────────────────────
# EVOLUÇÕES DE PENDÊNCIAS (v1.3)
# ──────────────────────────────────────────────

TIPOS_EVOLUCAO = [
    "COMENTARIO",
    "ANDAMENTO",
    "CONCLUSAO",
    "REABERTURA",
    "ALTERACAO_PRAZO",
    "ALTERACAO_PRIORIDADE",
    "ALTERACAO_RESPONSAVEL",
]

def criar_evolucao_pendencia(
    pendencia_id: int,
    descricao: str,
    usuario_id: Optional[int] = None,
    usuario_nome: Optional[str] = None,
    proximo_contato: Optional[str] = None,
) -> int:
    """
    Registra uma evolução/comentário em uma pendência.
    Se proximo_contato for fornecido, atualiza automaticamente
    a data_limite da pendência.
    Retorna o ID da evolução criada.
    """
    conn = _get_conn()
    try:
        cursor = conn.cursor()

        # Montar descricao com proximo_contato se fornecido
        descricao_final = descricao
        if proximo_contato:
            try:
                data_fmt = datetime.strptime(proximo_contato, "%Y-%m-%d").strftime("%d/%m/%Y")
                descricao_final += f"\n\nPróximo contato definido para {data_fmt}"
            except ValueError:
                pass

        cursor.execute(
            """
            INSERT INTO evolucao_pendencias
                (pendencia_id, descricao, tipo_evolucao, usuario_id, usuario_nome)
            VALUES (?, ?, 'COMENTARIO', ?, ?)
            """,
            (pendencia_id, descricao_final, usuario_id, usuario_nome),
        )
        evolucao_id = cursor.lastrowid

        # Atualizar data_limite da pendência se proximo_contato foi fornecido
        if proximo_contato:
            cursor.execute(
                "UPDATE pendencias_comerciais SET data_limite = ? WHERE id = ?",
                (proximo_contato, pendencia_id),
            )

        conn.commit()
        return evolucao_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_evolucoes_pendencia(pendencia_id: int) -> pd.DataFrame:
    """
    Retorna todas as evoluções de uma pendência, ordenadas da mais recente para a mais antiga.
    """
    conn = _get_conn()
    try:
        df = pd.read_sql_query(
            """
            SELECT
                e.id,
                e.descricao,
                e.tipo_evolucao,
                e.usuario_nome,
                e.criado_em
            FROM evolucao_pendencias e
            WHERE e.pendencia_id = ?
            ORDER BY e.id DESC
            """,
            conn,
            params=(pendencia_id,),
        )
        return df
    finally:
        conn.close()

def concluir_pendencia_com_evolucao(
    pendencia_id: int,
    usuario_id: Optional[int] = None,
    usuario_nome: Optional[str] = None,
    observacao: str = "",
) -> None:
    """
    Conclui uma pendência e registra evolução de conclusão automaticamente.
    """
    conn = _get_conn()
    try:
        cursor = conn.cursor()

        # Concluir pendência
        cursor.execute(
            "UPDATE pendencias_comerciais SET status = 'FECHADA' WHERE id = ?",
            (pendencia_id,),
        )

        # Registrar evolução
        descricao = observacao if observacao else "Pendência concluída"
        cursor.execute(
            """
            INSERT INTO evolucao_pendencias
                (pendencia_id, descricao, tipo_evolucao, usuario_id, usuario_nome)
            VALUES (?, ?, 'CONCLUSAO', ?, ?)
            """,
            (pendencia_id, descricao, usuario_id, usuario_nome),
        )

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def reabrir_pendencia_com_evolucao(
    pendencia_id: int,
    usuario_id: Optional[int] = None,
    usuario_nome: Optional[str] = None,
    motivo: str = "",
) -> None:
    """
    Reabre uma pendência e registra evolução de reabertura automaticamente.
    """
    conn = _get_conn()
    try:
        cursor = conn.cursor()

        # Reabrir pendência
        cursor.execute(
            "UPDATE pendencias_comerciais SET status = 'ABERTA' WHERE id = ?",
            (pendencia_id,),
        )

        # Registrar evolução
        descricao = motivo if motivo else "Pendência reaberta"
        cursor.execute(
            """
            INSERT INTO evolucao_pendencias
                (pendencia_id, descricao, tipo_evolucao, usuario_id, usuario_nome)
            VALUES (?, ?, 'REABERTURA', ?, ?)
            """,
            (pendencia_id, descricao, usuario_id, usuario_nome),
        )

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

# ──────────────────────────────────────────────
# v1.1 — NOVAS FUNÇÕES PARA CENTRAL DE OPORTUNIDADES (AGENDA OPERACIONAL)
# ──────────────────────────────────────────────

def get_proximas_acoes_consolidadas(
    filtro_responsavel: Optional[str] = None,
    filtro_cliente: Optional[str] = None,
    filtro_periodo_inicio: Optional[str] = None,
    filtro_periodo_fim: Optional[str] = None,
    filtro_status: Optional[str] = None,
) -> pd.DataFrame:
    """
    Retorna agenda consolidada (próximas ações de interações + pendências abertas).
    Usada na Central de Oportunidades aba '📅 Próximas Ações'.
    """
    conn = _get_conn()
    try:
        hoje = date.today().strftime("%Y-%m-%d")

        # Query unificada: ações de interações
        query_interacoes = """
        SELECT
            i.data_proxima_acao AS data,
            c.razao_social AS cliente,
            i.contato_nome AS contato,
            i.responsavel,
            COALESCE(i.tipo_prox_acao, i.proxima_acao) AS tipo_acao,
            i.obs_prox_acao AS observacao,
            'Interação' AS origem,
            i.status_interacao,
            i.id AS origem_id
        FROM interacoes i
        LEFT JOIN clientes c ON i.cliente_id = c.id
        WHERE i.status_interacao = 'ABERTA'
          AND i.data_proxima_acao IS NOT NULL
        """

        # Query unificada: pendências
        query_pendencias = """
        SELECT
            p.data_limite AS data,
            c.razao_social AS cliente,
            '' AS contato,
            p.responsavel,
            'Pendência: ' || p.prioridade AS tipo_acao,
            p.descricao AS observacao,
            'Pendência' AS origem,
            p.status,
            p.id AS origem_id
        FROM pendencias_comerciais p
        LEFT JOIN clientes c ON p.cliente_id = c.id
        WHERE p.status = 'ABERTA'
          AND p.data_limite IS NOT NULL
        """

        conditions_inter = []
        params_inter = []

        conditions_pend = []
        params_pend = []

        if filtro_responsavel:
            conditions_inter.append("i.responsavel = ?")
            params_inter.append(filtro_responsavel)
            conditions_pend.append("p.responsavel = ?")
            params_pend.append(filtro_responsavel)

        if filtro_cliente:
            conditions_inter.append("c.razao_social LIKE ?")
            params_inter.append(f"%{filtro_cliente}%")
            conditions_pend.append("c.razao_social LIKE ?")
            params_pend.append(f"%{filtro_cliente}%")

        if filtro_periodo_inicio:
            conditions_inter.append("i.data_proxima_acao >= ?")
            params_inter.append(filtro_periodo_inicio)
            conditions_pend.append("p.data_limite >= ?")
            params_pend.append(filtro_periodo_inicio)

        if filtro_periodo_fim:
            conditions_inter.append("i.data_proxima_acao <= ?")
            params_inter.append(filtro_periodo_fim)
            conditions_pend.append("p.data_limite <= ?")
            params_pend.append(filtro_periodo_fim)

        if filtro_status:
            if filtro_status == "VENCIDA":
                conditions_inter.append("i.data_proxima_acao < ?")
                params_inter.append(hoje)
                conditions_pend.append("p.data_limite < ?")
                params_pend.append(hoje)
            elif filtro_status == "HOJE":
                conditions_inter.append("i.data_proxima_acao = ?")
                params_inter.append(hoje)
                conditions_pend.append("p.data_limite = ?")
                params_pend.append(hoje)
            elif filtro_status == "FUTURO":
                conditions_inter.append("i.data_proxima_acao > ?")
                params_inter.append(hoje)
                conditions_pend.append("p.data_limite > ?")
                params_pend.append(hoje)

        where_inter = (" AND " + " AND ".join(conditions_inter)) if conditions_inter else ""
        where_pend = (" AND " + " AND ".join(conditions_pend)) if conditions_pend else ""

        query_full = f"""
        SELECT * FROM (
            {query_interacoes}{where_inter}
            UNION ALL
            {query_pendencias}{where_pend}
        )
        ORDER BY
            CASE
                WHEN data < '{hoje}' THEN 0
                WHEN data = '{hoje}' THEN 1
                ELSE 2
            END,
            data ASC
        """

        params_full = params_inter + params_pend
        df = pd.read_sql_query(query_full, conn, params=params_full)
        return df

    finally:
        conn.close()

def get_contagem_proximas_acoes() -> dict:
    """
    Retorna contagens para cards: atrasadas, hoje, próximos 7 dias, próximos 30 dias.
    """
    conn = _get_conn()
    try:
        hoje = date.today().strftime("%Y-%m-%d")
        daqui_7 = (date.today() + timedelta(days=7)).strftime("%Y-%m-%d")
        daqui_30 = (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")

        # Atrasadas (data < hoje)
        atrasadas = conn.execute("""
            SELECT COUNT(*) FROM (
                SELECT data_proxima_acao FROM interacoes
                WHERE status_interacao = 'ABERTA' AND data_proxima_acao < ?
                UNION ALL
                SELECT data_limite FROM pendencias_comerciais
                WHERE status = 'ABERTA' AND data_limite < ?
            )
        """, (hoje, hoje)).fetchone()[0]

        # Hoje
        hoje_count = conn.execute("""
            SELECT COUNT(*) FROM (
                SELECT data_proxima_acao FROM interacoes
                WHERE status_interacao = 'ABERTA' AND data_proxima_acao = ?
                UNION ALL
                SELECT data_limite FROM pendencias_comerciais
                WHERE status = 'ABERTA' AND data_limite = ?
            )
        """, (hoje, hoje)).fetchone()[0]

        # Próximos 7 dias (excluindo hoje)
        prox_7 = conn.execute("""
            SELECT COUNT(*) FROM (
                SELECT data_proxima_acao FROM interacoes
                WHERE status_interacao = 'ABERTA'
                  AND data_proxima_acao > ? AND data_proxima_acao <= ?
                UNION ALL
                SELECT data_limite FROM pendencias_comerciais
                WHERE status = 'ABERTA'
                  AND data_limite > ? AND data_limite <= ?
            )
        """, (hoje, daqui_7, hoje, daqui_7)).fetchone()[0]

        # Próximos 30 dias (excluindo os 7 primeiros)
        prox_30 = conn.execute("""
            SELECT COUNT(*) FROM (
                SELECT data_proxima_acao FROM interacoes
                WHERE status_interacao = 'ABERTA'
                  AND data_proxima_acao > ? AND data_proxima_acao <= ?
                UNION ALL
                SELECT data_limite FROM pendencias_comerciais
                WHERE status = 'ABERTA'
                  AND data_limite > ? AND data_limite <= ?
            )
        """, (daqui_7, daqui_30, daqui_7, daqui_30)).fetchone()[0]

        return {
            "atrasadas": atrasadas,
            "hoje": hoje_count,
            "proximos_7": prox_7,
            "proximos_30": prox_30,
        }

    finally:
        conn.close()

# ──────────────────────────────────────────────
# v1.1 — FUNÇÕES PARA CLIENTE 360 (RESUMO EXECUTIVO)
# ──────────────────────────────────────────────

def get_ultimo_contato(cliente_id: int) -> Optional[dict]:
    """
    Retorna a interação mais recente do cliente (último contato).
    """
    conn = _get_conn()
    try:
        row = conn.execute(
            """
            SELECT
                i.data_interacao,
                i.contato_nome,
                i.contato_cargo,
                i.tipo_interacao,
                i.resultado,
                i.responsavel,
                i.resumo AS descricao
            FROM interacoes i
            WHERE i.cliente_id = ?
            ORDER BY i.data_interacao DESC, i.id DESC
            LIMIT 1
            """,
            (cliente_id,),
        ).fetchone()
        if row:
            return {
                "data_interacao": row[0],
                "contato_nome": row[1],
                "contato_cargo": row[2],
                "tipo_interacao": row[3],
                "resultado": row[4],
                "responsavel": row[5],
                "descricao": row[6],
            }
        return None
    finally:
        conn.close()

def get_pendencias_abertas_cliente(cliente_id: int) -> pd.DataFrame:
    """
    Retorna pendências abertas de um cliente específico.
    """
    return get_pendencias(cliente_id=cliente_id, status="ABERTA")

def get_proximas_acoes_cliente(cliente_id: int) -> pd.DataFrame:
    """
    Retorna próximas ações (interações abertas com data_proxima_acao) de um cliente.
    """
    conn = _get_conn()
    try:
        df = pd.read_sql_query(
            """
            SELECT
                i.data_proxima_acao AS data,
                i.tipo_prox_acao AS tipo_acao,
                i.obs_prox_acao AS observacao,
                i.responsavel,
                CASE
                    WHEN i.data_proxima_acao < date('now') THEN 'VENCIDA'
                    WHEN i.data_proxima_acao = date('now') THEN 'HOJE'
                    ELSE 'PENDENTE'
                END AS status
            FROM interacoes i
            WHERE i.cliente_id = ?
              AND i.status_interacao = 'ABERTA'
              AND i.data_proxima_acao IS NOT NULL
            ORDER BY i.data_proxima_acao ASC
            """,
            conn,
            params=(cliente_id,),
        )
        return df
    finally:
        conn.close()

def get_ultimos_eventos_cliente(cliente_id: int, limite: int = 10) -> pd.DataFrame:
    """
    Retorna os últimos eventos de um cliente:
    - Interações
    - Pendências criadas
    - Pendências concluídas
    - Evoluções de pendência
    - Oportunidades criadas
    Ordenação cronológica decrescente.
    """
    conn = _get_conn()
    try:
        query = f"""
        SELECT data, tipo, descricao, responsavel FROM (
            SELECT
                i.data_interacao AS data,
                'Interação: ' || i.tipo_interacao AS tipo,
                i.resumo AS descricao,
                i.responsavel
            FROM interacoes i
            WHERE i.cliente_id = ?

            UNION ALL

            SELECT
                p.criado_em AS data,
                'Pendência Criada' AS tipo,
                p.descricao,
                p.responsavel
            FROM pendencias_comerciais p
            WHERE p.cliente_id = ?

            UNION ALL

            SELECT
                p.data_limite AS data,
                'Pendência Concluída' AS tipo,
                p.descricao,
                p.responsavel
            FROM pendencias_comerciais p
            WHERE p.cliente_id = ? AND p.status = 'FECHADA'

            UNION ALL

            SELECT
                e.criado_em AS data,
                'Evolução: ' || e.tipo_evolucao AS tipo,
                e.descricao,
                e.usuario_nome AS responsavel
            FROM evolucao_pendencias e
            JOIN pendencias_comerciais p ON e.pendencia_id = p.id
            WHERE p.cliente_id = ?

            UNION ALL

            SELECT
                o.data_abertura AS data,
                'Oportunidade: ' || o.origem AS tipo,
                o.descricao,
                '' AS responsavel
            FROM oportunidades o
            WHERE o.cliente_id = ?
        )
        WHERE data IS NOT NULL
        ORDER BY data DESC
        LIMIT ?
        """
        df = pd.read_sql_query(
            query,
            conn,
            params=(cliente_id, cliente_id, cliente_id, cliente_id, cliente_id, limite),
        )
        return df
    finally:
        conn.close()

def get_timeline_unificada(
    cliente_id: int,
    limite: int = 50,
) -> pd.DataFrame:
    """
    Retorna timeline unificada do cliente contendo:
    - Interações
    - Evoluções de pendências
    - Pendências concluídas
    - Pendências reabertas
    Ordenação cronológica decrescente.
    v1.3 — Substitui get_ultimos_eventos_cliente.
    """
    conn = _get_conn()
    try:
        query = f"""
        SELECT data, tipo_evento, descricao, detalhes, responsavel, icone FROM (
            SELECT
                i.data_interacao AS data,
                'INTERACAO' AS tipo_evento,
                i.tipo_interacao || ': ' || i.resumo AS descricao,
                COALESCE('Contato: ' || i.contato_nome || ' | Resultado: ' || i.resultado, '') AS detalhes,
                i.responsavel,
                '📞' AS icone
            FROM interacoes i
            WHERE i.cliente_id = ?

            UNION ALL

            SELECT
                e.criado_em AS data,
                'EVOLUCAO_' || e.tipo_evolucao AS tipo_evento,
                e.descricao,
                'Evolução em pendência' AS detalhes,
                e.usuario_nome AS responsavel,
                CASE e.tipo_evolucao
                    WHEN 'CONCLUSAO' THEN '✅'
                    WHEN 'REABERTURA' THEN '🔄'
                    WHEN 'COMENTARIO' THEN '💬'
                    WHEN 'ANDAMENTO' THEN '📌'
                    ELSE '📝'
                END AS icone
            FROM evolucao_pendencias e
            JOIN pendencias_comerciais p ON e.pendencia_id = p.id
            WHERE p.cliente_id = ?

            UNION ALL

            SELECT
                criado_em AS data,
                'PENDENCIA_CRIADA' AS tipo_evento,
                'Pendência: ' || descricao,
                'Prioridade: ' || prioridade || ' | Vencimento: ' || data_limite AS detalhes,
                responsavel,
                '📌' AS icone
            FROM pendencias_comerciais
            WHERE cliente_id = ? AND criado_em IS NOT NULL

            UNION ALL

            SELECT
                o.data_abertura AS data,
                'OPORTUNIDADE' AS tipo_evento,
                'Oportunidade: ' || COALESCE(origem, ''),
                descricao,
                '' AS responsavel,
                '💎' AS icone
            FROM oportunidades o
            WHERE o.cliente_id = ?
        )
        WHERE data IS NOT NULL
        ORDER BY data DESC
        LIMIT ?
        """
        df = pd.read_sql_query(
            query,
            conn,
            params=(cliente_id, cliente_id, cliente_id, cliente_id, limite),
        )
        return df
    finally:
        conn.close()

def get_contatos_conhecidos(cliente_id: int) -> pd.DataFrame:
    """
    Retorna contatos extraídos das interações de um cliente,
    agrupados por nome, com cargo, telefone e email.
    Apenas registros com contato_nome válido.
    """
    conn = _get_conn()
    try:
        df = pd.read_sql_query(
            """
            SELECT
                i.contato_nome,
                i.contato_cargo,
                i.contato_telefone,
                i.contato_email,
                MAX(i.data_interacao) AS ultimo_contato
            FROM interacoes i
            WHERE i.cliente_id = ?
              AND i.contato_nome IS NOT NULL
              AND i.contato_nome != ''
            GROUP BY i.contato_nome
            ORDER BY ultimo_contato DESC
            """,
            conn,
            params=(cliente_id,),
        )
        return df
    finally:
        conn.close()
