"""
Repository Implementation: Alternativa
DESCRIÇÃO: Implementação concreta do repositório de alternativas
PADRÃO: Adapter para AlternativaModel existente
"""

import logging
from typing import Optional, Dict, List, Any

from src.domain.interfaces import IAlternativaRepository
from src.models.alternativa import AlternativaModel
from src.models.database import db

logger = logging.getLogger(__name__)


class AlternativaRepositoryImpl(IAlternativaRepository):
    """Implementação de repositório de alternativas"""

    def criar(
        self,
        id_questao: int,
        letra: str,
        texto: str,
        correta: bool = False,
        imagem: Optional[str] = None,
        escala_imagem: Optional[float] = None
    ) -> Optional[int]:
        """Cria uma alternativa"""
        try:
            kwargs = {
                'letra': letra,
                'texto': texto,
                'correta': correta
            }
            if imagem is not None:
                kwargs['imagem'] = imagem
            if escala_imagem is not None:
                kwargs['escala_imagem'] = escala_imagem
            id_alternativa = AlternativaModel.criar(id_questao, **kwargs)
            if id_alternativa:
                logger.info(f"Alternativa criada: {letra} (questão {id_questao})")
            return id_alternativa
        except Exception as e:
            logger.error(f"Erro ao criar alternativa: {e}", exc_info=True)
            return None

    def criar_conjunto_completo(
        self,
        id_questao: int,
        alternativas_dados: List[Dict[str, Any]]
    ) -> bool:
        """Cria conjunto completo de 5 alternativas"""
        try:
            sucesso = AlternativaModel.criar_conjunto_completo(
                id_questao,
                alternativas_dados
            )
            if sucesso:
                logger.info(f"Conjunto de alternativas criado: questão {id_questao}")
            return sucesso
        except Exception as e:
            logger.error(f"Erro ao criar conjunto de alternativas: {e}", exc_info=True)
            return False

    def buscar_por_questao(self, id_questao: int) -> List[Dict[str, Any]]:
        """Busca todas alternativas de uma questão"""
        try:
            alternativas = AlternativaModel.listar_por_questao(id_questao)
            logger.debug(f"Alternativas obtidas: {len(alternativas)} (questão {id_questao})")
            return alternativas
        except Exception as e:
            logger.error(f"Erro ao buscar alternativas: {e}", exc_info=True)
            return []

    def atualizar(
        self,
        id_alternativa: int,
        texto: Optional[str] = None,
        correta: Optional[bool] = None,
        imagem: Optional[str] = None,
        escala_imagem: Optional[float] = None
    ) -> bool:
        """Atualiza uma alternativa"""
        try:
            kwargs = {}
            if texto is not None:
                kwargs['texto'] = texto
            if correta is not None:
                kwargs['correta'] = correta
            if imagem is not None:
                kwargs['imagem'] = imagem
            if escala_imagem is not None:
                kwargs['escala_imagem'] = escala_imagem
            sucesso = AlternativaModel.atualizar(id_alternativa, **kwargs)
            if sucesso:
                logger.info(f"Alternativa atualizada: ID {id_alternativa}")
            return sucesso
        except Exception as e:
            logger.error(f"Erro ao atualizar alternativa: {e}", exc_info=True)
            return False

    def validar_alternativas(self, id_questao: int) -> Dict[str, Any]:
        """Valida estrutura de alternativas de uma questão"""
        try:
            resultado = AlternativaModel.validar_alternativas(id_questao)
            logger.debug(f"Validação de alternativas: questão {id_questao}")
            return resultado
        except Exception as e:
            logger.error(f"Erro ao validar alternativas: {e}", exc_info=True)
            return {'valido': False, 'total': 0, 'tem_correta': False, 'erros': [str(e)]}

    def deletar_por_questao(self, id_questao: int) -> bool:
        """Deleta todas as alternativas de uma questão."""
        try:
            logger.info(f"Deletando todas as alternativas da questão ID: {id_questao}")
            query = "DELETE FROM alternativa WHERE id_questao = ?"
            # Retorna True se a operação for bem-sucedida, mesmo que nenhuma linha seja afetada
            db.execute_update(query, (id_questao,))
            return True
        except Exception as e:
            logger.error(f"Erro ao deletar alternativas por questão: {e}", exc_info=True)
            return False
