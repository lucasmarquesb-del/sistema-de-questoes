"""
Model ORM para Questão
"""
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import BaseModel
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from src.models.orm.nivel_escolar import NivelEscolar

class Questao(BaseModel):
    """
    Questão - tabela principal
    """
    __tablename__ = 'questao'

    codigo = Column(String(20), unique=True, nullable=False, index=True)
    titulo = Column(String(200), nullable=True, index=True)
    enunciado = Column(Text, nullable=False)

    # Foreign Keys
    uuid_tipo_questao = Column(Text, ForeignKey('tipo_questao.uuid'), nullable=False)
    uuid_fonte = Column(Text, ForeignKey('fonte_questao.uuid'), nullable=True)
    uuid_ano_referencia = Column(Text, ForeignKey('ano_referencia.uuid'), nullable=True)
    uuid_dificuldade = Column(Text, ForeignKey('dificuldade.uuid'), nullable=True)
    uuid_imagem_enunciado = Column(Text, ForeignKey('imagem.uuid'), nullable=True)

    # Campos de imagem
    escala_imagem_enunciado = Column(Numeric(3, 2), nullable=True, default=1.0)

    # Campos adicionais
    observacoes = Column(Text, nullable=True)
    data_modificacao = Column(DateTime, onupdate=datetime.utcnow, nullable=True)

    # Relationships
    tipo = relationship("TipoQuestao", back_populates="questoes")
    fonte = relationship("FonteQuestao", back_populates="questoes")
    ano = relationship("AnoReferencia", back_populates="questoes")
    dificuldade = relationship("Dificuldade", back_populates="questoes")
    imagem_enunciado = relationship("Imagem", back_populates="questoes_enunciado", foreign_keys=[uuid_imagem_enunciado])

    # Relationships 1:N
    alternativas = relationship("Alternativa", back_populates="questao", cascade="all, delete-orphan")
    resposta = relationship("RespostaQuestao", back_populates="questao", uselist=False, cascade="all, delete-orphan")

    # Relationships N:N
    tags = relationship("Tag", secondary="questao_tag", back_populates="questoes")
    listas = relationship("Lista", secondary="lista_questao", back_populates="questoes")
    # Relacionamento N:N com niveis escolares
    niveis_escolares = relationship(
        "NivelEscolar",
        secondary="questao_nivel",
        back_populates="questoes"
    )
    # Relationship para versões
    versoes = relationship(
        "Questao",
        secondary="questao_versao",
        primaryjoin="Questao.uuid == QuestaoVersao.uuid_questao_original",
        secondaryjoin="Questao.uuid == QuestaoVersao.uuid_questao_versao",
        backref="questao_original"
    )

    def __repr__(self):
        return f"<Questao(codigo={self.codigo}, titulo={self.titulo})>"

    def to_dict(self) -> dict:
        """Converte o model para dicionario."""
        return {
            # ... seus campos existentes ...
            "uuid": self.uuid,
            "codigo": self.codigo,
            "titulo": self.titulo,
            "enunciado": self.enunciado,
            # ... outros campos ...

            # ADICIONE ESTES CAMPOS:
            "niveis_escolares": [n.to_dict() for n in self.niveis_escolares],
            "codigos_niveis": self.codigos_niveis,
        }
    @classmethod
    def buscar_por_codigo(cls, session, codigo: str):
        """Busca questão por código"""
        return session.query(cls).filter_by(codigo=codigo, ativo=True).first()

    @classmethod
    def buscar_por_titulo(cls, session, titulo: str):
        """Busca questões por título (LIKE)"""
        return session.query(cls).filter(
            cls.titulo.ilike(f"%{titulo}%"),
            cls.ativo == True
        ).all()

    @classmethod
    def buscar_por_fonte(cls, session, sigla_fonte: str):
        """Busca questões por fonte"""
        from .fonte_questao import FonteQuestao
        return session.query(cls).join(FonteQuestao).filter(
            FonteQuestao.sigla == sigla_fonte,
            cls.ativo == True
        ).all()

    @classmethod
    def buscar_por_ano(cls, session, ano: int):
        """Busca questões por ano"""
        from .ano_referencia import AnoReferencia
        return session.query(cls).join(AnoReferencia).filter(
            AnoReferencia.ano == ano,
            cls.ativo == True
        ).all()

    @classmethod
    def buscar_por_tag(cls, session, nome_tag: str):
        """Busca questões por tag"""
        from .tag import Tag
        return session.query(cls).join(cls.tags).filter(
            Tag.nome == nome_tag,
            cls.ativo == True
        ).all()

    @classmethod
    def buscar_por_dificuldade(cls, session, codigo_dificuldade: str):
        """Busca questões por dificuldade"""
        from .dificuldade import Dificuldade
        return session.query(cls).join(Dificuldade).filter(
            Dificuldade.codigo == codigo_dificuldade,
            cls.ativo == True
        ).all()

    @classmethod
    def buscar_questoes(cls, session, **filtros):
        """
        Busca questões com filtros combinados

        Args:
            fonte: sigla da fonte
            ano: ano inteiro
            tags: lista de nomes de tags
            dificuldade: código da dificuldade
            tipo: código do tipo de questão

        Returns:
            Lista de questões que atendem aos critérios
        """
        query = session.query(cls).filter(cls.ativo == True)

        # Filtro por fonte
        if 'fonte' in filtros and filtros['fonte']:
            from .fonte_questao import FonteQuestao
            query = query.join(FonteQuestao).filter(FonteQuestao.sigla == filtros['fonte'])

        # Filtro por ano
        if 'ano' in filtros and filtros['ano']:
            from .ano_referencia import AnoReferencia
            query = query.join(AnoReferencia).filter(AnoReferencia.ano == filtros['ano'])

        # Filtro por dificuldade
        if 'dificuldade' in filtros and filtros['dificuldade']:
            from .dificuldade import Dificuldade
            query = query.join(Dificuldade).filter(Dificuldade.codigo == filtros['dificuldade'])

        # Filtro por tipo
        if 'tipo' in filtros and filtros['tipo']:
            from .tipo_questao import TipoQuestao
            query = query.join(TipoQuestao).filter(TipoQuestao.codigo == filtros['tipo'])

        # Filtro por tags (AND - questão deve ter todas as tags)
        if 'tags' in filtros and filtros['tags']:
            from .tag import Tag
            for nome_tag in filtros['tags']:
                query = query.join(cls.tags).filter(Tag.nome == nome_tag)

        return query.all()

    def adicionar_tag(self, session, tag):
        """Adiciona uma tag à questão"""
        if tag not in self.tags:
            self.tags.append(tag)
            session.flush()

    def remover_tag(self, session, tag):
        """Remove uma tag da questão"""
        if tag in self.tags:
            self.tags.remove(tag)
            session.flush()

    def obter_alternativa_correta(self):
        """Retorna a alternativa correta (apenas para objetivas)"""
        if self.resposta and self.resposta.uuid_alternativa_correta:
            for alt in self.alternativas:
                if alt.uuid == self.resposta.uuid_alternativa_correta:
                    return alt
        return None

    def adicionar_nivel(self, nivel: "NivelEscolar") -> None:
        """
        Adiciona um nivel escolar a questao.

        Args:
            nivel: NivelEscolar a adicionar
        """
        if nivel not in self.niveis_escolares:
            self.niveis_escolares.append(nivel)

    def remover_nivel(self, nivel: "NivelEscolar") -> None:
        """
        Remove um nivel escolar da questao.

        Args:
            nivel: NivelEscolar a remover
        """
        if nivel in self.niveis_escolares:
            self.niveis_escolares.remove(nivel)

    def definir_niveis(self, niveis: List["NivelEscolar"]) -> None:
        """
        Define os niveis escolares da questao (substitui os existentes).

        Args:
            niveis: Lista de NivelEscolar
        """
        self.niveis_escolares = niveis

    @property
    def codigos_niveis(self) -> List[str]:
        """Retorna lista de codigos dos niveis (EF1, EM, etc.)."""
        return [n.codigo for n in self.niveis_escolares]

    @property
    def nomes_niveis(self) -> List[str]:
        """Retorna lista de nomes dos niveis."""
        return [n.nome for n in self.niveis_escolares]