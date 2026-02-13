"""Rotas de gerenciamento de usuários (autenticado + admin)."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.core.security import get_current_user, require_admin
from backend.db.database import get_db
from backend.models.user import User
from backend.schemas.user import UserOut, UserUpdate

router = APIRouter(tags=["users"])


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    """Retorna os dados do usuário autenticado."""
    return current_user


@router.get("/admin/users", response_model=List[UserOut])
def list_users(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Lista todos os usuários (somente admin)."""
    return db.query(User).order_by(User.created_at.desc()).all()


@router.patch("/admin/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    data: UserUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Atualiza status (ativo/inativo) ou role de um usuário (somente admin)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado",
        )

    if data.is_active is not None:
        user.is_active = data.is_active
    if data.role is not None:
        user.role = data.role

    db.commit()
    db.refresh(user)
    return user
