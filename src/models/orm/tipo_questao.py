"""
Model ORM para Tipo de Questão
"""
from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from .base import BaseModel


class TipoQuestao(BaseModel):
    """
    Tipo de Questão (OBJETIVA, DISCURSIVA)
    """
    __tablename__ = 'tipo_questao'

    codigo = Column(String(20), unique=True, nullable=False, index=True)
    nome = Column(String(100), nullable=False)

    # Relationships
    questoes = relationship("Questao", back_populates="tipo")

    def __repr__(self):
        return f"<TipoQuestao(codigo={self.codigo}, nome={self.nome})>"

    @classmethod
    def buscar_por_codigo(cls, session, codigo: str):
        """Busca tipo de questão por código"""
        return session.query(cls).filter_by(codigo=codigo, ativo=True).first()
