"""
Módulo Gestão de Terceiros — ULITEC CRM v1.8.0

Responsável pelo controle completo dos serviços enviados para fornecedores externos.

Abas:
  1. Serviços Terceirizados — Cadastro, consulta e filtros
  2. Cadastros Gerais — Fornecedores, Serviços e Marcas (CRUD)
  3. Indicadores — Painel resumo com métricas e gráficos
"""

from datetime import date, datetime, timedelta

import pandas as pd
import plotly.express as px
import sqlite3
import streamlit as st

from auth import verificar_acesso, sidebar_usuario

# ── Proteção ──
verificar_acesso()
sidebar_usuario()

st.set_page_config(page_title="Gestão de Terceiros", layout="wide")

st.title("🔧 Gestão de Terceiros")

# ============================================================
# FUNÇÕES DE BANCO
# ============================================================

def get_conn():
    return sqlite3.connect("crm.db")


# ── Migração automática ──
def migrar_banco():
    conn = get_conn()
    novo = False
    for col, tipo in [("numero_os","TEXT"),("data_orcamento","DATE"),("data_aprovacao","DATE"),("data_recebimento","DATE")]:
        try:
            conn.execute(f"ALTER TABLE terceiros_servicos ADD COLUMN {col} {tipo}")
            conn.commit()
            novo = True
        except Exception:
            pass
    conn.close()
    if novo:
        import streamlit as st
        st.rerun()

migrar_banco()

def migrar_os_antigas():
    conn = get_conn()
    try:
        conn.execute("""
            UPDATE terceiros_servicos
            SET numero_os = os_erp
            WHERE (numero_os IS NULL OR numero_os = '')
              AND (os_erp IS NOT NULL AND os_erp != '')
        """)
        conn.commit()
    except Exception:
        pass
    conn.close()

migrar_os_antigas()


# ── Helpers ──
def carregar_fornecedores_ativos():
    conn = get_conn()
    try:
        df = pd.read_sql("SELECT id, nome FROM terceiros_fornecedores WHERE ativo = 1 ORDER BY nome", conn)
    except Exception:
        df = pd.DataFrame(columns=["id", "nome"])
    conn.close()
    return df

def carregar_marcas_ativas():
    conn = get_conn()
    try:
        df = pd.read_sql("SELECT id, nome FROM terceiros_marcas WHERE ativo = 1 ORDER BY nome", conn)
    except Exception:
        df = pd.DataFrame(columns=["id", "nome"])
    conn.close()
    return df

def carregar_servicos_ativos():
    conn = get_conn()
    try:
        df = pd.read_sql("SELECT id, nome FROM terceiros_servicos_tipos WHERE ativo = 1 ORDER BY nome", conn)
    except Exception:
        df = pd.DataFrame(columns=["id", "nome"])
    conn.close()
    return df

STATUS_OPCOES = ["ENVIADO", "ORÇADO", "APROVADO", "RECEBIDO", "CANCELADO"]


# ── Integração Pipeline ──
def buscar_os_por_termo(termo):
    if not termo or len(termo.strip()) < 1:
        return pd.DataFrame()
    conn = get_conn()
    t = f"%{termo.strip()}%"
    try:
        df = pd.read_sql("""
            SELECT os.id, os.numero_os,
                   COALESCE(c.razao_social, c.nome_fantasia, 'SEM CLIENTE') AS cliente,
                   os.equipamento, os.status, os.valor_proposta
            FROM ordens_servico os
            LEFT JOIN clientes c ON os.cliente_id = c.id
            WHERE os.numero_os LIKE ?
               OR COALESCE(c.razao_social, '') LIKE ?
               OR COALESCE(c.nome_fantasia, '') LIKE ?
            ORDER BY os.numero_os LIMIT 30
        """, conn, params=(t, t, t))
    except Exception:
        df = pd.DataFrame()
    conn.close()
    return df

