"""
Repository Implementation: Lista
DESCRIÇÃO: Implementação concreta do repositório de listas usando Model existente
PADRÃO: Adapter - adapta ListaModel existente para interface IListaRepository
"""

import logging
from typing import Optional, Dict, List, Any

from src.domain.interfaces import IListaRepository
from src.models.lista import ListaModel

logger = logging.getLogger(__name__)


class ListaRepositoryImpl(IListaRepository):
    """Implementação de repositório de listas usando ListaModel."""

    def criar(
        self,
        titulo: str,
        tipo: Optional[str] = None,
        cabecalho: Optional[str] = None,
        instrucoes: Optional[str] = None
    ) -> Optional[int]:
        """Cria uma lista."""
        try:
            return ListaModel.criar(titulo, tipo, cabecalho, instrucoes)
        except Exception as e:
            logger.error(f"Erro ao criar lista no repositório: {e}", exc_info=True)
            return None

    def buscar_por_id(self, id_lista: int) -> Optional[Dict[str, Any]]:
        """Busca lista por ID."""
        try:
            return ListaModel.buscar_por_id(id_lista)
        except Exception as e:
            logger.error(f"Erro ao buscar lista por ID no repositório: {e}", exc_info=True)
            return None

    def buscar_todas(self) -> List[Dict[str, Any]]:
        """Busca todas as listas."""
        try:
            return ListaModel.listar_todas()
        except Exception as e:
            logger.error(f"Erro ao buscar todas as listas no repositório: {e}", exc_info=True)
            return []

    def atualizar(
        self,
        id_lista: int,
        titulo: Optional[str] = None,
        tipo: Optional[str] = None,
        cabecalho: Optional[str] = None,
        instrucoes: Optional[str] = None
    ) -> bool:
        """Atualiza uma lista."""
        try:
            return ListaModel.atualizar(id_lista, titulo, tipo, cabecalho, instrucoes)
        except Exception as e:
            logger.error(f"Erro ao atualizar lista no repositório: {e}", exc_info=True)
            return False

    def deletar(self, id_lista: int) -> bool:
        """Deleta uma lista."""
        try:
            return ListaModel.deletar(id_lista)
        except Exception as e:
            logger.error(f"Erro ao deletar lista no repositório: {e}", exc_info=True)
            return False

    def adicionar_questao(self, id_lista: int, id_questao: int, ordem: int) -> bool:
        """Adiciona questão a uma lista."""
        # O model atual não usa 'ordem', mas a interface exige.
        # A lógica de ordenação precisaria ser implementada no model 'lista_questao'
        try:
            return ListaModel.adicionar_questao(id_lista, id_questao)
        except Exception as e:
            logger.error(f"Erro ao adicionar questão à lista no repositório: {e}", exc_info=True)
            return False

    def remover_questao(self, id_lista: int, id_questao: int) -> bool:
        """Remove questão de uma lista."""
        try:
            return ListaModel.remover_questao(id_lista, id_questao)
        except Exception as e:
            logger.error(f"Erro ao remover questão da lista no repositório: {e}", exc_info=True)
            return False

    def obter_questoes(self, id_lista: int) -> List[Dict[str, Any]]:
        """Obtém questões de uma lista."""
        try:
            return ListaModel.listar_questoes(id_lista)
        except Exception as e:
            logger.error(f"Erro ao obter questões da lista no repositório: {e}", exc_info=True)
            return []

    def reordenar_questoes(self, id_lista: int, questoes_ordem: List[tuple[int, int]]) -> bool:
        """Reordena questões de uma lista."""
        # Esta funcionalidade não existe no model atual.
        # Seria necessário implementar uma lógica de atualização da ordem na tabela 'lista_questao'
        logger.warning("A funcionalidade 'reordenar_questoes' não está implementada no model.")
        return False