"""
Base Model para todos os models ORM com UUID
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, Text, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class BaseModel(Base):
    """
    Classe base abstrata para todos os models
    Fornece UUID, timestamps e flag ativo
    """
    __abstract__ = True

    uuid = Column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    data_criacao = Column(DateTime, default=datetime.utcnow, nullable=False)
    ativo = Column(Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<{self.__class__.__name__}(uuid={self.uuid})>"

    def to_dict(self):
        """Converte o model para dicionário"""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result