def formatar_os_display(row):
    c = row.get("cliente", "?")
    e = f" | {row['equipamento']}" if row.get("equipamento") else ""
    return f"OS {row['numero_os']} | {c}{e}"


# ── Preenchimento automático de datas conforme status ──
def auto_preencher_datas():
    status_novo = st.session_state.get("status_serv", "ENVIADO")
    hoje = date.today()
    mapa = {
        "ORÇADO": "data_orcamento",
        "APROVADO": "data_aprovacao",
        "RECEBIDO": "data_recebimento",
    }
    col_data = mapa.get(status_novo)
    if col_data and not st.session_state.get(f"{col_data}_serv"):
        st.session_state[f"{col_data}_serv"] = hoje


# ============================================================
# ABA 1
# ============================================================

def aba_servicos_terceirizados():
    st.markdown("### 📋 Serviços Terceirizados")

    editando = st.session_state.get("edit_servico_id") is not None

    with st.expander(
        f"✏️ Editando Serviço #{st.session_state.edit_servico_id}" if editando else "➕ Novo Serviço",
        expanded=editando,
    ):
        df_forn = carregar_fornecedores_ativos()
        df_marcas = carregar_marcas_ativas()
        df_serv = carregar_servicos_ativos()

        if df_forn.empty:
            st.warning("Cadastre ao menos um fornecedor na aba 'Cadastros Gerais'."); return
        if df_marcas.empty:
            st.warning("Cadastre ao menos uma marca na aba 'Cadastros Gerais'."); return
        if df_serv.empty:
            st.warning("Cadastre ao menos um tipo de serviço na aba 'Cadastros Gerais'."); return

        # ── Carregar dados na edição ──
        if editando and "edit_data_loaded" not in st.session_state:
            conn = get_conn()
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM terceiros_servicos WHERE id = ?", (st.session_state.edit_servico_id,)).fetchone()
            conn.close()
            if row:
                for k in ["fornecedor_id","marca_id","servico_id","modelo","valor","descricao","status","observacoes"]:
                    st.session_state[f"sel_{k}_serv" if k in ["fornecedor_id","marca_id","servico_id"] else f"{k}_serv"] = row[k]
                st.session_state["sel_forn_serv"] = row["fornecedor_id"]
                st.session_state["sel_marca_serv"] = row["marca_id"]
                st.session_state["sel_serv_serv"] = row["servico_id"]
                st.session_state["modelo_serv"] = row["modelo"]
                st.session_state["valor_serv"] = row["valor"]
                try:
                    st.session_state["data_envio_serv"] = datetime.strptime(row["data_envio"], "%Y-%m-%d").date() if row["data_envio"] else date.today()
                except:
                    st.session_state["data_envio_serv"] = date.today()
                try:
                    st.session_state["data_retorno_serv"] = datetime.strptime(row["data_retorno"], "%Y-%m-%d").date() if row["data_retorno"] else None
                except:
                    st.session_state["data_retorno_serv"] = None
                st.session_state["descricao_serv"] = row["descricao"] or ""
                st.session_state["status_serv"] = row["status"]
                st.session_state["observacoes_serv"] = row["observacoes"] or ""
                st.session_state["numero_os_serv"] = row["numero_os"] or ""
                # Novas datas de fluxo
                for col_data in ["data_orcamento","data_aprovacao","data_recebimento"]:
                    try:
                        val = datetime.strptime(row[col_data], "%Y-%m-%d").date() if row[col_data] else None
                    except:
                        val = None
                    st.session_state[f"{col_data}_serv"] = val
                st.session_state["edit_data_loaded"] = True

        # ── OS busca ──
        st.markdown("##### 🔗 Vinculação com Pipeline OS (opcional)")
        termo = st.text_input("🔍 Buscar OS por número ou cliente", placeholder="Digite número da OS ou nome do cliente...", key="busca_os_serv")
        if st.button("🔄 Limpar OS", key="btn_limpar_os"):
            st.session_state["numero_os_serv"] = ""
            st.session_state["os_selecionada_info"] = None

        os_num = st.session_state.get("numero_os_serv", "")
        os_info = st.session_state.get("os_selecionada_info")

        # Carregar info OS na edição
        if editando and os_num and not os_info:
            df_tmp = buscar_os_por_termo(os_num)
            if not df_tmp.empty:
                r = df_tmp.iloc[0]
                st.session_state["os_selecionada_info"] = {"numero_os":r["numero_os"],"cliente":r["cliente"],"equipamento":r.get("equipamento",""),"status":r.get("status","")}
                os_info = st.session_state["os_selecionada_info"]

        # Mostrar resultados da busca
        if termo and len(termo) >= 2 and not os_num:
            df_os = buscar_os_por_termo(termo)
            if not df_os.empty:
                displays = [formatar_os_display(r) for _, r in df_os.iterrows()]
                nums = df_os["numero_os"].tolist()
                mapa = dict(zip(displays, nums))
                esc = st.selectbox("Resultados — selecione uma OS", options=[""] + displays, format_func=lambda x: x if x else "Selecione...", key="sel_os_result")
                if esc:
                    n = mapa.get(esc, esc)
                    st.session_state["numero_os_serv"] = n
                    rs = df_os[df_os["numero_os"] == n].iloc[0]
                    st.session_state["os_selecionada_info"] = {"numero_os":rs["numero_os"],"cliente":rs["cliente"],"equipamento":rs.get("equipamento",""),"status":rs.get("status","")}
            else:
                st.caption("Nenhuma OS encontrada.")
        elif not termo and not os_num:
            st.caption("Digite ao menos 2 caracteres para buscar uma OS.")

        if os_info:
            st.info(f"**OS {os_info['numero_os']}** — Cliente: {os_info['cliente']}  {' | Equipamento: '+os_info['equipamento'] if os_info.get('equipamento') else ''} | Status: {os_info.get('status','N/D')}")

        st.markdown("---")

        status = st.selectbox(
            "Status interno", options=STATUS_OPCOES, key="status_serv",
            on_change=auto_preencher_datas
        )

        # ── Campos principais ──
        col1, col2 = st.columns(2)
        with col1:
            fornecedor_id = st.selectbox("Fornecedor", options=df_forn["id"].tolist(), format_func=lambda x: df_forn.loc[df_forn["id"]==x,"nome"].values[0], key="sel_forn_serv")
            marca_id = st.selectbox("Marca", options=df_marcas["id"].tolist(), format_func=lambda x: df_marcas.loc[df_marcas["id"]==x,"nome"].values[0], key="sel_marca_serv")
            modelo = st.text_input("Modelo", placeholder="Ex: A06B-6096-H102", key="modelo_serv")
        with col2:
            servico_id = st.selectbox("Tipo de Serviço", options=df_serv["id"].tolist(), format_func=lambda x: df_serv.loc[df_serv["id"]==x,"nome"].values[0], key="sel_serv_serv")
            valor = st.number_input("Valor cobrado (R$)", min_value=0.0, step=10.0, format="%.2f", key="valor_serv")
            data_envio = st.date_input("Data envio", value=date.today(), key="data_envio_serv")
            data_retorno = st.date_input("Data retorno", value=None, key="data_retorno_serv")

        st.markdown("##### 📅 Datas do Fluxo")
        c1, c2, c3 = st.columns(3)
        with c1:
            data_orcamento = st.date_input("Data orçamento", value=st.session_state.get("data_orcamento_serv"), key="data_orcamento_serv")
        with c2:
            data_aprovacao = st.date_input("Data aprovação", value=st.session_state.get("data_aprovacao_serv"), key="data_aprovacao_serv")
        with c3:
            data_recebimento = st.date_input("Data recebimento", value=st.session_state.get("data_recebimento_serv"), key="data_recebimento_serv")

        descricao = st.text_area("Descrição complementar", placeholder="Descrição opcional do serviço", key="descricao_serv")
        observacoes = st.text_area("Observações", key="observacoes_serv")

        # ── Botões ──
        if editando:
            ca, cb = st.columns([2, 1])
            with ca:
                if st.button("💾 Salvar Alterações", type="primary", width="stretch", key="btn_salvar"):
                    _executar_salvar_servico(fornecedor_id, marca_id, servico_id, modelo, descricao, valor, status, data_envio, data_retorno, observacoes, editando, data_orcamento, data_aprovacao, data_recebimento)
            with cb:
                if st.button("❌ Cancelar Edição", width="stretch", key="btn_cancelar"):
                    for chave in ["edit_servico_id", "edit_data_loaded", "numero_os_serv", "os_selecionada_info"]:
                        st.session_state.pop(chave, None)
        else:
            if st.button("💾 Salvar", type="primary", width="stretch", key="btn_salvar"):
                _executar_salvar_servico(fornecedor_id, marca_id, servico_id, modelo, descricao, valor, status, data_envio, data_retorno, observacoes, editando, data_orcamento, data_aprovacao, data_recebimento)

    # ── Tabela ──
    _exibir_tabela_servicos()


