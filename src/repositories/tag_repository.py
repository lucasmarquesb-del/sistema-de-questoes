"""Repository para Tags"""
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from src.infrastructure.logging import get_audit_logger, get_metrics_collector
from src.models.orm import Tag
from .base_repository import BaseRepository

class TagRepository(BaseRepository[Tag]):
    def __init__(self, session: Session):
        super().__init__(Tag, session)
        self._audit = get_audit_logger()
        self._metrics = get_metrics_collector()
        self._logger = logging.getLogger(__name__)
    
    def criar(self, **kwargs) -> Optional[Tag]:
        """Cria uma nova tag com auditoria e métricas."""
        try:
            tag = super().criar(**kwargs)
            if tag and self._audit:
                self._audit.tag_criada(
                    tag_id=str(tag.uuid),
                    nome=tag.nome,
                    numeracao=tag.numeracao
                )
            if self._metrics:
                self._metrics.increment("tags_criadas")
            return tag
        except Exception as e:
            self._logger.error(f"Erro ao criar tag: {e}", exc_info=True)
            if self._metrics:
                self._metrics.increment("erros_criar_tag")
            return None

    def atualizar(self, uuid: str, **kwargs) -> Optional[Tag]:
        """Atualiza uma tag com auditoria e métricas."""
        try:
            tag_antiga = self.buscar_por_uuid(uuid)
            tag_atualizada = super().atualizar(uuid, **kwargs)
            if tag_atualizada and self._audit:
                campos_alterados = [k for k in kwargs if getattr(tag_antiga, k) != kwargs[k]]
                if campos_alterados:
                    self._audit.tag_editada(
                        tag_id=str(tag_atualizada.uuid),
                        campos_alterados=campos_alterados
                    )
            if self._metrics:
                self._metrics.increment("tags_atualizadas")
            return tag_atualizada
        except Exception as e:
            self._logger.error(f"Erro ao atualizar tag {uuid}: {e}", exc_info=True)
            if self._metrics:
                self._metrics.increment("erros_atualizar_tag")
            return None
    
    def desativar(self, uuid: str) -> bool:
        """Desativa uma tag (soft delete) com auditoria e métricas."""
        try:
            tag = self.buscar_por_uuid(uuid)
            if tag and tag.ativo:
                resultado = super().desativar(uuid)
                if resultado and self._audit:
                    self._audit.tag_deletada(
                        tag_id=str(tag.uuid),
                        nome=tag.nome
                    )
                if self._metrics:
                    self._metrics.increment("tags_desativadas")
                return resultado
            return False
        except Exception as e:
            self._logger.error(f"Erro ao desativar tag {uuid}: {e}", exc_info=True)
            if self._metrics:
                self._metrics.increment("erros_desativar_tag")
            return False

    def buscar_por_nome(self, nome: str) -> Optional[Tag]:
        return self.session.query(Tag).filter_by(nome=nome, ativo=True).first()
    
    def buscar_por_numeracao(self, numeracao: str) -> Optional[Tag]:
        return self.session.query(Tag).filter_by(numeracao=numeracao, ativo=True).first()
    
    def listar_raizes(self) -> List[Tag]:
        return self.session.query(Tag).filter_by(uuid_tag_pai=None, ativo=True).order_by(Tag.ordem).all()
    
    def listar_filhas(self, numeracao_pai: str) -> List[Tag]:
        tag_pai = self.buscar_por_numeracao(numeracao_pai)
        if not tag_pai:
            return []
        return self.session.query(Tag).filter_by(uuid_tag_pai=tag_pai.uuid, ativo=True).order_by(Tag.ordem).all()
    
    def obter_caminho_completo(self, numeracao: str) -> str:
        tag = self.buscar_por_numeracao(numeracao)
        return tag.obter_caminho_completo() if tag else ""

    def obter_maior_numeracao_raiz(self, prefixo: str = '') -> int:
        """
        Obtém o maior número usado em tags raiz (incluindo inativas).

        Args:
            prefixo: 'V' para vestibular, 'N' para série, '' para conteúdo

        Returns:
            Maior número encontrado ou 0 se nenhum
        """
        query = self.session.query(Tag.numeracao).filter(Tag.uuid_tag_pai == None)

        if prefixo:
            query = query.filter(Tag.numeracao.like(f'{prefixo}%'))

        numeracoes = [row[0] for row in query.all() if row[0]]

        if not numeracoes:
            return 0

        # Extrair números
        numeros = []
        for num in numeracoes:
            try:
                if prefixo:
                    # Ex: "V1" -> 1
                    numeros.append(int(num[len(prefixo):]))
                elif num and num[0].isdigit():
                    # Tags de conteúdo começam com dígito, ex: "1", "2", "10"
                    numeros.append(int(num.split('.')[0]))
            except (ValueError, IndexError):
                pass

        return max(numeros) if numeros else 0

    def obter_maior_numeracao_filha(self, uuid_pai: str) -> int:
        """
        Obtém o maior número usado em tags filhas (incluindo inativas).

        Args:
            uuid_pai: UUID da tag pai

        Returns:
            Maior número encontrado ou 0 se nenhum
        """
        query = self.session.query(Tag.numeracao).filter(Tag.uuid_tag_pai == uuid_pai)
        numeracoes = [row[0] for row in query.all() if row[0]]

        if not numeracoes:
            return 0

        # Extrair o último número da numeração (ex: "1.2.3" -> 3)
        numeros = []
        for num in numeracoes:
            try:
                ultimo = num.split('.')[-1]
                numeros.append(int(ultimo))
            except (ValueError, IndexError):
                pass

        return max(numeros) if numeros else 0

    def listar_por_disciplina(
            self,
            uuid_disciplina: str,
            apenas_ativas: bool = True
    ) -> List["Tag"]:
        """
        Lista todas as tags de uma disciplina especifica.

        Args:
            uuid_disciplina: UUID da disciplina
            apenas_ativas: Se True, retorna apenas tags ativas

        Returns:
            Lista de Tag ordenada por numeracao
        """
        from src.models.orm.tag import Tag

        query = self.session.query(Tag).filter(
            Tag.uuid_disciplina == uuid_disciplina
        )

        if apenas_ativas:
            query = query.filter(Tag.ativo == True)

        return query.order_by(Tag.numeracao).all()

    def listar_raiz_por_disciplina(
            self,
            uuid_disciplina: str,
            apenas_ativas: bool = True
    ) -> List["Tag"]:
        """
        Lista as tags raiz (sem pai) de uma disciplina.

        Args:
            uuid_disciplina: UUID da disciplina
            apenas_ativas: Se True, retorna apenas tags ativas

        Returns:
            Lista de Tag de primeiro nivel
        """
        from src.models.orm.tag import Tag

        query = self.session.query(Tag).filter(
            Tag.uuid_disciplina == uuid_disciplina,
            Tag.uuid_tag_pai == None
        )

        if apenas_ativas:
            query = query.filter(Tag.ativo == True)

        return query.order_by(Tag.ordem, Tag.numeracao).all()

    def criar_para_disciplina(
            self,
            uuid_disciplina: str,
            dados: dict
    ) -> Optional["Tag"]:
        """
        Cria uma nova tag associada a uma disciplina.

        Args:
            uuid_disciplina: UUID da disciplina
            dados: Dicionario com os dados da tag
                   {numeracao, nome, nivel?, uuid_tag_pai?, ordem?, descricao?}

        Returns:
            Tag criada ou None se falhar
        """
        import uuid
        from datetime import datetime
        from src.models.orm.tag import Tag

        try:
            tag = Tag(
                uuid=str(uuid.uuid4()),
                uuid_disciplina=uuid_disciplina,
                uuid_tag_pai=dados.get("uuid_tag_pai"),
                numeracao=dados["numeracao"],
                nome=dados["nome"],
                nivel=dados.get("nivel", 1),
                ordem=dados.get("ordem", 0),
                ativo=dados.get("ativo", True),
                data_criacao=datetime.now(),
            )

            self.session.add(tag)
            self.session.commit()

            logger.info(f"Tag criada: {tag.numeracao} - {tag.nome} (disciplina {uuid_disciplina[:8]}...)")
            return tag

        except Exception as e:
            self.session.rollback()
            logger.error(f"Erro ao criar tag: {e}")
            return None

    def mover_para_disciplina(
            self,
            uuid_tag: str,
            uuid_disciplina: str
    ) -> bool:
        """
        Move uma tag (e seus filhos) para outra disciplina.

        Args:
            uuid_tag: UUID da tag a mover
            uuid_disciplina: UUID da disciplina destino

        Returns:
            True se movido com sucesso
        """
        from src.models.orm.tag import Tag

        try:
            tag = self.buscar_por_uuid(uuid_tag)
            if not tag:
                return False

            # Move a tag
            tag.uuid_disciplina = uuid_disciplina

            # Move todos os descendentes (filhos, netos, etc.)
            def mover_filhos(tag_pai):
                for filho in tag_pai.filhos:
                    filho.uuid_disciplina = uuid_disciplina
                    mover_filhos(filho)

            mover_filhos(tag)

            self.session.commit()
            logger.info(f"Tag {uuid_tag[:8]}... movida para disciplina {uuid_disciplina[:8]}...")
            return True

        except Exception as e:
            self.session.rollback()
            logger.error(f"Erro ao mover tag: {e}")
            return False

    def buscar_arvore_disciplina(self, uuid_disciplina: str) -> List[dict]:
        """
        Retorna a arvore completa de tags de uma disciplina.

        Formato para exibicao em TreeView.

        Args:
            uuid_disciplina: UUID da disciplina

        Returns:
            Lista de dicionarios com estrutura hierarquica
        """

        def construir_arvore(tag) -> dict:
            filhos_ativos = [f for f in tag.filhos if f.ativo]
            filhos_ativos.sort(key=lambda x: (x.ordem, x.numeracao))

            return {
                "uuid": tag.uuid,
                "numeracao": tag.numeracao,
                "nome": tag.nome,
                "nivel": tag.nivel,
                "texto": f"{tag.numeracao} - {tag.nome}",
                "filhos": [construir_arvore(filho) for filho in filhos_ativos]
            }

        tags_raiz = self.listar_raiz_por_disciplina(uuid_disciplina)
        return [construir_arvore(tag) for tag in tags_raiz]

    def contar_por_disciplina(self, uuid_disciplina: str) -> int:
        """
        Conta quantas tags pertencem a uma disciplina.

        Args:
            uuid_disciplina: UUID da disciplina

        Returns:
            Quantidade de tags
        """
        from src.models.orm.tag import Tag

        return self.session.query(Tag).filter(
            Tag.uuid_disciplina == uuid_disciplina,
            Tag.ativo == True
        ).count()
