"""
Componentes UI reutilizáveis — ULITEC CRM v2.3

Biblioteca de componentes padronizados para todo o CRM.
Nenhuma regra de negócio — apenas interface.

Como usar:
    from components import (
        titulo_pagina, card_indicador, badge_status,
        linha_filtros, tabela_padrao, mensagem_sucesso,
        caixa_busca, ...
    )
"""

import streamlit as st
import pandas as pd

# ═══════════════════════════════════════════════════════════
# ETAPA 3 — STATUS
# ═══════════════════════════════════════════════════════════

STATUS_PADRAO = [
    "ENVIADO",
    "ORÇADO",
    "APROVADO",
    "RECEBIDO",
    "CANCELADO",
]

CORES_STATUS = {
    "ENVIADO":     ("#2563eb", "#dbeafe"),      # Azul
    "ORÇADO":      ("#f59e0b", "#fef3c7"),      # Amarelo
    "APROVADO":    ("#16a34a", "#dcfce7"),      # Verde
    "RECEBIDO":    ("#6366f1", "#e0e7ff"),      # Índigo
    "CANCELADO":   ("#dc2626", "#fee2e2"),      # Vermelho
    "ABERTA":      ("#2563eb", "#dbeafe"),      # Azul
    "FECHADA":     ("#16a34a", "#dcfce7"),      # Verde
    "VENCIDA":     ("#dc2626", "#fee2e2"),      # Vermelho
    "PENDENTE":    ("#f59e0b", "#fef3c7"),      # Amarelo
    "CONCLUIDA":   ("#16a34a", "#dcfce7"),      # Verde
    "PERDIDA":     ("#dc2626", "#fee2e2"),      # Vermelho
}

def badge_status(status: str, tamanho: str = "pequeno") -> str:
    """
    Gera um badge HTML padronizado para qualquer status.

    Parâmetros:
        status: Texto do status (ex: "APROVADO", "CANCELADO")
        tamanho: "pequeno" (default) | "medio" | "grande"

    Retorna:
        String HTML com o badge formatado.

    Exemplo:
        st.markdown(badge_status("APROVADO"), unsafe_allow_html=True)
    """
    chave = status.upper().strip() if status else ""
    cor_texto, cor_fundo = CORES_STATUS.get(
        chave,
        ("#374151", "#f3f4f6")  # Cinza default
    )

    tamanhos = {
        "pequeno":  {"padding": "2px 8px", "font": "0.75rem"},
        "medio":    {"padding": "4px 14px", "font": "0.85rem"},
        "grande":   {"padding": "6px 20px", "font": "1rem"},
    }
    estilo = tamanhos.get(tamanho, tamanhos["pequeno"])

    return f"""
    <span style="
        display: inline-block;
        background-color: {cor_fundo};
        color: {cor_texto};
        font-weight: 600;
        padding: {estilo['padding']};
        border-radius: 12px;
        font-size: {estilo['font']};
        border: 1px solid {cor_texto}22;
    ">{status}</span>
    """

# ═══════════════════════════════════════════════════════════
# ETAPA 2 — HEADERS
# ═══════════════════════════════════════════════════════════

def titulo_pagina(icone: str, titulo: str, descricao: str = ""):
    """
    Título padronizado de página.

    Parâmetros:
        icone: Emoji/ícone da página (ex: "📊", "🎯")
        titulo: Nome da página
        descricao: Texto opcional abaixo do título

    Exemplo:
        titulo_pagina("📊", "Dashboard Comercial", "Visão geral dos indicadores")
    """
    st.title(f"{icone} {titulo}")
    if descricao:
        st.markdown(descricao)

def subtitulo(texto: str):
    """Subtítulo padronizado com `st.subheader`."""
    st.subheader(texto)

def cabecalho_modulo(icone: str, titulo: str, descricao: str = ""):
    """
    Cabeçalho completo de módulo (título + descrição + divisor).

    Parâmetros:
        icone: Emoji do módulo
        titulo: Nome do módulo
        descricao: Texto opcional explicativo

    Exemplo:
        cabecalho_modulo("📞", "Relacionamento Comercial",
                         "Registre interações e gerencie pendências")
    """
    st.title(f"{icone} {titulo}")
    if descricao:
        st.markdown(descricao)
    st.divider()

def secao_divisoria(texto: str = ""):
    """
    Divisor visual entre seções, com texto opcional.

    Parâmetros:
        texto: Texto opcional para exibir acima do divisor
    """
    if texto:
        st.markdown(f"### {texto}")
    st.divider()

