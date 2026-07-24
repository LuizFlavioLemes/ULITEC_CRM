"""
╔══════════════════════════════════════════════════════════════════════════════╗
║            passenger_wsgi.py — cPanel Passenger + Streamlit Proxy          ║
║                    ULITEC CRM Industrial — Versão de Diagnóstico            ║
╚══════════════════════════════════════════════════════════════════════════════╝

MOTIVAÇÃO ARQUITETURAL:
=======================

O Passenger (Phusion Passenger / LiteSpeed Passenger) é um servidor de
aplicação WSGI. Ele segue o modelo:

    HTTP Request → Passenger → application(environ, start_response) → Response

O Streamlit NÃO é uma aplicação WSGI. Ele é construído sobre o Tornado,
um servidor web assíncrono que opera em seu próprio event loop. O modelo
do Streamlit é:

    Terminal → streamlit run app.py → Tornado escuta em :8501 → Browser conecta

Esses dois modelos são FUNDAMENTALMENTE INCOMPATÍVEIS. Não é possível
"importar" uma aplicação Streamlit dentro de um contexto WSGI e esperar
que ela funcione, porque:

1. O Streamlit espera ser o ponto de entrada principal (main process)
2. st.set_page_config() depende do runtime Tornado inicializado
3. st.session_state, st.button(), st.switch_page() exigem o event loop
4. O protocolo WebSocket (usado pelo Streamlit para reatividade) não
   existe no modelo WSGI tradicional

ESTRATÉGIA ADOTADA (PROXY REVERSO VIA SUBPROCESSO):
====================================================

    ┌──────────┐     ┌───────────┐     ┌──────────────────┐
    │ Navegador │────▶│  Apache   │────▶│   Passenger      │
    └──────────┘     └───────────┘     └────────┬─────────┘
                                                │ WSGI
                                         ┌──────▼──────────┐
                                         │ passenger_wsgi  │
                                         │  (proxy reverso) │
                                         └──────┬──────────┘
                                                │ HTTP para 127.0.0.1:8501
                                         ┌──────▼──────────┐
                                         │ Streamlit        │
                                         │ (Tornado :8501)  │
                                         │  rodando app.py  │
                                         └──────────────────┘

Passo a passo:
1. Passenger carrega este módulo (passenger_wsgi.py)
2. Bootstrap é executado (.env, SQLite WAL, schema, monkey-patch)
3. Na primeira requisição HTTP, um subprocesso é criado:
   python -m streamlit run app.py --server.port 8501 --server.headless true
4. Aguardamos até 30s pelo health check (HTTP GET /)
5. Requisições WSGI são convertidas para HTTP e encaminhadas ao Streamlit
6. Respostas do Streamlit são devolvidas ao Passenger → Apache → Navegador

LIMITAÇÕES CONHECIDAS DESTA ABORDAGEM:
=======================================

1. WEBSOCKET: O proxy HTTP simples não suporta WebSocket. O Streamlit usa
   WebSocket para comunicação em tempo real (st.button, st.selectbox, etc.).
   Sem WebSocket, a interface pode carregar estaticamente mas elementos
   interativos podem não funcionar. Isso é uma limitação fundamental do
   modelo WSGI síncrono.

2. PORTAS: O subprocesso ocupa uma porta (8501). Se o cPanel bloquear
   binding de portas pelo usuário, esta estratégia falhará.

3. SUBPROCESSO: Alguns ambientes cPanel podem restringir subprocess.Popen
   por políticas de segurança (suexec, CageFS, etc.).

4. GERENCIAMENTO DE PROCESSO: O Passenger pode matar o subprocesso quando
   detectar inatividade ou quando fizer restart da aplicação.

OBJETIVO DESTE ARQUIVO:
========================

Determinar, com EVIDÊNCIAS OBJETIVAS registradas em logs, se o ambiente
cPanel específico do ULITEC CRM suporta esta arquitetura ou se há
limitações técnicas intransponíveis.

Toda falha será registrada com:
- Exceção completa + traceback
- stdout e stderr do subprocesso
- Último comando executado
- Estado do ambiente (Python, PATH, diretório, portas)

NENHUMA INFORMAÇÃO DE ERRO SERÁ OCULTADA.

Autor: Engenharia ULITEC
Versão: 3.0 — Diagnóstico Definitivo
Data: 2026-07-03
"""

# ══════════════════════════════════════════════════════════════════════════════
# IMPORTS — Apenas biblioteca padrão + logging
# ══════════════════════════════════════════════════════════════════════════════

import os
import sys
import time
import json
import socket
import signal
import atexit
import platform
import threading
import subprocess
import traceback as tb_module
from pathlib import Path
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTES DE CONFIGURAÇÃO
# ══════════════════════════════════════════════════════════════════════════════

# --- Streamlit ---
STREAMLIT_PORT = int(os.environ.get("STREAMLIT_PORT", "8501"))
STREAMLIT_HOST = "127.0.0.1"
STREAMLIT_BASE_URL = f"http://{STREAMLIT_HOST}:{STREAMLIT_PORT}"

# --- Timeouts ---
HEALTH_CHECK_TIMEOUT_SEC = 30      # Tempo máximo aguardando Streamlit subir
HEALTH_CHECK_INTERVAL_SEC = 2      # Intervalo entre tentativas de health check
HEALTH_CHECK_RETRIES = HEALTH_CHECK_TIMEOUT_SEC // HEALTH_CHECK_INTERVAL_SEC
PROXY_REQUEST_TIMEOUT_SEC = 60     # Timeout para requisições proxy

# --- Headers HTTP que NÃO devem ser repassados (hop-by-hop) ---
HOP_BY_HOP_HEADERS = {
    "connection", "keep-alive", "proxy-authenticate",
    "proxy-authorization", "te", "trailers",
    "transfer-encoding", "upgrade",
}

# ══════════════════════════════════════════════════════════════════════════════
# SISTEMA DE LOG ESTRUTURADO
# ══════════════════════════════════════════════════════════════════════════════
#
# O log é escrito em stderr (capturado pelo Passenger em passenger.log e
# error.log). Cada evento é prefixado com timestamp ISO 8601, nível e
# marcador [PASSENGER_WSGI] para fácil filtragem.
#
# Além do log textual, mantemos um buffer em memória (_diagnostic_log) que
# acumula TODOS os eventos. Esse buffer é exibido na página de erro HTML
# para diagnóstico remoto (sem acesso SSH).
# ══════════════════════════════════════════════════════════════════════════════

_diagnostic_log = []  # Lista de dicts: {timestamp, level, message}
_diagnostic_lock = threading.Lock()

def _diag_log(level: str, message: str):
    """
    Registra evento de diagnóstico UNIFICADO.

    - Escreve em stderr (aparece nos logs do Passenger/cPanel)
    - Acumula em _diagnostic_log (aparece na página de erro HTML)
    - Thread-safe (lock)
    """
    timestamp = datetime.now().isoformat()
    entry = {
        "timestamp": timestamp,
        "level": level,
        "message": message,
    }
    with _diagnostic_lock:
        _diagnostic_log.append(entry)

    # Formatar para stderr
    line = f"[PASSENGER_WSGI] {timestamp} {level:5s} {message}"
    print(line, file=sys.stderr, flush=True)

