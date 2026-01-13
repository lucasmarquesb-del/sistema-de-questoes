"""
Controller: Questão (Refatorado)
DESCRIÇÃO: Controller refatorado seguindo princípios SOLID
RESPONSABILIDADE ÚNICA: Orquestrar casos de uso de questões
ARQUITETURA: Clean Architecture com camadas bem definidas
MUDANÇAS EM RELAÇÃO AO CONTROLLER ANTIGO:
    - SRP: Services especializados (Validation, Image, Statistics)
    - DIP: Depende de interfaces (IQuestaoRepository), não de Models concretos
    - OCP: Extensível via injeção de serviços
    - Funções menores e mais focadas
    - DTOs para comunicação entre camadas
    - Logging apropriado
    - Tratamento de erros consistente
"""

import logging
from typing import Optional, List, Dict, Any
from pathlib import Path

from src.domain.interfaces import IQuestaoRepository, IAlternativaRepository
from src.application.services import ValidationService, ImageService, StatisticsService
from src.application.dtos import (
    QuestaoCreateDTO,
    QuestaoUpdateDTO,
    QuestaoResponseDTO,
    FiltroQuestaoDTO
)

logger = logging.getLogger(__name__)


class QuestaoControllerRefactored:
    """Controller refatorado para operações com questões

    Segue princípios SOLID:
    - Single Responsibility: Apenas orquestra casos de uso
    - Open/Closed: Extensível via injeção de dependências
    - Liskov Substitution: Aceita qualquer implementação de IQuestaoRepository
    - Interface Segregation: Usa interfaces específicas
    - Dependency Inversion: Depende de abstrações, não de implementações
    """

    def __init__(
        self,
        questao_repository: IQuestaoRepository,
        alternativa_repository: IAlternativaRepository,
        validation_service: ValidationService,
        image_service: ImageService,
        statistics_service: StatisticsService
    ):
        """
        Args:
            questao_repository: Repositório de questões (interface)
            alternativa_repository: Repositório de alternativas (interface)
            validation_service: Serviço de validação
            image_service: Serviço de processamento de imagens
            statistics_service: Serviço de estatísticas
        """
        self.questao_repository = questao_repository
        self.alternativa_repository = alternativa_repository
        self.validation_service = validation_service
        self.image_service = image_service
        self.statistics_service = statistics_service

        logger.info("QuestaoControllerRefactored inicializado com injeção de dependências")

    def criar_questao_completa(
        self,
        dto: QuestaoCreateDTO
    ) -> Optional[int]:
        """Cria questão completa com alternativas e tags

        Args:
            dto: DTO com dados da questão

        Returns:
            ID da questão criada ou None em caso de erro

        Raises:
            ValueError: Se houver erros de validação nos dados de entrada.
        """
        try:
            # 1. Validar dados
            logger.info("Validando dados da questão")
            validacao = self.validation_service.validar_questao_completa(dto.to_dict())

            if not validacao.valido:
                logger.error(f"Validação falhou: {validacao.erros}")
                raise ValueError("Erros de validação encontrados:\n\n- " + "\n- ".join(validacao.erros))

            if validacao.avisos:
                logger.warning(f"Avisos de validação: {validacao.avisos}")

            # 2. Processar imagem (se fornecida)
            imagem_path = dto.imagem_enunciado
            if imagem_path:
                logger.info(f"Processando imagem: {imagem_path}")
                imagem_path = self.image_service.processar_imagem_questao(imagem_path)

                if not imagem_path:
                    logger.error("Falha ao processar imagem")
                    # Lançar exceção que será capturada pelo erro genérico
                    raise IOError("Falha ao processar a imagem do enunciado.")

            # 3. Criar questão no banco
            logger.info("Criando questão no banco de dados")
            id_questao = self.questao_repository.criar(
                titulo=dto.titulo,
                enunciado=dto.enunciado,
                tipo=dto.tipo,
                ano=dto.ano,
                fonte=dto.fonte,
                id_dificuldade=dto.id_dificuldade,
                resolucao=dto.resolucao,
                gabarito_discursiva=dto.gabarito_discursiva,
                observacoes=dto.observacoes,
                imagem_enunciado=imagem_path,
                escala_imagem_enunciado=dto.escala_imagem_enunciado
            )

            if not id_questao:
                logger.error("Falha ao criar questão no banco")
                raise RuntimeError("Falha ao salvar a questão principal no banco de dados.")

            logger.info(f"Questão criada com sucesso: ID {id_questao}")

            # 4. Criar alternativas (se questão objetiva)
            if dto.tipo == 'OBJETIVA' and dto.alternativas:
                logger.info(f"Criando {len(dto.alternativas)} alternativas")
                alternativas_dados = [alt.to_dict() for alt in dto.alternativas]

                sucesso = self.alternativa_repository.criar_conjunto_completo(
                    id_questao,
                    alternativas_dados
                )

                if not sucesso:
                    logger.error("Falha ao criar alternativas")
                    # Rollback: inativar questão criada
                    self.questao_repository.inativar(id_questao)
                    raise RuntimeError("Falha ao salvar as alternativas no banco de dados.")

            # 5. Vincular tags
            if dto.tags:
                logger.info(f"Vinculando {len(dto.tags)} tags")
                for id_tag in dto.tags:
                    self.questao_repository.vincular_tag(id_questao, id_tag)

            logger.info(f"Questão completa criada com sucesso: ID {id_questao}")
            return id_questao

        except ValueError as e:
            # Re-lança exceções de validação para a camada da View tratar
            logger.warning(f"Erro de validação ao criar questão: {e}")
            raise e
        except Exception as e:
            # Captura outras exceções (IOError, RuntimeError, etc.) e loga como erro grave
            logger.error(f"Erro inesperado ao criar questão completa: {e}", exc_info=True)
            return None

    def atualizar_questao_completa(
        self,
        dto: QuestaoUpdateDTO
    ) -> bool:
        """Atualiza questão completa, incluindo alternativas e tags."""
        try:
            # 1. Verificar se questão existe
            questao_atual = self.questao_repository.buscar_por_id(dto.id_questao)
            if not questao_atual:
                logger.error(f"Questão não encontrada para atualização: ID {dto.id_questao}")
                return False

            # 2. Validar dados do DTO
            dados_validacao = dto.to_dict()
            if len(dados_validacao) > 1:
                validacao = self.validation_service.validar_questao_completa(dados_validacao)
                if not validacao.valido:
                    logger.error(f"Validação da atualização falhou: {validacao.erros}")
                    raise ValueError("Erros de validação encontrados:\n\n- " + "\n- ".join(validacao.erros))

            # 3. Processar imagem (se houver)
            if dto.imagem_enunciado:
                logger.info(f"Processando nova imagem para questão ID {dto.id_questao}")
                dto.imagem_enunciado = self.image_service.processar_imagem_questao(
                    dto.imagem_enunciado, id_questao=dto.id_questao
                )
                if not dto.imagem_enunciado:
                    raise IOError("Falha ao processar a imagem do enunciado durante a atualização.")

            # 4. Atualizar dados principais da questão
            logger.info(f"Atualizando dados principais da questão ID {dto.id_questao}")
            if not self.questao_repository.atualizar(id_questao=dto.id_questao, **dto.to_dict(exclude={'id_questao', 'alternativas', 'tags'})):
                raise RuntimeError("Falha ao atualizar os dados principais da questão no banco de dados.")

            # 5. Atualizar alternativas (deletar e recriar)
            if dto.alternativas is not None:
                logger.info(f"Atualizando alternativas para questão ID {dto.id_questao}")
                if not self.alternativa_repository.deletar_por_questao(dto.id_questao):
                    raise RuntimeError("Falha ao deletar alternativas antigas.")
                
                if dto.tipo == 'OBJETIVA' and dto.alternativas:
                    alternativas_dados = [alt.to_dict() for alt in dto.alternativas]
                    if not self.alternativa_repository.criar_conjunto_completo(dto.id_questao, alternativas_dados):
                        raise RuntimeError("Falha ao criar o novo conjunto de alternativas.")

            # 6. Sincronizar tags
            if dto.tags is not None:
                logger.info(f"Sincronizando tags para questão ID {dto.id_questao}")
                tags_atuais = self.questao_repository.obter_tags(dto.id_questao)
                ids_atuais = {tag['id_tag'] for tag in tags_atuais}
                ids_novos = set(dto.tags)

                # Desvincular tags removidas
                for id_tag in ids_atuais - ids_novos:
                    self.questao_repository.desvincular_tag(dto.id_questao, id_tag)

                # Vincular novas tags
                for id_tag in ids_novos - ids_atuais:
                    self.questao_repository.vincular_tag(dto.id_questao, id_tag)

            logger.info(f"Questão ID {dto.id_questao} atualizada com sucesso.")
            return True

        except (ValueError, RuntimeError, IOError) as e:
            logger.error(f"Erro ao atualizar questão ID {dto.id_questao}: {e}")
            raise e
        except Exception as e:
            logger.error(f"Erro inesperado ao atualizar questão ID {dto.id_questao}: {e}", exc_info=True)
            return False

    def buscar_questoes(
        self,
        filtro: FiltroQuestaoDTO
    ) -> List[QuestaoResponseDTO]:
        """Busca questões com filtros

        Args:
            filtro: DTO com filtros de busca

        Returns:
            Lista de DTOs de resposta
        """
        try:
            logger.info(f"Buscando questões com filtros: {filtro.to_dict()}")

            # Desempacotar o DTO para passar como argumentos nomeados
            questoes = self.questao_repository.buscar_por_filtros(**filtro.to_dict())

            logger.info(f"Encontradas {len(questoes)} questões")

            # Converter para DTOs
            dtos = []
            for questao in questoes:
                try:
                    # O repositório já mapeia 'id_questao' para 'id'
                    dto = QuestaoResponseDTO.from_dict(questao)
                    dtos.append(dto)
                except Exception as e:
                    logger.warning(f"Erro ao converter dados da questão {questao.get('id_questao')}: {e}")

            return dtos

        except Exception as e:
            logger.error(f"Erro ao buscar questões: {e}", exc_info=True)
            return []

    def obter_questao_completa(
        self,
        id_questao: int
    ) -> Optional[QuestaoResponseDTO]:
        """Obtém questão completa com alternativas e tags

        Args:
            id_questao: ID da questão

        Returns:
            DTO de resposta ou None se não encontrada
        """
        try:
            logger.info(f"Obtendo questão completa: ID {id_questao}")

            # Buscar questão
            questao = self.questao_repository.buscar_por_id(id_questao)
            if not questao:
                logger.warning(f"Questão não encontrada: ID {id_questao}")
                return None

            # Buscar alternativas (se objetiva)
            if questao.get('tipo') == 'OBJETIVA':
                alternativas = self.alternativa_repository.buscar_por_questao(id_questao)
                questao['alternativas'] = alternativas

            # Buscar tags
            tags = self.questao_repository.obter_tags(id_questao)
            questao['tags'] = tags

            # Converter para DTO
            dto = QuestaoResponseDTO.from_dict(questao)

            logger.info(f"Questão obtida: ID {id_questao}")
            return dto

        except Exception as e:
            logger.error(f"Erro ao obter questão: {e}", exc_info=True)
            return None

    def inativar_questao(self, id_questao: int) -> bool:
        """Inativa uma questão

        Args:
            id_questao: ID da questão

        Returns:
            True se inativação bem-sucedida, False caso contrário
        """
        try:
            logger.info(f"Inativando questão: ID {id_questao}")
            sucesso = self.questao_repository.inativar(id_questao)

            if sucesso:
                logger.info(f"Questão inativada: ID {id_questao}")
            else:
                logger.warning(f"Falha ao inativar questão: ID {id_questao}")

            return sucesso

        except Exception as e:
            logger.error(f"Erro ao inativar questão: {e}", exc_info=True)
            return False

    def reativar_questao(self, id_questao: int) -> bool:
        """Reativa uma questão

        Args:
            id_questao: ID da questão

        Returns:
            True se reativação bem-sucedida, False caso contrário
        """
        try:
            logger.info(f"Reativando questão: ID {id_questao}")
            sucesso = self.questao_repository.reativar(id_questao)

            if sucesso:
                logger.info(f"Questão reativada: ID {id_questao}")
            else:
                logger.warning(f"Falha ao reativar questão: ID {id_questao}")

            return sucesso

        except Exception as e:
            logger.error(f"Erro ao reativar questão: {e}", exc_info=True)
            return False

    def obter_estatisticas(self) -> Dict[str, Any]:
        """Obtém estatísticas do sistema

        Returns:
            Dicionário com estatísticas
        """
        try:
            logger.info("Obtendo estatísticas")
            estatisticas = self.statistics_service.obter_resumo_completo()
            return estatisticas

        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}", exc_info=True)
            return {}


# Factory function para criar controller com dependências
def criar_questao_controller() -> QuestaoControllerRefactored:
    """Factory para criar QuestaoController com todas as dependências injetadas

    Returns:
        Controller configurado e pronto para uso
    """
    from src.infrastructure.repositories import (
        QuestaoRepositoryImpl,
        AlternativaRepositoryImpl
    )
    from src.models.database import db

    # Criar repositórios
    questao_repo = QuestaoRepositoryImpl()
    alternativa_repo = AlternativaRepositoryImpl()

    # Criar serviços
    validation_service = ValidationService()

    project_root = db.get_project_root()
    imagens_dir = project_root / 'imagens'
    image_service = ImageService(imagens_dir)

    statistics_service = StatisticsService(questao_repo)

    # Criar controller
    controller = QuestaoControllerRefactored(
        questao_repository=questao_repo,
        alternativa_repository=alternativa_repo,
        validation_service=validation_service,
        image_service=image_service,
        statistics_service=statistics_service
    )

    logger.info("QuestaoController criado via factory")

    return controller


logger.info("QuestaoControllerRefactored carregado")
