"""
Controller: Lista
DESCRIÇÃO: Gerencia a lógica de negócio para criação e manipulação de listas de questões.
"""
import logging
from typing import List, Optional

from src.domain.interfaces import IListaRepository, IQuestaoRepository
from src.application.dtos.lista_dto import ListaCreateDTO, ListaUpdateDTO, ListaResponseDTO
from src.application.dtos.questao_dto import QuestaoResponseDTO

logger = logging.getLogger(__name__)


class ListaController:
    """Controller para orquestrar as operações de listas de questões."""

    def __init__(self, lista_repository: IListaRepository, questao_repository: IQuestaoRepository):
        self.lista_repository = lista_repository
        self.questao_repository = questao_repository
        logger.info("ListaController inicializado com injeção de dependências.")

    def criar_lista(self, dto: ListaCreateDTO) -> Optional[int]:
        """Cria uma nova lista."""
        try:
            logger.info(f"Criando nova lista com título: {dto.titulo}")
            return self.lista_repository.criar(**dto.to_dict())
        except Exception as e:
            logger.error(f"Erro ao criar lista: {e}", exc_info=True)
            return None

    def atualizar_lista(self, dto: ListaUpdateDTO) -> bool:
        """Atualiza os metadados de uma lista existente."""
        try:
            logger.info(f"Atualizando lista ID: {dto.id_lista}")
            update_data = dto.to_dict()
            id_lista = update_data.pop('id_lista')
            return self.lista_repository.atualizar(id_lista, **update_data)
        except Exception as e:
            logger.error(f"Erro ao atualizar lista ID {dto.id_lista}: {e}", exc_info=True)
            return False

    def deletar_lista(self, id_lista: int) -> bool:
        """Deleta uma lista e seus vínculos com questões."""
        try:
            logger.info(f"Deletando lista ID: {id_lista}")
            return self.lista_repository.deletar(id_lista)
        except Exception as e:
            logger.error(f"Erro ao deletar lista ID {id_lista}: {e}", exc_info=True)
            return False

    def listar_todas_listas(self) -> List[ListaResponseDTO]:
        """Retorna uma lista com todas as listas cadastradas."""
        try:
            logger.info("Listando todas as listas.")
            listas_data = self.lista_repository.buscar_todas()
            # Mapear o id do repo para o id do DTO
            dtos = []
            for item in listas_data:
                item['id'] = item.get('id_lista')
                dtos.append(ListaResponseDTO.from_dict(item))
            return dtos
        except Exception as e:
            logger.error(f"Erro ao listar todas as listas: {e}", exc_info=True)
            return []

    def obter_lista_completa(self, id_lista: int) -> Optional[ListaResponseDTO]:
        """Retorna os detalhes de uma lista, incluindo suas questões."""
        try:
            logger.info(f"Buscando lista completa ID: {id_lista}")
            lista_data = self.lista_repository.buscar_por_id(id_lista)
            if not lista_data:
                return None
            
            questoes_data = self.lista_repository.obter_questoes(id_lista)
            
            # Mapear 'id_questao' para 'id' para cada questão nos dados brutos
            for q in questoes_data:
                q['id'] = q.get('id_questao') # Garante que 'id' esteja presente para o DTO
            
            # Mapear para DTOs
            lista_data['id'] = lista_data.get('id_lista')
            lista_dto = ListaResponseDTO.from_dict(lista_data)
            lista_dto.questoes = [QuestaoResponseDTO.from_dict(q) for q in questoes_data]
            
            return lista_dto
        except Exception as e:
            logger.error(f"Erro ao obter lista completa ID {id_lista}: {e}", exc_info=True)
            return None

    def adicionar_questao_lista(self, id_lista: int, id_questao: int) -> bool:
        """Adiciona uma questão a uma lista."""
        try:
            logger.info(f"Adicionando questão {id_questao} à lista {id_lista}")
            # A interface do repositório espera 'ordem', mas o model não usa. Passamos um valor padrão.
            return self.lista_repository.adicionar_questao(id_lista, id_questao, ordem=0)
        except Exception as e:
            logger.error(f"Erro ao adicionar questão à lista: {e}", exc_info=True)
            return False

    def remover_questao_lista(self, id_lista: int, id_questao: int) -> bool:
        """Remove uma questão de uma lista."""
        try:
            logger.info(f"Removendo questão {id_questao} da lista {id_lista}")
            return self.lista_repository.remover_questao(id_lista, id_questao)
        except Exception as e:
            logger.error(f"Erro ao remover questão da lista: {e}", exc_info=True)
            return False


def criar_lista_controller() -> ListaController:
    """Factory para criar uma instância do ListaController com suas dependências."""
    from src.infrastructure.repositories.lista_repository_impl import ListaRepositoryImpl
    from src.infrastructure.repositories.questao_repository_impl import QuestaoRepositoryImpl

    lista_repo = ListaRepositoryImpl()
    questao_repo = QuestaoRepositoryImpl()
    
    controller = ListaController(
        lista_repository=lista_repo,
        questao_repository=questao_repo
    )
    logger.info("ListaController criado via factory.")
    return controller