def _executar_salvar_servico(fornecedor_id, marca_id, servico_id, modelo, descricao, valor, status, data_envio, data_retorno, observacoes, editando, data_orcamento=None, data_aprovacao=None, data_recebimento=None):
    if not modelo.strip():
        st.error("O campo Modelo é obrigatório.")
        return
    conn = get_conn()
    try:
        os_num = st.session_state.get("numero_os_serv", "") or None
        if editando:
            conn.execute("""
                UPDATE terceiros_servicos SET fornecedor_id=?, marca_id=?, servico_id=?, modelo=?,
                    descricao=?, valor=?, status=?, data_envio=?, data_retorno=?, observacoes=?, numero_os=?,
                    data_orcamento=?, data_aprovacao=?, data_recebimento=?
                WHERE id=?
            """, (fornecedor_id, marca_id, servico_id, modelo.strip(), descricao.strip(), valor,
                  status, data_envio, data_retorno, observacoes.strip(), os_num,
                  data_orcamento, data_aprovacao, data_recebimento,
                  st.session_state.edit_servico_id))
            msg = "Serviço atualizado com sucesso!"
        else:
            conn.execute("""
                INSERT INTO terceiros_servicos (fornecedor_id, marca_id, servico_id, modelo, descricao,
                    valor, status, data_envio, data_retorno, observacoes, usuario, numero_os,
                    data_orcamento, data_aprovacao, data_recebimento)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (fornecedor_id, marca_id, servico_id, modelo.strip(), descricao.strip(), valor,
                  status, data_envio, data_retorno, observacoes.strip(),
                  st.session_state.get("usuario_nome", ""), os_num,
                  data_orcamento, data_aprovacao, data_recebimento))
            msg = "Serviço registrado com sucesso!"
        conn.commit()
        st.success(msg)
        for chave in ["edit_servico_id", "edit_data_loaded", "numero_os_serv", "os_selecionada_info"]:
            st.session_state.pop(chave, None)
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")
    finally:
        conn.close()


def _exibir_tabela_servicos():
    st.markdown("### 📄 Serviços Cadastrados")
    conn = get_conn()
    try:
        df = pd.read_sql("""
            SELECT ts.id, tf.nome AS fornecedor, tm.nome AS marca, tst.nome AS servico,
                   ts.modelo, ts.valor, ts.status, ts.data_envio, ts.data_retorno,
                   ts.descricao, ts.observacoes, ts.fornecedor_id, ts.marca_id,
                   ts.servico_id, ts.numero_os,
                   COALESCE(c.razao_social, c.nome_fantasia, '') AS os_cliente
            FROM terceiros_servicos ts
            LEFT JOIN terceiros_fornecedores tf ON ts.fornecedor_id = tf.id
            LEFT JOIN terceiros_marcas tm ON ts.marca_id = tm.id
            LEFT JOIN terceiros_servicos_tipos tst ON ts.servico_id = tst.id
            LEFT JOIN ordens_servico os ON ts.numero_os = os.numero_os
            LEFT JOIN clientes c ON os.cliente_id = c.id
            ORDER BY ts.data_cadastro DESC
        """, conn)
    except Exception:
        df = pd.DataFrame()
    conn.close()

    if df.empty:
        st.info("Nenhum serviço registrado ainda.")
        return

    # Filtros com keys únicas
    st.markdown("#### 🔍 Filtros")
    with st.container():
        ca, cb, cc, cd, ce = st.columns(5)
        with ca: f1 = st.selectbox("Fornecedor", ["Todos"] + sorted(df["fornecedor"].dropna().unique()), key="filtro_forn")
        with cb: f2 = st.selectbox("Marca", ["Todos"] + sorted(df["marca"].dropna().unique()), key="filtro_marca")
        with cc: f3 = st.selectbox("Serviço", ["Todos"] + sorted(df["servico"].dropna().unique()), key="filtro_serv")
        with cd: f4 = st.selectbox("Status", ["Todos"] + sorted(df["status"].dropna().unique()), key="filtro_status")
        with ce:
            di = st.date_input("Data início", value=None, key="filtro_dt_ini")
            df2 = st.date_input("Data fim", value=None, key="filtro_dt_fim")

    dff = df.copy()
    if f1 != "Todos": dff = dff[dff["fornecedor"] == f1]
    if f2 != "Todos": dff = dff[dff["marca"] == f2]
    if f3 != "Todos": dff = dff[dff["servico"] == f3]
    if f4 != "Todos": dff = dff[dff["status"] == f4]
    if di: dff = dff[pd.to_datetime(dff["data_envio"], errors="coerce") >= pd.Timestamp(di)]
    if df2: dff = dff[pd.to_datetime(dff["data_envio"], errors="coerce") <= pd.Timestamp(df2)]

    if dff.empty:
        st.info("Nenhum serviço com os filtros.")
        return

    st.markdown("#### 📝 Resultados")
    for _, r in dff.iterrows():
        with st.container(border=True):
            cols = st.columns([2, 2, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1])
            with cols[0]:
                os_num = r.get("numero_os", "")
                os_cliente = r.get("os_cliente", "")
                if os_num:
                    os_txt = f"<small><a href='#' onclick='return false;' title='Abrir OS {os_num} no Pipeline'>OS {os_num}</a></small>"
                    if os_cliente:
                        os_txt += f"<br/><small style='font-size:0.8em;color:#888;'>{os_cliente}</small>"
                    os_txt += "<br/>"
                else:
                    os_txt = ""
                st.markdown(f"{os_txt}**{r['fornecedor']}**", unsafe_allow_html=True)
            with cols[1]: st.markdown(f"{r['marca']}<br/><small>{r['modelo']}</small>", unsafe_allow_html=True)
            with cols[2]: st.markdown(f"**Serviço**<br/>{r['servico']}", unsafe_allow_html=True)
            with cols[3]:
                v = f"R$ {r['valor']:,.2f}" if pd.notna(r['valor']) else "-"
                st.markdown(f"**Valor**<br/>{v}", unsafe_allow_html=True)
            with cols[4]: st.markdown(f"**Status**<br/>{r['status']}", unsafe_allow_html=True)
            with cols[5]: st.markdown(f"**Envio**<br/>{r['data_envio']}", unsafe_allow_html=True)
            with cols[6]: st.markdown(f"**Retorno**<br/>{r.get('data_retorno','-') or '-'}", unsafe_allow_html=True)
            with cols[7]: st.markdown("**Ações**")
            with cols[8]:
                if st.button("✏️", key=f"ed_{r['id']}", help="Editar"):
                    st.session_state.edit_servico_id = int(r["id"])
                    st.session_state.pop("edit_data_loaded", None)

        with st.popover("🗑️", help="Excluir"):
            st.warning(f"Excluir **{r['modelo']}** — {r['fornecedor']}?")
            if st.button("✅ Sim, excluir", key=f"del_{r['id']}", type="primary"):
                cx = get_conn()
                try:
                    cx.execute("DELETE FROM terceiros_servicos WHERE id = ?", (int(r["id"]),))
                    cx.commit()
                    st.success("Excluído!")
                except Exception as e:
                    st.error(f"Erro: {e}")
                finally:
                    cx.close()

    st.caption(f"Total: {len(dff)}")


# ============================================================
# ABA 2 — CADASTROS GERAIS
# ============================================================

def cadastro_fornecedores():
    st.markdown("#### 🏢 Fornecedores")
    conn = get_conn()
    with st.form("form_forn", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1: nome = st.text_input("Nome *"); cidade = st.text_input("Cidade")
        with c2: estado = st.text_input("Estado"); contato = st.text_input("Contato")
        with c3: tel = st.text_input("Telefone"); ativo = st.checkbox("Ativo", value=True)
        obs = st.text_area("Observações")
        if st.form_submit_button("💾 Salvar Fornecedor", type="primary", width="stretch"):
            if nome.strip():
                try:
                    conn.execute("INSERT INTO terceiros_fornecedores (nome,cidade,estado,contato,telefone,observacoes,ativo) VALUES (?,?,?,?,?,?,?)",
                                 (nome.strip(),cidade.strip(),estado.strip(),contato.strip(),tel.strip(),obs.strip(),1 if ativo else 0))
                    conn.commit()
                    st.success("Fornecedor cadastrado!")
                except sqlite3.IntegrityError: st.warning("Já existe.")
                except Exception as e: st.error(f"Erro: {e}")
            else: st.error("Nome obrigatório.")
    df = pd.read_sql("SELECT * FROM terceiros_fornecedores ORDER BY nome", conn)
    conn.close()
    if not df.empty:
        for _, r in df.iterrows():
            a,b,c = st.columns([4,1,1])
            with a: st.markdown(f"**{r['nome']}** — {r['cidade']}/{r['estado']}")
            with b: st.markdown(f"{'✅ Ativo' if r['ativo'] else '❌ Inativo'}")
            with c:
                if st.button("🗑️", key=f"df_{r['id']}"):
                    cx = get_conn()
                    cx.execute("DELETE FROM terceiros_fornecedores WHERE id = ?", (r["id"],))
                    cx.commit(); cx.close()
    else: st.info("Nenhum fornecedor.")


def cadastro_servicos():
    st.markdown("#### 🔧 Tipos de Serviço")
    conn = get_conn()
    with st.form("form_serv_tipo", clear_on_submit=True):
        nome = st.text_input("Nome *")
        cat = st.text_input("Categoria")
        ativo = st.checkbox("Ativo", value=True)
        if st.form_submit_button("💾 Salvar Serviço", type="primary", width="stretch"):
            if nome.strip():
                try:
                    conn.execute("INSERT INTO terceiros_servicos_tipos (nome,categoria,ativo) VALUES (?,?,?)",
                                 (nome.strip(),cat.strip(),1 if ativo else 0))
                    conn.commit()
                    st.success("Serviço cadastrado!")
                except sqlite3.IntegrityError: st.warning("Já existe.")
                except Exception as e: st.error(f"Erro: {e}")
            else: st.error("Nome obrigatório.")
    df = pd.read_sql("SELECT * FROM terceiros_servicos_tipos ORDER BY nome", conn)
    conn.close()
    if not df.empty:
        for _, r in df.iterrows():
            a,b,c = st.columns([4,1,1])
            with a: st.markdown(f"**{r['nome']}** — {r['categoria']}")
            with b: st.markdown(f"{'✅ Ativo' if r['ativo'] else '❌ Inativo'}")
            with c:
                if st.button("🗑️", key=f"dst_{r['id']}"):
                    cx = get_conn()
                    cx.execute("DELETE FROM terceiros_servicos_tipos WHERE id = ?", (r["id"],))
                    cx.commit(); cx.close()
    else: st.info("Nenhum tipo de serviço.")


def cadastro_marcas():
    st.markdown("#### 🏷️ Marcas")
    conn = get_conn()
    with st.form("form_marca_cad", clear_on_submit=True):
        nome = st.text_input("Nome *")
        ativo = st.checkbox("Ativo", value=True)
        if st.form_submit_button("💾 Salvar Marca", type="primary", width="stretch"):
            if nome.strip():
                try:
                    conn.execute("INSERT INTO terceiros_marcas (nome,ativo) VALUES (?,?)",
                                 (nome.strip(),1 if ativo else 0))
                    conn.commit()
                    st.success("Marca cadastrada!")
                except sqlite3.IntegrityError: st.warning("Já existe.")
                except Exception as e: st.error(f"Erro: {e}")
            else: st.error("Nome obrigatório.")
    df = pd.read_sql("SELECT * FROM terceiros_marcas ORDER BY nome", conn)
    conn.close()
    if not df.empty:
        for _, r in df.iterrows():
            a,b,c = st.columns([4,1,1])
            with a: st.markdown(f"**{r['nome']}**")
            with b: st.markdown(f"{'✅ Ativo' if r['ativo'] else '❌ Inativo'}")
            with c:
                if st.button("🗑️", key=f"dm_{r['id']}"):
                    cx = get_conn()
                    cx.execute("DELETE FROM terceiros_marcas WHERE id = ?", (r["id"],))
                    cx.commit(); cx.close()
    else: st.info("Nenhuma marca.")


def aba_cadastros_gerais():
    st.markdown("### ⚙️ Cadastros Gerais")
    t1, t2, t3 = st.tabs(["Fornecedores", "Serviços", "Marcas"])
    with t1: cadastro_fornecedores()
    with t2: cadastro_servicos()
    with t3: cadastro_marcas()


# ============================================================
# ABA 3 — INDICADORES
# ============================================================

def aba_indicadores():
    st.markdown("### 📊 Indicadores")
    conn = get_conn()
    try:
        df = pd.read_sql("""
            SELECT ts.id, tf.nome AS fornecedor, tm.nome AS marca, tst.nome AS servico,
                   ts.modelo, ts.valor, ts.status, ts.data_envio, ts.data_retorno
            FROM terceiros_servicos ts
            LEFT JOIN terceiros_fornecedores tf ON ts.fornecedor_id = tf.id
            LEFT JOIN terceiros_marcas tm ON ts.marca_id = tm.id
            LEFT JOIN terceiros_servicos_tipos tst ON ts.servico_id = tst.id
        """, conn)
    except Exception:
        df = pd.DataFrame()
    conn.close()
    if df.empty:
        st.info("Nenhum dado disponível.")
        return

    df["valor"] = pd.to_numeric(df["valor"], errors="coerce").fillna(0)

    # Segmentação por status
    df_recebido = df[df["status"] == "RECEBIDO"].copy()
    df_aprovado = df[df["status"] == "APROVADO"].copy()
    df_orcado = df[df["status"] == "ORÇADO"].copy()

    # Métricas principais
    total_gasto = df_recebido["valor"].sum()
    qtd_recebido = len(df_recebido)
    qtd_aprovado = len(df_aprovado)
    qtd_orcado = len(df_orcado)

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: st.metric("Total Gasto (RECEBIDO)", f"R$ {total_gasto:,.2f}")
    with c2: st.metric("Compromissos (APROVADO)", qtd_aprovado)
    with c3: st.metric("Orçamentos Pendentes (ORÇADO)", qtd_orcado)
    with c4: st.metric("Qtd Recebidos", qtd_recebido)
    with c5:
        md = df_recebido["valor"].mean() if qtd_recebido > 0 else 0
        st.metric("Médio Recebido", f"R$ {md:,.2f}")

    # Gastos por fornecedor (apenas RECEBIDO)
    if qtd_recebido > 0:
        st.markdown("#### 🏆 Total Gasto por Fornecedor (RECEBIDO)")
        rk = df_recebido.groupby("fornecedor")["valor"].agg(["sum","count","mean"]).reset_index().rename(columns={"sum":"total","count":"qtd","mean":"media"}).sort_values("total",ascending=False)
        rk["tf"] = rk["total"].apply(lambda x: f"R$ {x:,.2f}")
        rk["mf"] = rk["media"].apply(lambda x: f"R$ {x:,.2f}")
        st.dataframe(rk[["fornecedor","tf","qtd","mf"]], column_config={"fornecedor":"Fornecedor","tf":"Total","qtd":"Qtd","mf":"Médio"}, hide_index=True, width="stretch")
        if not df_recebido.empty: st.metric("Fornecedor + usado (RECEBIDO)", df_recebido.groupby("fornecedor").size().idxmax())
        st.markdown("#### 📈 Gastos (RECEBIDO)")
        st.plotly_chart(px.bar(rk.head(10), x="fornecedor", y="total", title="Top 10 Fornecedores (RECEBIDO)", text_auto=".2s"), width="stretch")

    # Quantidade por fornecedor (total geral)
    if not df.empty:
        st.markdown("#### 📊 Qtd por Fornecedor")
        qtd_df = df.groupby("fornecedor").size().reset_index(name="q").sort_values("q",ascending=False)
        st.plotly_chart(px.bar(qtd_df.head(10), x="fornecedor", y="q", title="Top 10 (Geral)", text_auto=True), width="stretch")

    # Médio por serviço (apenas recebidos)
    if qtd_recebido > 0:
        st.markdown("#### 💰 Médio por Serviço (RECEBIDO)")
        vm = df_recebido.groupby("servico")["valor"].agg(["mean","count"]).reset_index().rename(columns={"mean":"vm","count":"qtd"}).sort_values("vm",ascending=False)
        vm["vmf"] = vm["vm"].apply(lambda x: f"R$ {x:,.2f}")
        st.dataframe(vm[["servico","vmf","qtd"]], column_config={"servico":"Serviço","vmf":"Médio","qtd":"Qtd"}, hide_index=True, width="stretch")

    # Orçamentos pendentes por fornecedor
    if qtd_orcado > 0:
        st.markdown("#### 📋 Orçamentos Pendentes por Fornecedor (ORÇADO)")
        orc = df_orcado.groupby("fornecedor").size().reset_index(name="qtd_orcado").sort_values("qtd_orcado",ascending=False)
        st.dataframe(orc, column_config={"fornecedor":"Fornecedor","qtd_orcado":"Qtd Orçamentos"}, hide_index=True, width="stretch")
        if not df_orcado.empty:
            st.plotly_chart(px.bar(orc.head(10), x="fornecedor", y="qtd_orcado", title="Orçamentos Pendentes por Fornecedor", text_auto=True), width="stretch")

    # Tabela dinâmica (apenas recebidos)
    with st.expander("📋 Tabela Dinâmica (RECEBIDO)"):
        if qtd_recebido > 0:
            ag = st.selectbox("Agregação", ["sum","mean","count","max","min"])
            if ag == "count":
                st.dataframe(df_recebido.pivot_table(index="fornecedor", columns=["servico"], values="id", aggfunc="count", fill_value=0))
            else:
                st.dataframe(df_recebido.pivot_table(index="fornecedor", columns=["servico"], values="valor", aggfunc=ag, fill_value=0))
        else:
            st.info("Nenhum recebido para exibir.")


# ============================================================
# RENDERIZAÇÃO
# ============================================================

t1, t2, t3 = st.tabs(["📋 Serviços Terceirizados", "⚙️ Cadastros Gerais", "📊 Indicadores"])
with t1: aba_servicos_terceirizados()
with t2: aba_cadastros_gerais()
with t3: aba_indicadores()