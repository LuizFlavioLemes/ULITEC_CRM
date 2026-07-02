from pathlib import Path
import sqlite3

import streamlit as st

from auth import sidebar_usuario
from permissions import (
    verificar_acesso_pagina,
)
from services.relacionamento import (
    salvar_configs_relacionamento,
    carregar_configs_relacionamento,
    get_config,
    set_config,
)

# ── Proteção: apenas quem pode ver ao menos uma aba da administração ──
# MASTER, SÓCIO e GERENTE (limitado) podem acessar
verificar_acesso_pagina("MASTER", "SÓCIO", "GERENTE")
sidebar_usuario()


DB_PATH = Path("crm.db")
BACKUP_DIR = Path("backups")


st.title("⚙️ Administração")

st.info(
    """
    Centro de administração do CRM ULITEC.

    Todas as regras operacionais, comerciais e indicadores do BI serão definidos aqui.
    """
)

# =====================================================
# ABAS
# =====================================================

aba1, aba2, aba3, aba4, aba5, aba6, aba7, aba8 = st.tabs(
    [
        "Classificação",
        "Relacionamento",
        "Operação",
        "BI",
        "Sistema",
        "Banco",
        "👥 Gestão de Usuários",
        "ℹ️ Info. Instalação",
    ]
)

# =====================================================
# CLASSIFICAÇÃO
# =====================================================

with aba1:

    st.subheader("📊 Classificação Automática de Clientes")

    configs = carregar_configs_relacionamento()

    col1, col2 = st.columns(2)

    with col1:

        st.markdown("### Classe A")

        st.number_input(
            "Faturamento anual mínimo Classe A (R$)",
            value=int(configs.get("fat_A", "100000")),
            key="fat_a"
        )

        st.number_input(
            "Quantidade mínima de OS Classe A",
            value=int(configs.get("os_A", "12")),
            key="os_a"
        )

        st.number_input(
            "Quantidade mínima de faturamentos Classe A",
            value=int(configs.get("fat_qtd_A", "12")),
            key="fat_qtd_a"
        )

    with col2:

        st.markdown("### Classe B")

        st.number_input(
            "Faturamento anual mínimo Classe B (R$)",
            value=int(configs.get("fat_B", "50000")),
            key="fat_b"
        )

        st.number_input(
            "Quantidade mínima de OS Classe B",
            value=int(configs.get("os_B", "6")),
            key="os_b"
        )

        st.number_input(
            "Quantidade mínima de faturamentos Classe B",
            value=int(configs.get("fat_qtd_B", "6")),
            key="fat_qtd_b"
        )

    col3, col4 = st.columns(2)

    with col3:

        st.markdown("### Classe C")

        st.number_input(
            "Faturamento anual mínimo Classe C (R$)",
            value=int(configs.get("fat_C", "10000")),
            key="fat_c"
        )

        st.number_input(
            "Quantidade mínima de OS Classe C",
            value=int(configs.get("os_C", "2")),
            key="os_c"
        )

        st.number_input(
            "Quantidade mínima de faturamentos Classe C",
            value=int(configs.get("fat_qtd_C", "2")),
            key="fat_qtd_c"
        )

    with col4:

        st.markdown("### Classe D")

        st.info(
            "Clientes abaixo dos critérios da Classe C."
        )

# =====================================================
# RELACIONAMENTO
# =====================================================

with aba2:

    st.subheader("🤝 Relacionamento Comercial")

    # Carregar configurações salvas
    configs = carregar_configs_relacionamento()

    for classe in ["A", "B", "C", "D"]:

        st.markdown(f"### Classe {classe}")

        col1, col2 = st.columns(2)

        with col1:

            st.number_input(
                f"WhatsApp (dias) - Classe {classe}",
                value=int(configs.get(f"whats_{classe}", "30")),
                key=f"whats_{classe}"
            )

            st.number_input(
                f"E-mail (dias) - Classe {classe}",
                value=int(configs.get(f"email_{classe}", "45")),
                key=f"email_{classe}"
            )

        with col2:

            st.number_input(
                f"Ligação (dias) - Classe {classe}",
                value=int(configs.get(f"ligacao_{classe}", "60")),
                key=f"ligacao_{classe}"
            )

            st.number_input(
                f"Visita presencial (dias) - Classe {classe}",
                value=int(configs.get(f"visita_{classe}", "90")),
                key=f"visita_{classe}"
            )

        st.divider()

    st.number_input(
        "Avisar quantos dias antes do vencimento da visita",
        value=int(configs.get("alerta_visita", "15")),
        key="alerta_visita"
    )

    st.number_input(
        "Avisar quantos dias antes do vencimento do contato",
        value=int(configs.get("alerta_contato", "7")),
        key="alerta_contato"
    )

# =====================================================
# OPERAÇÃO
# =====================================================

with aba3:

    st.subheader("🏭 Operação Interna")

    from services.relacionamento import get_config as get_config_oper

    st.number_input(
        "Prazo máximo para envio da proposta (dias)",
        value=int(get_config_oper("envio_proposta", "3")),
        key="envio_proposta"
    )

    st.number_input(
        "Primeiro follow-up (dias)",
        value=int(get_config_oper("followup_1", "2")),
        key="followup_1"
    )

    st.number_input(
        "Segundo follow-up (dias)",
        value=int(get_config_oper("followup_2", "7")),
        key="followup_2"
    )

    st.number_input(
        "Terceiro follow-up (dias)",
        value=int(get_config_oper("followup_3", "15")),
        key="followup_3"
    )

    st.number_input(
        "Dias para considerar proposta esquecida",
        value=int(get_config_oper("proposta_esquecida", "30")),
        key="proposta_esquecida"
    )

    st.number_input(
        "Prazo para expedição (dias)",
        value=int(get_config_oper("expedicao", "5")),
        key="expedicao"
    )

    st.number_input(
        "Prazo para solicitar feedback do cliente",
        value=int(get_config_oper("feedback_cliente", "7")),
        key="feedback_cliente"
    )

# =====================================================
# BI
# =====================================================

with aba4:

    st.subheader("📈 Inteligência Comercial")

    st.markdown("### Clientes em Risco")

    st.number_input(
        "Dias sem faturamento - Classe A",
        value=90,
        key="risco_a"
    )

    st.number_input(
        "Dias sem faturamento - Classe B",
        value=180,
        key="risco_b"
    )

    st.number_input(
        "Dias sem faturamento - Classe C",
        value=365,
        key="risco_c"
    )

    st.number_input(
        "Dias sem faturamento - Classe D",
        value=730,
        key="risco_d"
    )

    st.divider()

    st.number_input(
        "Percentual de queda de faturamento para alerta",
        value=30,
        key="queda_fat"
    )

    st.number_input(
        "Percentual de queda de OS para alerta",
        value=50,
        key="queda_os"
    )

    st.number_input(
        "Percentual de queda de propostas para alerta",
        value=30,
        key="queda_prop"
    )

    st.divider()

    st.number_input(
        "Meses para cálculo de tendência",
        value=12,
        key="periodo_tendencia"
    )

    st.number_input(
        "Dias para Alerta de Preventiva Vencida (Clientes Ativos)",
        value=730,
        key="dias_alerta_preventiva",
        step=30
    )

    st.number_input(
        "Dias para Alerta de Proposta Enviada sem Retorno",
        value=7,
        key="dias_followup_proposta",
        step=1
    )

    st.checkbox(
        "Comparar automaticamente com o mesmo mês do ano anterior",
        value=True
    )

# =====================================================
# SISTEMA
# =====================================================

