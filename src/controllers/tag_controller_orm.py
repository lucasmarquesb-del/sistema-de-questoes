"""
TagController - Nova versão usando ORM + Service Layer
Substitui tag_controller.py (legacy)
"""
from typing import Dict, List, Optional, Any
from services import services
from src.application.dtos.tag_dto import TagResponseDTO


class TagControllerORM:
    """
    Controller para operações de tags usando ORM e Service Layer

    IMPORTANTE: Este controller usa a Service Facade com UUIDs e estrutura hierárquica
    """

    @staticmethod
    def listar_todas() -> List[Dict[str, Any]]:
        """
        Lista todas as tags ativas

        Returns:
            Lista de dicts com dados das tags (uuid, nome, numeracao, nivel, caminho_completo)
        """
        try:
            return services.tag.listar_todas()
        except Exception as e:
            print(f"Erro ao listar tags: {e}")
            return []

    @staticmethod
    def listar_raizes() -> List[Dict[str, Any]]:
        """
        Lista apenas tags raiz (sem pai)

        Returns:
            Lista de tags raiz
        """
        try:
            return services.tag.listar_raizes()
        except Exception as e:
            print(f"Erro ao listar tags raiz: {e}")
            return []

    @staticmethod
    def listar_filhas(numeracao_pai: str) -> List[Dict[str, Any]]:
        """
        Lista tags filhas de uma tag pai

        Args:
            numeracao_pai: Numeração da tag pai (ex: '2.1')

        Returns:
            Lista de tags filhas
        """
        try:
            return services.tag.listar_filhas(numeracao_pai)
        except Exception as e:
            print(f"Erro ao listar tags filhas: {e}")
            return []

    @staticmethod
    def buscar_por_nome(nome: str) -> Optional[Dict[str, Any]]:
        """
        Busca tag por nome

        Args:
            nome: Nome da tag

        Returns:
            Dict com dados da tag ou None
        """
        try:
            return services.tag.buscar_por_nome(nome)
        except Exception as e:
            print(f"Erro ao buscar tag por nome: {e}")
            return None

    @staticmethod
    def buscar_por_numeracao(numeracao: str) -> Optional[Dict[str, Any]]:
        """
        Busca tag por numeração

        Args:
            numeracao: Numeração da tag (ex: '2.1.3')

        Returns:
            Dict com dados da tag ou None
        """
        try:
            return services.tag.buscar_por_numeracao(numeracao)
        except Exception as e:
            print(f"Erro ao buscar tag por numeração: {e}")
            return None

    @staticmethod
    def obter_arvore_hierarquica() -> List[TagResponseDTO]:
        """
        Retorna estrutura hierárquica completa das tags

        Returns:
            Lista de TagResponseDTOs representando a árvore de tags
        """
        try:
            tree_dicts = services.tag.obter_arvore_hierarquica()

            def convert_to_dto_recursive(node_dict):
                dto = TagResponseDTO.from_dict(node_dict)
                if 'filhas' in node_dict and node_dict['filhas']:
                    dto.filhos = [convert_to_dto_recursive(child) for child in node_dict['filhas']]
                return dto

            return [convert_to_dto_recursive(root_dict) for root_dict in tree_dicts]

        except Exception as e:
            print(f"Erro ao obter árvore hierárquica: {e}")
            return []