# ═══════════════════════════════════════════════════════════
# ETAPA 4 — KPIs
# ═══════════════════════════════════════════════════════════

def card_indicador(
    rotulo: str,
    valor,
    delta: str = None,
    help_text: str = None,
    icone: str = "",
    use_container: bool = True,
):
    """
    Card de indicador (KPI) padronizado.

    Parâmetros:
        rotulo: Nome do indicador (ex: "Clientes Ativos")
        valor: Valor do indicador (int, float, str formatada)
        delta: Variação opcional (ex: "+15%")
        help_text: Texto de tooltip opcional
        icone: Emoji opcional para prefixar o rótulo
        use_container: Se True (default), usa st.columns

    Exemplo:
        card_indicador("Receita", "R$ 1.2M", delta="+12%",
                       help_text="Faturamento total do período", icone="📈")
    """
    rotulo_exib = f"{icone} {rotulo}" if icone else rotulo
    st.metric(
        label=rotulo_exib,
        value=valor,
        delta=delta,
        help=help_text,
    )

def linha_indicadores(indicadores: list, cols: int = 4):
    """
    Linha completa de KPIs padronizados.

    Parâmetros:
        indicadores: Lista de dicionários, cada um com:
            - "rotulo": str
            - "valor": qualquer
            - "delta": str (opcional)
            - "help": str (opcional)
            - "icone": str (opcional)
        cols: Número de colunas (default=4)

    Exemplo:
        linha_indicadores([
            {"rotulo": "Clientes", "valor": 150, "icone": "🏢"},
            {"rotulo": "Receita", "valor": "R$ 1.2M", "delta": "+12%"},
        ])
    """
    colunas = st.columns(cols)
    for i, indicador in enumerate(indicadores):
        with colunas[i % cols]:
            card_indicador(
                rotulo=indicador.get("rotulo", ""),
                valor=indicador.get("valor", "-"),
                delta=indicador.get("delta"),
                help_text=indicador.get("help"),
                icone=indicador.get("icone", ""),
            )

# ═══════════════════════════════════════════════════════════
# ETAPA 5 — FILTROS
# ═══════════════════════════════════════════════════════════

def filtro_unidade_sidebar():
    """
    Filtro de unidade (filial) no sidebar.

    Gerencia automaticamente st.session_state["unidade_ativa"].

    Retorna:
        String com a unidade selecionada ("GRUPO", "ULITEC SP", "ULITEC RS")

    Exemplo:
        unidade = filtro_unidade_sidebar()
    """
    from permissions import pode_selecionar_unidade

    if "unidade_ativa" not in st.session_state:
        st.session_state["unidade_ativa"] = "GRUPO"
    if "unidade_usuario" not in st.session_state:
        st.session_state["unidade_usuario"] = "ULITEC SP"

    opcoes = ["Grupo (Consolidado)", "ULITEC SP", "ULITEC RS"]

    if pode_selecionar_unidade():
        idx_map = {"GRUPO": 0, "ULITEC SP": 1, "ULITEC RS": 2}
        idx = idx_map.get(st.session_state["unidade_ativa"], 0)

        escolha = st.sidebar.selectbox(
            "🏢 Filtrar Unidade",
            options=opcoes,
            index=idx,
        )
        mapa_reverso = {"Grupo (Consolidado)": "GRUPO", "ULITEC SP": "ULITEC SP", "ULITEC RS": "ULITEC RS"}
        st.session_state["unidade_ativa"] = mapa_reverso[escolha]
    else:
        st.session_state["unidade_ativa"] = st.session_state["unidade_usuario"]

    return st.session_state["unidade_ativa"]

def filtro_periodo_sidebar(
    chave: str = "filtro_periodo",
    label: str = "📅 Período",
    opcoes: list = None,
    default: str = "Últimos 30 dias",
):
    """
    Filtro de período no sidebar.

    Parâmetros:
        chave: Chave do session_state
        label: Rótulo do filtro
        opcoes: Lista de opções de período
        default: Valor padrão

    Retorna:
        String com o período selecionado
    """
    if opcoes is None:
        opcoes = [
            "Hoje",
            "Últimos 7 dias",
            "Últimos 15 dias",
            "Últimos 30 dias",
            "Últimos 60 dias",
            "Últimos 90 dias",
            "Mês Atual",
            "Ano Atual",
            "Todo o Período",
        ]

    return st.sidebar.selectbox(
        label,
        options=opcoes,
        index=opcoes.index(default) if default in opcoes else 0,
        key=chave,
    )

