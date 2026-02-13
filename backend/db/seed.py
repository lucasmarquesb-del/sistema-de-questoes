"""Seed do banco de dados - cria admin inicial se não existir."""

import logging
from sqlalchemy.orm import Session
from backend.models.user import User
from backend.core.config import get_settings

logger = logging.getLogger(__name__)


def seed_admin(db: Session):
    """Cria o usuário administrador se não existir."""
    settings = get_settings()
    admin_email = settings.ADMIN_EMAIL

    existing = db.query(User).filter(User.email == admin_email).first()
    if existing:
        logger.info(f"Admin já existe: {admin_email}")
        return

    admin = User(
        email=admin_email,
        name="Administrador",
        role="admin",
        is_active=True,
    )
    db.add(admin)
    db.commit()
    logger.info(f"Admin criado: {admin_email}")
