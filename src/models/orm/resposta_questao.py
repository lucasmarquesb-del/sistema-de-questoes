"""
Model ORM para Resposta de Questão (Unificada)
"""
import uuid as uuid_lib
from sqlalchemy import Column, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class RespostaQuestao(Base):
    """
    Resposta unificada para questões objetivas e discursivas
    """
    __tablename__ = 'resposta_questao'

    uuid = Column(Text, primary_key=True, default=lambda: str(uuid_lib.uuid4()))
    uuid_questao = Column(Text, ForeignKey('questao.uuid'), unique=True, nullable=False)

    # Para questões OBJETIVAS
    uuid_alternativa_correta = Column(Text, ForeignKey('alternativa.uuid'), nullable=True)

    # Para questões DISCURSIVAS
    gabarito_discursivo = Column(Text, nullable=True)

    # Campos comuns
    resolucao = Column(Text, nullable=True)  # Resolução detalhada
    justificativa = Column(Text, nullable=True)  # Justificativa/critérios
    autor_resolucao = Column(Text, nullable=True)  # Autor da resolução
    data_criacao = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    questao = relationship("Questao", back_populates="resposta")
    alternativa_correta = relationship("Alternativa", foreign_keys=[uuid_alternativa_correta])

    def __repr__(self):
        return f"<RespostaQuestao(questao={self.uuid_questao[:8]})>"

    @classmethod
    def criar_resposta_objetiva(cls, session, uuid_questao: str, uuid_alternativa_correta: str,
                                resolucao: str = None, justificativa: str = None, autor: str = None):
        """
        Cria uma resposta para questão objetiva

        Args:
            session: Sessão do SQLAlchemy
            uuid_questao: UUID da questão
            uuid_alternativa_correta: UUID da alternativa correta
            resolucao: Resolução detalhada (opcional)
            justificativa: Justificativa da resposta (opcional)
            autor: Autor da resolução (opcional)

        Returns:
            Objeto RespostaQuestao
        """
        resposta = cls(
            uuid_questao=uuid_questao,
            uuid_alternativa_correta=uuid_alternativa_correta,
            gabarito_discursivo=None,
            resolucao=resolucao,
            justificativa=justificativa,
            autor_resolucao=autor
        )
        session.add(resposta)
        session.flush()
        return resposta

    @classmethod
    def criar_resposta_discursiva(cls, session, uuid_questao: str, gabarito_discursivo: str,
                                  resolucao: str = None, justificativa: str = None, autor: str = None):
        """
        Cria uma resposta para questão discursiva

        Args:
            session: Sessão do SQLAlchemy
            uuid_questao: UUID da questão
            gabarito_discursivo: Gabarito em LaTeX
            resolucao: Resolução detalhada (opcional)
            justificativa: Critérios de avaliação (opcional)
            autor: Autor da resolução (opcional)

        Returns:
            Objeto RespostaQuestao
        """
        resposta = cls(
            uuid_questao=uuid_questao,
            uuid_alternativa_correta=None,
            gabarito_discursivo=gabarito_discursivo,
            resolucao=resolucao,
            justificativa=justificativa,
            autor_resolucao=autor
        )
        session.add(resposta)
        session.flush()
        return resposta

    @classmethod
    def buscar_por_questao(cls, session, uuid_questao: str):
        """Busca resposta de uma questão"""
        return session.query(cls).filter_by(uuid_questao=uuid_questao).first()

    def eh_objetiva(self) -> bool:
        """Verifica se a resposta é de questão objetiva"""
        return self.uuid_alternativa_correta is not None

    def eh_discursiva(self) -> bool:
        """Verifica se a resposta é de questão discursiva"""
        return self.gabarito_discursivo is not None