def linha_filtros(filtros: list):
    """
    Linha de filtros padronizada em colunas.

    Parâmetros:
        filtros: Lista de dicionários com:
            - "tipo": "selectbox" | "multiselect" | "text" | "date" | "number"
            - "rotulo": str
            - "opcoes": list (para selectbox/multiselect)
            - "default": valor padrão
            - "key": str (chave session_state)
            - "cols": int (largura em colunas, default=1)

    Retorna:
        Dicionário com {chave: valor} de cada filtro

    Exemplo:
        valores = linha_filtros([
            {"tipo": "selectbox", "rotulo": "Estado", "opcoes": ["SP", "RS"], "key": "f_estado"},
            {"tipo": "text", "rotulo": "Cliente", "key": "f_cliente"},
        ])
    """
    total_cols = sum(f.get("cols", 1) for f in filtros)
    colunas = st.columns(max(total_cols, 1))

    resultados = {}
    col_idx = 0
    for i, filtro in enumerate(filtros):
        largura = filtro.get("cols", 1)
        chave = filtro.get("key", f"filtro_{i}")
        rotulo = filtro.get("rotulo", "")
        default = filtro.get("default")

        with colunas[col_idx]:
            if filtro["tipo"] == "selectbox":
                opcoes = filtro.get("opcoes", [])
                idx = 0
                if default and default in opcoes:
                    idx = opcoes.index(default)
                resultados[chave] = st.selectbox(
                    rotulo,
                    options=opcoes,
                    index=idx,
                    key=chave,
                )

            elif filtro["tipo"] == "multiselect":
                opcoes = filtro.get("opcoes", [])
                resultados[chave] = st.multiselect(
                    rotulo,
                    options=opcoes,
                    default=default if default else opcoes,
                    key=chave,
                )

            elif filtro["tipo"] == "text":
                placeholder = filtro.get("placeholder", "")
                resultados[chave] = st.text_input(
                    rotulo,
                    placeholder=placeholder,
                    key=chave,
                )

            elif filtro["tipo"] == "date":
                import datetime
                resultados[chave] = st.date_input(
                    rotulo,
                    value=default if default else datetime.date.today(),
                    key=chave,
                )

            elif filtro["tipo"] == "number":
                step = filtro.get("step", 1)
                min_val = filtro.get("min", 0)
                max_val = filtro.get("max", 100)
                resultados[chave] = st.number_input(
                    rotulo,
                    min_value=min_val,
                    max_value=max_val,
                    value=default if default else min_val,
                    step=step,
                    key=chave,
                )

            else:
                resultados[chave] = None

        col_idx += largura

    return resultados

# ═══════════════════════════════════════════════════════════
# ETAPA 6 — FORMULÁRIOS (helpers)
# ═══════════════════════════════════════════════════════════

def campo_obrigatorio(rotulo: str, placeholder: str = "", chave: str = None):
    """
    Campo de texto obrigatório com asterisco visual.

    Retorna:
        Valor digitado (str)
    """
    return st.text_input(
        f"{rotulo} *",
        placeholder=placeholder,
        key=chave,
    )

def campo_opcional(rotulo: str, placeholder: str = "", chave: str = None):
    """
    Campo de texto opcional.

    Retorna:
        Valor digitado (str)
    """
    return st.text_input(
        rotulo,
        placeholder=placeholder,
        key=chave,
    )

def campo_data(rotulo: str, valor_padrao=None, chave: str = None):
    """Campo de data padronizado."""
    import datetime
    if valor_padrao is None:
        valor_padrao = datetime.date.today()
    return st.date_input(rotulo, value=valor_padrao, key=chave)

def campo_valor(rotulo: str, valor_padrao: float = 0.0, chave: str = None):
    """Campo de valor monetário padronizado."""
    return st.number_input(
        rotulo,
        min_value=0.0,
        value=valor_padrao,
        step=100.0,
        format="%.2f",
        key=chave,
    )

def campo_observacao(rotulo: str = "📝 Observações", altura: int = 100, chave: str = None):
    """Campo de observações/texto livre padronizado."""
    return st.text_area(rotulo, height=altura, key=chave)

def botoes_form(salvar: bool = True, cancelar: bool = True, excluir: bool = False):
    """
    Botões padronizados para formulários.

    Parâmetros:
        salvar: Exibe botão "💾 Salvar" (default=True)
        cancelar: Exibe botão "↩️ Cancelar" (default=True)
        excluir: Exibe botão "🗑 Excluir" (default=False)

    Retorna:
        Tupla (salvar_click, cancelar_click, excluir_click)
    """
    cols = []
    if salvar:
        cols.append("💾 Salvar")
    if cancelar:
        cols.append("↩️ Cancelar")
    if excluir:
        cols.append("🗑 Excluir")

    botoes = {}
    if cols:
        col_botoes = st.columns(len(cols))
        for i, label in enumerate(cols):
            tipo = "primary" if "Salvar" in label else "secondary"
            botoes[label] = col_botoes[i].button(label, type=tipo, width="stretch")

    return (
        botoes.get("💾 Salvar", False),
        botoes.get("↩️ Cancelar", False),
        botoes.get("🗑 Excluir", False),
    )

