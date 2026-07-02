"""
Pacote de componentes UI reutilizáveis — ULITEC CRM v2.3

Todos os componentes de interface do CRM devem utilizar esta biblioteca
para garantir padronização visual e reduzir código duplicado.

Uso:
    from components import (
        titulo_pagina,
        card_indicador,
        linha_filtros,
        ...
    )
"""

from components.ui import (
    # Headers
    titulo_pagina,
    subtitulo,
    cabecalho_modulo,
    secao_divisoria,
    # Cards
    card_indicador,
    linha_indicadores,
    # Status
    badge_status,
    CORES_STATUS,
    STATUS_PADRAO,
    # Filtros
    linha_filtros,
    filtro_unidade_sidebar,
    filtro_periodo_sidebar,
    # Tabelas
    tabela_padrao,
    # Mensagens
    mensagem_sucesso,
    mensagem_erro,
    mensagem_atencao,
    mensagem_info,
    confirmacao,
    # Containers
    container_resultado,
    # Busca
    caixa_busca,
    # Gráficos
    config_grafico,
    grafico_barras,
    # Rodapé
    rodape_padrao,
)

__all__ = [
    "titulo_pagina",
    "subtitulo",
    "cabecalho_modulo",
    "secao_divisoria",
    "card_indicador",
    "linha_indicadores",
    "badge_status",
    "CORES_STATUS",
    "STATUS_PADRAO",
    "linha_filtros",
    "filtro_unidade_sidebar",
    "filtro_periodo_sidebar",
    "tabela_padrao",
    "mensagem_sucesso",
    "mensagem_erro",
    "mensagem_atencao",
    "mensagem_info",
    "confirmacao",
    "container_resultado",
    "caixa_busca",
    "config_grafico",
    "grafico_barras",
    "rodape_padrao",
]