def _diag_info(msg: str):
    _diag_log("INFO", msg)

def _diag_warn(msg: str):
    _diag_log("WARN", msg)

def _diag_error(msg: str):
    _diag_log("ERROR", msg)

def _diag_debug(msg: str):
    _diag_log("DEBUG", msg)

# ══════════════════════════════════════════════════════════════════════════════
# BLOCO 1: DIAGNÓSTICO DO AMBIENTE (EXECUTADO NO IMPORT)
# ══════════════════════════════════════════════════════════════════════════════
#
# ANTES de fazer qualquer coisa, coletamos informações detalhadas do
# ambiente. Isso é crucial para diagnosticar problemas sem acesso SSH.
# ══════════════════════════════════════════════════════════════════════════════

_diag_info("=" * 70)
_diag_info("INICIALIZAÇÃO — Coleta de ambiente")
_diag_info("=" * 70)

# 1.1 — Informações do Python
_diag_info(f"Timestamp UTC: {datetime.now(timezone.utc).isoformat()}")
_diag_info(f"Python version: {sys.version}")
_diag_info(f"Python executable: {sys.executable}")
_diag_info(f"Python implementation: {platform.python_implementation()}")
_diag_info(f"Platform: {platform.platform()}")
_diag_info(f"Architecture: {platform.machine()}")
_diag_info(f"Hostname: {platform.node()}")

# 1.2 — Diretório da aplicação
APP_DIR = os.path.dirname(os.path.abspath(__file__))
_diag_info(f"APP_DIR (este arquivo): {APP_DIR}")

# 1.3 — Configurar sys.path e working directory
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)
    _diag_info(f"APP_DIR adicionado ao sys.path (posição 0)")
else:
    _diag_info(f"APP_DIR já está no sys.path")

os.chdir(APP_DIR)
_diag_info(f"os.getcwd(): {os.getcwd()}")

# 1.4 — sys.path completo
_diag_info("sys.path completo:")
for i, p in enumerate(sys.path):
    _diag_info(f"  sys.path[{i}] = {p}")

# 1.5 — Variáveis de ambiente relevantes
_env_keys_of_interest = [
    "PATH", "HOME", "USER", "PYTHONPATH", "VIRTUAL_ENV",
    "STREAMLIT_PORT", "ULITEC_AMBIENTE", "PASSENGER_APP_ENV",
    "LANG", "LC_ALL", "TMPDIR", "TMP", "TEMP",
]
_diag_info("Variáveis de ambiente relevantes:")
for key in _env_keys_of_interest:
    val = os.environ.get(key, "(não definida)")
    if key in ("PATH",):
        _diag_info(f"  {key} = {val[:200]}...")  # Trunca PATH longo
    else:
        _diag_info(f"  {key} = {val}")

# 1.6 — Verificar se o módulo streamlit pode ser importado
try:
    import streamlit as _st_test
    _diag_info(f"Streamlit importado com sucesso. Versão: {_st_test.__version__}")
    _diag_info(f"Streamlit local: {getattr(_st_test, '__file__', 'desconhecido')}")
except ImportError as e:
    _diag_error(f"FALHA ao importar streamlit: {e}")
    _diag_error("Streamlit NÃO ESTÁ INSTALADO no ambiente Python do Passenger.")
    _STREAMLIT_AVAILABLE = False
else:
    _STREAMLIT_AVAILABLE = True

# 1.7 — Verificar conteúdo do diretório da aplicação
_diag_info("Conteúdo do diretório da aplicação:")
_app_root = Path(APP_DIR)
try:
    for item in sorted(_app_root.iterdir()):
        is_dir = "📁" if item.is_dir() else "📄"
        size = ""
        if item.is_file():
            try:
                size = f" ({item.stat().st_size} bytes)"
            except Exception:
                size = " (erro ao ler tamanho)"
        _diag_info(f"  {is_dir} {item.name}{size}")
except Exception as e:
    _diag_error(f"Erro ao listar diretório: {e}")

# 1.8 — Verificar se app.py existe
_app_py_path = _app_root / "app.py"
if _app_py_path.exists():
    _diag_info(f"app.py encontrado: {_app_py_path} ({_app_py_path.stat().st_size} bytes)")
else:
    _diag_error(f"app.py NÃO ENCONTRADO em {_app_py_path}")

# ══════════════════════════════════════════════════════════════════════════════
# BLOCO 2: BOOTSTRAP (SQLite, WAL, schema, monkey-patch)
# ══════════════════════════════════════════════════════════════════════════════
#
# O bootstrap é executado NO PROCESSO PAI (Passenger). Ele configura:
# - Carregamento do .env
# - Monkey-patch de .connect (força caminho absoluto)
# - Ativação de WAL + PRAGMAs
# - Criação de tabelas (CREATE IF NOT EXISTS)
# - Migrações de schema (ALTER TABLE defensivos)
# - Seeds de dados (unidades, tipos de produto, NCMs, configs)
#
# Isso é feito AQUI, e não no subprocesso, porque:
# - O monkey-patch precisa ser aplicado antes de qualquer import que use 
# - O schema precisa existir antes do subprocesso Streamlit iniciar
# - Se falhar, temos diagnóstico completo antes mesmo de tentar o Streamlit
# ══════════════════════════════════════════════════════════════════════════════

_bootstrap_error = None

_diag_info("---")
_diag_info("BLOCO 2: Executando bootstrap (utils.bootstrap)")

try:
    import utils.bootstrap  # noqa: F401 — executa _init_database() no import
    _diag_info("Bootstrap executado com SUCESSO.")
except Exception as e:
    _bootstrap_error = f"BOOTSTRAP FALHOU: {e}\n\n{tb_module.format_exc()}"
    _diag_error(_bootstrap_error)
    _diag_error(
        "O CRM NÃO PODE funcionar sem o bootstrap. "
        "Verifique o erro acima."
    )

# ══════════════════════════════════════════════════════════════════════════════
# BLOCO 3: VERIFICAÇÃO DE CONECTIVIDADE DE REDE LOCAL
# ══════════════════════════════════════════════════════════════════════════════
#
# Antes de tentar iniciar o Streamlit, verificamos se conseguimos fazer
# bind na porta 8501 e se 127.0.0.1 é acessível. Isso detecta:
# - Porta já ocupada por outro processo
# - Bloqueio de firewall local (iptables, nftables)
# - Restrições do cPanel/CageFS a sockets
# ══════════════════════════════════════════════════════════════════════════════

_diag_info("---")
_diag_info("BLOCO 3: Verificação de conectividade local")

