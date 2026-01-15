"""
Model ORM para Alternativa
"""
import uuid as uuid_lib
from sqlalchemy import Column, String, Text, ForeignKey, Integer, Numeric, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class Alternativa(Base):
    """
    Alternativa de questão objetiva
    """
    __tablename__ = 'alternativa'

    uuid = Column(Text, primary_key=True, default=lambda: str(uuid_lib.uuid4()))
    uuid_questao = Column(Text, ForeignKey('questao.uuid'), nullable=False)
    letra = Column(String(1), nullable=False)  # A, B, C, D, E
    ordem = Column(Integer, nullable=False)  # 1, 2, 3, 4, 5 (para randomização)
    texto = Column(Text, nullable=False)
    uuid_imagem = Column(Text, ForeignKey('imagem.uuid'), nullable=True)
    escala_imagem = Column(Numeric(3, 2), nullable=True, default=1.0)
    data_criacao = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    questao = relationship("Questao", back_populates="alternativas")
    imagem = relationship("Imagem", back_populates="alternativas")

    def __repr__(self):
        return f"<Alternativa(letra={self.letra}, questao={self.uuid_questao[:8]})>"

    @classmethod
    def buscar_por_questao(cls, session, uuid_questao: str):
        """Busca todas as alternativas de uma questão, ordenadas"""
        return session.query(cls).filter_by(
            uuid_questao=uuid_questao
        ).order_by(cls.ordem).all()

    def eh_correta(self) -> bool:
        """Verifica se esta alternativa é a correta"""
        if self.questao and self.questao.resposta:
            return self.questao.resposta.uuid_alternativa_correta == self.uuid
        return False
