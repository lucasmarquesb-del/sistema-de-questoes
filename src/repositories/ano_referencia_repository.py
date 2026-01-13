"""Repository para Anos de Referência"""
from typing import Optional, List
from sqlalchemy.orm import Session
from models.orm import AnoReferencia
from .base_repository import BaseRepository

class AnoReferenciaRepository(BaseRepository[AnoReferencia]):
    def __init__(self, session: Session):
        super().__init__(AnoReferencia, session)
    
    def buscar_por_ano(self, ano: int) -> Optional[AnoReferencia]:
        return self.session.query(AnoReferencia).filter_by(ano=ano, ativo=True).first()
    
    def criar_ou_obter(self, ano: int) -> AnoReferencia:
        return AnoReferencia.criar_ou_obter(self.session, ano)
    
    def listar_anos_ordenados(self, ordem_desc: bool = True) -> List[AnoReferencia]:
        return AnoReferencia.listar_todos(self.session, ordem_desc)
