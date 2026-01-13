"""
DTOs - Data Transfer Objects

Export de todos os DTOs para compatibilidade com views
"""
from .tag_dto import TagCreateDTO, TagUpdateDTO, TagResponseDTO
from .export_dto import ExportOptionsDTO

# Re-export from parent dtos.py
from ..base_dtos import (
    QuestaoCreateDTO,
    QuestaoUpdateDTO,
    QuestaoResponseDTO,
    AlternativaDTO,
    ListaCreateDTO,
    ListaUpdateDTO,
    ListaResponseDTO,
    FiltroQuestaoDTO
)

__all__ = [
    'QuestaoCreateDTO',
    'QuestaoUpdateDTO',
    'QuestaoResponseDTO',
    'AlternativaDTO',
    'ListaCreateDTO',
    'ListaUpdateDTO',
    'ListaResponseDTO',
    'FiltroQuestaoDTO',
    'TagCreateDTO',
    'TagUpdateDTO',
    'TagResponseDTO',
    'ExportOptionsDTO',
]