with aba5:

    st.subheader("🖥️ Configurações Gerais")

    st.selectbox(
        "Unidade padrão",
        [
            "ULITEC SP",
            "ULITEC RS",
            "GRUPO"
        ]
    )

    st.checkbox(
        "Exibir clientes inativos",
        value=True
    )

    st.checkbox(
        "Exibir leads frios",
        value=True
    )

    st.number_input(
        "Dias para arquivar oportunidade perdida",
        value=180
    )

    st.number_input(
        "Dias para arquivar proposta cancelada",
        value=180
    )

    st.divider()
    st.subheader("🔌 Diagnóstico de APIs de IA")

    st.markdown(
        "Teste a conexão com os providers de IA configurados no `.env`."
    )

    col_diag1, col_diag2 = st.columns(2)

    with col_diag1:
        if st.button("🧪 Testar conexão Groq (padrão)", width="stretch"):
            with st.spinner("Testando conexão com Groq..."):
                try:
                    from services.ia.groq_client import testar_conexao
                    import os
                    from dotenv import load_dotenv
                    load_dotenv()

                    api_key = os.getenv("GROQ_API_KEY", "")
                    modelo = os.getenv("GROQ_MODEL", "")

                    if not api_key:
                        st.error("❌ GROQ_API_KEY não configurada no .env")
                        st.info(
                            "Para obter uma chave gratuita da Groq:\n"
                            "1. Acesse https://console.groq.com/keys\n"
                            "2. Clique em 'Create API Key'\n"
                            "3. Configure GROQ_API_KEY no .env\n"
                            "4. O modelo llama-3.3-70b-versatile é gratuito e sem limites de cota."
                        )
                    else:
                        sucesso, msg = testar_conexao(api_key)
                        if sucesso:
                            st.success(msg)
                            st.info(f"📐 Modelo configurado: `{modelo}`")
                        else:
                            st.error(msg)
                except ImportError as e:
                    st.error(f"❌ Erro de importação: {e}")
                    st.warning("Execute: `pip install groq python-dotenv`")
                except Exception as e:
                    st.error(f"❌ Erro inesperado: {str(e)}")

    with col_diag2:
        if st.button("🧪 Testar conexão Gemini (fallback)", width="stretch"):
            with st.spinner("Testando conexão com Google Gemini..."):
                try:
                    from services.ia.gemini_client import testar_conexao
                    import os
                    from dotenv import load_dotenv
                    load_dotenv()

                    api_key = os.getenv("GEMINI_API_KEY", "")
                    modelo = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

                    if not api_key:
                        st.error("❌ GEMINI_API_KEY não configurada no .env")
                    else:
                        sucesso, msg = testar_conexao(api_key)
                        if sucesso:
                            st.success(msg)
                            st.info(f"📐 Modelo configurado: `{modelo}`")
                        else:
                            st.error(msg)
                            st.markdown(
                                "---\n"
                                "**🔑 Para criar uma nova chave gratuita:**\n"
                                "1. Acesse [Google AI Studio](https://aistudio.google.com/app/apikey)\n"
                                "2. Clique em 'Create API Key' → 'Create API key in new project'\n"
                                "3. NÃO configure billing\n"
                                "4. Atualize a chave no arquivo `.env`"
                            )
                except ImportError as e:
                    st.error(f"❌ Erro de importação: {e}")
                    st.warning("Execute: `pip install google-generativeai python-dotenv`")
                except Exception as e:
                    st.error(f"❌ Erro inesperado: {str(e)}")

    col_diag3, _ = st.columns(2)
    with col_diag3:
        if st.button("🧪 Testar conexão OpenAI (fallback)", width="stretch"):
            with st.spinner("Testando conexão com OpenAI..."):
                try:
                    import os
                    from dotenv import load_dotenv
                    load_dotenv()

                    api_key = os.getenv("OPENAI_API_KEY", "")

                    if not api_key:
                        st.warning("⚠️ OPENAI_API_KEY não configurada no .env")
                        st.info(
                            "Para usar OpenAI como fallback:\n"
                            "1. Obtenha uma chave em https://platform.openai.com/api-keys\n"
                            "2. Configure no `.env`:\n"
                            "   `IA_PROVIDER=openai`\n"
                            "   `OPENAI_API_KEY=sua-chave-aqui`"
                        )
                    else:
                        from openai import OpenAI
                        client = OpenAI(api_key=api_key)
                        modelos = client.models.list()
                        st.success(f"✅ Conexão OpenAI OK. {len(list(modelos))} modelos disponíveis.")
                        st.info(f"📐 Modelo configurado: `{os.getenv('OPENAI_MODEL', 'gpt-4o-mini')}`")
                except ImportError:
                    st.error("❌ Pacote `openai` não instalado.")
                    st.warning("Execute: `pip install openai`")
                except Exception as e:
                    st.error(f"❌ Erro na conexão OpenAI: {str(e)}")

    # Exibe status atual do provider
    st.divider()
    st.markdown("### 📋 Status atual da configuração")
    try:
        import os
        from dotenv import load_dotenv
        load_dotenv()

        provider = os.getenv("IA_PROVIDER", "groq")
        modelo_groq = os.getenv("GROQ_MODEL", "")
        modelo_gemini = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        modelo_openai = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        col_s1.metric("Provider ativo", provider.upper())
        col_s2.metric("Modelo Groq (padrão)", modelo_groq)
        col_s3.metric("Modelo Gemini", modelo_gemini)
        col_s4.metric("Modelo OpenAI", modelo_openai)
    except Exception:
        st.warning("Não foi possível ler o .env")

# =====================================================
# CENTRAL DE ADMINISTRAÇÃO DO SISTEMA
# =====================================================

