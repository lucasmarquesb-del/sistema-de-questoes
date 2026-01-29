# -*- coding: utf-8 -*-
"""
Tabela de relacionamento N:N entre Questao e NivelEscolar.
"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Table

from src.models.orm.base import Base

# Tabela de associacao
questao_nivel = Table(
    'questao_nivel',
    Base.metadata,
    Column('uuid_questao', String(36), ForeignKey('questao.uuid', ondelete='CASCADE'), primary_key=True),
    Column('uuid_nivel', String(36), ForeignKey('nivel_escolar.uuid', ondelete='CASCADE'), primary_key=True),
    Column('data_criacao', DateTime, default=datetime.now)
)