# ═══════════════════════════════════════════════════════════
# ETAPA 7 — TABELAS
# ═══════════════════════════════════════════════════════════

import pandas as pd

def tabela_padrao(
    dados: pd.DataFrame,
    height: int = 400,
    uso_largura: bool = True,
    ocultar_indice: bool = True,
    coluna_config: dict = None,
):
    """
    Tabela padronizada com `st.dataframe`.

    Parâmetros:
        dados: DataFrame a exibir
        height: Altura em pixels (default=400)
        uso_largura: Usar largura total (default=True)
        ocultar_indice: Ocultar coluna de índice (default=True)
        coluna_config: Configurações de coluna (opcional)

    Exemplo:
        tabela_padrao(df, height=500, coluna_config={
            "valor": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
        })
    """
    width_val = "stretch" if uso_largura else "content"
    kwargs = {
        "width": width_val,
        "height": height,
        "hide_index": ocultar_indice,
    }
    if coluna_config:
        kwargs["column_config"] = coluna_config

    st.dataframe(dados, **kwargs)

def aplicar_estilo_tabela(
    df: pd.DataFrame,
    coluna_cor: str = "status",
    mapa_cores: dict = None,
):
    """
    Aplica estilo condicional a um DataFrame baseado em coluna.

    Parâmetros:
        df: DataFrame
        coluna_cor: Nome da coluna usada para definir cores
        mapa_cores: Dict {valor: "background-color: #xxx; color: #xxx"}

    Retorna:
        Styler do pandas para usar com .style.apply()

    Exemplo:
        st.dataframe(aplicar_estilo_tabela(df, "status", {
            "ATIVO": "background-color: #dcfce7; color: #166534",
        }))
    """
    if mapa_cores is None:
        mapa_cores = {}

    def colorir_linha(row):
        valor = str(row.get(coluna_cor, "")).upper().strip()
        estilo = mapa_cores.get(valor, "")
        if estilo:
            return [estilo] * len(row)
        # Verifica CORES_STATUS
        cor_texto, cor_fundo = CORES_STATUS.get(valor, ("", ""))
        if cor_fundo:
            return [f"background-color: {cor_fundo}; color: {cor_texto}"] * len(row)
        return [""] * len(row)

    return df.style.apply(colorir_linha, axis=1)

# ═══════════════════════════════════════════════════════════
# ETAPA 2 — MENSAGENS
# ═══════════════════════════════════════════════════════════

def mensagem_sucesso(texto: str):
    """Mensagem de sucesso padronizada."""
    st.success(texto)

def mensagem_erro(texto: str):
    """Mensagem de erro padronizada."""
    st.error(f"❌ {texto}")

def mensagem_atencao(texto: str):
    """Mensagem de alerta/atenção padronizada."""
    st.warning(f"⚠️ {texto}")

def mensagem_info(texto: str):
    """Mensagem informativa padronizada."""
    st.info(texto)

def confirmacao(texto: str, ao_confirmar, *args, **kwargs):
    """
    Caixa de confirmação padronizada.

    Parâmetros:
        texto: Texto da mensagem de confirmação
        ao_confirmar: Função callback se confirmado
        *args, **kwargs: Argumentos passados para o callback

    Exemplo:
        confirmacao("Deseja excluir este registro?", excluir_registro, id=123)
    """
    with st.container(border=True):
        st.warning(f"❗ {texto}")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Confirmar", type="primary", width="stretch"):
                return ao_confirmar(*args, **kwargs)
        with col2:
            if st.button("❌ Cancelar", width="stretch"):
                return None

def container_resultado(titulo: str = "", expandido: bool = True):
    """
    Container padronizado para resultados/expansão de conteúdo.

    Parâmetros:
        titulo: Título do container
        expandido: Se começa expandido (default=True)

    Retorna:
        Contexto do st.expander

    Exemplo:
        with container_resultado("Detalhes"):
            st.write("Conteúdo aqui")
    """
    if titulo:
        return st.expander(titulo, expanded=expandido)
    return st.container(border=True)

