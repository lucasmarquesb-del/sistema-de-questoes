"""
DTOs para Tags - Compatibilidade com views
"""
from dataclasses import dataclass, field
from typing import Optional, List, Any


@dataclass
class TagCreateDTO:
    """DTO para criação de tag"""
    nome: str
    id_tag_pai: Optional[int] = None


@dataclass
class TagUpdateDTO:
    """DTO para atualização de tag"""
    id_tag: int
    nome: str


@dataclass
class TagResponseDTO:
    """DTO para resposta de tag"""
    id: int
    uuid: str
    nome: str
    numeracao: str
    nivel: int
    caminho_completo: Optional[str] = None
    filhos: List['TagResponseDTO'] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict):
        """Cria DTO a partir de dict"""
        return cls(
            id=data.get('id', 0),
            uuid=data.get('uuid', ''),
            nome=data.get('nome', ''),
            numeracao=data.get('numeracao', ''),
            nivel=data.get('nivel', 1),
            caminho_completo=data.get('caminho_completo'),
            filhos=[]
        )
