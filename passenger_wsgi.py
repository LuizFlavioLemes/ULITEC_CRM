"""
passenger_wsgi.py — WSGI Entry Point para cPanel Python Application
===================================================================

Este arquivo é o ponto de entrada usado pelo Passenger (cPanel) para
iniciar a aplicação Streamlit.

O Passenger gerencia o ciclo de vida do processo:
- Inicia automaticamente após deploy
- Reinicia se o processo cair
- Gerencia múltiplas requisições

Para Streamlit no cPanel:
1. O Passenger carrega este módulo
2. O app.py do Streamlit é importado como módulo
3. As páginas são servidas via interface web do Streamlit

Configuração no cPanel → Setup Python App:
- Application startup file: passenger_wsgi.py
- Application Entry point: application
"""

import os
import sys

# ── Corrigir path para incluir a raiz do projeto ──
app_dir = os.path.dirname(os.path.abspath(__file__))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

# ── Definir working directory como raiz do projeto ──
os.chdir(app_dir)

# ── Importar módulo principal do Streamlit ──
# O Passenger mantém o processo vivo entre requisições
# O Streamlit gerencia seu próprio servidor internamente
try:
    import app  # noqa: F401 — carrega a aplicação Streamlit
except ImportError as e:
    import traceback

    error_msg = (
        f"Erro ao importar app.py: {e}\n{traceback.format_exc()}"
    )

    def application(environ, start_response):
        status = "500 Internal Server Error"
        headers = [("Content-Type", "text/plain; charset=utf-8")]
        start_response(status, headers)
        return [error_msg.encode("utf-8")]

else:
    # ── WSGI callable (exigido pelo Passenger) ──
    def application(environ, start_response):
        """
        Entry point WSGI.

        O Passenger chama esta função a cada requisição HTTP.
        O Streamlit gerencia o roteamento internamente via Tornado.
        """
        status = "200 OK"
        headers = [("Content-Type", "text/html; charset=utf-8")]
        start_response(status, headers)
        return [
            b"ULITEC CRM -- Aplicacao Streamlit ativa.\n"
            b"Acesse a URL configurada no cPanel para usar o sistema."
        ]