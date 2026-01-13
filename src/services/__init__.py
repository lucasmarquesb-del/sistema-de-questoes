"""
Services - Camada de lógica de negócio usando ORM
"""
from .service_facade import services
from .questao_service import QuestaoService
from .lista_service import ListaService
from .tag_service import TagService
from .alternativa_service import AlternativaService

__all__ = [
    'services',
    'QuestaoService',
    'ListaService',
    'TagService',
    'AlternativaService',
]
