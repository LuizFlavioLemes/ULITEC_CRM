"""
Módulo de Inteligência Comercial — ULITEC CRM v1.5.2

FACADE DE COMPATIBILIDADE RETROATIVA.

Este arquivo foi modularizado em services/inteligencia/.
Todas as funções, constantes e utilitários são reexportados aqui
para garantir compatibilidade total com imports existentes.

NENHUMA FUNCIONALIDADE FOI ALTERADA.
"""

# ── Reexportar constantes ──
from services.inteligencia.utils import (
    LIMITE_DIAS_VISITA_ESFRIANDO,
    LIMITE_DIAS_SEM_VISITA,
    LIMITE_MESES_SEM_FATURAMENTO,
    TOP_N,
    TOP_SCORE,
    PERIODO_ATUAL_DIAS,
    PERIODO_ANTERIOR_DIAS,
    PESO_MAQUINAS_MITSUBISHI,
    PESO_FATURAMENTO,
    PESO_CLASSE_ABC,
    PESO_DIAS_SEM_CONTATO,
    PESO_DIAS_SEM_VISITA,
    PESO_QUEDA_FATURAMENTO,
    PESO_PREVENTIVAS_VENCIDAS,
    PESO_OPORTUNIDADES,
    PENALIDADE_RELACIONAMENTO_ATIVO,
    PESO_OS,
    PESO_VISITA,
)

# ── Reexportar funções auxiliares ──
from services.inteligencia.utils import (
    _get_conn,
    _data_limite,
    _get_dias,
    _normalizar_log,
    _verificar_relacionamento_ativo,
)

# ── Reexportar funções de clientes ──
from services.inteligencia.clientes import (
    get_clientes_esfriando,
    get_clientes_esquentando,
    get_clientes_sem_visita,
    get_clientes_sem_faturamento,
    get_clientes_muitas_os,
    get_clientes_parque_relevante,
)

# ── Reexportar função de indicadores ──
from services.inteligencia.indicadores import (
    classificar_abcd,
)

# ── Reexportar funções de mercado ──
from services.inteligencia.mercado import (
    get_preventivas_vencidas,
    get_prospeccao_mitsubishi,
    get_top_faturamento_12m,
    get_ultima_interacao_clientes,
)

# ── Reexportar função de score ──
from services.inteligencia.score import (
    calcular_score_comercial,
)

# ── Reexportar função de resumo ──
from services.inteligencia.resumo import (
    get_resumo_executivo,
)

__all__ = [
    # Constantes
    "LIMITE_DIAS_VISITA_ESFRIANDO",
    "LIMITE_DIAS_SEM_VISITA",
    "LIMITE_MESES_SEM_FATURAMENTO",
    "TOP_N",
    "TOP_SCORE",
    "PERIODO_ATUAL_DIAS",
    "PERIODO_ANTERIOR_DIAS",
    "PESO_MAQUINAS_MITSUBISHI",
    "PESO_FATURAMENTO",
    "PESO_CLASSE_ABC",
    "PESO_DIAS_SEM_CONTATO",
    "PESO_DIAS_SEM_VISITA",
    "PESO_QUEDA_FATURAMENTO",
    "PESO_PREVENTIVAS_VENCIDAS",
    "PESO_OPORTUNIDADES",
    "PENALIDADE_RELACIONAMENTO_ATIVO",
    "PESO_OS",
    "PESO_VISITA",
    # Clientes
    "get_clientes_esfriando",
    "get_clientes_esquentando",
    "get_clientes_sem_visita",
    "get_clientes_sem_faturamento",
    "get_clientes_muitas_os",
    "get_clientes_parque_relevante",
    # Indicadores
    "classificar_abcd",
    # Mercado
    "get_preventivas_vencidas",
    "get_prospeccao_mitsubishi",
    "get_top_faturamento_12m",
    "get_ultima_interacao_clientes",
    # Score
    "calcular_score_comercial",
    # Resumo
    "get_resumo_executivo",
]