def _check_port_availability(host: str, port: int) -> dict:
    """
    Verifica se uma porta está disponível para bind.

    Retorna dict com:
        available: bool
        can_bind: bool
        already_in_use: bool
        error: str ou None
    """
    result = {
        "available": False,
        "can_bind": False,
        "already_in_use": False,
        "error": None,
    }

    # Teste 1: Verificar se a porta já está em uso (connect)
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        connect_result = sock.connect_ex((host, port))
        sock.close()
        if connect_result == 0:
            result["already_in_use"] = True
            _diag_warn(f"Porta {host}:{port} já está em uso (connect_ex retornou 0).")
        else:
            _diag_info(f"Porta {host}:{port} parece livre (connect_ex retornou {connect_result}).")
    except Exception as e:
        _diag_error(f"Erro ao verificar porta {host}:{port} (connect): {e}")

    # Teste 2: Tentar fazer bind efetivamente
    try:
        test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        test_sock.bind((host, port))
        test_sock.listen(1)
        result["can_bind"] = True
        _diag_info(f"Bind bem-sucedido em {host}:{port}. (socket de teste fechado em seguida)")
        test_sock.close()
    except PermissionError as e:
        result["error"] = f"PERMISSION_DENIED: {e}"
        _diag_error(f"Permissão negada ao fazer bind em {host}:{port}: {e}")
        _diag_error("Isso indica que o cPanel/CageFS restringe abertura de portas.")
    except OSError as e:
        result["error"] = f"OS_ERROR: {e}"
        _diag_error(f"Erro de SO ao fazer bind em {host}:{port}: {e}")

    result["available"] = result["can_bind"] or result["already_in_use"]
    return result

_port_check = _check_port_availability(STREAMLIT_HOST, STREAMLIT_PORT)

# ══════════════════════════════════════════════════════════════════════════════
# BLOCO 4: GERENCIAMENTO DO SUBPROCESSO STREAMLIT
# ══════════════════════════════════════════════════════════════════════════════
#
# Estrutura:
#   _streamlit_process: instância de subprocess.Popen ou None
#   _streamlit_ready: bool indicando se health check passou
#   _streamlit_startup_error: dict com detalhes do erro de inicialização
#   _startup_lock: mutex para evitar múltiplos inícios simultâneos
#
# O subprocesso é iniciado sob demanda (lazy initialization) na primeira
# requisição HTTP. Isso evita timeouts durante o carregamento do Passenger.
# ══════════════════════════════════════════════════════════════════════════════

_streamlit_process = None
_streamlit_ready = False
_streamlit_startup_error = None  # dict com diagnóstico detalhado de falha
_startup_lock = threading.Lock()

# Buffers para capturar stdout/stderr completos do subprocesso
_streamlit_stdout_buffer = []
_streamlit_stderr_buffer = []

def _collect_subprocess_output(process):
    """
    Coleta stdout e stderr do subprocesso de forma não-bloqueante.

    É chamada durante o health check para capturar mensagens de erro
    que o Streamlit emitiu durante a inicialização.
    """
    try:
        if process.stdout:
            # Lê sem bloquear (modo não-bloqueante requer configuração
            # adicional; usamos read1 em alguns sistemas)
            pass
    except Exception:
        pass

def _read_available(pipe, buffer_list):
    """
    Tenta ler dados disponíveis de um pipe sem bloquear.
    Acumula no buffer_list.
    """
    try:
        import select
        if pipe and select.select([pipe], [], [], 0)[0]:
            data = pipe.read1(8192) if hasattr(pipe, 'read1') else pipe.read(8192)
            if data:
                text = data.decode("utf-8", errors="replace")
                buffer_list.append(text)
                return text
    except Exception:
        pass
    return ""

def _is_process_alive(proc) -> bool:
    """
    Verifica se um subprocesso ainda está em execução.
    Retorna True se o processo está vivo (poll() retorna None).
    Retorna False se o processo já terminou ou se proc é None.
    """
    if proc is None:
        return False
    return proc.poll() is None

def _health_check_http() -> bool:
    """
    Testa se o Streamlit está respondendo via HTTP na porta configurada.

    Retorna True se receber qualquer resposta HTTP (2xx, 3xx, 4xx),
    indicando que o servidor Tornado está aceitando conexões.
    Retorna False se a conexão for recusada ou der timeout.
    """
    try:
        req = Request(
            f"{STREAMLIT_BASE_URL}/_stcore/health",
            headers={"User-Agent": "Passenger-HealthCheck/3.0"},
        )
        resp = urlopen(req, timeout=5)
        _diag_debug(f"Health check: /_stcore/health respondeu HTTP {resp.status}")
        return True
    except HTTPError as e:
        _diag_debug(f"Health check: /_stcore/health HTTP {e.code}")
        return e.code < 500
    except URLError:
        # Fallback: tenta a raiz /
        try:
            req2 = Request(
                f"{STREAMLIT_BASE_URL}/",
                headers={"User-Agent": "Passenger-HealthCheck/3.0"},
            )
            urlopen(req2, timeout=3)
            _diag_debug("Health check: / respondeu (fallback)")
            return True
        except Exception:
            return False
    except Exception:
        return False

