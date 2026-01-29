# -*- coding: utf-8 -*-
"""
Model ORM para a tabela disciplina.

Representa as disciplinas do sistema (Matematica, Fisica, Portugues, etc.)
Cada disciplina possui seus proprios conteudos (tags).
"""

import uuid
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text
from sqlalchemy.orm import relationship

from src.models.orm.base import Base

if TYPE_CHECKING:
    from src.models.orm.tag import Tag


class Disciplina(Base):
    """
    Model para disciplinas.
    
    Attributes:
        uuid: Identificador unico (UUID)
        codigo: Codigo curto (MAT, FIS, QUI, etc.)
        nome: Nome completo (Matematica, Fisica, etc.)
        descricao: Descricao da disciplina
        cor: Cor para exibicao na UI (hexadecimal)
        ordem: Ordem de exibicao
        ativo: Se esta ativa para uso
        data_criacao: Data de criacao do registro
    """
    
    __tablename__ = 'disciplina'
    
    # Colunas
    uuid = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    codigo = Column(String(10), unique=True, nullable=False)
    nome = Column(String(100), nullable=False)
    descricao = Column(Text, nullable=True)
    cor = Column(String(7), default='#3498db')
    ordem = Column(Integer, nullable=False, default=0)
    ativo = Column(Boolean, nullable=False, default=True)
    data_criacao = Column(DateTime, default=datetime.now)
    
    # Relacionamentos
    tags = relationship("Tag", back_populates="disciplina", lazy="dynamic")
    
    def __repr__(self) -> str:
        return f"<Disciplina(uuid='{self.uuid[:8]}...', codigo='{self.codigo}', nome='{self.nome}')>"
    
    def __str__(self) -> str:
        return f"{self.codigo} - {self.nome}"
    
    def to_dict(self) -> dict:
        """Converte o model para dicionario."""
        return {
            "uuid": self.uuid,
            "codigo": self.codigo,
            "nome": self.nome,
            "descricao": self.descricao,
            "cor": self.cor,
            "ordem": self.ordem,
            "ativo": self.ativo,
            "data_criacao": self.data_criacao.isoformat() if self.data_criacao else None,
        }
    
    @property
    def total_conteudos(self) -> int:
        """Retorna o total de conteudos (tags) da disciplina."""
        return self.tags.count()
    
    @property
    def conteudos_raiz(self) -> List["Tag"]:
        """Retorna apenas os conteudos de primeiro nivel (sem pai)."""
        return [tag for tag in self.tags if tag.uuid_tag_pai is None]
    
    @classmethod
    def gerar_uuid(cls) -> str:
        """Gera um novo UUID."""
        return str(uuid.uuid4())
    
    @classmethod
    def get_disciplinas_padrao(cls) -> List[dict]:
        """Retorna disciplinas padrao para insercao inicial."""
        return [
            {"codigo": "MAT", "nome": "Matematica", "descricao": "Matematica e Raciocinio Logico", "cor": "#3498db", "ordem": 1},
            {"codigo": "FIS", "nome": "Fisica", "descricao": "Fisica Geral e Aplicada", "cor": "#e74c3c", "ordem": 2},
            {"codigo": "QUI", "nome": "Quimica", "descricao": "Quimica Geral, Organica e Inorganica", "cor": "#9b59b6", "ordem": 3},
            {"codigo": "BIO", "nome": "Biologia", "descricao": "Biologia Geral, Ecologia e Genetica", "cor": "#27ae60", "ordem": 4},
            {"codigo": "POR", "nome": "Portugues", "descricao": "Lingua Portuguesa e Literatura", "cor": "#f39c12", "ordem": 5},
            {"codigo": "RED", "nome": "Redacao", "descricao": "Producao Textual", "cor": "#e67e22", "ordem": 6},
            {"codigo": "HIS", "nome": "Historia", "descricao": "Historia Geral e do Brasil", "cor": "#1abc9c", "ordem": 7},
            {"codigo": "GEO", "nome": "Geografia", "descricao": "Geografia Geral e do Brasil", "cor": "#16a085", "ordem": 8},
            {"codigo": "FIL", "nome": "Filosofia", "descricao": "Filosofia Geral", "cor": "#8e44ad", "ordem": 9},
            {"codigo": "SOC", "nome": "Sociologia", "descricao": "Sociologia Geral", "cor": "#2c3e50", "ordem": 10},
            {"codigo": "ING", "nome": "Ingles", "descricao": "Lingua Inglesa", "cor": "#c0392b", "ordem": 11},
            {"codigo": "ESP", "nome": "Espanhol", "descricao": "Lingua Espanhola", "cor": "#d35400", "ordem": 12},
        ]