# ═══════════════════════════════════════════════════════════
# ETAPA 8 — BUSCA INTELIGENTE
# ═══════════════════════════════════════════════════════════

def caixa_busca(
    placeholder: str = "🔍 Buscar...",
    chave: str = "caixa_busca",
    help_text: str = None,
    label: str = None,
    valor_padrao: str = "",
):
    """
    Caixa de busca padronizada.

    Parâmetros:
        placeholder: Texto de placeholder
        chave: Chave session_state
        help_text: Texto de ajuda
        label: Rótulo (se None, usa apenas o placeholder)
        valor_padrao: Valor inicial

    Retorna:
        String com o termo digitado

    Exemplo:
        termo = caixa_busca("Buscar cliente...", chave="busca_cliente")
    """
    if label:
        return st.text_input(
            label,
            placeholder=placeholder,
            help=help_text,
            key=chave,
            value=valor_padrao,
        )
    return st.text_input(
        "🔍",
        placeholder=placeholder,
        help=help_text,
        key=chave,
        label_visibility="collapsed",
        value=valor_padrao,
    )

# ═══════════════════════════════════════════════════════════
# ETAPA 9 — GRÁFICOS
# ═══════════════════════════════════════════════════════════

def config_grafico(
    altura: int = 400,
    titulo: str = None,
    usar_largura_total: bool = True,
):
    """
    Retorna configuração padrão para gráficos Plotly.

    Parâmetros:
        altura: Altura do gráfico em pixels
        titulo: Título do gráfico
        usar_largura_total: Usar toda largura disponível

    Retorna:
        Dict com layout configurado para usar em fig.update_layout()

    Exemplo:
        fig.update_layout(**config_grafico(altura=500, titulo="Vendas por Mês"))
    """
    layout = {
        "height": altura,
        "margin": dict(l=10, r=10, t=40 if titulo else 10, b=10),
        "font": dict(size=12),
    }
    if titulo:
        layout["title"] = titulo
    return layout

def grafico_barras(
    dados: pd.DataFrame,
    x: str,
    y: str,
    titulo: str = "",
    cor: str = None,
    altura: int = 400,
    horizontal: bool = False,
    color_coluna: str = None,
):
    """
    Gráfico de barras padronizado usando Plotly.

    Parâmetros:
        dados: DataFrame com os dados
        x: Nome da coluna para eixo X
        y: Nome da coluna para eixo Y
        titulo: Título do gráfico
        cor: Cor única das barras (ex: "#2563eb")
        altura: Altura em pixels
        horizontal: Se True, barras horizontais
        color_coluna: Coluna para colorir por categoria

    Exemplo:
        grafico_barras(df, x="mes", y="vendas", titulo="Vendas por Mês")
    """
    import plotly.express as px

    if horizontal:
        fig = px.bar(
            dados,
            x=y,
            y=x,
            orientation="h",
            title=titulo,
            color=color_coluna,
            color_discrete_sequence=[cor] if cor and not color_coluna else None,
        )
    else:
        fig = px.bar(
            dados,
            x=x,
            y=y,
            title=titulo,
            color=color_coluna,
            color_discrete_sequence=[cor] if cor and not color_coluna else None,
        )

    fig.update_layout(**config_grafico(altura=altura))

    if horizontal:
        fig.update_layout(yaxis=dict(categoryorder="total ascending"))

    st.plotly_chart(fig, width="stretch")
    return fig

# ═══════════════════════════════════════════════════════════
# HELPERS ADICIONAIS
# ═══════════════════════════════════════════════════════════

def espacamento(altura: int = 1):
    """Adiciona espaçamento vertical."""
    for _ in range(altura):
        st.markdown("")

def linha_separadora():
    """Linha separadora padronizada (`st.divider()`)."""
    st.divider()

# ═══════════════════════════════════════════════════════════
# RODAPÉ PADRONIZADO
# ═══════════════════════════════════════════════════════════

def rodape_padrao():
    """
    Renderiza um rodapé padronizado em todas as páginas do CRM.

    Exibe:
        ULITEC CRM | v1.0.3 | Ambiente: DEV

    Deve ser chamado ao final de toda página Streamlit (após o conteúdo principal).
    """
    from services.version import get_version_short_info

    info = get_version_short_info()

    st.markdown("---")
    st.markdown(
        f"""
        <div style="text-align: center; color: #999; font-size: 0.8rem; padding: 0.5rem 0;">
            {info['sistema']} &nbsp;|&nbsp;
            v{info['versao']} &nbsp;|&nbsp;
            Ambiente: {info['ambiente']}
        </div>
        """,
        unsafe_allow_html=True,
    )