def _start_streamlit() -> bool:
    """
    Inicia o Streamlit como subprocesso, com controle de concorrência.

    REGRAS DE GERENCIAMENTO (CORRIGIDAS):
    ======================================

    1. LOCK GLOBAL: Todo o bloco de inicialização é protegido por
       _startup_lock. Apenas UMA thread por vez executa este código.
       Threads concorrentes aguardam o lock e depois encontram
       _streamlit_ready = True (se a primeira teve sucesso).

    2. PROCESSO EXISTENTE VIVO: Se _streamlit_process existe e
       poll() is None, fazemos um health check HTTP rápido (5s).
       Se responder → _streamlit_ready = True e retorna.
       Se NÃO responder → mata o processo antigo e cria um novo.
       ISSO EVITA A CRIAÇÃO DE MÚLTIPLOS PIDs.

    3. PROCESSO EXISTENTE MORTO: Se poll() não é None, coleta
       stdout/stderr, descarta o processo e cria um novo.

    4. A flag _streamlit_ready só é setada APÓS o health check
       confirmar que o Streamlit está respondendo.

    5. Se a criação falhar (exceção), _streamlit_ready NÃO é setada,
       _streamlit_process é definido como None, e o erro é registrado
       em _streamlit_startup_error.
    """
    global _streamlit_process, _streamlit_ready, _streamlit_startup_error

    with _startup_lock:
        # ── Já está pronto? Retorna imediatamente ──
        if _streamlit_ready:
            _diag_debug("_start_streamlit: já estava pronto, retornando.")
            return True

        _diag_info("---")
        _diag_info("BLOCO 4: Iniciando subprocesso Streamlit")

        # ── Verificar pré-condições ──
        if not _STREAMLIT_AVAILABLE:
            _streamlit_startup_error = {
                "fase": "pre_check",
                "motivo": "streamlit_nao_instalado",
                "detalhe": (
                    "O módulo 'streamlit' não pôde ser importado. "
                    "Verifique se está instalado no virtualenv do cPanel."
                ),
            }
            _diag_error("Streamlit não está instalado. Abortando.")
            return False

        if not _app_py_path.exists():
            _streamlit_startup_error = {
                "fase": "pre_check",
                "motivo": "app_py_nao_encontrado",
                "detalhe": f"app.py não encontrado em {_app_py_path}",
            }
            _diag_error("app.py não encontrado. Abortando.")
            return False

        if _bootstrap_error is not None:
            _streamlit_startup_error = {
                "fase": "pre_check",
                "motivo": "bootstrap_falhou",
                "detalhe": _bootstrap_error,
            }
            _diag_error("Bootstrap falhou. Abortando.")
            return False

        # ═══════════════════════════════════════════════════════════
        # VERIFICAÇÃO DE PROCESSO EXISTENTE (CORRIGIDA v2)
        # ═══════════════════════════════════════════════════════════
        #
        # ESTRATÉGIA EM DUAS CAMADAS:
        #
        # Camada 1 — PORTA (fonte da verdade):
        #   A porta 8501 é a verdade absoluta. Independentemente de
        #   _streamlit_process ser None (reinício do Passenger, processo
        #   órfão), se a porta estiver respondendo HTTP, REUTILIZAMOS.
        #
        # Camada 2 — PROCESSO (otimização):
        #   Se _streamlit_process existe, verificamos se está vivo.
        #   Se estiver vivo E a porta responder → reutiliza.
        #   Se estiver morto → limpa e continua.

        # ── Camada 1: Verificar a PORTA primeiro ──
        # A porta é a fonte da verdade — mesmo que _streamlit_process seja
        # None (ex: Passenger reiniciou, processo órfão), se houver um
        # Streamlit respondendo na porta, devemos reutilizá-lo.
        _port_is_listening = False
        try:
            test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_sock.settimeout(2)
            if test_sock.connect_ex((STREAMLIT_HOST, STREAMLIT_PORT)) == 0:
                _port_is_listening = True
                _diag_info(
                    f"Porta {STREAMLIT_HOST}:{STREAMLIT_PORT} está em uso "
                    f"(alguém está escutando)."
                )
            else:
                _diag_info(
                    f"Porta {STREAMLIT_HOST}:{STREAMLIT_PORT} está LIVRE."
                )
            test_sock.close()
        except Exception as e:
            _diag_warn(f"Erro ao verificar porta: {e}")

        if _port_is_listening:
            # Alguém está escutando na porta — verificar se é Streamlit
            _diag_info("Porta ocupada. Testando se responde HTTP (Streamlit)...")
            if _health_check_http():
                _diag_info(
                    "Streamlit respondendo na porta. Reutilizando instância "
                    "existente (possível processo órfão de execução anterior)."
                )
                _streamlit_ready = True
                _streamlit_startup_error = None
                # Não temos o objeto Popen (processo órfão), mas isso é OK:
                # o proxy só precisa que a porta responda.
                # _streamlit_process permanece None (não controlamos este
                # processo), mas _streamlit_ready = True evita criar outro.
                return True
            else:
                # Porta ocupada, mas NÃO responde HTTP.
                # Pode ser: outro serviço, processo zumbi, ou Streamlit
                # que ainda está subindo (ainda não respondeu).
                # NÃO criamos outro processo — isso só pioraria.
                _diag_error(
                    f"Porta {STREAMLIT_HOST}:{STREAMLIT_PORT} está ocupada "
                    f"mas NÃO responde a HTTP. Provável processo zumbi ou "
                    f"serviço desconhecido ocupando a porta."
                )
                _diag_error(
                    "ABORTANDO inicialização para não criar múltiplos "
                    "processos conflitantes."
                )
                _streamlit_startup_error = {
                    "fase": "porta_ocupada_desconhecida",
                    "motivo": "porta_ocupada_sem_resposta_http",
                    "detalhe": (
                        f"A porta {STREAMLIT_HOST}:{STREAMLIT_PORT} está "
                        f"ocupada por um processo que NÃO responde a HTTP. "
                        f"Não é possível determinar se é um Streamlit válido. "
                        f"SUGESTÃO: acesse o cPanel → Setup Python App → "
                        f"Restart, ou aguarde o processo antigo expirar. "
                        f"Se o problema persistir, mate manualmente o processo "
                        f"na porta {STREAMLIT_PORT} via SSH ou Terminal do cPanel."
                    ),
                }
                return False

        # ── Camada 2: Verificar _streamlit_process (se existir) ──
        if _streamlit_process is not None:
            if _is_process_alive(_streamlit_process):
                pid_existente = _streamlit_process.pid
                _diag_info(
                    f"Subprocesso Streamlit existe (PID {pid_existente}) "
                    f"mas porta está livre — processo pode estar em "
                    f"inicialização ou sem bind. Mantendo referência."
                )
                # Processo existe, está vivo, mas porta não responde.
                # Pode ser que ainda esteja iniciando. Vamos tentar
                # health check no loop abaixo (se chegarmos lá).
            else:
                exit_code = _streamlit_process.poll()
                _diag_warn(
                    f"Subprocesso Streamlit anterior morreu "
                    f"(código {exit_code})."
                )
                _flush_subprocess_output()
                _streamlit_process = None
                _streamlit_ready = False

        # ═══════════════════════════════════════════════════════════
        # CRIAR NOVO SUBPROCESSO (apenas se porta está LIVRE)
        # ═══════════════════════════════════════════════════════════
        #
        # Só chegamos aqui se:
        # - A porta NÃO está ocupada OU
        # - _streamlit_process existe e está vivo (reutilizaremos no
        #   health check loop)

        # Construir comando (usado para logging/diagnóstico em ambos os caminhos)
        cmd = [
            sys.executable,
            "-m", "streamlit",
            "run", "app.py",
            "--server.port", str(STREAMLIT_PORT),
            "--server.headless", "true",
            "--server.address", STREAMLIT_HOST,
            "--server.enableCORS", "false",
            "--server.enableXsrfProtection", "false",
            "--browser.gatherUsageStats", "false",
            "--logger.level", "info",
            "--server.enableStaticServing", "true",
        ]

        # Se já temos um processo vivo, pular criação e ir direto
        # para o health check
        if _streamlit_process is not None and _is_process_alive(_streamlit_process):
            _diag_info(
                f"Reutilizando processo existente (PID {_streamlit_process.pid}). "
                f"Pulando criação de subprocesso."
            )
            pid = _streamlit_process.pid
        else:
            # Porta livre — criar novo subprocesso
            _diag_info("Porta livre. Criando novo subprocesso Streamlit...")

            # Limpar buffers de diagnóstico
            _streamlit_stdout_buffer.clear()
            _streamlit_stderr_buffer.clear()
            _streamlit_startup_error = None

            _diag_info(f"Comando: {' '.join(cmd)}")
            _diag_info(f"Working directory: {APP_DIR}")
            _diag_info(f"Python executable: {sys.executable}")

            subprocess_env = os.environ.copy()
            subprocess_env["STREAMLIT_SERVER_PORT"] = str(STREAMLIT_PORT)
            subprocess_env["STREAMLIT_SERVER_HEADLESS"] = "true"
            subprocess_env["STREAMLIT_SERVER_ADDRESS"] = STREAMLIT_HOST
            if "ULITEC_AMBIENTE" not in subprocess_env:
                subprocess_env["ULITEC_AMBIENTE"] = "CLOUD"

            # Criar subprocesso
            try:
                _streamlit_process = subprocess.Popen(
                    cmd,
                    cwd=APP_DIR,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=subprocess_env,
                )
                pid = _streamlit_process.pid
                _diag_info(f"Subprocesso Streamlit criado com PID: {pid}")
                _diag_info(f"PID {pid} — aguardando health check...")

            except FileNotFoundError as e:
                _streamlit_startup_error = {
                    "fase": "subprocess_creation",
                    "motivo": "executable_not_found",
                    "detalhe": f"Não foi possível executar '{sys.executable}'. Erro: {e}",
                    "traceback": tb_module.format_exc(),
                }
                _diag_error(f"FALHA FileNotFoundError: {e}")
                _streamlit_process = None
                return False

            except PermissionError as e:
                _streamlit_startup_error = {
                    "fase": "subprocess_creation",
                    "motivo": "permission_denied",
                    "detalhe": (
                        f"Permissão negada ao executar subprocesso. Erro: {e}\n"
                        f"O cPanel provavelmente BLOQUEIA subprocess.Popen."
                    ),
                    "traceback": tb_module.format_exc(),
                }
                _diag_error(f"FALHA PermissionError: {e} — cPanel BLOQUEIA subprocessos!")
                _streamlit_process = None
                return False

            except Exception as e:
                _streamlit_startup_error = {
                    "fase": "subprocess_creation",
                    "motivo": "unknown_error",
                    "detalhe": f"Erro inesperado: {e}",
                    "traceback": tb_module.format_exc(),
                }
                _diag_error(f"FALHA inesperada: {e}")
                _streamlit_process = None
                return False

        # ═══════════════════════════════════════════════════════════
        # HEALTH CHECK LOOP
        # ═══════════════════════════════════════════════════════════

        _diag_info(f"Iniciando health check (até {HEALTH_CHECK_TIMEOUT_SEC}s)...")
        health_start = time.time()

        for attempt in range(1, HEALTH_CHECK_RETRIES + 1):
            time.sleep(HEALTH_CHECK_INTERVAL_SEC)
            elapsed = time.time() - health_start

            # Verificar se o processo ainda está vivo
            if not _is_process_alive(_streamlit_process):
                exit_code = _streamlit_process.poll()
                _diag_error(
                    f"Streamlit morreu na tentativa {attempt}/{HEALTH_CHECK_RETRIES} "
                    f"(código {exit_code}, após {elapsed:.1f}s)"
                )

                stdout_text = ""
                stderr_text = ""
                try:
                    stdout_text = _streamlit_process.stdout.read().decode(
                        "utf-8", errors="replace"
                    )
                except Exception:
                    stdout_text = "(erro ao ler stdout)"
                try:
                    stderr_text = _streamlit_process.stderr.read().decode(
                        "utf-8", errors="replace"
                    )
                except Exception:
                    stderr_text = "(erro ao ler stderr)"

                _diag_error(f"STDOUT ({len(stdout_text)} chars):\n{stdout_text[-3000:]}")
                _diag_error(f"STDERR ({len(stderr_text)} chars):\n{stderr_text[-3000:]}")

                _streamlit_startup_error = {
                    "fase": "streamlit_morreu",
                    "pid": pid,
                    "exit_code": exit_code,
                    "tentativa": attempt,
                    "tempo_decorrido_s": elapsed,
                    "stdout": stdout_text,
                    "stderr": stderr_text,
                    "comando": " ".join(cmd),
                    "cwd": APP_DIR,
                }
                # NÃO setar _streamlit_ready
                return False

            # Health check HTTP
            if _health_check_http():
                _diag_info(
                    f"Health check OK! Tentativa {attempt}/{HEALTH_CHECK_RETRIES} "
                    f"— Streamlit respondendo após {elapsed:.1f}s"
                )
                _streamlit_ready = True
                _streamlit_startup_error = None
                return True

            _diag_debug(
                f"Health check tentativa {attempt}/{HEALTH_CHECK_RETRIES}: "
                f"ainda não responde"
            )

            # Coletar output disponível (não-bloqueante)
            _read_available(_streamlit_process.stdout, _streamlit_stdout_buffer)
            stderr_chunk = _read_available(
                _streamlit_process.stderr, _streamlit_stderr_buffer
            )
            if stderr_chunk:
                _diag_debug(f"Streamlit stderr parcial: {stderr_chunk[:300]}")

        # ── Timeout ──
        total_elapsed = time.time() - health_start
        _diag_error(
            f"TIMEOUT: Streamlit não respondeu em {total_elapsed:.1f}s "
            f"({HEALTH_CHECK_RETRIES} tentativas)"
        )

        # Coletar output acumulado
        stdout_final = "".join(_streamlit_stdout_buffer)
        stderr_final = "".join(_streamlit_stderr_buffer)
        try:
            more_stdout = _streamlit_process.stdout.read().decode(
                "utf-8", errors="replace"
            )
            stdout_final += more_stdout
        except Exception:
            pass
        try:
            more_stderr = _streamlit_process.stderr.read().decode(
                "utf-8", errors="replace"
            )
            stderr_final += more_stderr
        except Exception:
            pass

        _diag_error(f"STDOUT acumulado ({len(stdout_final)} chars):\n{stdout_final[-3000:]}")
        _diag_error(f"STDERR acumulado ({len(stderr_final)} chars):\n{stderr_final[-3000:]}")

        _streamlit_startup_error = {
            "fase": "timeout",
            "pid": pid,
            "tempo_decorrido_s": total_elapsed,
            "tentativas": HEALTH_CHECK_RETRIES,
            "stdout": stdout_final,
            "stderr": stderr_final,
            "comando": " ".join(cmd),
            "cwd": APP_DIR,
        }
        # NÃO setar _streamlit_ready
        return False

