"""
Controller: Tag
DESCRIÇÃO: Gerencia lógica de negócio de tags hierárquicas
RELACIONAMENTOS: ITagRepository, IQuestaoRepository
USADO POR: TagManager (view), QuestaoForm (view)
"""
import logging
from typing import List, Optional, Dict, Any

from src.domain.interfaces import ITagRepository, IQuestaoRepository
from src.application.dtos.tag_dto import TagCreateDTO, TagUpdateDTO, TagResponseDTO

logger = logging.getLogger(__name__)


class TagController:
    """Controller para gerenciar a lógica de negócio de Tags."""

    def __init__(self, tag_repository: ITagRepository, questao_repository: IQuestaoRepository):
        """
        Inicializa o controller com os repositórios necessários.

        Args:
            tag_repository: Repositório para operações com tags.
            questao_repository: Repositório para operações com questões (usado para validação).
        """
        self.tag_repository = tag_repository
        self.questao_repository = questao_repository
        logger.info("TagController inicializado com injeção de dependências.")

    def _build_tree(self, tags: List[Dict[str, Any]]) -> List[TagResponseDTO]:
        """Constrói uma árvore de DTOs a partir de uma lista hierárquica de dicionários."""
        tree = []
        for tag_data in tags:
            dto = TagResponseDTO.from_dict(tag_data)
            if 'filhos' in tag_data and tag_data['filhos']:
                dto.filhos = self._build_tree(tag_data['filhos'])
            tree.append(dto)
        return tree

    def obter_arvore_tags_completa(self) -> List[TagResponseDTO]:
        """
        Busca todas as tags e as retorna em uma estrutura de árvore de DTOs.

        Returns:
            Uma lista de TagResponseDTO representando a raiz da árvore.
        """
        try:
            logger.info("Buscando hierarquia completa de tags.")
            hierarquia = self.tag_repository.buscar_hierarquia_completa()
            return self._build_tree(hierarquia)
        except Exception as e:
            logger.error(f"Erro ao obter a árvore de tags: {e}", exc_info=True)
            return []

    def criar_tag(self, dto: TagCreateDTO) -> Optional[TagResponseDTO]:
        """
        Cria uma nova tag, calculando sua ordem, nível e numeração.
        """
        try:
            logger.info(f"Tentando criar nova tag: '{dto.nome}'")
            
            # 1. Obter tags no mesmo nível (irmãs)
            siblings = self.tag_repository.buscar_filhas(dto.id_tag_pai) if dto.id_tag_pai else self.tag_repository.buscar_todas(nivel=1)
            
            # 2. Validação de nome duplicado (ignora case)
            if any(s['nome'].upper() == dto.nome.upper() for s in siblings):
                raise ValueError(f"O nome '{dto.nome}' já existe nesta categoria.")
            
            # 3. Calcular ordem, nível e numeração
            ordem = (max(s['ordem'] for s in siblings) + 1) if siblings else 1
            
            if dto.id_tag_pai:
                parent_tag = self.tag_repository.buscar_por_id(dto.id_tag_pai)
                if not parent_tag:
                    raise ValueError("A tag pai especificada não foi encontrada.")
                nivel = parent_tag['nivel'] + 1
                numeracao = f"{parent_tag['numeracao']}.{ordem}"
            else:
                nivel = 1
                numeracao = str(ordem)

            # 4. Criar a tag via repositório
            id_nova_tag = self.tag_repository.criar(
                nome=dto.nome,
                numeracao=numeracao,
                nivel=nivel,
                id_pai=dto.id_tag_pai,
                ordem=ordem
            )
            if not id_nova_tag:
                return None

            # 5. Retornar a tag criada como DTO
            tag_criada = self.tag_repository.buscar_por_id(id_nova_tag)
            return TagResponseDTO.from_dict(tag_criada) if tag_criada else None

        except ValueError as ve:
            logger.warning(f"Erro de validação ao criar tag: {ve}")
            raise ve
        except Exception as e:
            logger.error(f"Erro inesperado ao criar tag: {e}", exc_info=True)
            return None

    def atualizar_tag(self, dto: TagUpdateDTO) -> bool:
        """
        Atualiza uma tag existente.
        """
        try:
            logger.info(f"Atualizando tag ID: {dto.id_tag}")
            update_data = dto.to_dict()
            del update_data['id_tag']
            
            return self.tag_repository.atualizar(dto.id_tag, **update_data)
        except Exception as e:
            logger.error(f"Erro ao atualizar tag: {e}", exc_info=True)
            return False

    def deletar_tag(self, id_tag: int) -> bool:
        """
        Deleta uma tag após validar as regras de negócio.
        """
        try:
            logger.info(f"Tentando deletar tag ID: {id_tag}")

            # 1. Regra de negócio: não permitir deletar tag com filhos
            filhos = self.tag_repository.buscar_filhas(id_tag)
            if filhos:
                raise ValueError("Não é possível excluir uma tag que possui sub-tags. Remova-as primeiro.")

            # 2. Tentar deletar via repositório (que chama o model com forcar=False)
            sucesso = self.tag_repository.deletar(id_tag)
            
            if not sucesso:
                # Se o model/repo retornou False, é porque a tag está em uso.
                raise ValueError("Não é possível excluir a tag pois ela está vinculada a uma ou mais questões.")

            return True

        except ValueError as ve:
            logger.warning(f"Falha na validação ao deletar tag: {ve}")
            raise ve
        except Exception as e:
            logger.error(f"Erro inesperado ao deletar tag: {e}", exc_info=True)
            raise RuntimeError("Ocorreu um erro inesperado ao tentar deletar a tag.") from e


def criar_tag_controller() -> TagController:
    """
    Factory para criar uma instância do TagController com suas dependências.

    Returns:
        Uma instância de TagController.
    """
    from src.infrastructure.repositories.tag_repository_impl import TagRepositoryImpl
    from src.infrastructure.repositories.questao_repository_impl import QuestaoRepositoryImpl

    tag_repo = TagRepositoryImpl()
    questao_repo = QuestaoRepositoryImpl()
    
    controller = TagController(
        tag_repository=tag_repo,
        questao_repository=questao_repo
    )
    logger.info("TagController criado via factory.")
    return controller

logger.info("TagController carregado")