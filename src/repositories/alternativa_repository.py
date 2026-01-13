"""Repository para Alternativas"""
from typing import List
from sqlalchemy.orm import Session
from models.orm import Alternativa, Questao
from .base_repository import BaseRepository

class AlternativaRepository(BaseRepository[Alternativa]):
    def __init__(self, session: Session):
        super().__init__(Alternativa, session)
    
    def buscar_por_questao(self, codigo_questao: str) -> List[Alternativa]:
        questao = self.session.query(Questao).filter_by(codigo=codigo_questao, ativo=True).first()
        if not questao:
            return []
        return self.session.query(Alternativa).filter_by(uuid_questao=questao.uuid).order_by(Alternativa.ordem).all()
    
    def buscar_alternativa_correta(self, codigo_questao: str):
        questao = self.session.query(Questao).filter_by(codigo=codigo_questao, ativo=True).first()
        if questao and questao.resposta:
            return self.session.query(Alternativa).filter_by(uuid=questao.resposta.uuid_alternativa_correta).first()
        return None
