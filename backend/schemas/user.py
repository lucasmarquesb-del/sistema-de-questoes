"""Schemas Pydantic para serialização de dados de usuário."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class UserOut(BaseModel):
    id: int
    email: str
    name: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    is_active: Optional[bool] = None
    role: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
