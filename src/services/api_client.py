"""Cliente HTTP centralizado para comunicação com o backend."""

import logging
from typing import Optional
import requests

logger = logging.getLogger(__name__)


class ApiClient:
    """Wrapper sobre requests com autenticação JWT automática."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self._token: Optional[str] = None

    @property
    def token(self) -> Optional[str]:
        return self._token

    @token.setter
    def token(self, value: Optional[str]):
        self._token = value

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    def get(self, path: str, **kwargs) -> requests.Response:
        url = f"{self.base_url}{path}"
        return requests.get(url, headers=self._headers(), timeout=15, **kwargs)

    def post(self, path: str, **kwargs) -> requests.Response:
        url = f"{self.base_url}{path}"
        return requests.post(url, headers=self._headers(), timeout=15, **kwargs)

    def patch(self, path: str, **kwargs) -> requests.Response:
        url = f"{self.base_url}{path}"
        return requests.patch(url, headers=self._headers(), timeout=15, **kwargs)

    def health_check(self) -> bool:
        """Verifica se o backend está acessível."""
        try:
            resp = self.get("/health")
            return resp.status_code == 200
        except requests.ConnectionError:
            logger.warning("Backend inacessível")
            return False

    def get_me(self) -> Optional[dict]:
        """Retorna dados do usuário autenticado, ou None se token inválido."""
        try:
            resp = self.get("/me")
            if resp.status_code == 200:
                return resp.json()
            logger.warning(f"/me retornou status {resp.status_code}")
            return None
        except requests.RequestException as e:
            logger.error(f"Erro ao chamar /me: {e}")
            return None

    def list_users(self) -> Optional[list]:
        """Lista todos os usuários (admin)."""
        try:
            resp = self.get("/admin/users")
            if resp.status_code == 200:
                return resp.json()
            return None
        except requests.RequestException as e:
            logger.error(f"Erro ao listar usuários: {e}")
            return None

    def update_user(self, user_id: int, data: dict) -> Optional[dict]:
        """Atualiza um usuário (admin)."""
        try:
            resp = self.patch(f"/admin/users/{user_id}", json=data)
            if resp.status_code == 200:
                return resp.json()
            return None
        except requests.RequestException as e:
            logger.error(f"Erro ao atualizar usuário: {e}")
            return None
