"""
DTOs - Data Transfer Objects

Export de todos os DTOs para compatibilidade com views
"""
from .tag_dto import TagCreateDTO, TagUpdateDTO, TagResponseDTO
from .export_dto import ExportOptionsDTO

# Re-export from parent dtos.py
import sys
from pathlib import Path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from dtos import (
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
