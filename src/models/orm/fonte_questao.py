"""
Model ORM para Fonte de Questão
"""
from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import BaseModel


class FonteQuestao(BaseModel):
    """
    Fonte de Questão (ENEM, FUVEST, AUTORAL, etc.)
    """
    __tablename__ = 'fonte_questao'

    sigla = Column(String(50), unique=True, nullable=False, index=True)
    nome_completo = Column(String(200), nullable=False)
    tipo_instituicao = Column(String(50), nullable=False)  # VESTIBULAR, CONCURSO, AUTORAL
    data_criacao = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    questoes = relationship("Questao", back_populates="fonte")

    def __repr__(self):
        return f"<FonteQuestao(sigla={self.sigla}, nome={self.nome_completo})>"

    @classmethod
    def buscar_por_sigla(cls, session, sigla: str):
        """Busca fonte por sigla"""
        return session.query(cls).filter_by(sigla=sigla, ativo=True).first()

    @classmethod
    def listar_todas(cls, session):
        """Lista todas as fontes ativas"""
        return session.query(cls).filter_by(ativo=True).order_by(cls.sigla).all()
