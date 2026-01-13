"""
Repository Implementation: Tag
DESCRIÇÃO: Implementação concreta do repositório de tags
PADRÃO: Adapter para TagModel existente
"""

import logging
from typing import Optional, Dict, List, Any

from src.domain.interfaces import ITagRepository
from src.models.tag import TagModel

logger = logging.getLogger(__name__)


class TagRepositoryImpl(ITagRepository):
    """Implementação de repositório de tags usando TagModel."""

    def criar(self, nome: str, numeracao: str, nivel: int, id_pai: Optional[int], ordem: int) -> Optional[int]:
        """Cria uma tag. Note que o nome já é convertido para maiúsculo pelo Model."""
        try:
            return TagModel.criar(
                nome=nome,
                numeracao=numeracao,
                nivel=nivel,
                id_tag_pai=id_pai, # Mapeando para o nome correto do argumento do Model
                ordem=ordem
            )
        except Exception as e:
            logger.error(f"Erro ao criar tag no repositório: {e}", exc_info=True)
            return None

    def buscar_por_id(self, id_tag: int) -> Optional[Dict[str, Any]]:
        """Busca tag por ID."""
        return TagModel.buscar_por_id(id_tag)

    def buscar_todas(self, nivel: Optional[int] = None, apenas_ativas: bool = True) -> List[Dict[str, Any]]:
        """Busca todas as tags, opcionalmente filtrando por nível."""
        if nivel is not None:
            # Corrigindo o nome do método chamado
            return TagModel.listar_por_nivel(nivel, apenas_ativas=apenas_ativas)
        return TagModel.listar_todas(apenas_ativas=apenas_ativas)

    def buscar_filhas(self, id_tag_pai: int) -> List[Dict[str, Any]]:
        """Busca tags filhas de uma tag pai."""
        return TagModel.listar_filhas(id_tag_pai)

    def buscar_hierarquia_completa(self) -> List[Dict[str, Any]]:
        """
        Busca toda hierarquia de tags e a constrói como uma árvore.
        Este método implementa a lógica que estava faltando.
        """
        try:
            logger.debug("Construindo hierarquia de tags no repositório...")
            tags = TagModel.listar_todas(apenas_ativas=True)
            contagem_questoes = TagModel.contar_questoes_por_tag()

            tags_map = {}
            for tag in tags:
                tag['filhos'] = []
                tag['questoes'] = contagem_questoes.get(tag['id_tag'], 0)
                tags_map[tag['id_tag']] = tag
            
            hierarquia = []
            for tag in tags:
                if tag['id_tag_pai']:
                    if tag['id_tag_pai'] in tags_map:
                        tags_map[tag['id_tag_pai']]['filhos'].append(tag)
                else:
                    hierarquia.append(tag)
            
            logger.debug("Hierarquia de tags construída com sucesso.")
            return hierarquia
        except Exception as e:
            logger.error(f"Erro ao construir hierarquia de tags: {e}", exc_info=True)
            return []

    def atualizar(self, id_tag: int, **kwargs) -> bool:
        """Atualiza uma tag. O nome do argumento 'id_pai' é mapeado para 'id_tag_pai'."""
        try:
            # O model já lida com kwargs, mas mapeamos 'id_pai' se ele vier do controller
            if 'id_pai' in kwargs:
                kwargs['id_tag_pai'] = kwargs.pop('id_pai')
            
            return TagModel.atualizar(id_tag, **kwargs)
        except Exception as e:
            logger.error(f"Erro ao atualizar tag no repositório: {e}", exc_info=True)
            return False

    def deletar(self, id_tag: int) -> bool:
        """
        Deleta uma tag usando a lógica de negócio do Model.
        O Model já verifica se a tag está em uso.
        """
        try:
            # O model retorna False se a tag estiver em uso e forcar=False
            return TagModel.deletar(id_tag, forcar=False)
        except Exception as e:
            logger.error(f"Erro ao deletar tag no repositório: {e}", exc_info=True)
            return False