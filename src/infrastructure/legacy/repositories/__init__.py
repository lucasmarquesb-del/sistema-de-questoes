"""
Repositories (Implementations)
DESCRIÇÃO: Implementações concretas das interfaces de repositório
PRINCÍPIO: Dependency Inversion - estas implementações satisfazem contratos do domínio
"""

from .questao_repository_impl import QuestaoRepositoryImpl
from .alternativa_repository_impl import AlternativaRepositoryImpl
from .tag_repository_impl import TagRepositoryImpl
from .lista_repository_impl import ListaRepositoryImpl

__all__ = [
    'QuestaoRepositoryImpl',
    'AlternativaRepositoryImpl',
    'TagRepositoryImpl',
    'ListaRepositoryImpl'
]
