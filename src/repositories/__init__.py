"""
Módulo de Repositories - Camada de acesso a dados com ORM
"""
from .base_repository import BaseRepository
from .questao_repository import QuestaoRepository
from .resposta_questao_repository import RespostaQuestaoRepository
from .alternativa_repository import AlternativaRepository
from .tag_repository import TagRepository
from .lista_repository import ListaRepository
from .dificuldade_repository import DificuldadeRepository
from .imagem_repository import ImagemRepository
from .fonte_questao_repository import FonteQuestaoRepository
from .ano_referencia_repository import AnoReferenciaRepository
from .tipo_questao_repository import TipoQuestaoRepository

__all__ = [
    'BaseRepository',
    'QuestaoRepository',
    'RespostaQuestaoRepository',
    'AlternativaRepository',
    'TagRepository',
    'ListaRepository',
    'DificuldadeRepository',
    'ImagemRepository',
    'FonteQuestaoRepository',
    'AnoReferenciaRepository',
    'TipoQuestaoRepository',
]
