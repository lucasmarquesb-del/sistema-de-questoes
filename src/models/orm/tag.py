"""
Model ORM para Tag
"""
from sqlalchemy import Column, String, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel

# Se estiver usando TYPE_CHECKING:
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.models.orm.disciplina import Disciplina

class Tag(BaseModel):
    """
    Tag para categorização de questões (hierárquica)
    """
    __tablename__ = 'tag'

    nome = Column(String(200), unique=True, nullable=False, index=True)
    numeracao = Column(String(50), unique=True, nullable=False, index=True)
    nivel = Column(Integer, nullable=False)
    uuid_tag_pai = Column(Text, ForeignKey('tag.uuid'), nullable=True)
    ordem = Column(Integer, nullable=False, default=0)
    uuid_disciplina = Column(String(36), ForeignKey('disciplina.uuid'), nullable=True)

    # Self-referential relationship
    tag_pai = relationship("Tag", remote_side="Tag.uuid", back_populates="tags_filhas")
    tags_filhas = relationship("Tag", back_populates="tag_pai", cascade="all, delete-orphan")
    disciplina = relationship("Disciplina", back_populates="tags")

    # Relationship com questões (N:N via questao_tag)
    questoes = relationship("Questao", secondary="questao_tag", back_populates="tags")

    def __repr__(self):
        return f"<Tag(numeracao={self.numeracao}, nome={self.nome})>"

    @classmethod
    def buscar_por_nome(cls, session, nome: str):
        """Busca tag por nome"""
        return session.query(cls).filter_by(nome=nome, ativo=True).first()

    @classmethod
    def buscar_por_numeracao(cls, session, numeracao: str):
        """Busca tag por numeração"""
        return session.query(cls).filter_by(numeracao=numeracao, ativo=True).first()

    @classmethod
    def listar_raizes(cls, session):
        """Lista todas as tags raiz (sem pai)"""
        return session.query(cls).filter_by(
            uuid_tag_pai=None,
            ativo=True
        ).order_by(cls.ordem).all()

    @classmethod
    def listar_por_nivel(cls, session, nivel: int):
        """Lista tags por nível"""
        return session.query(cls).filter_by(
            nivel=nivel,
            ativo=True
        ).order_by(cls.ordem).all()

    def obter_caminho_completo(self) -> str:
        """
        Retorna o caminho completo da tag (incluindo pais)
        Exemplo: "MATEMÁTICA > ÁLGEBRA > FUNÇÃO AFIM"
        """
        caminho = [self.nome]
        tag_atual = self
        while tag_atual.tag_pai:
            tag_atual = tag_atual.tag_pai
            caminho.insert(0, tag_atual.nome)
        return " > ".join(caminho)

    def obter_filhas_recursivo(self) -> list:
        """
        Retorna todas as tags filhas recursivamente
        """
        resultado = []
        for filha in self.tags_filhas:
            if filha.ativo:
                resultado.append(filha)
                resultado.extend(filha.obter_filhas_recursivo())
        return resultado

    def to_dict(self) -> dict:
        """Converte o model para dicionario."""
        return {
            "uuid": self.uuid,
            "uuid_disciplina": self.uuid_disciplina,
            "uuid_tag_pai": self.uuid_tag_pai,
            "numeracao": self.numeracao,
            "nome": self.nome,
            "nivel": self.nivel,
            "ordem": self.ordem,
            "ativo": self.ativo,
            "data_criacao": self.data_criacao.isoformat() if self.data_criacao else None,
            # Dados da disciplina (se carregada)
            "disciplina_codigo": self.disciplina.codigo if self.disciplina else None,
            "disciplina_nome": self.disciplina.nome if self.disciplina else None,
        }

    @property
    def caminho_completo(self) -> str:
        """Retorna o caminho completo da tag (ex: 'Numeros > Naturais > Primos')."""
        partes = [self.nome]
        tag_atual = self.pai  # Assumindo que voce tem um relacionamento 'pai'

        while tag_atual:
            partes.insert(0, tag_atual.nome)
            tag_atual = tag_atual.pai if hasattr(tag_atual, 'pai') else None

        return " > ".join(partes)

    @property
    def eh_raiz(self) -> bool:
        """Retorna True se e uma tag raiz (sem pai)."""
        return self.uuid_tag_pai is None