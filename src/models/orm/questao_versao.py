"""
Tabela de relacionamento Questão-Versão (N:N)
"""
from sqlalchemy import Column, Text, ForeignKey, DateTime
from datetime import datetime
from .base import Base


class QuestaoVersao(Base):
    """
    Tabela associativa para relacionar versões de questões
    """
    __tablename__ = 'questao_versao'

    uuid_questao_original = Column(Text, ForeignKey('questao.uuid'), primary_key=True)
    uuid_questao_versao = Column(Text, ForeignKey('questao.uuid'), primary_key=True)
    observacao = Column(Text, nullable=True)
    data_vinculo = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<QuestaoVersao(original={self.uuid_questao_original[:8]}, versao={self.uuid_questao_versao[:8]})>"