def _flush_subprocess_output():
    """
    Lê e descarta stdout/stderr pendentes do subprocesso morto.
    """
    global _streamlit_stdout_buffer, _streamlit_stderr_buffer
    if _streamlit_process is not None:
        try:
            if _streamlit_process.stdout:
                data = _streamlit_process.stdout.read()
                if data:
                    _streamlit_stdout_buffer.append(
                        data.decode("utf-8", errors="replace")
                    )
        except Exception:
            pass
        try:
            if _streamlit_process.stderr:
                data = _streamlit_process.stderr.read()
                if data:
                    _streamlit_stderr_buffer.append(
                        data.decode("utf-8", errors="replace")
                    )
        except Exception:
            pass

def _stop_streamlit():
    """
    Encerra o subprocesso Streamlit graciosamente.
    Registrado via atexit para execução no shutdown do Passenger.

    Sequência:
    1. SIGTERM (terminate)
    2. Aguarda 10 segundos
    3. SIGKILL (kill) se ainda estiver vivo
    """
    global _streamlit_process, _streamlit_ready
    if _streamlit_process is not None:
        pid = _streamlit_process.pid
        _diag_info(f"Encerrando Streamlit (PID {pid})...")
        _flush_subprocess_output()
        try:
            _streamlit_process.terminate()
            _streamlit_process.wait(timeout=10)
            _diag_info(f"Streamlit (PID {pid}) encerrado via SIGTERM.")
        except subprocess.TimeoutExpired:
            _diag_warn(f"Streamlit (PID {pid}) não respondeu ao SIGTERM. Enviando SIGKILL.")
            _streamlit_process.kill()
            _streamlit_process.wait()
            _diag_info(f"Streamlit (PID {pid}) encerrado via SIGKILL.")
        except Exception as e:
            _diag_warn(f"Erro ao encerrar Streamlit (PID {pid}): {e}")
        finally:
            _streamlit_process = None
            _streamlit_ready = False

