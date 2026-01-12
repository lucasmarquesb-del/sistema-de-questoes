"""
DTOs: Lista
DESCRIÇÃO: Data Transfer Objects para operações com listas
"""

from typing import Optional, List
from dataclasses import dataclass, field


@dataclass
class ListaCreateDTO:
    """DTO para criação de lista"""

    titulo: str
    tipo: Optional[str] = None
    cabecalho: Optional[str] = None
    instrucoes: Optional[str] = None

    def to_dict(self) -> dict:
        """Converte para dicionário"""
        return {
            'titulo': self.titulo,
            'tipo': self.tipo,
            'cabecalho': self.cabecalho,
            'instrucoes': self.instrucoes
        }


@dataclass
class ListaUpdateDTO:
    """DTO para atualização de lista"""

    id_lista: int
    titulo: Optional[str] = None
    tipo: Optional[str] = None
    cabecalho: Optional[str] = None
    instrucoes: Optional[str] = None

    def to_dict(self) -> dict:
        """Converte para dicionário (apenas campos não-None)"""
        dados = {'id_lista': self.id_lista}

        if self.titulo is not None:
            dados['titulo'] = self.titulo

        if self.tipo is not None:
            dados['tipo'] = self.tipo

        if self.cabecalho is not None:
            dados['cabecalho'] = self.cabecalho

        if self.instrucoes is not None:
            dados['instrucoes'] = self.instrucoes

        return dados


@dataclass
class ListaResponseDTO:
    """DTO para resposta de lista"""

    id: int
    titulo: str
    tipo: Optional[str]
    cabecalho: Optional[str]
    instrucoes: Optional[str]
    data_criacao: str
    total_questoes: int = 0  # Adicionado campo para a contagem de questões
    questoes: List[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Converte para dicionário"""
        return {
            'id': self.id,
            'titulo': self.titulo,
            'tipo': self.tipo,
            'cabecalho': self.cabecalho,
            'instrucoes': self.instrucoes,
            'data_criacao': self.data_criacao,
            'total_questoes': self.total_questoes,
            'questoes': self.questoes
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ListaResponseDTO':
        """Cria DTO a partir de dicionário"""
        return cls(
            id=data['id'],
            titulo=data['titulo'],
            tipo=data.get('tipo'),
            cabecalho=data.get('cabecalho'),
            instrucoes=data.get('instrucoes'),
            data_criacao=data.get('data_criacao', ''),
            total_questoes=data.get('total_questoes', 0), # Popula o novo campo
            questoes=data.get('questoes', [])
        )
