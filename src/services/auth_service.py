"""Serviço de autenticação — gerencia fluxo OAuth e armazenamento de token."""

import json
import logging
import socket
import threading
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, parse_qs

from PyQt6.QtCore import QObject, pyqtSignal

from src.services.api_client import ApiClient

logger = logging.getLogger(__name__)

TOKEN_DIR = Path.home() / ".mathbank"
TOKEN_FILE = TOKEN_DIR / "token.json"


class AuthService(QObject):
    """Gerencia autenticação OAuth com o backend.

    Signals:
        login_successful(dict): Emitido quando login é bem-sucedido, com dados do usuário.
        login_failed(str): Emitido quando login falha, com mensagem de erro.
        login_pending(str): Emitido quando conta aguarda aprovação.
    """

    login_successful = pyqtSignal(dict)
    login_failed = pyqtSignal(str)
    login_pending = pyqtSignal(str)

    def __init__(self, api_client: ApiClient):
        super().__init__()
        self.api_client = api_client
        self._server: Optional[HTTPServer] = None
        self._server_thread: Optional[threading.Thread] = None

    def start_login(self):
        """Inicia o fluxo de login: abre servidor local e browser."""
        port = self._find_free_port()
        self._start_local_server(port)

        backend_url = self.api_client.base_url
        login_url = f"{backend_url}/login/google?port={port}"
        logger.info(f"Abrindo browser para login: {login_url}")
        webbrowser.open(login_url)

    def try_restore_session(self) -> Optional[dict]:
        """Tenta restaurar sessão a partir do token salvo.

        Returns:
            dict com dados do usuário se token válido, None caso contrário.
        """
        token = self._load_token()
        if not token:
            return None

        self.api_client.token = token
        user_data = self.api_client.get_me()
        if user_data:
            logger.info(f"Sessão restaurada: {user_data.get('email')}")
            return user_data

        # Token inválido/expirado
        self._clear_token()
        self.api_client.token = None
        return None

    def logout(self):
        """Remove token e limpa sessão."""
        self._clear_token()
        self.api_client.token = None
        logger.info("Logout realizado")

    def _find_free_port(self) -> int:
        """Encontra uma porta TCP livre."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("localhost", 0))
            return s.getsockname()[1]

    def _start_local_server(self, port: int):
        """Inicia servidor HTTP temporário para receber callback OAuth."""
        auth_service = self

        class CallbackHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                parsed = urlparse(self.path)
                if parsed.path == "/callback":
                    params = parse_qs(parsed.query)
                    token = params.get("token", [None])[0]

                    if token:
                        # Enviar resposta HTML ao browser
                        self.send_response(200)
                        self.send_header("Content-Type", "text/html")
                        self.end_headers()
                        self.wfile.write(b"""
                        <html><body style="font-family:sans-serif;text-align:center;padding:60px;">
                            <h2 style="color:#16a34a;">Login realizado com sucesso!</h2>
                            <p>Voce ja pode voltar ao aplicativo. Esta janela sera fechada automaticamente.</p>
                            <script>setTimeout(function(){window.close();}, 2000);</script>
                        </body></html>
                        """)

                        # Processar token
                        auth_service._on_token_received(token)
                    else:
                        self.send_response(400)
                        self.send_header("Content-Type", "text/html")
                        self.end_headers()
                        self.wfile.write(b"""
                        <html><body style="font-family:sans-serif;text-align:center;padding:60px;">
                            <h2 style="color:#dc2626;">Erro na autenticacao</h2>
                            <p>Token nao recebido. Tente novamente.</p>
                        </body></html>
                        """)
                        auth_service.login_failed.emit("Token não recebido do servidor")
                else:
                    self.send_response(404)
                    self.end_headers()

            def log_message(self, format, *args):
                # Silenciar logs do servidor HTTP
                pass

        self._server = HTTPServer(("localhost", port), CallbackHandler)
        self._server_thread = threading.Thread(target=self._server.handle_request, daemon=True)
        self._server_thread.start()
        logger.info(f"Servidor local iniciado em localhost:{port}")

    def _on_token_received(self, token: str):
        """Chamado quando o token JWT é recebido via callback."""
        self.api_client.token = token
        user_data = self.api_client.get_me()

        if user_data:
            self._save_token(token)
            logger.info(f"Login bem-sucedido: {user_data.get('email')}")
            self.login_successful.emit(user_data)
        else:
            self.api_client.token = None
            self.login_failed.emit("Não foi possível validar o token")

    def _save_token(self, token: str):
        """Salva token JWT em arquivo local."""
        TOKEN_DIR.mkdir(parents=True, exist_ok=True)
        TOKEN_FILE.write_text(json.dumps({"token": token}), encoding="utf-8")

    def _load_token(self) -> Optional[str]:
        """Carrega token JWT do arquivo local."""
        if not TOKEN_FILE.exists():
            return None
        try:
            data = json.loads(TOKEN_FILE.read_text(encoding="utf-8"))
            return data.get("token")
        except (json.JSONDecodeError, OSError):
            return None

    def _clear_token(self):
        """Remove arquivo de token."""
        if TOKEN_FILE.exists():
            TOKEN_FILE.unlink()