atexit.register(_stop_streamlit)

# ══════════════════════════════════════════════════════════════════════════════
# BLOCO 5: PÁGINA DE DIAGNÓSTICO HTML
# ══════════════════════════════════════════════════════════════════════════════
#
# Quando ocorre um erro, em vez de retornar um simples "500 Internal Server
# Error", retornamos uma página HTML completa com TODO o diagnóstico coletado.
# Isso permite identificar o problema sem acesso SSH, apenas visualizando a
# resposta no navegador.
# ══════════════════════════════════════════════════════════════════════════════

def _build_diagnostic_html(error_summary: str, extra_sections: list[tuple[str, str]] = None) -> str:
    """
    Constrói uma página HTML de diagnóstico com:
    - Sumário do erro
    - Log de diagnóstico completo
    - Seções extras (stdout, stderr, comando, etc.)
    - Informações do ambiente
    """
    # Construir tabela de log
    log_rows = []
    with _diagnostic_lock:
        # Últimos 200 eventos (mais relevantes primeiro)
        recent_logs = list(_diagnostic_log[-200:])
        recent_logs.reverse()  # Mais recente primeiro

    for entry in recent_logs:
        ts = entry["timestamp"]
        level = entry["level"]
        msg = entry["message"].replace("&", "&").replace("<", "<").replace(">", ">")
        # Colorir por nível
        color = {
            "ERROR": "#dc3545",
            "WARN": "#ffc107",
            "INFO": "#0d6efd",
            "DEBUG": "#6c757d",
        }.get(level, "#6c757d")
        log_rows.append(
            f'<tr style="color:{color}">'
            f'<td style="white-space:nowrap;padding:2px 8px;font-family:monospace;font-size:12px">{ts}</td>'
            f'<td style="padding:2px 8px;font-weight:bold;font-family:monospace;font-size:12px">{level}</td>'
            f'<td style="padding:2px 8px;font-family:monospace;font-size:12px;white-space:pre-wrap;word-break:break-all">{msg}</td>'
            f'</tr>'
        )

    log_table = "\n".join(log_rows) if log_rows else "<tr><td colspan='3'>Nenhum log registrado.</td></tr>"

    # Construir seções extras
    extra_html = ""
    if extra_sections:
        for title, content in extra_sections:
            safe_content = content.replace("&", "&").replace("<", "<").replace(">", ">")
            extra_html += f"""
            <div style="margin-top:20px">
                <h4 style="color:#dc3545;margin-bottom:5px">{title}</h4>
                <pre style="background:#1a1a2e;color:#e0e0e0;padding:12px;border-radius:4px;overflow-x:auto;font-size:12px;max-height:400px;overflow-y:auto">{safe_content}</pre>
            </div>
            """

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ULITEC CRM — Diagnóstico de Deploy</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:'Segoe UI',system-ui,sans-serif; background:#0d1117; color:#c9d1d9; padding:20px; }}
  .container {{ max-width:1200px; margin:0 auto; }}
  h1 {{ color:#58a6ff; border-bottom:2px solid #30363d; padding-bottom:10px; margin-bottom:20px; }}
  h2 {{ color:#f0883e; margin:20px 0 10px 0; }}
  h3 {{ color:#7ee787; margin:15px 0 8px 0; }}
  h4 {{ color:#f97583; margin:10px 0 5px 0; }}
  .card {{ background:#161b22; border:1px solid #30363d; border-radius:6px; padding:16px; margin-bottom:16px; }}
  .error-box {{ background:#2d1111; border:1px solid #dc3545; border-radius:6px; padding:16px; margin-bottom:16px; }}
  table {{ width:100%; border-collapse:collapse; }}
  th {{ background:#21262d; padding:6px 8px; text-align:left; font-size:12px; color:#8b949e; border-bottom:1px solid #30363d; }}
  td {{ border-bottom:1px solid #21262d; }}
  pre {{ white-space:pre-wrap; word-break:break-all; }}
  .badge-ok {{ display:inline-block; background:#1b3a1b; color:#7ee787; padding:2px 8px; border-radius:3px; font-size:12px; }}
  .badge-fail {{ display:inline-block; background:#3a1b1b; color:#f97583; padding:2px 8px; border-radius:3px; font-size:12px; }}
  .badge-warn {{ display:inline-block; background:#3a351b; color:#f0883e; padding:2px 8px; border-radius:3px; font-size:12px; }}
</style>
</head>
<body>
<div class="container">
<h1>🏭 ULITEC CRM — Diagnóstico de Deploy</h1>
<p style="color:#8b949e;margin-bottom:20px">
  Esta página contém o diagnóstico completo do processo de inicialização do CRM.
  Use as informações abaixo para identificar a causa do erro.
</p>

<div class="error-box">
  <h3>❌ Erro Detectado</h3>
  <pre style="color:#f97583;white-space:pre-wrap">{error_summary}</pre>
</div>

<h2>📋 Resumo do Ambiente</h2>
<div class="card">
  <p><strong>Python:</strong> {sys.version.split()[0]} ({sys.executable})</p>
  <p><strong>Platform:</strong> {platform.platform()}</p>
  <p><strong>APP_DIR:</strong> {APP_DIR}</p>
  <p><strong>Streamlit disponível:</strong> <span class="{'badge-ok' if _STREAMLIT_AVAILABLE else 'badge-fail'}">{'✅ SIM' if _STREAMLIT_AVAILABLE else '❌ NÃO'}</span></p>
  <p><strong>Bootstrap:</strong> <span class="{'badge-ok' if _bootstrap_error is None else 'badge-fail'}">{'✅ OK' if _bootstrap_error is None else '❌ FALHOU'}</span></p>
  <p><strong>Porta {STREAMLIT_PORT}:</strong> <span class="{'badge-ok' if _port_check.get('can_bind') else 'badge-warn' if _port_check.get('already_in_use') else 'badge-fail'}">{"✅ Bind OK" if _port_check.get('can_bind') else '⚠️ Já em uso' if _port_check.get('already_in_use') else '❌ Bloqueada'}</span></p>
  <p><strong>Subprocesso:</strong> {"✅ Rodando" if _streamlit_ready else '❌ Não iniciado' if _streamlit_process is None else '⏳ Inicializando...'}</p>
</div>

{extra_html}

<h2>📝 Log de Diagnóstico (mais recentes primeiro)</h2>
<div class="card" style="max-height:600px;overflow-y:auto">
  <table>
    <thead><tr><th>Timestamp</th><th>Nível</th><th>Mensagem</th></tr></thead>
    <tbody>{log_table}</tbody>
  </table>
</div>

<p style="color:#484f58;font-size:11px;margin-top:20px;text-align:center">
  passenger_wsgi.py v3.0 — ULITEC CRM Industrial — {datetime.now().isoformat()}
</p>
</div>
</body>
</html>"""

# ══════════════════════════════════════════════════════════════════════════════
# BLOCO 6: FUNÇÃO WSGI application()
# ══════════════════════════════════════════════════════════════════════════════
#
# Esta é a função chamada pelo Passenger a cada requisição HTTP.
#
# Fluxo:
# 1. Se bootstrap falhou → página de diagnóstico com o erro
# 2. Se Streamlit não está pronto → tenta iniciar
# 3. Se inicialização falhou → página de diagnóstico completa
# 4. Se Streamlit está pronto → proxy reverso HTTP
# 5. Se proxy falhar (conexão recusada) → registra e retorna 502
# ══════════════════════════════════════════════════════════════════════════════

def _convert_wsgi_environ_to_headers(environ: dict) -> dict:
    """
    Converte cabeçalhos do padrão WSGI para cabeçalhos HTTP.

    No WSGI, headers da requisição são prefixados com HTTP_ e usam _
    em vez de -. Exemplo:
        HTTP_CONTENT_TYPE → Content-Type
        HTTP_X_FORWARDED_FOR → X-Forwarded-For

    Headers hop-by-hop e o Host original do WSGI são removidos,
    pois serão substituídos pelo Host do Streamlit.
    """
    headers = {}
    for key, value in environ.items():
        if key.startswith("HTTP_"):
            # Remove prefixo HTTP_, substitui _ por -, title case
            header_name = key[5:].replace("_", "-").title()
            if header_name.lower() not in HOP_BY_HOP_HEADERS:
                headers[header_name] = value

    # Adiciona Host do WSGI (pode ser útil para debug)
    if "SERVER_NAME" in environ:
        host = environ["SERVER_NAME"]
        server_port = environ.get("SERVER_PORT", "80")
        if server_port not in ("80", "443"):
            host = f"{host}:{server_port}"
        headers["X-Forwarded-Host"] = host
        headers["X-Forwarded-Proto"] = environ.get("wsgi.url_scheme", "http")

    # Host que o Streamlit espera
    headers["Host"] = f"{STREAMLIT_HOST}:{STREAMLIT_PORT}"

    return headers

def application(environ: dict, start_response):
    """
    ENTRY POINT WSGI — Chamado pelo Passenger a cada requisição.

    Parâmetros:
        environ: dicionário WSGI com dados da requisição
        start_response: callable(status, headers) para iniciar a resposta

    Retorna:
        iterable de bytes (corpo da resposta)
    """
    # Declaração de variáveis globais que são MODIFICADAS dentro desta função.
    # Sem esta declaração, qualquer atribuição (ex: _streamlit_ready = False)
    # faz o Python criar uma variável LOCAL com o mesmo nome, ocultando a global
    # e causando UnboundLocalError ao tentar LER antes de atribuir.
    global _streamlit_ready

    # ── Diagnóstico da requisição ──
    method = environ.get("REQUEST_METHOD", "UNKNOWN")
    path = environ.get("PATH_INFO", "/")
    _diag_debug(f"Requisição recebida: {method} {path}")

    # ── CASO 1: Bootstrap falhou ──
    # Se o bootstrap não conseguiu executar, não faz sentido tentar
    # iniciar o Streamlit. Retornamos diagnóstico completo.
    if _bootstrap_error is not None:
        _diag_error("Requisição rejeitada: bootstrap falhou.")
        html = _build_diagnostic_html(
            error_summary="O bootstrap (utils/bootstrap.py) falhou ao inicializar. "
                          "O banco de dados ou as migrações não puderam ser configurados.",
            extra_sections=[
                ("Erro do Bootstrap", _bootstrap_error),
            ],
        )
        status = "500 Internal Server Error"
        resp_headers = [
            ("Content-Type", "text/html; charset=utf-8"),
            ("Content-Length", str(len(html.encode("utf-8")))),
        ]
        start_response(status, resp_headers)
        return [html.encode("utf-8")]

    # ── CASO 2: Streamlit não está pronto → tentar iniciar ──
    if not _streamlit_ready:
        _diag_info("Streamlit não está pronto. Iniciando...")
        started = _start_streamlit()

        if not started:
            # Falha na inicialização — construir página de diagnóstico completa
            error_sections = []

            if _streamlit_startup_error:
                se = _streamlit_startup_error
                error_sections.append((
                    "Fase da Falha",
                    se.get("fase", "desconhecida")
                ))
                error_sections.append((
                    "Motivo",
                    se.get("motivo", se.get("detalhe", "Desconhecido"))
                ))
                if "comando" in se:
                    error_sections.append(("Último Comando", se["comando"]))
                if "cwd" in se:
                    error_sections.append(("Working Directory", se["cwd"]))
                if "pid" in se:
                    error_sections.append(("PID do Subprocesso", str(se["pid"])))
                if "exit_code" in se:
                    error_sections.append(("Código de Saída", str(se["exit_code"])))
                if "stdout" in se and se["stdout"]:
                    error_sections.append(("STDOUT do Streamlit", se["stdout"]))
                if "stderr" in se and se["stderr"]:
                    error_sections.append(("STDERR do Streamlit", se["stderr"]))
                if "traceback" in se:
                    error_sections.append(("Traceback", se["traceback"]))

            html = _build_diagnostic_html(
                error_summary=(
                    "O subprocesso Streamlit NÃO CONSEGUIU INICIAR.\n\n"
                    "Possíveis causas:\n"
                    "1. cPanel bloqueia subprocess.Popen (política de segurança)\n"
                    "2. Streamlit não está instalado no ambiente Python do Passenger\n"
                    "3. A porta 8501 está bloqueada ou ocupada\n"
                    "4. O app.py possui erro que impede a inicialização\n"
                    "5. Timeout: o Streamlit demorou mais de 30s para responder\n\n"
                    "Verifique as seções abaixo para diagnóstico detalhado."
                ),
                extra_sections=error_sections,
            )
            status = "500 Internal Server Error"
            resp_headers = [
                ("Content-Type", "text/html; charset=utf-8"),
                ("Content-Length", str(len(html.encode("utf-8")))),
            ]
            start_response(status, resp_headers)
            return [html.encode("utf-8")]

    # ── CASO 3: Streamlit pronto → proxy reverso ──
    # Construir URL alvo
    query_string = environ.get("QUERY_STRING", "")
    target_url = f"{STREAMLIT_BASE_URL}{path}"
    if query_string:
        target_url += f"?{query_string}"

    # Converter headers WSGI → HTTP
    proxy_headers = _convert_wsgi_environ_to_headers(environ)

    # Ler corpo da requisição (para POST, PUT, etc.)
    body = None
    content_length = environ.get("CONTENT_LENGTH")
    if content_length:
        try:
            content_length_int = int(content_length)
            if content_length_int > 0:
                body = environ["wsgi.input"].read(content_length_int)
        except (ValueError, KeyError, OSError):
            pass

    # Encaminhar requisição
    try:
        req = Request(
            target_url,
            data=body,
            headers=proxy_headers,
            method=method,
        )
        # Remove header Host que urllib pode adicionar automaticamente
        # (já definimos no proxy_headers)
        response = urlopen(req, timeout=PROXY_REQUEST_TIMEOUT_SEC)

        # Sucesso: devolver resposta do Streamlit
        status = f"{response.status} {response.reason}"
        resp_headers = [
            (k, v) for k, v in response.headers.items()
            if k.lower() not in HOP_BY_HOP_HEADERS
        ]
        # Adiciona header para debug
        resp_headers.append(("X-Served-By", "Passenger-WSGI-Proxy/3.0"))
        start_response(status, resp_headers)
        response_body = response.read()
        return [response_body]

    except HTTPError as e:
        # Streamlit respondeu com erro HTTP (4xx, 5xx).
        # WebSocket /_stcore/stream sempre retorna 400 via HTTP —
        # não propagar o erro, apenas retornar 200 vazio.
        if path.startswith("/_stcore/stream"):
            _diag_debug(
                f"WebSocket /_stcore/stream não suportado via proxy HTTP "
                f"(HTTP {e.code}). Ignorando."
            )
            status = "200 OK"
            resp_headers = [
                ("Content-Type", "text/plain; charset=utf-8"),
                ("Content-Length", "0"),
            ]
            start_response(status, resp_headers)
            return [b""]
        # Para outros endpoints, repassar o erro normalmente
        _diag_warn(f"Streamlit retornou HTTP {e.code} para {method} {path}")
        status = f"{e.code} {e.reason}"
        resp_headers = [
            (k, v) for k, v in e.headers.items()
            if k.lower() not in HOP_BY_HOP_HEADERS
        ]
        resp_headers.append(("X-Served-By", "Passenger-WSGI-Proxy/3.0"))
        start_response(status, resp_headers)
        error_body = e.read()
        return [error_body]

    except URLError as e:
        # Conexão recusada ou timeout.
        # IMPORTANTE: Não resetar _streamlit_ready para endpoints WebSocket
        # (/_stcore/stream), pois eles SEMPRE falham via proxy HTTP.
        # O Streamlit continua vivo — só o WebSocket não funciona aqui.
        if path.startswith("/_stcore/stream"):
            _diag_debug(
                f"WebSocket /_stcore/stream não suportado via proxy HTTP. "
                f"Ignorando (Streamlit continua rodando)."
            )
            # Retorna 200 vazio para não quebrar o frontend
            status = "200 OK"
            resp_headers = [
                ("Content-Type", "text/plain; charset=utf-8"),
                ("Content-Length", "0"),
            ]
            start_response(status, resp_headers)
            return [b""]
        # Para outros endpoints, resetar _streamlit_ready para forçar
        # reinicialização (pode ser que o Streamlit tenha morrido)
        _diag_error(f"Conexão com Streamlit FALHOU: {e}")
        _diag_error(f"Target: {target_url}")
        _diag_error("Marcando Streamlit como não-pronto. Tentará reiniciar na próxima requisição.")
        _streamlit_ready = False  # Força reinicialização

        # Tenta coletar output do subprocesso para diagnóstico
        _flush_subprocess_output()
        stdout_tail = "".join(_streamlit_stdout_buffer)[-2000:]
        stderr_tail = "".join(_streamlit_stderr_buffer)[-2000:]

        extra = []
        if stdout_tail:
            extra.append(("STDOUT do Streamlit", stdout_tail))
        if stderr_tail:
            extra.append(("STDERR do Streamlit", stderr_tail))
        extra.append(("URL Alvo", target_url))
        extra.append(("Erro", str(e)))

        html = _build_diagnostic_html(
            error_summary=(
                f"O Streamlit parou de responder durante a requisição.\n"
                f"Erro: {e}\n\n"
                f"O sistema tentará reiniciar o Streamlit na próxima requisição.\n"
                f"Recarregue a página para tentar novamente."
            ),
            extra_sections=extra,
        )
        status = "502 Bad Gateway"
        resp_headers = [
            ("Content-Type", "text/html; charset=utf-8"),
            ("Content-Length", str(len(html.encode("utf-8")))),
        ]
        start_response(status, resp_headers)
        return [html.encode("utf-8")]

    except Exception as e:
        # Erro inesperado no proxy
        _diag_error(f"Erro inesperado no proxy: {e}")
        _diag_error(tb_module.format_exc())

        html = _build_diagnostic_html(
            error_summary=f"Erro interno no proxy WSGI: {e}",
            extra_sections=[
                ("Traceback", tb_module.format_exc()),
                ("URL Alvo", target_url),
            ],
        )
        status = "500 Internal Server Error"
        resp_headers = [
            ("Content-Type", "text/html; charset=utf-8"),
            ("Content-Length", str(len(html.encode("utf-8")))),
        ]
        start_response(status, resp_headers)
        return [html.encode("utf-8")]

# ══════════════════════════════════════════════════════════════════════════════
# FIM DO MÓDULO
# ══════════════════════════════════════════════════════════════════════════════
#
# Resumo do que foi configurado:
# - Ambiente diagnosticado (Python, PATH, diretório, portas)
# - Bootstrap executado (SQLite, WAL, schema)
# - Subprocesso Streamlit gerenciado (lazy init, health check)
# - Proxy reverso WSGI → HTTP
# - Página de diagnóstico HTML para erros
# - Logs detalhados em stderr
#
# Para testar: acesse a URL configurada no cPanel.
# Se funcionar: verá a interface do Streamlit.
# Se falhar: verá uma página HTML com diagnóstico completo.
# ══════════════════════════════════════════════════════════════════════════════

_diag_info("=" * 70)
_diag_info("MÓDULO passenger_wsgi.py CARREGADO COM SUCESSO")
_diag_info("Aguardando primeira requisição HTTP do Passenger...")
_diag_info("=" * 70)