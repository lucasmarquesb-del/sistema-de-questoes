"""Rotas de autenticação com Google OAuth 2.0."""

import logging
from urllib.parse import urlencode

import requests
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session

from backend.core.config import get_settings
from backend.core.security import create_access_token
from backend.db.database import get_db
from backend.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(tags=["auth"])

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


@router.get("/login/google")
def login_google(port: int = 0):
    """Redireciona para a tela de consentimento do Google.

    Args:
        port: Porta do servidor local no app desktop para receber o callback.
    """
    settings = get_settings()
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "state": str(port),
        "prompt": "select_account",
    }
    url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
    return RedirectResponse(url)


@router.get("/auth/callback")
def auth_callback(code: str, state: str = "0", db: Session = Depends(get_db)):
    """Callback do Google OAuth. Troca code por token, valida email, gera JWT.

    Redireciona para o app desktop via localhost se port > 0.
    """
    settings = get_settings()

    # 1. Trocar authorization code por access token
    token_data = requests.post(
        GOOGLE_TOKEN_URL,
        data={
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        },
        timeout=10,
    )

    if token_data.status_code != 200:
        logger.error(f"Erro ao trocar code por token: {token_data.text}")
        return _error_page("Erro ao autenticar com o Google. Tente novamente.")

    token_json = token_data.json()
    access_token = token_json.get("access_token")

    if not access_token:
        return _error_page("Token do Google inválido.")

    # 2. Obter informações do usuário
    userinfo = requests.get(
        GOOGLE_USERINFO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )

    if userinfo.status_code != 200:
        return _error_page("Erro ao obter dados do usuário.")

    userinfo_json = userinfo.json()
    email = userinfo_json.get("email")
    name = userinfo_json.get("name", "")

    if not email:
        return _error_page("Email não disponível na conta Google.")

    # 3. Verificar/criar usuário no banco
    user = db.query(User).filter(User.email == email).first()

    if not user:
        # Novo usuário — criar com is_active=False (aguarda aprovação)
        user = User(email=email, name=name, role="user", is_active=False)
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"Novo usuário registrado (aguardando aprovação): {email}")
        return _pending_page(email)

    # Atualizar nome se mudou
    if name and user.name != name:
        user.name = name
        db.commit()

    if not user.is_active:
        return _pending_page(email)

    # 4. Gerar JWT do sistema
    jwt_token = create_access_token(user.email, user.role)
    logger.info(f"Login bem-sucedido: {email}")

    # 5. Redirecionar para o app desktop
    port = int(state) if state.isdigit() else 0
    if port > 0:
        return RedirectResponse(f"http://localhost:{port}/callback?token={jwt_token}")

    # Fallback: mostrar token na página
    return _success_page(jwt_token)


def _error_page(message: str) -> HTMLResponse:
    return HTMLResponse(f"""
    <html><body style="font-family:sans-serif;text-align:center;padding:60px;">
        <h2 style="color:#dc2626;">Erro na Autenticacao</h2>
        <p>{message}</p>
        <p>Voce pode fechar esta janela.</p>
    </body></html>
    """)


def _pending_page(email: str) -> HTMLResponse:
    return HTMLResponse(f"""
    <html><body style="font-family:sans-serif;text-align:center;padding:60px;">
        <h2 style="color:#ca8a04;">Aguardando Aprovacao</h2>
        <p>A conta <strong>{email}</strong> foi registrada com sucesso.</p>
        <p>O administrador precisa aprovar seu acesso antes que voce possa utilizar o sistema.</p>
        <p>Voce pode fechar esta janela.</p>
    </body></html>
    """)


def _success_page(token: str) -> HTMLResponse:
    return HTMLResponse(f"""
    <html><body style="font-family:sans-serif;text-align:center;padding:60px;">
        <h2 style="color:#16a34a;">Login Realizado!</h2>
        <p>Voce ja pode voltar ao aplicativo.</p>
        <p style="font-size:12px;color:#666;">Se o aplicativo nao detectou o login automaticamente, copie o codigo abaixo:</p>
        <input type="text" value="{token}" readonly
               style="width:400px;padding:8px;text-align:center;font-family:monospace;"
               onclick="this.select()">
        <script>window.close();</script>
    </body></html>
    """)
