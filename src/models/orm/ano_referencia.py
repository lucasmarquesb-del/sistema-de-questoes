"""
Model ORM para Ano de Referência
"""
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from .base import BaseModel


class AnoReferencia(BaseModel):
    """
    Ano de Referência das questões (2024, 2025, etc.)
    """
    __tablename__ = 'ano_referencia'

    ano = Column(Integer, unique=True, nullable=False, index=True)
    descricao = Column(String(100), nullable=False)

    # Relationships
    questoes = relationship("Questao", back_populates="ano")

    def __repr__(self):
        return f"<AnoReferencia(ano={self.ano})>"

    @classmethod
    def buscar_por_ano(cls, session, ano: int):
        """Busca ano de referência"""
        return session.query(cls).filter_by(ano=ano, ativo=True).first()

    @classmethod
    def listar_todos(cls, session, ordem_desc=True):
        """Lista todos os anos ativos"""
        query = session.query(cls).filter_by(ativo=True)
        if ordem_desc:
            query = query.order_by(cls.ano.desc())
        else:
            query = query.order_by(cls.ano)
        return query.all()

    @classmethod
    def criar_ou_obter(cls, session, ano: int):
        """Cria um novo ano ou retorna existente"""
        ano_ref = cls.buscar_por_ano(session, ano)
        if not ano_ref:
            ano_ref = cls(
                ano=ano,
                descricao=str(ano)
            )
            session.add(ano_ref)
            session.flush()
        return ano_ref
