"""
Tabela de relacionamento Questão-Tag (N:N)
"""
from sqlalchemy import Table, Column, Text, ForeignKey, DateTime
from datetime import datetime
from .base import Base


QuestaoTag = Table(
    'questao_tag',
    Base.metadata,
    Column('uuid_questao', Text, ForeignKey('questao.uuid'), primary_key=True),
    Column('uuid_tag', Text, ForeignKey('tag.uuid'), primary_key=True),
    Column('data_associacao', DateTime, default=datetime.utcnow, nullable=False)
)
