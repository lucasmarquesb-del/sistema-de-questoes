"""
DTOs (Data Transfer Objects)
DESCRIÇÃO: Objetos para transferência de dados entre camadas
PRINCÍPIO: Desacoplamento - Views não precisam conhecer estrutura do domínio
BENEFÍCIOS:
    - API estável entre camadas
    - Facilita versionamento
    - Valida dados na entrada
"""

from .questao_dto import (
    QuestaoCreateDTO,
    QuestaoUpdateDTO,
    QuestaoResponseDTO,
    AlternativaDTO
)
from .lista_dto import (
    ListaCreateDTO,
    ListaUpdateDTO,
    ListaResponseDTO
)
from .filtro_dto import FiltroQuestaoDTO

__all__ = [
    'QuestaoCreateDTO',
    'QuestaoUpdateDTO',
    'QuestaoResponseDTO',
    'AlternativaDTO',
    'ListaCreateDTO',
    'ListaUpdateDTO',
    'ListaResponseDTO',
    'FiltroQuestaoDTO'
]
