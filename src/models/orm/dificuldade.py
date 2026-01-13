"""
Model ORM para Dificuldade
"""
from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from .base import BaseModel


class Dificuldade(BaseModel):
    """
    Nível de dificuldade (FACIL, MEDIO, DIFICIL)
    """
    __tablename__ = 'dificuldade'

    codigo = Column(String(20), unique=True, nullable=False, index=True)

    # Relationships
    questoes = relationship("Questao", back_populates="dificuldade")

    def __repr__(self):
        return f"<Dificuldade(codigo={self.codigo})>"

    @classmethod
    def buscar_por_codigo(cls, session, codigo: str):
        """Busca dificuldade por código"""
        return session.query(cls).filter_by(codigo=codigo, ativo=True).first()

    @classmethod
    def listar_todas(cls, session):
        """Lista todas as dificuldades ativas"""
        return session.query(cls).filter_by(ativo=True).all()
