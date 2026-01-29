# -*- coding: utf-8 -*-
"""
Model ORM para a tabela nivel_escolar.

Representa os niveis de escolaridade que podem ser associados as questoes.
"""

import uuid
from datetime import datetime
from typing import List
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text
from sqlalchemy.orm import relationship

from src.models.orm.base import Base


class NivelEscolar(Base):
    """
    Model para niveis escolares.
    
    Attributes:
        uuid: Identificador unico (UUID)
        codigo: Codigo curto (EF1, EF2, EM, etc.)
        nome: Nome completo (Ensino Fundamental I, etc.)
        descricao: Descricao detalhada
        ordem: Ordem de exibicao
        ativo: Se esta ativo para uso
        data_criacao: Data de criacao do registro
    """
    
    __tablename__ = 'nivel_escolar'
    
    # Colunas
    uuid = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    codigo = Column(String(10), unique=True, nullable=False)
    nome = Column(String(100), nullable=False)
    descricao = Column(Text, nullable=True)
    ordem = Column(Integer, nullable=False, default=0)
    ativo = Column(Boolean, nullable=False, default=True)
    data_criacao = Column(DateTime, default=datetime.now)
    
    # Relacionamento N:N com questoes
    questoes = relationship(
        "Questao",
        secondary="questao_nivel",
        back_populates="niveis_escolares"
    )
    
    def __repr__(self) -> str:
        return f"<NivelEscolar(uuid='{self.uuid[:8]}...', codigo='{self.codigo}')>"
    
    def __str__(self) -> str:
        return f"{self.codigo} - {self.nome}"
    
    def to_dict(self) -> dict:
        """Converte o model para dicionario."""
        return {
            "uuid": self.uuid,
            "codigo": self.codigo,
            "nome": self.nome,
            "descricao": self.descricao,
            "ordem": self.ordem,
            "ativo": self.ativo,
            "data_criacao": self.data_criacao.isoformat() if self.data_criacao else None,
        }
    
    @classmethod
    def gerar_uuid(cls) -> str:
        """Gera um novo UUID."""
        return str(uuid.uuid4())
    
    @classmethod
    def get_niveis_padrao(cls) -> List[dict]:
        """Retorna niveis padrao para insercao inicial."""
        return [
            {"codigo": "EF1", "nome": "Ensino Fundamental I", "descricao": "1 ao 5 ano", "ordem": 1},
            {"codigo": "EF2", "nome": "Ensino Fundamental II", "descricao": "6 ao 9 ano", "ordem": 2},
            {"codigo": "EM", "nome": "Ensino Medio", "descricao": "1 a 3 serie", "ordem": 3},
            {"codigo": "PRE", "nome": "Pre-Vestibular", "descricao": "Cursinho preparatorio", "ordem": 4},
            {"codigo": "EJA", "nome": "Educacao de Jovens e Adultos", "descricao": "EJA", "ordem": 5},
            {"codigo": "TEC", "nome": "Ensino Tecnico", "descricao": "Cursos tecnicos", "ordem": 6},
            {"codigo": "SUP", "nome": "Ensino Superior", "descricao": "Graduacao", "ordem": 7},
            {"codigo": "POS", "nome": "Pos-Graduacao", "descricao": "Mestrado e Doutorado", "ordem": 8},
        ]
