"""
Módulo central de permissões do CRM ULITEC.

TODA decisão de acesso deve passar exclusivamente por este módulo.
NENHUMA página deve comparar texto de perfil diretamente.

Perfis (hierarquia):
    MASTER > SÓCIO > GERENTE > OPERADOR > CONSULTA

MASTER herda automaticamente TODAS as permissões do SÓCIO.
A única diferença é que MASTER possui também permissões de desenvolvimento.
"""

import streamlit as st

# ═══════════════════════════════════════════════════════════
# 1. HIERARQUIA DE PERFIS
# ═══════════════════════════════════════════════════════════

_HIERARQUIA = {
    "CONSULTA": 0,
    "OPERADOR": 1,
    "GERENTE": 2,
    "SÓCIO": 3,
    "MASTER": 4,
}

PERFIS_VALIDOS = list(_HIERARQUIA.keys())

def _get_perfil() -> str:
    """Retorna o perfil do usuário logado ou string vazia."""
    return st.session_state.get("perfil", "")

def _get_nivel() -> int:
    """Retorna o nível hierárquico do perfil atual (-1 se não logado/inválido)."""
    return _HIERARQUIA.get(_get_perfil(), -1)

# ═══════════════════════════════════════════════════════════
# 2. MATRIZ DE PERMISSÕES (BASE ÚNICA)
# ═══════════════════════════════════════════════════════════
#
# Hierarquia de herança:
#   MASTER = SÓCIO + desenvolvimento
#   SÓCIO  = GERENTE + administração
#   GERENTE = OPERADOR + exclusão + importação
#   OPERADOR = CONSULTA + edição
#   CONSULTA = apenas visualização
#
# Cada perfil declara APENAS o que acrescenta em relação ao anterior.
# O cálculo final é feito pela função _get_permissoes().

_PERMISSOES_BASE = {
    "CONSULTA": {
        "visualizar": True,
        "editar": False,
        "excluir": False,
        "importar": False,
        "administrar": False,
        "desenvolver": False,
        "gerenciar_usuarios": False,
        "gerenciar_usuarios_limitado": False,
        "selecionar_unidade": False,
    },
    "OPERADOR": {
        "editar": True,
    },
    "GERENTE": {
        "excluir": True,
        "importar": True,
        "gerenciar_usuarios_limitado": True,
        "selecionar_unidade": True,
    },
    "SÓCIO": {
        "administrar": True,
        "gerenciar_usuarios": True,
    },
    "MASTER": {
        "desenvolver": True,
    },
}

# Cache de permissões calculadas por perfil
_CACHE_PERMISSOES = {}

def _get_permissoes(perfil: str) -> dict:
    """
    Retorna o dicionário completo de permissões para um perfil,
    respeitando a hierarquia de herança.
    """
    if perfil in _CACHE_PERMISSOES:
        return _CACHE_PERMISSOES[perfil]

    perfil_nivel = _HIERARQUIA.get(perfil, -1)

    # Começa com as permissões base de CONSULTA
    permissoes = dict(_PERMISSOES_BASE["CONSULTA"])

    # Percorre todos os perfis do nível mais baixo até o atual
    for p, nivel in sorted(_HIERARQUIA.items(), key=lambda x: x[1]):
        if nivel <= perfil_nivel and nivel >= _HIERARQUIA["CONSULTA"]:
            if p in _PERMISSOES_BASE:
                for chave, valor in _PERMISSOES_BASE[p].items():
                    permissoes[chave] = valor

    _CACHE_PERMISSOES[perfil] = permissoes
    return permissoes

def _get_permissoes_usuario() -> dict:
    """Retorna as permissões do usuário logado."""
    return _get_permissoes(_get_perfil())

# ═══════════════════════════════════════════════════════════
# 3. VERIFICAÇÕES DE PERFIL
# ═══════════════════════════════════════════════════════════

def tem_acesso(*perfis_autorizados: str) -> bool:
    """
    Verifica se o usuário atual possui UM dos perfis autorizados.

    Uso:
        tem_acesso("MASTER", "SÓCIO")
        tem_acesso("MASTER")
        tem_acesso("OPERADOR", "GERENTE", "SÓCIO", "MASTER")
    """
    if not st.session_state.get("usuario_logado", False):
        return False
    return _get_perfil() in perfis_autorizados

def tem_acesso_minimo(perfil_minimo: str) -> bool:
    """
    Verifica se o usuário possui nível hierárquico >= ao perfil mínimo.

    Uso:
        tem_acesso_minimo("OPERADOR")  # OPERADOR, GERENTE, SÓCIO, MASTER
        tem_acesso_minimo("GERENTE")   # GERENTE, SÓCIO, MASTER
    """
    if not st.session_state.get("usuario_logado", False):
        return False
    return _get_nivel() >= _HIERARQUIA.get(perfil_minimo, -1)

def eh_master() -> bool:
    return _get_perfil() == "MASTER"

def eh_socio() -> bool:
    return _get_perfil() == "SÓCIO"

def eh_gerente() -> bool:
    return _get_perfil() == "GERENTE"

def eh_operador() -> bool:
    return _get_perfil() == "OPERADOR"

def eh_consulta() -> bool:
    return _get_perfil() == "CONSULTA"

# ═══════════════════════════════════════════════════════════
# 4. PERMISSÕES FUNCIONAIS (baseadas na MATRIZ)
# ═══════════════════════════════════════════════════════════
#
# Cada função consulta a matriz de permissões.
# MASTER herda automaticamente todas as permissões do SÓCIO.

