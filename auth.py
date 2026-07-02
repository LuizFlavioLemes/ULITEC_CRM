import sqlite3
from datetime import datetime
from functools import wraps

import bcrypt
import streamlit as st

from config import DB_PATH, MASTER_PASSWORD


def get_conn():
    return sqlite3.connect(str(DB_PATH))


def init_auth():
    """Inicializa o sistema de autenticação: adiciona colunas necessárias e cria usuário MASTER."""
    conn = get_conn()
    cursor = conn.cursor()

    # ── Flag para evitar migração repetida ──
    migracao_feita = cursor.execute(
        "SELECT 1 FROM pragma_table_info('usuarios') WHERE name='perfil_migrado_v2'"
    ).fetchone()
    if not migracao_feita:
        try:
            cursor.execute("ALTER TABLE usuarios ADD COLUMN perfil_migrado_v2 INTEGER DEFAULT 0")
            conn.commit()
        except Exception:
            pass

    # ── Adicionar colunas que podem estar faltando na tabela usuarios ──
    colunas_necessarias = {
        "senha_hash": "TEXT",
        "ultimo_login": "TEXT",
        "login": "TEXT",
        "perfil": "TEXT DEFAULT 'OPERADOR'",
        "unidade_id": "INTEGER",
        "ativo": "INTEGER DEFAULT 1",
    }
    for col, tipo in colunas_necessarias.items():
        try:
            cursor.execute(f"ALTER TABLE usuarios ADD COLUMN {col} {tipo}")
            conn.commit()
        except Exception:
            pass

    # ── Migrar nivel_acesso → perfil (VERSÃO CORRIGIDA V2.0) ──
    # Mapeia nivel_acesso legado para os novos perfis padronizados
    cursor.execute(
        """
        UPDATE usuarios
        SET perfil = CASE nivel_acesso
            WHEN 'SÓCIO' THEN 'SÓCIO'
            WHEN 'GERENTE' THEN 'GERENTE'
            WHEN 'GESTOR' THEN 'GERENTE'
            WHEN 'OPERADOR SP' THEN 'OPERADOR'
            WHEN 'OPERADOR RS' THEN 'OPERADOR'
            WHEN 'SOCIO' THEN 'SÓCIO'
            ELSE perfil
        END,
        perfil_migrado_v2 = 1
        WHERE (perfil_migrado_v2 IS NULL OR perfil_migrado_v2 = 0)
          AND nivel_acesso IS NOT NULL
          AND nivel_acesso != ''
        """
    )
    conn.commit()

    # ── Migrar perfis que estão com valor SOCIO (sem acento) para SÓCIO ──
    cursor.execute(
        "UPDATE usuarios SET perfil = 'SÓCIO' WHERE perfil = 'SOCIO' AND perfil_migrado_v2 = 0"
    )
    conn.commit()

    # ── Migrar perfis GESTOR para GERENTE ──
    cursor.execute(
        "UPDATE usuarios SET perfil = 'GERENTE' WHERE perfil = 'GESTOR' AND perfil_migrado_v2 = 0"
    )
    conn.commit()

    # ── Marcar todos os já migrados na flag ──
    cursor.execute(
        "UPDATE usuarios SET perfil_migrado_v2 = 1 WHERE perfil IS NOT NULL AND perfil != '' AND (perfil_migrado_v2 IS NULL OR perfil_migrado_v2 = 0)"
    )
    conn.commit()

    # ── Migrar senhas em texto puro para bcrypt ──
    usuarios_com_senha_plana = cursor.execute(
        """
        SELECT id, senha FROM usuarios
        WHERE senha IS NOT NULL AND senha != ''
          AND (senha_hash IS NULL OR senha_hash = '')
        """
    ).fetchall()

    for uid, senha in usuarios_com_senha_plana:
        if senha and not senha.startswith("$2b$"):
            hash_senha = bcrypt.hashpw(
                senha.encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")
            cursor.execute(
                "UPDATE usuarios SET senha_hash = ? WHERE id = ?",
                (hash_senha, uid),
            )
    conn.commit()

    # ── Garantir que o campo login tenha valor (usa nome como fallback) ──
    cursor.execute(
        """
        UPDATE usuarios
        SET login = nome
        WHERE login IS NULL OR login = ''
        """
    )
    conn.commit()

    # ── Garantir que usuários existentes tenham ativo = 1 ──
    cursor.execute(
        """
        UPDATE usuarios
        SET ativo = 1
        WHERE ativo IS NULL
        """
    )
    conn.commit()

    # ── Criar usuário MASTER automaticamente se não existir ──
    master = cursor.execute(
        "SELECT id FROM usuarios WHERE login = 'admin'"
    ).fetchone()

    if not master:
        senha_master = MASTER_PASSWORD or "Ulitec2026@"
        hash_admin = bcrypt.hashpw(
            senha_master.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")
        cursor.execute(
            """
            INSERT INTO usuarios (login, nome, senha_hash, perfil, ativo)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("admin", "admin", hash_admin, "MASTER", 1),
        )
        conn.commit()

    conn.close()


def verificar_login(login: str, senha: str) -> dict | None:
    """
    Verifica credenciais usando bcrypt.
    Retorna dicionário com dados do usuário ou None se inválido.
    """
    conn = get_conn()
    user = conn.execute(
        """
        SELECT id, nome, login, senha_hash, perfil, unidade_id, ativo
        FROM usuarios
        WHERE login = ?
        """,
        (login,),
    ).fetchone()
    conn.close()

    if not user:
        return None

    user_id, nome, user_login, senha_hash, perfil, unidade_id, ativo = user

    if not ativo:
        return None

    if not senha_hash:
        return None

    try:
        if not bcrypt.checkpw(
            senha.encode("utf-8"), senha_hash.encode("utf-8")
        ):
            return None
    except Exception:
        return None

    # ── Atualizar ultimo_login ──
    conn = get_conn()
    conn.execute(
        "UPDATE usuarios SET ultimo_login = ? WHERE id = ?",
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_id),
    )
    conn.commit()

    # ── Buscar nome da unidade ──
    unidade_nome = None
    if unidade_id:
        result = conn.execute(
            "SELECT nome FROM unidades WHERE id = ?", (unidade_id,)
        ).fetchone()
        if result:
            unidade_nome = result[0]
    conn.close()

    return {
        "id": user_id,
        "nome": nome,
        "login": user_login,
        "perfil": perfil,
        "unidade_id": unidade_id,
        "unidade_nome": unidade_nome,
    }


def fazer_login(user: dict):
    """Armazena dados do usuário na session_state."""
    st.session_state["usuario_logado"] = True
    st.session_state["usuario_id"] = user["id"]
    st.session_state["usuario_nome"] = user["nome"]
    st.session_state["perfil"] = user["perfil"]
    st.session_state["unidade_usuario"] = user["unidade_nome"] or "ULITEC SP"
    if user["unidade_nome"]:
        st.session_state["unidade_ativa"] = user["unidade_nome"]


def logout():
    """Limpa a sessão e retorna ao login."""
    st.session_state["usuario_logado"] = False
    for key in [
        "usuario_id",
        "usuario_nome",
        "perfil",
        "unidade_usuario",
        "unidade_ativa",
    ]:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()


def verificar_acesso(
    requer_login: bool = True, perfis: list[str] | None = None
):
    """
    Verifica autenticação e perfil no início de uma página.
    - requer_login: Se True, redireciona para login se não autenticado.
    - perfis: Lista de perfis permitidos. None = qualquer perfil autenticado.
    """
    if requer_login and not st.session_state.get("usuario_logado", False):
        st.warning("🔒 Você precisa estar logado para acessar esta página.")
        st.switch_page("app.py")
        st.stop()

    if perfis is not None:
        perfil_atual = st.session_state.get("perfil", "")
        if perfil_atual not in perfis:
            st.error(
                f"🚫 Acesso negado. Perfil necessário: {', '.join(perfis)}"
            )
            st.stop()


def requer_login(funcao):
    """Decorator: exige autenticação."""

    @wraps(funcao)
    def wrapper(*args, **kwargs):
        if not st.session_state.get("usuario_logado", False):
            st.warning("🔒 Você precisa estar logado para acessar esta página.")
            st.switch_page("app.py")
            st.stop()
            return
        return funcao(*args, **kwargs)

    return wrapper


def requer_perfil(*perfis_autorizados):
    """
    Decorator: exige autenticação E perfil específico.
    Uso: @requer_perfil("MASTER") ou @requer_perfil("MASTER", "GESTOR")
    """

    def decorator(funcao):
        @wraps(funcao)
        @requer_login
        def wrapper(*args, **kwargs):
            perfil_atual = st.session_state.get("perfil", "")
            if perfil_atual not in perfis_autorizados:
                st.error(
                    f"🚫 Acesso negado. Perfil necessário: {', '.join(perfis_autorizados)}"
                )
                st.stop()
                return
            return funcao(*args, **kwargs)

        return wrapper

    return decorator


def mostrar_login():
    """Renderiza o formulário de login."""
    st.markdown(
        """
        <div style="text-align: center; padding: 2rem 0;">
            <h1 style="font-size: 2.5rem;">🏭 CRM Industrial ULITEC</h1>
            <p style="font-size: 1.1rem; color: #666;">Faça login para continuar</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("login_form"):
        login_input = st.text_input("Usuário", placeholder="Digite seu login")
        senha_input = st.text_input(
            "Senha", type="password", placeholder="Digite sua senha"
        )

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submitted = st.form_submit_button(
                "🔑 Entrar", type="primary", width="stretch"
            )

    if submitted:
        if not login_input or not senha_input:
            st.error("Preencha usuário e senha.")
            return

        user = verificar_login(login_input, senha_input)
        if user:
            fazer_login(user)
            st.success(f"Bem-vindo(a), {user['nome']}!")
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos.")


def sidebar_usuario():
    """Exibe informações do usuário logado e botão de logout na sidebar."""
    if st.session_state.get("usuario_logado", False):
        st.sidebar.markdown("---")
        st.sidebar.markdown(
            f"""
            <div style="padding: 0.5rem; background: #f0f2f6; border-radius: 0.5rem;">
                <p style="margin:0; font-size:0.85rem; color:#555;">👤 <strong>{st.session_state.get('usuario_nome', '')}</strong></p>
                <p style="margin:0; font-size:0.75rem; color:#888;">Perfil: {st.session_state.get('perfil', '')}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.sidebar.button("🚪 Sair", width="stretch"):
            logout()