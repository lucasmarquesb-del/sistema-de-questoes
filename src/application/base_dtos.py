"""
DTOs simples para compatibilidade com views

Estes DTOs mantêm a mesma interface dos DTOs antigos mas são simples
dataclasses sem dependências complexas.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Any


@dataclass
class QuestaoCreateDTO:
    """DTO para criação de questão"""
    tipo: str
    enunciado: str
    titulo: Optional[str] = None
    fonte: Optional[str] = None
    ano: Optional[int] = None
    id_dificuldade: Optional[int] = None
    observacoes: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    alternativas: List[Any] = field(default_factory=list)
    resposta_objetiva: Optional[Any] = None
    resposta_discursiva: Optional[Any] = None


@dataclass
class QuestaoUpdateDTO:
    """DTO para atualização de questão"""
    id_questao: int
    tipo: str
    enunciado: str
    titulo: Optional[str] = None
    fonte: Optional[str] = None
    ano: Optional[int] = None
    id_dificuldade: Optional[int] = None
    observacoes: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    alternativas: List[Any] = field(default_factory=list)


@dataclass
class QuestaoResponseDTO:
    """DTO para resposta de questão"""
    id: int
    codigo: str
    titulo: Optional[str]
    tipo: str
    enunciado: str
    ano: Optional[int]
    fonte: Optional[str]
    dificuldade: Optional[str]
    observacoes: Optional[str]
    tags: List[str] = field(default_factory=list)
    alternativas: List[Any] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict):
        """Cria DTO a partir de dict"""
        return cls(
            id=data.get('id', 0),
            codigo=data.get('codigo', ''),
            titulo=data.get('titulo'),
            tipo=data.get('tipo', ''),
            enunciado=data.get('enunciado', ''),
            ano=data.get('ano'),
            fonte=data.get('fonte'),
            dificuldade=data.get('dificuldade'),
            observacoes=data.get('observacoes'),
            tags=data.get('tags', []),
            alternativas=data.get('alternativas', [])
        )


@dataclass
class AlternativaDTO:
    """DTO para alternativa"""
    letra: str
    texto: str
    correta: bool = False
    uuid_imagem: Optional[str] = None
    escala_imagem: float = 1.0


@dataclass
class ListaCreateDTO:
    """DTO para criação de lista"""
    titulo: str
    tipo: str = 'LISTA'
    cabecalho: Optional[str] = None
    instrucoes: Optional[str] = None
    codigos_questoes: List[str] = field(default_factory=list)


@dataclass
class ListaUpdateDTO:
    """DTO para atualização de lista"""
    id_lista: int
    titulo: str
    tipo: str = 'LISTA'
    cabecalho: Optional[str] = None
    instrucoes: Optional[str] = None


@dataclass
class ListaResponseDTO:
    """DTO para resposta de lista"""
    id: int
    codigo: str
    titulo: str
    tipo: str
    total_questoes: int
    questoes: List[QuestaoResponseDTO] = field(default_factory=list)
    tags_relacionadas: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict):
        """Cria DTO a partir de dict"""
        return cls(
            id=data.get('id', 0),
            codigo=data.get('codigo', ''),
            titulo=data.get('titulo', ''),
            tipo=data.get('tipo', ''),
            total_questoes=data.get('total_questoes', 0),
            questoes=[],
            tags_relacionadas=data.get('tags_relacionadas', [])
        )


@dataclass
class FiltroQuestaoDTO:
    """DTO para filtros de busca de questões"""
    titulo: Optional[str] = None
    tipo: Optional[str] = None
    ano_inicio: Optional[int] = None
    ano_fim: Optional[int] = None
    fonte: Optional[str] = None
    dificuldade: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    ativa: bool = True
