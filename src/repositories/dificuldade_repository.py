"""Repository para Dificuldades"""
from typing import Optional
from sqlalchemy.orm import Session
from models.orm import Dificuldade
from .base_repository import BaseRepository

class DificuldadeRepository(BaseRepository[Dificuldade]):
    def __init__(self, session: Session):
        super().__init__(Dificuldade, session)
    
    def buscar_por_codigo(self, codigo: str) -> Optional[Dificuldade]:
        return self.session.query(Dificuldade).filter_by(codigo=codigo, ativo=True).first()
