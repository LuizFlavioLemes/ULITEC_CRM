"""
Relatório IA — ULITEC CRM v1.7.0
Geração de relatórios técnicos padronizados com IA.
Provider agnóstico: usa ia_client (Groq por default, Gemini/OpenAI como fallback).
"""

import streamlit as st

from auth import sidebar_usuario
from permissions import verificar_acesso_pagina

verificar_acesso_pagina()
sidebar_usuario()

st.set_page_config(page_title="Relatório IA", layout="wide")
st.title("🤖 Relatório IA")
st.caption(
    "Gere relatórios técnicos no padrão ULITEC com assistência de IA. "
    "Descreva o serviço técnico e a IA estrutura no formato: Sintoma → Causa → Solução → Observações."
)

# ── Campos opcionais ──
col1, col2, col3 = st.columns(3)
with col1:
    cliente = st.text_input("👤 Cliente (opcional)", placeholder="Razão social do cliente")
    equipamento = st.text_input("🔧 Equipamento (opcional)", placeholder="Ex: Servomotor HF-KP73")
with col2:
    numero_os = st.text_input("📋 OS (opcional)", placeholder="Número da OS")
    marca = st.text_input("🏷️ Marca (opcional)", placeholder="Ex: Mitsubishi, Siemens, Fanuc")
with col3:
    serial = st.text_input("🔢 Serial (opcional)", placeholder="Número de série")
    modelo = st.text_input("📐 Modelo (opcional)", placeholder="Ex: HF-KP73, 6SC6500")

# ── Campo obrigatório ──
descricao_tecnica = st.text_area(
    "📝 Descrição Técnica *",
    height=180,
    placeholder=(
        "Exemplo:\n"
        "alarme z55 fcua-dx111 sem comunicação rs422 ci u12 danificado\n\n"
        "Ou uma descrição mais detalhada:\n"
        "Equipamento apresentava alarme Z55. Não comunicava com FCU8-DX837. "
        "Circuito de comunicação serial RS422 avariado. CI U12 com fuga térmica. "
        "Substituído CI e capacitores da fonte local."
    ),
    help="Campo obrigatório. Descreva o problema e o serviço realizado de forma livre. Mínimo de 10 caracteres.",
)

# ── Campos opcionais adicionais ──
with st.expander("➕ Campos opcionais adicionais"):
    col_a, col_b = st.columns(2)
    with col_a:
        componentes_substituidos = st.text_area(
            "Componentes substituídos",
            height=100,
            placeholder="CI U12 - driver RS422\nCapacitores eletrolíticos 47uF/25V (2 unidades)",
        )
    with col_b:
        observacoes_adicionais = st.text_area(
            "Observações do operador",
            height=100,
            placeholder="Cliente reportou queda de energia antes da falha.\nEquipamento com 8 anos de uso.",
        )

    modo_orcamento = st.checkbox(
        "🔨 Modo orçamento (serviço futuro)",
        help="Marque se este relatório é para um orçamento (serviço ainda não realizado).",
    )

st.markdown("---")

