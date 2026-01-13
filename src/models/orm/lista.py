"""
Model ORM para Lista
"""
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import BaseModel


class Lista(BaseModel):
    """
    Lista de questões (Prova, Lista de Exercícios, Simulado)
    """
    __tablename__ = 'lista'

    codigo = Column(String(20), unique=True, nullable=False, index=True)
    titulo = Column(String(200), nullable=False, index=True)
    tipo = Column(String(50), nullable=False)  # 'PROVA', 'LISTA', 'SIMULADO'
    cabecalho = Column(Text, nullable=True)
    instrucoes = Column(Text, nullable=True)
    data_modificacao = Column(DateTime, onupdate=datetime.utcnow, nullable=True)

    # Relationship com questões (N:N via lista_questao)
    questoes = relationship(
        "Questao",
        secondary="lista_questao",
        back_populates="listas",
        order_by="ListaQuestao.ordem_na_lista"
    )

    def __repr__(self):
        return f"<Lista(codigo={self.codigo}, titulo={self.titulo})>"

    @classmethod
    def buscar_por_codigo(cls, session, codigo: str):
        """Busca lista por código"""
        return session.query(cls).filter_by(codigo=codigo, ativo=True).first()

    @classmethod
    def buscar_por_titulo(cls, session, titulo: str):
        """Busca listas por título (LIKE)"""
        return session.query(cls).filter(
            cls.titulo.ilike(f"%{titulo}%"),
            cls.ativo == True
        ).all()

    @classmethod
    def buscar_por_tipo(cls, session, tipo: str):
        """Busca listas por tipo"""
        return session.query(cls).filter_by(
            tipo=tipo,
            ativo=True
        ).order_by(cls.data_criacao.desc()).all()

    def buscar_tags_relacionadas(self, session):
        """
        Busca todas as tags das questões desta lista

        Returns:
            Lista de tags únicas
        """
        tags = set()
        for questao in self.questoes:
            if questao.ativo:
                tags.update(questao.tags)
        return sorted(list(tags), key=lambda t: t.numeracao)

    def contar_questoes(self) -> int:
        """Retorna o número de questões ativas na lista"""
        return sum(1 for q in self.questoes if q.ativo)

    def adicionar_questao(self, session, questao, ordem: int = None):
        """
        Adiciona uma questão à lista

        Args:
            session: Sessão do SQLAlchemy
            questao: Objeto Questao
            ordem: Ordem na lista (opcional, usa próxima disponível se None)
        """
        from .lista_questao import ListaQuestao

        # Verificar se já existe
        associacao_existente = session.query(ListaQuestao).filter_by(
            uuid_lista=self.uuid,
            uuid_questao=questao.uuid
        ).first()

        if associacao_existente:
            return  # Já está na lista

        # Determinar ordem
        if ordem is None:
            max_ordem = session.query(ListaQuestao).filter_by(
                uuid_lista=self.uuid
            ).count()
            ordem = max_ordem + 1

        # Criar associação
        associacao = ListaQuestao(
            uuid_lista=self.uuid,
            uuid_questao=questao.uuid,
            ordem_na_lista=ordem
        )
        session.add(associacao)
        session.flush()

    def remover_questao(self, session, questao):
        """Remove uma questão da lista"""
        from .lista_questao import ListaQuestao

        associacao = session.query(ListaQuestao).filter_by(
            uuid_lista=self.uuid,
            uuid_questao=questao.uuid
        ).first()

        if associacao:
            session.delete(associacao)
            session.flush()

    def reordenar_questoes(self, session, codigos_questoes_ordenados: list):
        """
        Reordena questões da lista baseado em códigos

        Args:
            session: Sessão do SQLAlchemy
            codigos_questoes_ordenados: Lista de códigos de questões na ordem desejada
        """
        from .questao import Questao
        from .lista_questao import ListaQuestao

        for nova_ordem, codigo in enumerate(codigos_questoes_ordenados, start=1):
            questao = Questao.buscar_por_codigo(session, codigo)
            if questao:
                associacao = session.query(ListaQuestao).filter_by(
                    uuid_lista=self.uuid,
                    uuid_questao=questao.uuid
                ).first()

                if associacao:
                    associacao.ordem_na_lista = nova_ordem

        session.flush()

    def obter_questoes_ordenadas(self):
        """
        Retorna as questões da lista ordenadas

        Returns:
            Lista de tuplas (ordem, questao)
        """
        from .lista_questao import ListaQuestao

        resultado = []
        for questao in self.questoes:
            if questao.ativo:
                # Buscar ordem da associação
                ordem = 0
                for assoc in questao.listas:
                    if assoc.uuid == self.uuid:
                        # Precisamos acessar a tabela de associação
                        break
                resultado.append((ordem, questao))

        return sorted(resultado, key=lambda x: x[0])
