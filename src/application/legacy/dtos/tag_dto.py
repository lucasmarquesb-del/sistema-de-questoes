"""
Módulo: tag_dto.py
Descrição: Contém os Data Transfer Objects (DTOs) para a entidade Tag.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class TagCreateDTO:
    """DTO para criação de uma nova tag."""
    nome: str
    id_tag_pai: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Converte o DTO para um dicionário."""
        return {
            "nome": self.nome,
            "id_tag_pai": self.id_tag_pai
        }


@dataclass
class TagUpdateDTO:
    """DTO para atualização de uma tag existente."""
    id_tag: int
    nome: Optional[str] = None
    ordem: Optional[int] = None
    id_tag_pai: Optional[int] = None  # Permitir mover a tag na hierarquia

    def to_dict(self) -> Dict[str, Any]:
        """Converte o DTO para um dicionário, incluindo apenas os campos não-nulos."""
        data = {"id_tag": self.id_tag}
        if self.nome is not None:
            data["nome"] = self.nome
        if self.ordem is not None:
            data["ordem"] = self.ordem
        # Nota: enviar id_tag_pai como None é uma ação válida (mover para a raiz)
        if 'id_tag_pai' in self.__dict__:
            data["id_tag_pai"] = self.id_tag_pai
        return data


@dataclass
class TagResponseDTO:
    """DTO para representar uma tag na camada de apresentação (View)."""
    id_tag: int
    nome: str
    numeracao: Optional[str]
    nivel: int
    id_tag_pai: Optional[int]
    filhos: List['TagResponseDTO'] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TagResponseDTO':
        """Cria um DTO a partir de um dicionário (ex: vindo do repositório)."""
        return cls(
            id_tag=data.get('id_tag'),
            nome=data.get('nome'),
            numeracao=data.get('numeracao'),
            nivel=data.get('nivel'),
            id_tag_pai=data.get('id_tag_pai'),
            filhos=[]  # Filhos são populados separadamente em uma etapa de construção da árvore
        )