with aba6:

    from services.admin_sistema import (
        obter_status_sistema,
        gerar_backup_completo,
        exportar_backup_compactado,
        listar_backups_disponiveis,
        validar_arquivo_restauracao,
        executar_vacuum,
        executar_reindex,
        limpar_cache,
        limpar_logs_antigos,
        recalcular_estatisticas,
        registrar_manutencao,
        preparar_lista_reset,
        executar_reset_sistema,
        obter_modulos_limpeza,
        obter_status_todos_modulos,
        obter_dependencias_modulo,
        preparar_limpeza_modulo,
        executar_limpeza_modulo,
        # Funções de Restauração v2.4.2
        listar_backups,
        validar_backup,
        ler_manifesto_backup,
        restaurar_backup,
        criar_backup_automatico_pre_restauracao,
        obter_informacoes_backup,
    )
    from auth import verificar_login

    if not DB_PATH.exists():
        st.error("❌ Banco de dados crm.db não encontrado.")
        st.stop()

    perfil = st.session_state.get("perfil", "")
    is_master = perfil == "MASTER"

    # ── Criar sub-abas dentro de "Banco" ──
    sub_aba1, sub_aba2, sub_aba3, sub_aba4, sub_aba5, sub_aba6, sub_aba7 = st.tabs([
        "📊 Status do Sistema",
        "💾 Backup",
        "📦 Exportação",
        "🔄 Restauração",
        "🔧 Manutenção",
        "⚠️ Reset Controlado",
        "🧹 Limpeza Seletiva",
    ])

    # ============================================================
    # BLOCO 1 - STATUS DO SISTEMA
    # ============================================================

    with sub_aba1:

        st.subheader("📊 Status do Sistema")

        with st.spinner("Obtendo informações do sistema..."):
            status = obter_status_sistema()

        col_s1, col_s2, col_s3, col_s4 = st.columns(4)

        with col_s1:
            st.metric("Versão do CRM", status["crm_version"])
            st.metric("Tabelas", status["total_tabelas"])

        with col_s2:
            st.metric("Versão do Banco", status["db_version"])
            st.metric("Registros", f"{status['total_registros']:,}")

        with col_s3:
            st.metric("Tamanho do Banco", f"{status['tamanho_kb']:.0f} KB")
            st.metric("Último Backup",
                      status["ultimo_backup"] if status["ultimo_backup"] != "Nunca"
                      else "❌ Nunca")

        with col_s4:
            st.metric("Backups", status["qtd_backups"])
            st.metric("Espaço Backups", f"{status['espaco_backups_kb']:.0f} KB")

        st.divider()

        col_s5, col_s6, col_s7 = st.columns(3)

        with col_s5:
            st.info(f"📅 **Criação do Banco**\n\n{status['data_criacao']}")

        with col_s6:
            st.info(f"🔧 **Última Manutenção**\n\n{status['ultima_manutencao']}")

        with col_s7:
            total_mb = status["tamanho_mb"]
            backup_mb = status["espaco_backups_mb"]
            st.info(
                f"📦 **Resumo**\n\n"
                f"Banco: {total_mb:.2f} MB\n"
                f"Backups: {backup_mb:.2f} MB\n"
                f"Total: {total_mb + backup_mb:.2f} MB"
            )

    # ============================================================
    # BLOCO 2 - BACKUP
    # ============================================================

    with sub_aba2:

        st.subheader("💾 Central de Backup")

        st.markdown(
            "Gere backups completos do sistema. "
            "Cada backup registra automaticamente:"
        )

        col_b1, col_b2 = st.columns(2)

        with col_b1:
            st.markdown("- Data e hora")
            st.markdown("- Versão do CRM")
            st.markdown("- Quantidade de tabelas")

        with col_b2:
            st.markdown("- Quantidade de registros")
            st.markdown("- Tamanho do arquivo")
            st.markdown("- Manifesto em JSON")

        st.divider()

        if st.button("🛠️ Gerar Backup", type="primary", width="stretch"):
            with st.spinner("Gerando backup completo..."):
                try:
                    resultado = gerar_backup_completo()

                    st.success("✅ Backup gerado com sucesso!")

                    col_r1, col_r2, col_r3 = st.columns(3)
                    col_r1.metric("Arquivo", resultado["nome"])
                    col_r2.metric("Tamanho", f"{resultado['tamanho_kb']:.2f} KB")
                    col_r3.metric("Registros", f"{resultado['registros']:,}")

                    st.info(
                        f"📄 Manifesto salvo em: `{resultado['manifesto']}`"
                    )

                except Exception as e:
                    st.error(f"❌ Erro ao gerar backup: {str(e)}")

        st.divider()

        # Listar backups existentes
        st.markdown("### 📋 Backups Existentes")

        backups = listar_backups_disponiveis()
        backups_db = [b for b in backups if b.get("tipo") == "local" or b["nome"].endswith(".db")]

        if not backups_db:
            st.info("Nenhum backup encontrado.")
        else:
            for b in backups_db:
                col_bn1, col_bn2, col_bn3 = st.columns([3, 1, 1])
                col_bn1.markdown(f"`{b['nome']}`")
                col_bn2.markdown(f"{b['tamanho_kb']:.1f} KB")
                col_bn3.markdown(f"{b['modificado']}")

    # ============================================================
    # BLOCO 3 - EXPORTAÇÃO
    # ============================================================

    with sub_aba3:

        st.subheader("📦 Exportação de Backup")

        st.markdown(
            "Gere um arquivo compactado único contendo:"
        )

        col_e1, col_e2 = st.columns(2)

        with col_e1:
            st.markdown("- Banco SQLite (`crm.db`)")
            st.markdown("- Manifesto completo")
            st.markdown("- Arquivo de versionamento")

        with col_e2:
            st.markdown("- README para restauração")
            st.markdown("- Formato `.zip`")
            st.markdown(
                "Exemplo: "
                "`ULITEC_CRM_BACKUP_2026-07-05_143500.zip`"
            )

        st.divider()

        if st.button("📦 Exportar Backup", type="primary", width="stretch"):
            with st.spinner("Gerando arquivo compactado..."):
                try:
                    resultado = exportar_backup_compactado()

                    st.success("✅ Backup exportado com sucesso!")

                    col_e1, col_e2, col_e3 = st.columns(3)
                    col_e1.metric("Arquivo", resultado["nome"])
                    col_e2.metric("Tamanho", f"{resultado['tamanho_kb']:.2f} KB")
                    col_e3.metric("Registros", f"{resultado['registros']:,}")

                    st.info(f"📁 Salvo em: `{resultado['arquivo']}`")

                except Exception as e:
                    st.error(f"❌ Erro ao exportar: {str(e)}")

    # ============================================================
    # BLOCO 4 - MANIFESTO
    # ============================================================

    with sub_aba4:

        st.subheader("🔄 Restauração do Sistema")

        st.warning(
            "⚠️ **ATENÇÃO:** A restauração substituirá COMPLETAMENTE o banco de dados "
            "atual (`crm.db`) pelo backup selecionado.\n\n"
            "Antes de restaurar, o sistema cria automaticamente um backup de segurança "
            "do banco atual.\n\n"
            "**É obrigatório:** Backup automático ✅ → Log ✅ → Senha MASTER ✅ → "
            "Confirmação textual ✅"
        )

        st.divider()

        # ── Estado da sessão para o fluxo de restauração ──
        if "restore_backup_selecionado" not in st.session_state:
            st.session_state["restore_backup_selecionado"] = None
        if "restore_validacao" not in st.session_state:
            st.session_state["restore_validacao"] = None
        if "restore_backup_auto" not in st.session_state:
            st.session_state["restore_backup_auto"] = None
        if "restore_etapa" not in st.session_state:
            st.session_state["restore_etapa"] = "selecao"

        # ── Listar backups disponíveis ──
        backups_disponiveis = listar_backups()

        if not backups_disponiveis:
            st.info("📭 Nenhum backup disponível para restauração.")
            st.markdown(
                "Crie um backup na aba **💾 Backup** ou exporte "
                "na aba **📦 Exportação** primeiro."
            )
        else:
            # ── SELECAO ──
            st.markdown("### 📂 Passo 1: Selecionar Backup")

            opcoes_rest = {}
            for b in backups_disponiveis:
                label = f"{b['nome']} — {b['tamanho_kb']:.1f} KB — {b['modificado']} ({b['tipo']})"
                opcoes_rest[label] = b["caminho"]

                # Armazenar metadados em session_state
                if f"restore_info_{b['caminho']}" not in st.session_state:
                    info = obter_informacoes_backup(b["caminho"])
                    st.session_state[f"restore_info_{b['caminho']}"] = info

            selecao_label = st.selectbox(
                "Selecione um arquivo de backup",
                list(opcoes_rest.keys()),
                key="restore_select",
            )

            if selecao_label:
                caminho_sel = opcoes_rest[selecao_label]
                st.session_state["restore_backup_selecionado"] = caminho_sel

                # ── VALIDAÇÃO ──
                st.divider()
                st.markdown("### 🔍 Passo 2: Validação do Backup")

                if st.button("🔍 Validar Backup", type="primary", width="stretch"):
                    with st.spinner("Validando backup..."):
                        validacao = validar_backup(caminho_sel)
                        st.session_state["restore_validacao"] = validacao
                        st.session_state["restore_etapa"] = "validacao"

                # Exibir validação se existir
                validacao = st.session_state.get("restore_validacao")

                if validacao and st.session_state["restore_backup_selecionado"] == caminho_sel:
                    # Cards de verificação
                    st.markdown("#### 📋 Resultado da Validação")

                    for v in validacao.get("verificacoes", []):
                        status_icon = v.get("status", "❓")
                        item = v.get("item", "")
                        detalhe = v.get("detalhe", "")
                        col_vicon, col_vitem, col_vdet = st.columns([1, 3, 6])
                        col_vicon.markdown(f"**{status_icon}**")
                        col_vitem.markdown(f"**{item}**")
                        col_vdet.markdown(detalhe)

                    if validacao.get("valido") and validacao.get("pode_restaurar"):
                        st.success("✅ **Backup válido!** Pode prosseguir com a restauração.")
                    else:
                        st.error("❌ **Backup inválido!** Restauração bloqueada.")
                        for erro in validacao.get("erros", []):
                            st.markdown(f"- {erro}")

                    # Informações detalhadas em cards
                    st.divider()
                    st.markdown("#### 📊 Informações do Backup")

                    info_backup = st.session_state.get(f"restore_info_{caminho_sel}", {})

                    if info_backup and "erro" not in info_backup:
                        col_i1, col_i2, col_i3 = st.columns(3)
                        with col_i1:
                            st.metric("Arquivo", info_backup.get("nome", "?"))
                            st.metric("Tamanho", f"{info_backup.get('tamanho_kb', 0):.2f} KB")
                        with col_i2:
                            st.metric("Tabelas", info_backup.get("quantidade_tabelas", "?"))
                            st.metric("Registros", f"{info_backup.get('quantidade_registros', 0):,}")
                        with col_i3:
                            st.metric("Versão CRM", info_backup.get("versao_crm", "?"))
                            st.metric("Data", info_backup.get("data_backup", info_backup.get("modificado", "?")))

                        # Manifesto expandido
                        manifesto = ler_manifesto_backup(caminho_sel)
                        if manifesto.get("encontrado") and manifesto.get("manifesto"):
                            with st.expander("📄 Ver Manifesto Completo"):
                                st.json(manifesto["manifesto"])
                                st.caption(f"Fonte: {manifesto['fonte']}")

                        # Lista de tabelas
                        tabelas = info_backup.get("tabelas", [])
                        if tabelas:
                            with st.expander(f"📋 Tabelas ({len(tabelas)})"):
                                for t in tabelas:
                                    st.markdown(f"- `{t}`")

                    # ── ETAPAS DE SEGURANÇA (se backup válido) ──
                    if validacao.get("valido") and validacao.get("pode_restaurar"):
                        st.divider()
                        st.markdown("### 🔒 Passo 3: Backup Automático de Segurança")

                        if st.button("📦 Criar Backup Automático Pré-Restauração",
                                     width="stretch"):
                            with st.spinner("Criando backup de segurança do banco atual..."):
                                backup_auto = criar_backup_automatico_pre_restauracao()
                                if backup_auto["sucesso"]:
                                    st.session_state["restore_backup_auto"] = backup_auto
                                    st.success(
                                        f"✅ Backup automático criado: **{backup_auto['nome']}**"
                                    )
                                    st.info(
                                        f"📁 Salvo em: `{backup_auto['arquivo']}`\n\n"
                                        f"📦 Tamanho: {backup_auto['tamanho_kb']:.2f} KB"
                                    )
                                else:
                                    st.error(
                                        f"❌ Falha ao criar backup automático: "
                                        f"{backup_auto.get('erro', 'Erro desconhecido')}"
                                    )

                        # ── AUTENTICAÇÃO MASTER ──
                        st.divider()
                        st.markdown("### 🔐 Passo 4: Autenticação MASTER")

                        login_master = st.session_state.get("login", "")
                        senha_master_restore = st.text_input(
                            "Senha do usuário MASTER",
                            type="password",
                            key="restore_senha_master",
                        )

                        autenticado_restore = False
                        if senha_master_restore:
                            resultado_login = verificar_login(login_master, senha_master_restore)
                            if resultado_login and resultado_login.get("perfil") == "MASTER":
                                autenticado_restore = True
                                st.success("✅ Autenticado como MASTER")
                            else:
                                st.error("❌ Senha MASTER inválida.")

                        # ── CONFIRMAÇÃO TEXTUAL ──
                        st.divider()
                        st.markdown("### ✍️ Passo 5: Confirmação Textual")

                        confirmacao_texto_restore = st.text_input(
                            "Digite exatamente: **RESTAURAR SISTEMA**",
                            type="default",
                            key="restore_confirmacao_texto",
                        )

                        confirmacao_restore_ok = (
                            confirmacao_texto_restore == "RESTAURAR SISTEMA"
                        )

                        if confirmacao_texto_restore and not confirmacao_restore_ok:
                            st.error("❌ Texto de confirmação incorreto.")
                        elif confirmacao_restore_ok:
                            st.success("✅ Confirmação textual aceita.")

                        # ── VERIFICAR SE PODE RESTAURAR ──
                        backup_auto_feito = st.session_state.get("restore_backup_auto") is not None

                        pode_restaurar = (
                            validacao.get("valido", False)
                            and validacao.get("pode_restaurar", False)
                            and backup_auto_feito
                            and autenticado_restore
                            and confirmacao_restore_ok
                        )

                        # ── BOTÃO DE RESTAURAÇÃO ──
                        st.divider()
                        st.markdown("### ⚡ Passo 6: Executar Restauração")

                        if pode_restaurar:
                            st.error(
                                "🚨 **ÚLTIMA OPORTUNIDADE DE CANCELAR**\n\n"
                                "Esta ação substituirá COMPLETAMENTE o banco de dados atual "
                                "pelo backup selecionado.\n\n"
                                f"**Backup a restaurar:** {Path(caminho_sel).name}\n"
                                f"**Backup automático criado:** "
                                f"{st.session_state['restore_backup_auto']['nome']}\n\n"
                                "**Esta operação é IRREVERSÍVEL.**"
                            )

                            col_restore_confirmar, col_restore_cancelar = st.columns(2)

                            with col_restore_confirmar:
                                if st.button(
                                    "⚠️ CONFIRMAR RESTAURAÇÃO",
                                    type="primary",
                                    width="stretch",
                                ):
                                    with st.spinner(
                                        "🔄 Restaurando sistema...\n\n"
                                        "1/4 Backup automático ✓\n"
                                        "2/4 Substituindo banco...\n"
                                        "3/4 Verificando integridade...\n"
                                        "4/4 Gerando relatório..."
                                    ):
                                        try:
                                            usuario_atual = st.session_state.get(
                                                "usuario_nome", "Sistema"
                                            )
                                            resultado = restaurar_backup(
                                                caminho_sel,
                                                usuario=usuario_atual,
                                            )

                                            if resultado["sucesso"]:
                                                st.balloons()
                                                st.success(
                                                    "✅ **RESTAURAÇÃO CONCLUÍDA COM SUCESSO!**"
                                                )

                                                # ── RELATÓRIO ──
                                                st.divider()
                                                st.markdown("### 📊 Relatório da Restauração")

                                                col_rel1, col_rel2 = st.columns(2)
                                                with col_rel1:
                                                    st.metric(
                                                        "Backup Restaurado",
                                                        resultado["backup_restaurado"],
                                                    )
                                                    st.metric(
                                                        "Backup Automático",
                                                        resultado["backup_automatico_criado"],
                                                    )
                                                    st.metric(
                                                        "Tempo",
                                                        f"{resultado['tempo_segundos']:.2f}s",
                                                    )
                                                with col_rel2:
                                                    st.metric(
                                                        "Tabelas",
                                                        resultado["quantidade_tabelas"],
                                                    )
                                                    st.metric(
                                                        "Registros",
                                                        f"{resultado['quantidade_registros']:,}",
                                                    )
                                                    st.metric(
                                                        "Versão Restaurada",
                                                        resultado["versao_restaurada"],
                                                    )

                                                st.info(
                                                    f"📅 **Data da restauração:** "
                                                    f"{resultado['data_restauracao']}\n\n"
                                                    f"✅ **Integrity Check:** "
                                                    f"{resultado['integrity_check']}"
                                                )

                                                # Botão reiniciar
                                                st.divider()
                                                st.markdown("### 🔄 Reiniciar Aplicação")

                                                st.warning(
                                                    "Após a restauração, é recomendado "
                                                    "reiniciar a aplicação para garantir "
                                                    "que todas as conexões sejam "
                                                    "restabelecidas corretamente."
                                                )

                                                if st.button(
                                                    "🔄 Reiniciar Aplicação",
                                                    type="primary",
                                                    width="stretch",
                                                ):
                                                    st.rerun()

                                            else:
                                                st.error(
                                                    f"❌ **FALHA NA RESTAURAÇÃO**\n\n"
                                                    f"{resultado.get('erro', 'Erro desconhecido')}"
                                                )

                                                if resultado.get("backup_automatico"):
                                                    st.info(
                                                        "🔒 O backup automático foi preservado em:\n"
                                                        f"`{resultado['backup_automatico'].get('arquivo', '?')}`\n\n"
                                                        "O banco atual NÃO foi modificado."
                                                    )

                                        except Exception as e:
                                            st.error(f"❌ Erro crítico: {str(e)}")

                            with col_restore_cancelar:
                                if st.button(
                                    "❌ Cancelar",
                                    width="stretch",
                                ):
                                    # Limpar estado
                                    for key in list(st.session_state.keys()):
                                        if key.startswith("restore_"):
                                            del st.session_state[key]
                                    st.rerun()

                        else:
                            # Mostrar o que falta
                            pendentes = []
                            if not validacao.get("valido", False) or not validacao.get("pode_restaurar", False):
                                pendentes.append("❌ Backup inválido")
                            if not backup_auto_feito:
                                pendentes.append("⏳ Backup automático não criado")
                            if not autenticado_restore:
                                pendentes.append("⏳ Autenticação MASTER pendente")
                            if not confirmacao_restore_ok:
                                pendentes.append("⏳ Confirmação textual pendente")

                            st.warning(
                                "⚠️ Complete todos os passos de segurança:\n\n"
                                + "\n".join(f"- {p}" for p in pendentes)
                            )

    # ============================================================
    # BLOCO 5 - MANUTENÇÃO
    # ============================================================

    with sub_aba5:

        st.subheader("🔧 Manutenção do Sistema")

        if not is_master:
            st.warning(
                "⚠️ Área exclusiva para usuários **MASTER**."
            )
        else:
            st.markdown(
                "Ferramentas de manutenção do banco de dados SQLite."
            )

            col_m1, col_m2 = st.columns(2)

            with col_m1:

                if st.button("🧹 Vacuum", width="stretch"):
                    with st.spinner("Executando VACUUM..."):
                        resultado = executar_vacuum()
                        if resultado["sucesso"]:
                            st.success(
                                f"✅ VACUUM concluído. "
                                f"Economia: {resultado['economia_kb']} KB"
                            )
                            registrar_manutencao()
                        else:
                            st.error(f"❌ Erro: {resultado.get('erro', '')}")

                if st.button("🔄 Reindexar", width="stretch"):
                    with st.spinner("Recriando índices..."):
                        resultado = executar_reindex()
                        if resultado["sucesso"]:
                            st.success("✅ Índices recriados com sucesso.")
                            registrar_manutencao()
                        else:
                            st.error(f"❌ Erro: {resultado.get('erro', '')}")

                if st.button("🗑️ Limpar Cache", width="stretch"):
                    with st.spinner("Limpando cache..."):
                        resultado = limpar_cache()
                        if resultado["sucesso"]:
                            st.success("✅ Cache limpo com sucesso.")
                            registrar_manutencao()
                        else:
                            st.error(f"❌ Erro: {resultado.get('erro', '')}")

            with col_m2:

                if st.button("📊 Recalcular Estatísticas", width="stretch"):
                    with st.spinner("Recalculando estatísticas..."):
                        resultado = recalcular_estatisticas()
                        if resultado["sucesso"]:
                            st.success(
                                f"✅ {resultado['tabelas_analisadas']} tabelas analisadas."
                            )
                            registrar_manutencao()
                        else:
                            st.error(f"❌ Erro: {resultado.get('erro', '')}")

                if st.button("📋 Limpar Logs Antigos (90 dias)", width="stretch"):
                    with st.spinner("Removendo logs antigos..."):
                        resultado = limpar_logs_antigos(90)
                        if resultado["sucesso"]:
                            st.success(
                                f"✅ {resultado['removidos']} registros removidos."
                            )
                            registrar_manutencao()
                        else:
                            st.error(f"❌ Erro: {resultado.get('erro', '')}")

            st.divider()
            st.markdown("### Última Manutenção")
            status_m = obter_status_sistema()
            st.info(f"🔧 {status_m['ultima_manutencao']}")

    # ============================================================
    # BLOCO 6 - RESET CONTROLADO
    # ============================================================

    with sub_aba6:

        st.subheader("⚠️ Reset Controlado do Sistema")

        if not is_master:
            st.warning(
                "⚠️ Área exclusiva para usuários **MASTER**."
            )
        else:
            st.error(
                "🚨 **ATENÇÃO: Esta é a ferramenta mais crítica do CRM.**\n\n"
                "O reset controlado apaga **TODOS os dados operacionais** do sistema.\n"
                "Utilize apenas UMA vez, antes da entrada em produção.\n\n"
                "**O que NÃO será apagado:** Código fonte, Python, assets, "
                "ícones, layout, configurações da aplicação."
            )

            st.divider()

            # ── PASSO 1: Backup obrigatório ──
            st.markdown("### 🔴 Passo 1 - Backup Obrigatório")

            backup_gerado = st.session_state.get("reset_backup_gerado", False)
            backup_exportado = st.session_state.get("reset_backup_exportado", False)

            if not backup_gerado:
                st.warning(
                    "⚠️ É obrigatório gerar um backup antes de continuar."
                )

                if st.button("📦 1. Gerar Backup", type="primary", width="stretch"):
                    with st.spinner("Gerando backup obrigatório..."):
                        try:
                            resultado = gerar_backup_completo()
                            st.session_state["reset_backup_gerado"] = True
                            st.session_state["reset_backup_info"] = resultado
                            st.success(
                                f"✅ Backup gerado: {resultado['nome']}"
                            )
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Erro ao gerar backup: {str(e)}")
            else:
                st.success("✅ Backup gerado com sucesso!")
                info_b = st.session_state.get("reset_backup_info", {})
                st.markdown(f"**Arquivo:** `{info_b.get('nome', '')}`")

                # ── PASSO 2: Exportação obrigatória ──
                st.divider()
                st.markdown("### 🔴 Passo 2 - Exportação Obrigatória")

                if not backup_exportado:
                    st.warning(
                        "⚠️ É obrigatório exportar o backup antes de continuar."
                    )

                    if st.button("📦 2. Exportar Backup", type="primary", width="stretch"):
                        with st.spinner("Exportando backup compactado..."):
                            try:
                                resultado = exportar_backup_compactado()
                                st.session_state["reset_backup_exportado"] = True
                                st.session_state["reset_export_info"] = resultado
                                st.success(
                                    f"✅ Backup exportado: {resultado['nome']}"
                                )
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Erro ao exportar: {str(e)}")
                else:
                    st.success("✅ Backup exportado com sucesso!")
                    info_e = st.session_state.get("reset_export_info", {})
                    st.markdown(f"**Arquivo:** `{info_e.get('nome', '')}`")

                    # ── PASSO 3: Lista do que será apagado ──
                    st.divider()
                    st.markdown("### 🔴 Passo 3 - Itens que serão apagados")

                    itens_reset = preparar_lista_reset()

                    total_apagar = sum(i["registros"] for i in itens_reset)

                    st.markdown(
                        f"**Total de registros a serem removidos: {total_apagar:,}**"
                    )

                    col_reset_tabs = st.columns(2)
                    with col_reset_tabs[0]:
                        st.markdown("**Dados Operacionais**")
                        for item in itens_reset:
                            if item["registros"] > 0:
                                st.markdown(
                                    f"- ❌ {item['nome']} "
                                    f"({item['registros']} registros)"
                                )
                            else:
                                st.markdown(
                                    f"- ⬜ {item['nome']} (vazio)"
                                )

                    with col_reset_tabs[1]:
                        st.markdown("**Também serão removidos:**")
                        st.markdown("- 📁 Backups locais")
                        st.markdown("- 📦 Arquivos exportados")
                        st.markdown("- 📄 Manifestos")
                        st.markdown(
                            "- 👤 Usuários (exceto MASTER)"
                        )

                    st.markdown("**Preservado:**")
                    st.markdown(
                        "- ✅ Código fonte\n"
                        "- ✅ Python / Assets / Ícones / Layout\n"
                        "- ✅ Configurações da aplicação\n"
                        "- ✅ Unidades\n"
                        "- ✅ Usuário MASTER"
                    )

                    # ── PASSO 4: Confirmação textual ──
                    st.divider()
                    st.markdown("### 🔴 Passo 4 - Confirmação Textual")

                    confirmacao_texto = st.text_input(
                        "Digite exatamente: **RESETAR CRM ULITEC**",
                        type="default",
                        key="reset_confirmacao_texto",
                    )

                    confirmacao_ok = confirmacao_texto == "RESETAR CRM ULITEC"

                    if not confirmacao_ok and confirmacao_texto:
                        st.error("❌ Texto de confirmação incorreto.")

                    # ── PASSO 5: Senha MASTER ──
                    st.divider()
                    st.markdown("### 🔴 Passo 5 - Autenticação MASTER")

                    senha_master = st.text_input(
                        "Senha do usuário MASTER",
                        type="password",
                        key="reset_senha_master",
                    )

                    login_master = st.session_state.get("login", "")
                    autenticado = False

                    if senha_master:
                        resultado_login = verificar_login(login_master, senha_master)
                        if resultado_login and resultado_login.get("perfil") == "MASTER":
                            autenticado = True
                        else:
                            st.error("❌ Senha MASTER inválida.")

                    # ── PASSO 6: Confirmação final ──
                    st.divider()
                    st.markdown("### 🔴 Passo 6 - Confirmação Final")

                    pode_resetar = (
                        backup_gerado
                        and backup_exportado
                        and confirmacao_ok
                        and autenticado
                    )

                    if pode_resetar:
                        st.error(
                            "🚨 **ÚLTIMA OPORTUNIDADE DE CANCELAR**\n\n"
                            "Esta ação é IRREVERSÍVEL.\n"
                            "Todos os dados operacionais serão perdidos."
                        )

                        col_confirmar, col_cancelar = st.columns(2)

                        with col_confirmar:
                            if st.button(
                                "⚠️ CONFIRMAR RESET",
                                type="primary",
                                width="stretch",
                            ):
                                with st.spinner(
                                    "Executando reset do sistema..."
                                ):
                                    try:
                                        resultado = executar_reset_sistema()

                                        # Limpar session state
                                        for key in [
                                            "reset_backup_gerado",
                                            "reset_backup_exportado",
                                            "reset_backup_info",
                                            "reset_export_info",
                                        ]:
                                            if key in st.session_state:
                                                del st.session_state[key]

                                        st.success(
                                            "✅ **RESET CONCLUÍDO COM SUCESSO!**"
                                        )

                                        col_r1, col_r2, col_r3 = st.columns(3)
                                        col_r1.metric(
                                            "Registros Removidos",
                                            f"{resultado['total_registros_removidos']:,}",
                                        )
                                        col_r2.metric(
                                            "Usuários Removidos",
                                            resultado["usuarios_removidos"],
                                        )
                                        col_r3.metric(
                                            "Backups Removidos",
                                            resultado["backups_locais_removidos"],
                                        )

                                        st.info(
                                            "🆕 **Sistema resetado como nova instalação.**\n\n"
                                            "- Clientes: 0\n"
                                            "- OS: 0\n"
                                            "- Produtos: 0\n"
                                            "- Usuários: apenas MASTER\n"
                                            "- Backups: 0\n\n"
                                            "Recarregue a página para continuar."
                                        )

                                    except Exception as e:
                                        st.error(
                                            f"❌ Erro ao executar reset: {str(e)}"
                                        )

                        with col_cancelar:
                            if st.button(
                                "❌ Cancelar",
                                width="stretch",
                            ):
                                for key in [
                                    "reset_backup_gerado",
                                    "reset_backup_exportado",
                                    "reset_backup_info",
                                    "reset_export_info",
                                ]:
                                    if key in st.session_state:
                                        del st.session_state[key]
                                st.rerun()

                    else:
                        st.info(
                            "Preencha todos os passos acima para liberar "
                            "o botão de reset."
                        )

    # ============================================================
    # BLOCO 7 - LIMPEZA SELETIVA POR MÓDULO
    # ============================================================

    with sub_aba7:

        st.subheader("🧹 Limpeza Seletiva do Banco")

        if not is_master:
            st.warning(
                "⚠️ Área exclusiva para usuários **MASTER**."
            )
        else:
            st.markdown(
                "Selecione um módulo abaixo para visualizar os registros "
                "existentes e, se necessário, executar a limpeza seletiva "
                "**apenas** das tabelas daquele módulo."
            )

            st.divider()

            # ── Carregar status de todos os módulos ──
            with st.spinner("Carregando informações dos módulos..."):
                modulos_status = obter_status_todos_modulos()
                modulos_disponiveis = obter_modulos_limpeza()

            # ── Inicializar estado de seleção ──
            if "limpeza_modulo_selecionado" not in st.session_state:
                st.session_state["limpeza_modulo_selecionado"] = modulos_disponiveis[0] if modulos_disponiveis else None

            # ── Tabela visual dos módulos ──
            st.markdown("### 📋 Módulos Disponíveis")

            cols_modulos = st.columns(2)
            for idx, modulo in enumerate(modulos_status):
                col = cols_modulos[idx % 2]
                with col:
                    nome = modulo["modulo"]
                    total_reg = modulo["total_registros"]
                    qtd_tabs = modulo["quantidade_tabelas"]
                    tabelas_lista = [t["nome"] for t in modulo["tabelas"]]

                    with st.container(border=True):
                        col_check, col_info = st.columns([1, 10])
                        with col_check:
                            checked = st.checkbox(
                                "",
                                key=f"modulo_check_{nome}",
                                value=(st.session_state["limpeza_modulo_selecionado"] == nome),
                                label_visibility="collapsed",
                            )
                            if checked:
                                st.session_state["limpeza_modulo_selecionado"] = nome

                        with col_info:
                            st.markdown(f"**{nome}**")
                            st.caption(modulo["descricao"])
                            st.markdown(
                                f"Registros atuais: **{total_reg:,}** | "
                                f"Tabelas: **{qtd_tabs}**"
                            )
                            with st.expander("📄 Ver tabelas afetadas"):
                                for t in modulo["tabelas"]:
                                    nome_t = t["nome"]
                                    qtd_t = t["registros"]
                                    st.markdown(f"- `{nome_t}` ({qtd_t:,} registros)")

            st.divider()

            # ── Módulo selecionado para ações ──
            modulo_sel = st.session_state.get("limpeza_modulo_selecionado")
            if not modulo_sel or modulo_sel not in modulos_disponiveis:
                st.info("Selecione um módulo acima para continuar.")
            else:
                status_sel = next(
                    (m for m in modulos_status if m["modulo"] == modulo_sel),
                    None,
                )

                if status_sel:
                    st.markdown(f"### 🔍 Pré-visualização: {modulo_sel}")
                    st.markdown(f"**Descrição:** {status_sel['descricao']}")

                    col_prev1, col_prev2, col_prev3 = st.columns(3)
                    with col_prev1:
                        st.metric(
                            "Registros encontrados",
                            f"{status_sel['total_registros']:,}",
                        )
                    with col_prev2:
                        st.metric(
                            "Quantidade de tabelas",
                            status_sel["quantidade_tabelas"],
                        )
                    with col_prev3:
                        total_linhas = status_sel["total_registros"]
                        st.metric(
                            "Total de linhas afetadas",
                            f"{total_linhas:,}",
                        )

                    # ── Botão Visualizar Dependências ──
                    with st.popover("🔗 Visualizar Dependências", width="stretch"):
                        dep_info = obter_dependencias_modulo(modulo_sel)
                        st.markdown("### Grafo de Dependências")
                        for linha in dep_info["grafo"]:
                            st.markdown(f"- {linha}")
                        st.caption(
                            "Módulos listados abaixo podem ser afetados "
                            "pela limpeza deste módulo."
                        )

                    st.divider()

                    # ── Opção Resetar AUTOINCREMENT ──
                    reset_seq = st.checkbox(
                        "☐ Resetar sequência AUTOINCREMENT (apenas das tabelas afetadas)",
                        key="limpeza_reset_sequence",
                        value=False,
                    )

                    st.divider()

                    # ── Confirmação: Senha MASTER + Texto ──
                    st.markdown("### 🔐 Confirmação de Segurança")

                    senha_master_limpeza = st.text_input(
                        "Senha do usuário MASTER",
                        type="password",
                        key="limpeza_senha_master",
                    )

                    confirmacao_texto_limpeza = st.text_input(
                        "Digite exatamente: **CONFIRMAR LIMPEZA**",
                        type="default",
                        key="limpeza_confirmacao_texto",
                    )

                    confirmacao_ok_limpeza = (
                        confirmacao_texto_limpeza == "CONFIRMAR LIMPEZA"
                    )

                    if confirmacao_texto_limpeza and not confirmacao_ok_limpeza:
                        st.error("❌ Texto de confirmação incorreto.")

                    # Validar senha MASTER
                    login_master = st.session_state.get("login", "")
                    autenticado_limpeza = False
                    if senha_master_limpeza:
                        resultado_login = verificar_login(
                            login_master, senha_master_limpeza
                        )
                        if resultado_login and resultado_login.get("perfil") == "MASTER":
                            autenticado_limpeza = True
                        else:
                            st.error("❌ Senha MASTER inválida.")

                    pode_limpar = confirmacao_ok_limpeza and autenticado_limpeza

                    if pode_limpar:
                        st.warning(
                            "🚨 **ATENÇÃO:** Esta ação removerá **todos os registros** "
                            f"do módulo **{modulo_sel}**. As tabelas e "
                            "suas estruturas serão preservadas. Esta operação "
                            "NÃO pode ser desfeita."
                        )

                        if st.button(
                            f"🧹 Executar Limpeza: {modulo_sel}",
                            type="primary",
                            width="stretch",
                        ):
                            with st.spinner(
                                f"Executando limpeza do módulo {modulo_sel}..."
                            ):
                                try:
                                    resultado = executar_limpeza_modulo(
                                        modulo_sel,
                                        reset_sequence=reset_seq,
                                    )

                                    if resultado["sucesso"]:
                                        st.success(
                                            "✅ **LIMPEZA CONCLUÍDA COM SUCESSO!**"
                                        )
                                    else:
                                        st.warning(
                                            "⚠️ Limpeza concluída com alguns erros."
                                        )

                                    # ── Relatório ──
                                    st.divider()
                                    st.markdown("### 📊 Relatório da Limpeza")

                                    col_rel1, col_rel2, col_rel3, col_rel4 = st.columns(4)
                                    with col_rel1:
                                        st.metric(
                                            "Módulo",
                                            resultado["modulo"],
                                        )
                                    with col_rel2:
                                        st.metric(
                                            "Tabelas afetadas",
                                            resultado["tabelas_afetadas"],
                                        )
                                    with col_rel3:
                                        st.metric(
                                            "Registros removidos",
                                            f"{resultado['total_registros_removidos']:,}",
                                        )
                                    with col_rel4:
                                        st.metric(
                                            "Tempo",
                                            f"{resultado['tempo_segundos']} s",
                                        )

                                    st.caption(
                                        f"Data: {resultado['data_limpeza']} | "
                                        f"Reset sequence: {'Sim' if resultado['reset_sequence'] else 'Não'}"
                                    )

                                    # Detalhes das tabelas
                                    with st.expander("📄 Detalhes por tabela"):
                                        for det in resultado["detalhes"]:
                                            status_icone = {
                                                "ok": "✅",
                                                "vazia": "⬜",
                                                "erro": "❌",
                                            }.get(det["status"], "❓")
                                            st.markdown(
                                                f"{status_icone} `{det['tabela']}`: "
                                                f"{det['removidos']} registros removidos"
                                            )
                                            if det.get("erro"):
                                                st.error(f"Erro: {det['erro']}")

                                    if resultado.get("erros"):
                                        st.error("Erros encontrados:")
                                        for e in resultado["erros"]:
                                            st.markdown(
                                                f"- `{e['tabela']}`: {e['erro']}"
                                            )

                                    # Limpar session state de confirmação
                                    for key in [
                                        "limpeza_senha_master",
                                        "limpeza_confirmacao_texto",
                                        "limpeza_reset_sequence",
                                    ]:
                                        if key in st.session_state:
                                            del st.session_state[key]

                                    st.info(
                                        "🔄 Recarregue os módulos para "
                                        "visualizar o novo estado."
                                    )

                                except Exception as e:
                                    st.error(
                                        f"❌ Erro ao executar limpeza: {str(e)}"
                                    )

