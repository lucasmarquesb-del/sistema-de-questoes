"""
Service para gerenciar Alternativas - usa apenas ORM
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from repositories import AlternativaRepository, QuestaoRepository


class AlternativaService:
    """Service para operações de negócio com alternativas"""

    def __init__(self, session: Session):
        self.session = session
        self.alternativa_repo = AlternativaRepository(session)
        self.questao_repo = QuestaoRepository(session)

    def criar_alternativa(
        self,
        codigo_questao: str,
        letra: str,
        texto: str,
        uuid_imagem: Optional[str] = None,
        escala_imagem: float = 1.0
    ) -> Dict[str, Any]:
        """
        Cria uma alternativa

        Args:
            codigo_questao: Código da questão
            letra: Letra (A-E)
            texto: Texto da alternativa
            uuid_imagem: UUID da imagem (opcional)
            escala_imagem: Escala da imagem

        Returns:
            Dict com dados da alternativa criada
        """
        questao = self.questao_repo.buscar_por_codigo(codigo_questao)
        if not questao:
            raise ValueError(f"Questão não encontrada: {codigo_questao}")

        letra_ordem = {'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5}
        ordem = letra_ordem.get(letra, 1)

        alternativa = self.alternativa_repo.criar(
            uuid_questao=questao.uuid,
            letra=letra,
            ordem=ordem,
            texto=texto,
            uuid_imagem=uuid_imagem,
            escala_imagem=escala_imagem
        )

        self.session.flush()

        return {
            'uuid': alternativa.uuid,
            'letra': alternativa.letra,
            'texto': alternativa.texto,
            'ordem': alternativa.ordem
        }

    def listar_alternativas(self, codigo_questao: str) -> List[Dict[str, Any]]:
        """
        Lista alternativas de uma questão

        Args:
            codigo_questao: Código da questão

        Returns:
            Lista de alternativas ordenadas
        """
        alternativas = self.alternativa_repo.buscar_por_questao(codigo_questao)
        return [
            {
                'uuid': alt.uuid,
                'letra': alt.letra,
                'texto': alt.texto,
                'ordem': alt.ordem
            }
            for alt in alternativas
        ]

    def buscar_alternativa_correta(self, codigo_questao: str) -> Optional[Dict[str, Any]]:
        """
        Busca a alternativa correta de uma questão

        Args:
            codigo_questao: Código da questão

        Returns:
            Dict com dados da alternativa correta ou None
        """
        alternativa = self.alternativa_repo.buscar_alternativa_correta(codigo_questao)
        if not alternativa:
            return None

        return {
            'uuid': alternativa.uuid,
            'letra': alternativa.letra,
            'texto': alternativa.texto
        }
