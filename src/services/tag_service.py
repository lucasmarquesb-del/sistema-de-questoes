"""
Service para gerenciar Tags - usa apenas ORM
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from repositories import TagRepository


class TagService:
    """Service para operações de negócio com tags"""

    def __init__(self, session: Session):
        self.session = session
        self.tag_repo = TagRepository(session)

    def listar_todas(self) -> List[Dict[str, Any]]:
        """
        Lista todas as tags ativas

        Returns:
            Lista de dicts com dados das tags
        """
        tags = self.tag_repo.listar_todos()
        return [
            {
                'uuid': tag.uuid,
                'nome': tag.nome,
                'numeracao': tag.numeracao,
                'nivel': tag.nivel,
                'caminho_completo': tag.obter_caminho_completo()
            }
            for tag in tags
        ]

    def listar_raizes(self) -> List[Dict[str, Any]]:
        """
        Lista tags raiz (sem pai)

        Returns:
            Lista de tags raiz
        """
        tags = self.tag_repo.listar_raizes()
        return [
            {
                'uuid': tag.uuid,
                'nome': tag.nome,
                'numeracao': tag.numeracao,
                'nivel': tag.nivel
            }
            for tag in tags
        ]

    def listar_filhas(self, numeracao_pai: str) -> List[Dict[str, Any]]:
        """
        Lista tags filhas de uma tag pai

        Args:
            numeracao_pai: Numeração da tag pai

        Returns:
            Lista de tags filhas
        """
        tags = self.tag_repo.listar_filhas(numeracao_pai)
        return [
            {
                'uuid': tag.uuid,
                'nome': tag.nome,
                'numeracao': tag.numeracao,
                'nivel': tag.nivel
            }
            for tag in tags
        ]

    def buscar_por_nome(self, nome: str) -> Optional[Dict[str, Any]]:
        """
        Busca tag por nome

        Args:
            nome: Nome da tag

        Returns:
            Dict com dados da tag ou None
        """
        tag = self.tag_repo.buscar_por_nome(nome)
        if not tag:
            return None

        return {
            'uuid': tag.uuid,
            'nome': tag.nome,
            'numeracao': tag.numeracao,
            'nivel': tag.nivel,
            'caminho_completo': tag.obter_caminho_completo()
        }

    def buscar_por_numeracao(self, numeracao: str) -> Optional[Dict[str, Any]]:
        """
        Busca tag por numeração

        Args:
            numeracao: Numeração da tag (ex: 2.1.3)

        Returns:
            Dict com dados da tag ou None
        """
        tag = self.tag_repo.buscar_por_numeracao(numeracao)
        if not tag:
            return None

        return {
            'uuid': tag.uuid,
            'nome': tag.nome,
            'numeracao': tag.numeracao,
            'nivel': tag.nivel,
            'caminho_completo': tag.obter_caminho_completo()
        }

    def obter_arvore_hierarquica(self) -> List[Dict[str, Any]]:
        """
        Retorna estrutura hierárquica completa das tags

        Returns:
            Lista de dicts representando a árvore
        """
        def construir_arvore(tag):
            return {
                'uuid': tag.uuid,
                'nome': tag.nome,
                'numeracao': tag.numeracao,
                'nivel': tag.nivel,
                'filhas': [construir_arvore(filha) for filha in tag.tags_filhas if filha.ativo]
            }

        raizes = self.tag_repo.listar_raizes()
        return [construir_arvore(tag) for tag in raizes]
