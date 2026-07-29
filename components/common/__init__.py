"""
Biblioteca de Componentes Comuns (UI Framework) — ULITEC CRM
============================================================

Camada genérica e desacoplada de componentes Streamlit reutilizáveis.

Nenhum componente contém regra de negócio.
Nenhum componente acessa banco de dados.
Nenhum componente importa Services.

Uso:
    from components.common import page_header, metric_grid, panel
"""

from components.common.page_header import page_header, section_header, page_subtitle
from components.common.metric_grid import metric_grid, metric_card
from components.common.panel import panel, info_panel, warning_panel
from components.common.section import section, subsection, divider
from components.common.toolbar import toolbar, action_button
from components.common.empty_state import empty_state, no_results
from components.common.loading import loading_wrapper, spinner_context

__all__ = [
    "page_header",
    "section_header",
    "page_subtitle",
    "metric_grid",
    "metric_card",
    "panel",
    "info_panel",
    "warning_panel",
    "section",
    "subsection",
    "divider",
    "toolbar",
    "action_button",
    "empty_state",
    "no_results",
    "loading_wrapper",
    "spinner_context",
]