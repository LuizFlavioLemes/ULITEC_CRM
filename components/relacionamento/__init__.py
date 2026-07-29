"""
Componentes reutilizáveis do módulo de Relacionamento Comercial.
Cada função encapsula a interface de uma aba da página.
"""

from components.relacionamento.agenda import exibir_agenda
from components.relacionamento.registro import exibir_registro
from components.relacionamento.historico import exibir_historico
from components.relacionamento.pendencias import exibir_pendencias, exibir_nova_pendencia
from components.relacionamento.alertas import exibir_alertas

__all__ = [
    "exibir_agenda",
    "exibir_registro",
    "exibir_historico",
    "exibir_pendencias",
    "exibir_nova_pendencia",
    "exibir_alertas",
]