# =====================================================
# 👥 GESTÃO DE USUÁRIOS
# =====================================================

with aba7:

    st.subheader("👥 Gestão de Usuários")

    conn_usr = sqlite3.connect(str(DB_PATH))

    conn_usr.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            login TEXT UNIQUE,
            senha TEXT,
            nome TEXT,
            email TEXT,
            nivel_acesso TEXT
        )
    """)
    conn_usr.commit()

    try:
        conn_usr.execute("ALTER TABLE usuarios ADD COLUMN email TEXT;")
        conn_usr.commit()
    except Exception:
        pass

    with st.form("form_cadastro_usuario"):
        st.markdown("### ➕ Cadastrar Novo Usuário")

        col1, col2 = st.columns(2)

        with col1:
            nome_usr = st.text_input("Nome completo")
            login_usr = st.text_input("Login")

        with col2:
            senha_usr = st.text_input("Senha", type="password")
            nivel_acesso = st.selectbox(
                "Nível de Acesso",
                ["SÓCIO", "GERENTE", "OPERADOR SP", "OPERADOR RS"]
            )

        cadastrar = st.form_submit_button(
            "📌 Cadastrar Usuário",
            type="primary"
        )

        if cadastrar:
            if not nome_usr or not login_usr or not senha_usr:
                st.error("Preencha todos os campos obrigatórios.")
            else:
                try:
                    conn_usr.execute(
                        """
                        INSERT INTO usuarios (login, senha, nome, nivel_acesso)
                        VALUES (?, ?, ?, ?)
                        """,
                        (login_usr, senha_usr, nome_usr, nivel_acesso)
                    )
                    conn_usr.commit()
                    st.success(f"Usuário '{nome_usr}' cadastrado com sucesso!")
                except sqlite3.IntegrityError:
                    st.error(f"O login '{login_usr}' já existe no sistema.")

    st.divider()

    st.markdown("### 📋 Usuários Cadastrados")

    try:
        usuarios = conn_usr.execute(
            "SELECT id, nome, login, nivel_acesso FROM usuarios ORDER BY nome"
        ).fetchall()

        if not usuarios:
            st.info("Nenhum usuário cadastrado ainda.")
        else:
            col_h1, col_h2, col_h3, col_h4, col_h5 = st.columns([3, 3, 3, 3, 3])
            col_h1.markdown("**Nome**")
            col_h2.markdown("**Login**")
            col_h3.markdown("**Nível de Acesso**")
            col_h4.markdown("**Ação**")
            col_h5.markdown("")

            for uid, unome, ulogin, univel in usuarios:
                col1, col2, col3, col4, col5 = st.columns([3, 3, 3, 3, 3])
                col1.write(unome)
                col2.write(ulogin)
                col3.write(univel)

                with col4:
                    with st.popover("🔑 Redefinir Senha"):
                        with st.form(f"form_reset_{uid}", clear_on_submit=True):
                            nova_senha = st.text_input(
                                "Nova senha",
                                type="password",
                                key=f"nova_senha_{uid}"
                            )
                            confirmar = st.form_submit_button("Confirmar")

                            if confirmar:
                                if not nova_senha:
                                    st.error("Informe a nova senha.")
                                else:
                                    conn_usr.execute(
                                        "UPDATE usuarios SET senha = ? WHERE id = ?",
                                        (nova_senha, uid)
                                    )
                                    conn_usr.commit()
                                    st.success("Senha redefinida com sucesso!")

                col5.write("")

    except Exception as e:
        st.error(f"Erro ao carregar usuários: {e}")

    conn_usr.close()

# =====================================================
# INFORMAÇÕES DA INSTALAÇÃO
# =====================================================

with aba8:

    st.subheader("ℹ️ Informações da Instalação")

    from services.version import get_version_info, get_banner
    from services.deploy_manager import system_health, installation_report

    st.markdown(f"**{get_banner()}**")
    st.divider()

    info = get_version_info()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🏷️ Versão", info["versao"])
    with col2:
        st.metric("🔢 Build", info["build"])
    with col3:
        st.metric("🌐 Ambiente", info["ambiente"])
    with col4:
        st.metric("📅 Data da Release", info["data_release"])

    st.divider()

    col5, col6, col7, col8 = st.columns(4)
    with col5:
        st.metric("🐍 Python", info["python"])
    with col6:
        st.metric("🗄️ SQLite (módulo)", info["sqlite_modulo"])
    with col7:
        st.metric("💾 SQLite (banco)", info["sqlite_banco"])
    with col8:
        st.metric("📦 Sistema", info["sistema"])

    st.divider()

    # ── HEALTH CHECK ──
    st.subheader("🔍 Health Check do Sistema")

    if st.button("🚀 Executar Health Check", type="primary", width="stretch"):
        with st.spinner("Executando validação completa do sistema..."):
            health = system_health()

        # Status global
        status_cor = {
            "OK": "green",
            "WARNING": "orange",
            "ERROR": "red",
        }.get(health.status, "gray")
        st.markdown(f"### Status: :{status_cor}[{health.status}]")
        st.caption(f"Verificação executada em: {health.timestamp}")

        st.divider()

        # ── Pastas ──
        col_p1, col_p2 = st.columns([1, 3])
        with col_p1:
            st.markdown("#### 📁 Pastas")
        with col_p2:
            todas_ok = health.directories.get("todas_existiam", True)
            if todas_ok:
                st.success("Todas as pastas OK")
            else:
                st.warning("Algumas pastas foram criadas agora")

        pastas = health.directories.get("pastas", {})
        if pastas:
            cols_pastas = st.columns(3)
            for idx, (nome, status_str) in enumerate(pastas.items()):
                with cols_pastas[idx % 3]:
                    icone = "✔️" if "já existia" in status_str else "➕"
                    st.markdown(f"{icone} {nome}")

        st.divider()

        # ── Banco ──
        col_b1, col_b2 = st.columns([1, 3])
        with col_b1:
            st.markdown("#### 🗄️ Banco")
        with col_b2:
            db = health.database
            db_status = db.get("status", "ERROR")
            if db_status == "OK":
                st.success("Banco OK")
            else:
                st.error(f"Banco: {db_status}")

        if db.get("existe"):
            col_db1, col_db2, col_db3, col_db4 = st.columns(4)
            with col_db1:
                st.metric("Tamanho", f"{db.get('tamanho_kb', 0):.1f} KB")
            with col_db2:
                st.metric("Integridade", db.get("integridade", "N/A"))
            with col_db3:
                st.metric("Tabelas", db.get("quantidade_tabelas", 0))
            with col_db4:
                st.metric("Journal", db.get("journal_mode", "N/A"))
        else:
            st.error("❌ Banco crm.db não encontrado")

        st.divider()

        # ── Configuração ──
        col_c1, col_c2 = st.columns([1, 3])
        with col_c1:
            st.markdown("#### ⚙️ .env")
        with col_c2:
            env = health.environment
            env_status = env.get("status", "ERROR")
            if env_status == "OK":
                st.success("Configuração OK")
            elif env_status == "WARNING":
                st.warning(f"Variáveis pendentes: {', '.join(env.get('faltantes', []))}")
            else:
                st.error("Arquivo .env não encontrado")

        variaveis = env.get("variaveis", {})
        if variaveis:
            cols_env = st.columns(len(variaveis))
            for idx, (var_nome, var_info) in enumerate(variaveis.items()):
                with cols_env[idx]:
                    configurada = var_info.get("configurada", False)
                    icone = "✅" if configurada else "⚠️"
                    valor = var_info.get("valor") or var_info.get("valor_oculto", "?")
                    st.metric(
                        f"{icone} {var_nome}",
                        valor if len(valor) <= 20 else valor[:20] + "...",
                    )

        st.divider()

        # ── Arquivos ──
        col_a1, col_a2 = st.columns([1, 3])
        with col_a1:
            st.markdown("#### 📄 Arquivos")
        with col_a2:
            files = health.files
            total = f"{files.get('total_presentes', 0)}/{files.get('total_esperados', 0)}"
            if files.get("status") == "OK":
                st.success(f"Arquivos essenciais: {total}")
            else:
                st.warning(f"Arquivos essenciais: {total} (faltam: {', '.join(files.get('faltantes', []))})")

        arquivos = files.get("arquivos", {})
        if arquivos:
            cols_arq = st.columns(3)
            for idx, (nome_arq, presente) in enumerate(arquivos.items()):
                with cols_arq[idx % 3]:
                    icone = "✔️" if presente else "❌"
                    st.markdown(f"{icone} {nome_arq}")

        st.divider()

        # ── Versão ──
        col_v1, col_v2 = st.columns([1, 3])
        with col_v1:
            st.markdown("#### 🏷️ Versão")
        with col_v2:
            st.info(health.version)

        # ── Avisos ──
        if health.warnings:
            st.divider()
            st.warning("#### ⚠️ Avisos")
            for w in health.warnings:
                st.markdown(f"- {w}")

        # ── Erros ──
        if health.errors:
            st.divider()
            st.error("#### ❌ Erros")
            for e in health.errors:
                st.markdown(f"- {e}")

        # ── Relatório completo (expansível) ──
        st.divider()
        with st.expander("📋 Ver Relatório Completo (texto)"):
            relatorio = installation_report()
            st.code(relatorio, language=None)

    st.divider()
    st.caption(
        "Estas informações são gerenciadas exclusivamente pelo módulo "
        "`services/version.py` — a fonte única oficial da versão do CRM.\n\n"
        "Health Check gerenciado por `services/deploy_manager.py`."
    )

# =====================================================
# BOTÃO SALVAR CONFIGURAÇÕES
# =====================================================

if st.button("💾 Salvar Configurações"):

    params = {}

    for classe in ["A", "B", "C", "D"]:
        for prefixo in ["whats_", "email_", "ligacao_", "visita_"]:
            chave = f"{prefixo}{classe}"
            if chave in st.session_state:
                params[chave] = st.session_state[chave]

    for chave in [
        "fat_a", "fat_b", "fat_c",
        "os_a", "os_b", "os_c",
        "fat_qtd_a", "fat_qtd_b", "fat_qtd_c",
        "alerta_visita", "alerta_contato"
    ]:
        if chave in st.session_state:
            params[chave] = st.session_state[chave]

    salvar_configs_relacionamento(params)

    # v1.6.10 — salvar parâmetros operacionais
    for chave_oper in [
        "envio_proposta", "followup_1", "followup_2", "followup_3",
        "proposta_esquecida", "expedicao", "feedback_cliente"
    ]:
        if chave_oper in st.session_state:
            set_config(chave_oper, str(st.session_state[chave_oper]))

    st.success("✅ Configurações salvas com sucesso!")
