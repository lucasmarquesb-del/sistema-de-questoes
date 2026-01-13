"""
Tabela de relacionamento Lista-Questão (N:N com ordem)
"""
from sqlalchemy import Column, Text, ForeignKey, Integer, DateTime
from datetime import datetime
from .base import Base


class ListaQuestao(Base):
    """
    Tabela associativa entre Lista e Questão
    Permite ordem customizada
    """
    __tablename__ = 'lista_questao'

    uuid_lista = Column(Text, ForeignKey('lista.uuid'), primary_key=True)
    uuid_questao = Column(Text, ForeignKey('questao.uuid'), primary_key=True)
    ordem_na_lista = Column(Integer, nullable=False)
    data_adicao = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<ListaQuestao(lista={self.uuid_lista[:8]}, questao={self.uuid_questao[:8]}, ordem={self.ordem_na_lista})>"
