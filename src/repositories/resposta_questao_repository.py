"""
Repository para Respostas de Questões (Unificado)
"""
from typing import Optional
from sqlalchemy.orm import Session
from models.orm import RespostaQuestao, Questao
from .base_repository import BaseRepository


class RespostaQuestaoRepository(BaseRepository[RespostaQuestao]):
    """Repository para Respostas (objetivas + discursivas)"""

    def __init__(self, session: Session):
        super().__init__(RespostaQuestao, session)

    def buscar_por_questao(self, codigo_questao: str) -> Optional[RespostaQuestao]:
        """
        Busca resposta por código da questão

        Args:
            codigo_questao: Código da questão

        Returns:
            Resposta ou None
        """
        questao = self.session.query(Questao).filter_by(
            codigo=codigo_questao,
            ativo=True
        ).first()

        if not questao:
            return None

        return self.session.query(RespostaQuestao).filter_by(
            uuid_questao=questao.uuid
        ).first()

    def criar_resposta_objetiva(
        self,
        codigo_questao: str,
        uuid_alternativa_correta: str,
        resolucao: Optional[str] = None,
        justificativa: Optional[str] = None,
        autor: Optional[str] = None
    ) -> Optional[RespostaQuestao]:
        """
        Cria resposta para questão objetiva

        Args:
            codigo_questao: Código da questão
            uuid_alternativa_correta: UUID da alternativa correta
            resolucao: Resolução detalhada
            justificativa: Justificativa da resposta
            autor: Autor da resolução

        Returns:
            Resposta criada ou None
        """
        questao = self.session.query(Questao).filter_by(
            codigo=codigo_questao,
            ativo=True
        ).first()

        if not questao:
            return None

        return RespostaQuestao.criar_resposta_objetiva(
            self.session,
            uuid_questao=questao.uuid,
            uuid_alternativa_correta=uuid_alternativa_correta,
            resolucao=resolucao,
            justificativa=justificativa,
            autor=autor
        )

    def criar_resposta_discursiva(
        self,
        codigo_questao: str,
        gabarito_discursivo: str,
        resolucao: Optional[str] = None,
        justificativa: Optional[str] = None,
        autor: Optional[str] = None
    ) -> Optional[RespostaQuestao]:
        """
        Cria resposta para questão discursiva

        Args:
            codigo_questao: Código da questão
            gabarito_discursivo: Gabarito em LaTeX
            resolucao: Resolução detalhada
            justificativa: Critérios de avaliação
            autor: Autor da resolução

        Returns:
            Resposta criada ou None
        """
        questao = self.session.query(Questao).filter_by(
            codigo=codigo_questao,
            ativo=True
        ).first()

        if not questao:
            return None

        return RespostaQuestao.criar_resposta_discursiva(
            self.session,
            uuid_questao=questao.uuid,
            gabarito_discursivo=gabarito_discursivo,
            resolucao=resolucao,
            justificativa=justificativa,
            autor=autor
        )

    def atualizar_resolucao(
        self,
        codigo_questao: str,
        resolucao: str,
        autor: Optional[str] = None
    ) -> Optional[RespostaQuestao]:
        """
        Atualiza a resolução de uma resposta

        Args:
            codigo_questao: Código da questão
            resolucao: Nova resolução
            autor: Autor da resolução

        Returns:
            Resposta atualizada ou None
        """
        resposta = self.buscar_por_questao(codigo_questao)
        if resposta:
            resposta.resolucao = resolucao
            if autor:
                resposta.autor_resolucao = autor
            self.session.flush()
        return resposta

    def eh_objetiva(self, codigo_questao: str) -> bool:
        """
        Verifica se a resposta é de questão objetiva

        Args:
            codigo_questao: Código da questão

        Returns:
            True se objetiva, False caso contrário
        """
        resposta = self.buscar_por_questao(codigo_questao)
        return resposta.eh_objetiva() if resposta else False

    def eh_discursiva(self, codigo_questao: str) -> bool:
        """
        Verifica se a resposta é de questão discursiva

        Args:
            codigo_questao: Código da questão

        Returns:
            True se discursiva, False caso contrário
        """
        resposta = self.buscar_por_questao(codigo_questao)
        return resposta.eh_discursiva() if resposta else False
