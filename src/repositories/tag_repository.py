"""Repository para Tags"""
from typing import List, Optional
from sqlalchemy.orm import Session
from models.orm import Tag
from .base_repository import BaseRepository

class TagRepository(BaseRepository[Tag]):
    def __init__(self, session: Session):
        super().__init__(Tag, session)
    
    def buscar_por_nome(self, nome: str) -> Optional[Tag]:
        return self.session.query(Tag).filter_by(nome=nome, ativo=True).first()
    
    def buscar_por_numeracao(self, numeracao: str) -> Optional[Tag]:
        return self.session.query(Tag).filter_by(numeracao=numeracao, ativo=True).first()
    
    def listar_raizes(self) -> List[Tag]:
        return self.session.query(Tag).filter_by(uuid_tag_pai=None, ativo=True).order_by(Tag.ordem).all()
    
    def listar_filhas(self, numeracao_pai: str) -> List[Tag]:
        tag_pai = self.buscar_por_numeracao(numeracao_pai)
        if not tag_pai:
            return []
        return self.session.query(Tag).filter_by(uuid_tag_pai=tag_pai.uuid, ativo=True).order_by(Tag.ordem).all()
    
    def obter_caminho_completo(self, numeracao: str) -> str:
        tag = self.buscar_por_numeracao(numeracao)
        return tag.obter_caminho_completo() if tag else ""
