"""Repository para Tipos de Questões"""
from typing import Optional
from sqlalchemy.orm import Session
from src.models.orm import TipoQuestao
from .base_repository import BaseRepository
from src.models.orm.nivel_escolar import NivelEscolar

class TipoQuestaoRepository(BaseRepository[TipoQuestao]):
    def __init__(self, session: Session):
        super().__init__(TipoQuestao, session)
    
    def buscar_por_codigo(self, codigo: str) -> Optional[TipoQuestao]:
        return self.session.query(TipoQuestao).filter_by(codigo=codigo, ativo=True).first()

    def definir_niveis_questao(
            self,
            uuid_questao: str,
            uuids_niveis: List[str]
    ) -> bool:
        """
        Define os niveis escolares de uma questao.

        Args:
            uuid_questao: UUID da questao
            uuids_niveis: Lista de UUIDs dos niveis a associar

        Returns:
            True se bem-sucedido
        """
        from src.models.orm.questao import Questao
        from src.models.orm.nivel_escolar import NivelEscolar

        try:
            questao = self.session.query(Questao).filter(
                Questao.uuid == uuid_questao
            ).first()

            if not questao:
                return False

            # Busca os niveis pelos UUIDs
            niveis = self.session.query(NivelEscolar).filter(
                NivelEscolar.uuid.in_(uuids_niveis)
            ).all()

            # Define os niveis
            questao.niveis_escolares = niveis
            self.session.commit()

            logger.info(f"Niveis definidos para questao {uuid_questao[:8]}...: {len(niveis)} niveis")
            return True

        except Exception as e:
            self.session.rollback()
            logger.error(f"Erro ao definir niveis da questao: {e}")
            return False

    def adicionar_nivel_questao(
            self,
            uuid_questao: str,
            uuid_nivel: str
    ) -> bool:
        """
        Adiciona um nivel escolar a uma questao.

        Args:
            uuid_questao: UUID da questao
            uuid_nivel: UUID do nivel a adicionar

        Returns:
            True se bem-sucedido
        """
        from src.models.orm.questao import Questao
        from src.models.orm.nivel_escolar import NivelEscolar

        try:
            questao = self.session.query(Questao).filter(
                Questao.uuid == uuid_questao
            ).first()

            nivel = self.session.query(NivelEscolar).filter(
                NivelEscolar.uuid == uuid_nivel
            ).first()

            if not questao or not nivel:
                return False

            if nivel not in questao.niveis_escolares:
                questao.niveis_escolares.append(nivel)
                self.session.commit()

            return True

        except Exception as e:
            self.session.rollback()
            logger.error(f"Erro ao adicionar nivel a questao: {e}")
            return False

    def remover_nivel_questao(
            self,
            uuid_questao: str,
            uuid_nivel: str
    ) -> bool:
        """
        Remove um nivel escolar de uma questao.

        Args:
            uuid_questao: UUID da questao
            uuid_nivel: UUID do nivel a remover

        Returns:
            True se bem-sucedido
        """
        from src.models.orm.questao import Questao
        from src.models.orm.nivel_escolar import NivelEscolar

        try:
            questao = self.session.query(Questao).filter(
                Questao.uuid == uuid_questao
            ).first()

            nivel = self.session.query(NivelEscolar).filter(
                NivelEscolar.uuid == uuid_nivel
            ).first()

            if not questao or not nivel:
                return False

            if nivel in questao.niveis_escolares:
                questao.niveis_escolares.remove(nivel)
                self.session.commit()

            return True

        except Exception as e:
            self.session.rollback()
            logger.error(f"Erro ao remover nivel da questao: {e}")
            return False

    def buscar_por_nivel(
            self,
            uuid_nivel: str,
            apenas_ativas: bool = True
    ) -> List["Questao"]:
        """
        Busca questoes de um determinado nivel escolar.

        Args:
            uuid_nivel: UUID do nivel escolar
            apenas_ativas: Se True, retorna apenas questoes ativas

        Returns:
            Lista de Questao
        """
        from src.models.orm.questao import Questao
        from src.models.orm.nivel_escolar import NivelEscolar

        query = self.session.query(Questao).join(
            Questao.niveis_escolares
        ).filter(
            NivelEscolar.uuid == uuid_nivel
        )

        if apenas_ativas:
            query = query.filter(Questao.ativo == True)

        return query.all()

    def buscar_por_niveis(
            self,
            uuids_niveis: List[str],
            apenas_ativas: bool = True
    ) -> List["Questao"]:
        """
        Busca questoes que tenham QUALQUER um dos niveis especificados.

        Args:
            uuids_niveis: Lista de UUIDs dos niveis
            apenas_ativas: Se True, retorna apenas questoes ativas

        Returns:
            Lista de Questao (sem duplicatas)
        """
        from src.models.orm.questao import Questao
        from src.models.orm.nivel_escolar import NivelEscolar

        if not uuids_niveis:
            return []

        query = self.session.query(Questao).join(
            Questao.niveis_escolares
        ).filter(
            NivelEscolar.uuid.in_(uuids_niveis)
        )

        if apenas_ativas:
            query = query.filter(Questao.ativo == True)

        return query.distinct().all()

    def buscar_por_disciplina(
            self,
            uuid_disciplina: str,
            apenas_ativas: bool = True
    ) -> List["Questao"]:
        """
        Busca questoes que tenham tags de uma determinada disciplina.

        Args:
            uuid_disciplina: UUID da disciplina
            apenas_ativas: Se True, retorna apenas questoes ativas

        Returns:
            Lista de Questao
        """
        from src.models.orm.questao import Questao
        from src.models.orm.tag import Tag

        query = self.session.query(Questao).join(
            Questao.tags
        ).filter(
            Tag.uuid_disciplina == uuid_disciplina
        )

        if apenas_ativas:
            query = query.filter(Questao.ativo == True)

        return query.distinct().all()

    def buscar_avancada(
            self,
            uuid_disciplina: str = None,
            uuids_tags: List[str] = None,
            uuids_niveis: List[str] = None,
            uuid_fonte: str = None,
            texto: str = None,
            apenas_ativas: bool = True
    ) -> List["Questao"]:
        """
        Busca avancada com multiplos filtros.

        Args:
            uuid_disciplina: UUID da disciplina (filtra tags da disciplina)
            uuids_tags: Lista de UUIDs de tags (conteudo)
            uuids_niveis: Lista de UUIDs de niveis escolares
            uuid_fonte: UUID da fonte
            texto: Texto para buscar no enunciado
            apenas_ativas: Se True, retorna apenas questoes ativas

        Returns:
            Lista de Questao que atendem os criterios
        """
        from src.models.orm.questao import Questao
        from src.models.orm.tag import Tag
        from src.models.orm.nivel_escolar import NivelEscolar

        query = self.session.query(Questao)

        # Filtro por ativo
        if apenas_ativas:
            query = query.filter(Questao.ativo == True)

        # Filtro por disciplina (questoes que tem tags dessa disciplina)
        if uuid_disciplina:
            query = query.join(Questao.tags).filter(
                Tag.uuid_disciplina == uuid_disciplina
            )

        # Filtro por tags especificas
        if uuids_tags:
            # Questao deve ter PELO MENOS UMA das tags
            query = query.join(Questao.tags).filter(
                Tag.uuid.in_(uuids_tags)
            )

        # Filtro por niveis escolares
        if uuids_niveis:
            # Questao deve ter PELO MENOS UM dos niveis
            query = query.join(Questao.niveis_escolares).filter(
                NivelEscolar.uuid.in_(uuids_niveis)
            )

        # Filtro por fonte
        if uuid_fonte:
            query = query.filter(Questao.uuid_fonte == uuid_fonte)

        # Filtro por texto no enunciado
        if texto:
            query = query.filter(
                Questao.enunciado.ilike(f"%{texto}%")
            )

        return query.distinct().all()