# ── Botão Gerar ──
if st.button("🚀 GERAR RELATÓRIO", type="primary", width="stretch"):
    if not descricao_tecnica.strip():
        st.error("❌ A descrição técnica é obrigatória.")
    elif len(descricao_tecnica.strip()) < 10:
        st.error("❌ A descrição técnica deve ter pelo menos 10 caracteres.")
    else:
        with st.spinner("🔄 Gerando relatório no padrão ULITEC..."):
            try:
                from services.ia.prompt_builder import montar_contexto_relatorio_tecnico
                from services.ia.relatorio_ulitec import PROMPT_SISTEMA_ULITEC
                from services.ia.engine import gerar_relatorio_tecnico
                from services.ia.ia_client import _obter_config

                # ── Verifica qual provider está ativo antes de prosseguir ──
                config_atual = _obter_config()
                provider_ativo = config_atual.get("provider", "desconhecido")
                modelo_ativo = config_atual.get("modelo", "desconhecido")

                st.caption(
                    f"Provider: **{provider_ativo.upper()}** | "
                    f"Modelo: `{modelo_ativo}`"
                )

                prompt_usuario = montar_contexto_relatorio_tecnico(
                    descricao_tecnica=descricao_tecnica.strip(),
                    cliente=cliente.strip(),
                    numero_os=numero_os.strip(),
                    equipamento=equipamento.strip(),
                    marca=marca.strip(),
                    modelo=modelo.strip(),
                    serial=serial.strip(),
                    componentes_substituidos=componentes_substituidos.strip(),
                    observacoes=observacoes_adicionais.strip(),
                    modo_orcamento=modo_orcamento,
                )

                resultado = gerar_relatorio_tecnico(
                    prompt_sistema=PROMPT_SISTEMA_ULITEC,
                    prompt_usuario=prompt_usuario,
                )

                if resultado["sucesso"]:
                    st.markdown("---")
                    st.subheader("✅ RELATÓRIO GERADO")

                    st.markdown(resultado["conteudo"])

                    with st.expander("📊 Detalhes da geração"):
                        col_t1, col_t2, col_t3, col_t4 = st.columns(4)
                        col_t1.metric("Tokens (entrada)", resultado.get("prompt_tokens", 0))
                        col_t2.metric("Tokens (saída)", resultado.get("completion_tokens", 0))
                        col_t3.metric("Custo R$", f"{resultado.get('custo', 0):.6f}")
                        col_t4.metric("Tempo (s)", resultado.get("tempo_execucao", 0))

                    st.button(
                        "📋 COPIAR RELATÓRIO",
                        on_click=lambda: st.write("Relatório copiado!"),
                        key="btn_copiar_relatorio",
                        width="stretch",
                    )

                    st.info(
                        "💡 Selecione todo o texto acima (Ctrl+A), copie (Ctrl+C) "
                        "e cole no seu editor de texto ou e-mail."
                    )
                else:
                    erro = resultado.get("erro", "Erro desconhecido.")
                    erro_str = str(erro)

                    st.error(f"❌ Erro ao gerar relatório ({provider_ativo.upper()})")

                    with st.expander("📋 Detalhes do erro", expanded=True):
                        st.code(erro_str, language="text")

                    # Diagnóstico específico para o provider ativo
                    if provider_ativo == "groq":
                        if "401" in erro_str or "unauthorized" in erro_str.lower() or "invalid" in erro_str.lower():
                            st.warning(
                                "🔑 **Chave da API Groq inválida!**\n\n"
                                "**Solução:**\n"
                                "1. Obtenha uma chave gratuita em: https://console.groq.com/keys\n"
                                "2. Configure `GROQ_API_KEY` no arquivo `.env`\n"
                                "3. O modelo `llama-3.3-70b-versatile", "llama-3.1-8b-instant` é gratuito."
                            )
                            st.button(
                                "🔑 ABRIR CONSOLE GROQ",
                                type="secondary",
                                width="stretch",
                                key="btn_groq_console",
                                on_click=lambda: st.markdown(
                                    "<meta http-equiv='refresh' content='0;url=https://console.groq.com/keys'>",
                                    unsafe_allow_html=True,
                                ),
                            )
                        elif "429" in erro_str or "quota" in erro_str.lower() or "rate limit" in erro_str.lower():
                            st.warning("🚫 **Limite de taxa Groq excedido.** Aguarde e tente novamente.")
                        elif "timeout" in erro_str.lower():
                            st.warning("⏱️ **Tempo limite excedido.** Tente novamente.")
                        else:
                            st.warning(
                                f"🔧 **Erro inesperado no Groq.**\n\n"
                                f"Erro original: {erro_str}\n\n"
                                "Verificações:\n"
                                "1. O pacote `groq` está instalado? (pip install groq)\n"
                                "2. A GROQ_API_KEY é válida?\n"
                                "3. O GROQ_MODEL é válido?"
                            )
                    elif provider_ativo == "gemini":
                        st.warning(
                            "ℹ️ O provider atual é **Gemini**.\n\n"
                            "Se deseja usar Groq, altere `IA_PROVIDER=groq` no `.env`."
                        )
                    elif provider_ativo == "openai":
                        st.warning(
                            "ℹ️ O provider atual é **OpenAI**.\n\n"
                            "Se deseja usar Groq, altere `IA_PROVIDER=groq` no `.env`."
                        )
                    else:
                        st.warning(f"🔧 **Erro no provider '{provider_ativo}'.**\n\n{erro_str}")

            except Exception as e:
                st.error(f"❌ Erro inesperado: {str(e)}")
                st.warning(
                    "Verifique se o pacote do provider configurado está instalado "
                    "e se o .env está configurado corretamente."
                )
else:
    st.info(
        "Preencha a descrição técnica e clique em 'GERAR RELATÓRIO' para gerar "
        "o relatório técnico no padrão ULITEC (Sintoma → Causa → Solução → Observações)."
    )

    with st.expander("📖 Como funciona"):
        st.markdown("""
        ### ✍️ Preenchimento mínimo

        Basta descrever o serviço técnico de forma livre. Exemplo:

        ```
        alarme z55 fcua-dx111 sem comunicação rs422 ci u12 danificado
        ```

        ### 🤖 O que a IA faz

        1. **Estrutura** o relatório em: SINTOMA → CAUSA → SOLUÇÃO → OBSERVAÇÕES
        2. **Padroniza** a redação no padrão técnico ULITEC
        3. **Agrega valor** com processos como higienização ultrassônica e testes funcionais
        4. **Mantém** o tom técnico-formal da engenharia industrial

        ### ⚙️ Provider

        O provider é definido no arquivo `.env`:
        - `IA_PROVIDER=groq` (default) — usa Groq (llama-3.3-70b-versatile", "llama-3.1-8b-instant, gratuito e rápido)
        - `IA_PROVIDER=gemini` — usa Google Gemini (fallback)
        - `IA_PROVIDER=openai` — usa OpenAI (fallback)

        ### 📌 Dicas

        - Quanto mais detalhes, melhor o relatório
        - Informe componentes substituídos para enriquecer a SOLUÇÃO
        - Use o modo orçamento para serviços futuros
        - Todos os campos (exceto descrição técnica) são opcionais
        """)