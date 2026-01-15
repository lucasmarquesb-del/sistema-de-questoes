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
                'id': hash(tag.uuid) % 2147483647,  # Converter uuid para int positivo
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
                'id': hash(tag.uuid) % 2147483647,
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
                'id': hash(tag.uuid) % 2147483647,
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
            'id': hash(tag.uuid) % 2147483647,
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
            'id': hash(tag.uuid) % 2147483647,
            'uuid': tag.uuid,
            'nome': tag.nome,
            'numeracao': tag.numeracao,
            'nivel': tag.nivel,
            'caminho_completo': tag.obter_caminho_completo()
        }

    def obter_arvore_hierarquica(self, filtrar_por_nome: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retorna estrutura hierárquica completa das tags

        Args:
            filtrar_por_nome: Se fornecido, retorna apenas a árvore da tag raiz com esse nome

        Returns:
            Lista de dicts representando a árvore
        """
        def construir_arvore(tag):
            return {
                'id': hash(tag.uuid) % 2147483647,
                'uuid': tag.uuid,
                'nome': tag.nome,
                'numeracao': tag.numeracao,
                'nivel': tag.nivel,
                'filhas': [construir_arvore(filha) for filha in tag.tags_filhas if filha.ativo]
            }

        raizes = self.tag_repo.listar_raizes()

        # Filtrar por nome da tag raiz se especificado
        if filtrar_por_nome:
            raizes = [tag for tag in raizes if tag.nome.upper() == filtrar_por_nome.upper()]

        return [construir_arvore(tag) for tag in raizes]

    def obter_arvore_conteudos(self) -> List[Dict[str, Any]]:
        """
        Retorna apenas a árvore de tags de conteúdos (exclui vestibular e série)

        As tags de conteúdo têm numeração começando com número (1, 2, 3...)
        Tags de vestibular começam com "V" (V1, V2...)
        Tags de série/nível começam com "N" (N1, N2...)

        Returns:
            Lista de dicts representando a árvore de conteúdos
        """
        def construir_arvore(tag):
            return {
                'id': hash(tag.uuid) % 2147483647,
                'uuid': tag.uuid,
                'nome': tag.nome,
                'numeracao': tag.numeracao,
                'nivel': tag.nivel,
                'filhas': [construir_arvore(filha) for filha in tag.tags_filhas if filha.ativo]
            }

        raizes = self.tag_repo.listar_raizes()

        # Filtrar apenas tags de conteúdo (numeração começa com número, não V ou N)
        raizes_filtradas = [
            tag for tag in raizes
            if tag.numeracao and tag.numeracao[0].isdigit()
        ]

        return [construir_arvore(tag) for tag in raizes_filtradas]

    def listar_series(self) -> List[Dict[str, Any]]:
        """
        Lista tags de série/nível de escolaridade (numeração começa com N)

        Returns:
            Lista de dicts com dados das tags de série
        """
        raizes = self.tag_repo.listar_raizes()

        # Filtrar apenas tags de série (numeração começa com N)
        series = [
            tag for tag in raizes
            if tag.numeracao and tag.numeracao.startswith('N')
        ]

        return [
            {
                'id': hash(tag.uuid) % 2147483647,
                'uuid': tag.uuid,
                'nome': tag.nome,
                'numeracao': tag.numeracao
            }
            for tag in series
        ]
