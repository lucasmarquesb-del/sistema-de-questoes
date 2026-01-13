"""Repository para Tipos de Questões"""
from typing import Optional
from sqlalchemy.orm import Session
from models.orm import TipoQuestao
from .base_repository import BaseRepository

class TipoQuestaoRepository(BaseRepository[TipoQuestao]):
    def __init__(self, session: Session):
        super().__init__(TipoQuestao, session)
    
    def buscar_por_codigo(self, codigo: str) -> Optional[TipoQuestao]:
        return self.session.query(TipoQuestao).filter_by(codigo=codigo, ativo=True).first()
