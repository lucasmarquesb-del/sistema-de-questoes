"""
Repository Implementation: Questão
DESCRIÇÃO: Implementação concreta do repositório de questões usando Model existente
PADRÃO: Adapter - adapta QuestaoModel existente para interface IQuestaoRepository
BENEFÍCIOS:
    - Mantém compatibilidade com código legado
    - Permite migração gradual para nova arquitetura
    - Facilita testes com mock repositories
"""

import logging
from typing import Optional, Dict, List, Any
from datetime import datetime

from src.domain.interfaces import IQuestaoRepository
from src.models.questao import QuestaoModel

logger = logging.getLogger(__name__)


class QuestaoRepositoryImpl(IQuestaoRepository):
    """Implementação de repositório de questões usando QuestaoModel"""

    def criar(
        self,
        titulo: Optional[str],
        enunciado: str,
        tipo: str,
        ano: Optional[int],
        fonte: Optional[str],
        id_dificuldade: int,
        resolucao: Optional[str],
        imagem_enunciado: Optional[str],
        escala_imagem_enunciado: Optional[float]
    ) -> Optional[int]:
        """Cria uma nova questão

        Adapta chamada para QuestaoModel.criar
        """
        try:
            # Model requer ano e fonte como obrigatórios
            # Usar valores padrão se não fornecidos
            ano_final = ano if ano is not None else datetime.now().year
            fonte_final = fonte if fonte else 'AUTORAL'

            kwargs = {
                'titulo': titulo,
                'enunciado': enunciado,
                'tipo': tipo,
                'ano': ano_final,
                'fonte': fonte_final,
                'id_dificuldade': id_dificuldade
            }

            if resolucao is not None:
                kwargs['resolucao'] = resolucao

            if imagem_enunciado is not None:
                kwargs['imagem_enunciado'] = imagem_enunciado

            if escala_imagem_enunciado is not None:
                kwargs['escala_imagem_enunciado'] = escala_imagem_enunciado

            id_questao = QuestaoModel.criar(**kwargs)

            if id_questao:
                logger.info(f"Questão criada com sucesso: ID {id_questao}")
            else:
                logger.error("Falha ao criar questão (Model retornou None)")

            return id_questao

        except Exception as e:
            logger.error(f"Erro ao criar questão: {e}", exc_info=True)
            return None

    def buscar_por_id(self, id_questao: int) -> Optional[Dict[str, Any]]:
        """Busca questão por ID"""
        try:
            questao = QuestaoModel.buscar_por_id(id_questao)

            if questao:
                # Mapear id_questao para id (compatibilidade com DTOs)
                questao['id'] = questao.get('id_questao')
                questao['ativa'] = questao.get('ativo', True)
                logger.debug(f"Questão encontrada: ID {id_questao}")
            else:
                logger.debug(f"Questão não encontrada: ID {id_questao}")

            return questao

        except Exception as e:
            logger.error(f"Erro ao buscar questão por ID: {e}", exc_info=True)
            return None

    def buscar_por_filtros(
        self,
        titulo: Optional[str] = None,
        tipo: Optional[str] = None,
        ano: Optional[int] = None,
        fonte: Optional[str] = None,
        id_dificuldade: Optional[int] = None,
        tags: Optional[List[int]] = None,
        ativa: bool = True
    ) -> List[Dict[str, Any]]:
        """Busca questões aplicando filtros"""
        try:
            kwargs = {}

            if titulo is not None:
                kwargs['titulo'] = titulo

            if tipo is not None:
                kwargs['tipo'] = tipo

            if ano is not None:
                kwargs['ano'] = ano

            if fonte is not None:
                kwargs['fonte'] = fonte

            if id_dificuldade is not None:
                kwargs['id_dificuldade'] = id_dificuldade

            if tags is not None:
                kwargs['tags'] = tags

            questoes = QuestaoModel.buscar_por_filtros(**kwargs)

            # Mapear campos e filtrar por ativa
            questoes_mapeadas = []
            for q in questoes:
                # Mapear id_questao para id e ativo para ativa
                q['id'] = q.get('id_questao')
                q['ativa'] = q.get('ativo', True)

                # Filtrar por ativa se necessário
                if ativa and not q['ativa']:
                    continue

                questoes_mapeadas.append(q)

            logger.info(
                f"Busca de questões: {len(questoes_mapeadas)} encontradas "
                f"(filtros: {len(kwargs)})"
            )

            return questoes_mapeadas

        except Exception as e:
            logger.error(f"Erro ao buscar questões por filtros: {e}", exc_info=True)
            return []

    def atualizar(
        self,
        id_questao: int,
        titulo: Optional[str] = None,
        enunciado: Optional[str] = None,
        tipo: Optional[str] = None,
        ano: Optional[int] = None,
        fonte: Optional[str] = None,
        id_dificuldade: Optional[int] = None,
        resolucao: Optional[str] = None,
        imagem_enunciado: Optional[str] = None,
        escala_imagem_enunciado: Optional[float] = None
    ) -> bool:
        """Atualiza dados de uma questão"""
        try:
            kwargs = {}

            # Adicionar apenas campos fornecidos
            if titulo is not None:
                kwargs['titulo'] = titulo

            if enunciado is not None:
                kwargs['enunciado'] = enunciado

            if tipo is not None:
                kwargs['tipo'] = tipo

            if ano is not None:
                kwargs['ano'] = ano

            if fonte is not None:
                kwargs['fonte'] = fonte

            if id_dificuldade is not None:
                kwargs['id_dificuldade'] = id_dificuldade

            if resolucao is not None:
                kwargs['resolucao'] = resolucao

            if imagem_enunciado is not None:
                kwargs['imagem_enunciado'] = imagem_enunciado

            if escala_imagem_enunciado is not None:
                kwargs['escala_imagem_enunciado'] = escala_imagem_enunciado

            sucesso = QuestaoModel.atualizar(id_questao, **kwargs)

            if sucesso:
                logger.info(
                    f"Questão atualizada: ID {id_questao} "
                    f"({len(kwargs)} campos)"
                )
            else:
                logger.warning(f"Falha ao atualizar questão: ID {id_questao}")

            return sucesso

        except Exception as e:
            logger.error(f"Erro ao atualizar questão: {e}", exc_info=True)
            return False

    def inativar(self, id_questao: int) -> bool:
        """Inativa uma questão (soft delete)"""
        try:
            sucesso = QuestaoModel.inativar(id_questao)

            if sucesso:
                logger.info(f"Questão inativada: ID {id_questao}")
            else:
                logger.warning(f"Falha ao inativar questão: ID {id_questao}")

            return sucesso

        except Exception as e:
            logger.error(f"Erro ao inativar questão: {e}", exc_info=True)
            return False

    def reativar(self, id_questao: int) -> bool:
        """Reativa uma questão inativada"""
        try:
            sucesso = QuestaoModel.reativar(id_questao)

            if sucesso:
                logger.info(f"Questão reativada: ID {id_questao}")
            else:
                logger.warning(f"Falha ao reativar questão: ID {id_questao}")

            return sucesso

        except Exception as e:
            logger.error(f"Erro ao reativar questão: {e}", exc_info=True)
            return False

    def vincular_tag(self, id_questao: int, id_tag: int) -> bool:
        """Vincula uma tag a uma questão"""
        try:
            sucesso = QuestaoModel.vincular_tag(id_questao, id_tag)

            if sucesso:
                logger.info(
                    f"Tag vinculada: questão {id_questao} <-> tag {id_tag}"
                )
            else:
                logger.warning(
                    f"Falha ao vincular tag: questão {id_questao} <-> tag {id_tag}"
                )

            return sucesso

        except Exception as e:
            logger.error(f"Erro ao vincular tag: {e}", exc_info=True)
            return False

    def desvincular_tag(self, id_questao: int, id_tag: int) -> bool:
        """Desvincula uma tag de uma questão"""
        try:
            sucesso = QuestaoModel.desvincular_tag(id_questao, id_tag)

            if sucesso:
                logger.info(
                    f"Tag desvinculada: questão {id_questao} <-> tag {id_tag}"
                )
            else:
                logger.warning(
                    f"Falha ao desvincular tag: questão {id_questao} <-> tag {id_tag}"
                )

            return sucesso

        except Exception as e:
            logger.error(f"Erro ao desvincular tag: {e}", exc_info=True)
            return False

    def obter_tags(self, id_questao: int) -> List[Dict[str, Any]]:
        """Obtém todas as tags vinculadas a uma questão"""
        try:
            tags = QuestaoModel.listar_tags(id_questao)

            logger.debug(
                f"Tags obtidas para questão {id_questao}: {len(tags)} tags"
            )

            return tags

        except Exception as e:
            logger.error(f"Erro ao obter tags: {e}", exc_info=True)
            return []

    def contar_total(self, ativa: bool = True) -> int:
        """Conta total de questões"""
        try:
            questoes = self.buscar_por_filtros(ativa=ativa)
            total = len(questoes)

            logger.debug(
                f"Total de questões {'ativas' if ativa else 'todas'}: {total}"
            )

            return total

        except Exception as e:
            logger.error(f"Erro ao contar questões: {e}", exc_info=True)
            return 0

    def contar_por_tipo(self, ativa: bool = True) -> Dict[str, int]:
        """Conta questões por tipo"""
        try:
            questoes = self.buscar_por_filtros(ativa=ativa)

            contagem = {}
            for questao in questoes:
                tipo = questao.get('tipo', 'DESCONHECIDO')
                contagem[tipo] = contagem.get(tipo, 0) + 1

            logger.debug(f"Contagem por tipo: {contagem}")

            return contagem

        except Exception as e:
            logger.error(f"Erro ao contar questões por tipo: {e}", exc_info=True)
            return {}
