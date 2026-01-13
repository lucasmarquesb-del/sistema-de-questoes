"""
Services
DESCRIÇÃO: Serviços de aplicação especializados
PRINCÍPIO: Single Responsibility - cada service tem uma responsabilidade específica
"""

from .validation_service import ValidationService
from .image_service import ImageService
from .statistics_service import StatisticsService

__all__ = [
    'ValidationService',
    'ImageService',
    'StatisticsService'
]
