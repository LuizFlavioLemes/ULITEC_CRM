"""
Componentes do módulo de Inteligência Comercial.
Consomem exclusivamente funções de services/inteligencia_comercial.py e services/relacionamento.py.
Nenhum componente executa SQL diretamente (exceção: fila_operacional com SQL de OS/Pendências).
"""

from components.inteligencia.score import exibir_score
from components.inteligencia.listas import exibir_listas
from components.inteligencia.mercado import exibir_mercado
from components.inteligencia.indicadores import exibir_indicadores
from components.inteligencia.fila_operacional import exibir_fila_operacional
from components.inteligencia.acoes import exibir_acoes_relacionamento
from components.inteligencia.resumo import exibir_resumo_executivo
from components.inteligencia.painel_listas import (
    exibir_prioritarios,
    exibir_esfriando,
    exibir_esquentando,
    exibir_sem_faturamento,
    exibir_sem_visita,
    exibir_preventivas,
    exibir_parque_mitsubishi,
    exibir_top_faturamento,
)

__all__ = [
    "exibir_score",
    "exibir_listas",
    "exibir_mercado",
    "exibir_indicadores",
    "exibir_fila_operacional",
    "exibir_acoes_relacionamento",
    "exibir_resumo_executivo",
    "exibir_prioritarios",
    "exibir_esfriando",
    "exibir_esquentando",
    "exibir_sem_faturamento",
    "exibir_sem_visita",
    "exibir_preventivas",
    "exibir_parque_mitsubishi",
    "exibir_top_faturamento",
]