def pode_visualizar() -> bool:
    """Qualquer perfil autenticado pode visualizar."""
    return st.session_state.get("usuario_logado", False)

def pode_editar() -> bool:
    """MASTER, SÓCIO, GERENTE e OPERADOR podem editar. CONSULTA não."""
    permissoes = _get_permissoes_usuario()
    return permissoes.get("editar", False)

def pode_excluir() -> bool:
    """MASTER, SÓCIO e GERENTE podem excluir. OPERADOR e CONSULTA não."""
    permissoes = _get_permissoes_usuario()
    return permissoes.get("excluir", False)

def pode_importar() -> bool:
    """MASTER, SÓCIO e GERENTE podem importar dados."""
    permissoes = _get_permissoes_usuario()
    return permissoes.get("importar", False)

def pode_administrar() -> bool:
    """MASTER e SÓCIO podem administrar o sistema."""
    permissoes = _get_permissoes_usuario()
    return permissoes.get("administrar", False)

def pode_desenvolver() -> bool:
    """Apenas MASTER pode acessar ferramentas de desenvolvimento."""
    permissoes = _get_permissoes_usuario()
    return permissoes.get("desenvolver", False)

def pode_selecionar_unidade() -> bool:
    """
    MASTER, SÓCIO e GERENTE podem selecionar unidade livremente.
    OPERADOR e CONSULTA usam a unidade do usuário.
    """
    permissoes = _get_permissoes_usuario()
    return permissoes.get("selecionar_unidade", False)

# ═══════════════════════════════════════════════════════════
# 5. PERMISSÕES ADMINISTRATIVAS (baseadas na MATRIZ)
# ═══════════════════════════════════════════════════════════

def pode_gerenciar_usuarios() -> bool:
    """MASTER e SÓCIO podem gerenciar usuários (criar, editar, excluir)."""
    permissoes = _get_permissoes_usuario()
    return permissoes.get("gerenciar_usuarios", False)

def pode_gerenciar_usuarios_limitado() -> bool:
    """
    GERENTE pode visualizar usuários, resetar senha e bloquear.
    Não pode criar, excluir ou alterar perfil.
    """
    permissoes = _get_permissoes_usuario()
    return permissoes.get("gerenciar_usuarios_limitado", False)

# ═══════════════════════════════════════════════════════════
# 6. PERMISSÕES POR ABA (ADMINISTRAÇÃO E FUTURAS PÁGINAS)
# ═══════════════════════════════════════════════════════════
#
# Cada aba pode ter sua própria permissão.
# Uso futuro: pode_ver_aba("parametros") em qualquer página.

def _pode_ver_aba(perfil_minimo: str) -> bool:
    """Helper: verifica se o usuário tem nível >= ao perfil mínimo."""
    return _get_nivel() >= _HIERARQUIA.get(perfil_minimo, -1)

def pode_ver_aba_usuarios() -> bool:
    """
    MASTER: completo.
    SÓCIO: completo.
    GERENTE: visualizar, resetar senha, bloquear (limitado).
    """
    return _pode_ver_aba("GERENTE")

def pode_ver_aba_parametros() -> bool:
    """MASTER e SÓCIO. GERENTE não acessa."""
    return _pode_ver_aba("SÓCIO")

def pode_ver_aba_backup() -> bool:
    """MASTER e SÓCIO."""
    return _pode_ver_aba("SÓCIO")

def pode_ver_aba_banco() -> bool:
    """Apenas MASTER."""
    return eh_master()

def pode_ver_aba_dev() -> bool:
    """Apenas MASTER (ferramentas de desenvolvimento, logs, diagnósticos)."""
    return eh_master()

def pode_ver_aba_classificacao() -> bool:
    """MASTER e SÓCIO. GERENTE pode visualizar."""
    return _pode_ver_aba("SÓCIO")

def pode_ver_aba_relacionamento() -> bool:
    """MASTER, SÓCIO e GERENTE."""
    return _pode_ver_aba("GERENTE")

def pode_ver_aba_bi() -> bool:
    """MASTER e SÓCIO."""
    return _pode_ver_aba("SÓCIO")

# ═══════════════════════════════════════════════════════════
# 7. VALIDAÇÕES DE PÁGINA (PROTEÇÃO)
# ═══════════════════════════════════════════════════════════

def verificar_acesso_pagina(*perfis_autorizados: str):
    """
    Proteção para chamar no início de cada página.

    Uso:
        verificar_acesso_pagina()                    # qualquer autenticado
        verificar_acesso_pagina("MASTER", "SÓCIO")   # apenas estes perfis

    Se nenhum perfil for passado, permite qualquer autenticado.
    """
    if not st.session_state.get("usuario_logado", False):
        st.warning("🔒 Você precisa estar logado para acessar esta página.")
        st.switch_page("app.py")
        st.stop()

    if perfis_autorizados and not tem_acesso(*perfis_autorizados):
        st.error(
            f"🚫 Acesso negado. Perfil necessário: {', '.join(perfis_autorizados)}"
        )
        st.stop()

# ═══════════════════════════════════════════════════════════
# 7. MATRIZ DE PERMISSÕES (EXPOSTA PARA CONSULTA)
# ═══════════════════════════════════════════════════════════

MATRIZ_PERMISSOES = {}
for perfil in PERFIS_VALIDOS:
    MATRIZ_PERMISSOES[perfil] = _get_permissoes(perfil)