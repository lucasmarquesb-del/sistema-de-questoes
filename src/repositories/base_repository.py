"""
Base Repository para operações comuns de banco de dados
"""
from typing import TypeVar, Generic, Optional, List, Type
from sqlalchemy.orm import Session
from models.orm.base import Base

T = TypeVar('T', bound=Base)


class BaseRepository(Generic[T]):
    """
    Repository base com operações CRUD genéricas
    """

    def __init__(self, model_class: Type[T], session: Session):
        """
        Inicializa o repository

        Args:
            model_class: Classe do model ORM
            session: Sessão do SQLAlchemy
        """
        self.model_class = model_class
        self.session = session

    def criar(self, **kwargs) -> T:
        """
        Cria um novo registro

        Args:
            **kwargs: Dados do registro

        Returns:
            Instância do model criado
        """
        instancia = self.model_class(**kwargs)
        self.session.add(instancia)
        self.session.flush()
        return instancia

    def buscar_por_uuid(self, uuid: str) -> Optional[T]:
        """
        Busca registro por UUID

        Args:
            uuid: UUID do registro

        Returns:
            Instância do model ou None
        """
        return self.session.query(self.model_class).filter_by(
            uuid=uuid,
            ativo=True
        ).first()

    def listar_todos(self, apenas_ativos: bool = True) -> List[T]:
        """
        Lista todos os registros

        Args:
            apenas_ativos: Se True, retorna apenas registros ativos

        Returns:
            Lista de instâncias
        """
        query = self.session.query(self.model_class)
        if apenas_ativos and hasattr(self.model_class, 'ativo'):
            query = query.filter_by(ativo=True)
        return query.all()

    def atualizar(self, uuid: str, **kwargs) -> Optional[T]:
        """
        Atualiza um registro

        Args:
            uuid: UUID do registro
            **kwargs: Campos a atualizar

        Returns:
            Instância atualizada ou None
        """
        instancia = self.buscar_por_uuid(uuid)
        if instancia:
            for key, value in kwargs.items():
                if hasattr(instancia, key):
                    setattr(instancia, key, value)
            self.session.flush()
        return instancia

    def desativar(self, uuid: str) -> bool:
        """
        Desativa um registro (soft delete)

        Args:
            uuid: UUID do registro

        Returns:
            True se desativado, False se não encontrado
        """
        instancia = self.buscar_por_uuid(uuid)
        if instancia and hasattr(instancia, 'ativo'):
            instancia.ativo = False
            self.session.flush()
            return True
        return False

    def deletar(self, uuid: str) -> bool:
        """
        Deleta permanentemente um registro (hard delete)

        Args:
            uuid: UUID do registro

        Returns:
            True se deletado, False se não encontrado
        """
        instancia = self.session.query(self.model_class).filter_by(uuid=uuid).first()
        if instancia:
            self.session.delete(instancia)
            self.session.flush()
            return True
        return False

    def contar(self, apenas_ativos: bool = True) -> int:
        """
        Conta registros

        Args:
            apenas_ativos: Se True, conta apenas registros ativos

        Returns:
            Número de registros
        """
        query = self.session.query(self.model_class)
        if apenas_ativos and hasattr(self.model_class, 'ativo'):
            query = query.filter_by(ativo=True)
        return query.count()

    def existe(self, uuid: str) -> bool:
        """
        Verifica se um registro existe

        Args:
            uuid: UUID do registro

        Returns:
            True se existe, False caso contrário
        """
        return self.session.query(self.model_class).filter_by(
            uuid=uuid
        ).count() > 0

    def commit(self):
        """Faz commit da sessão"""
        self.session.commit()

    def rollback(self):
        """Faz rollback da sessão"""
        self.session.rollback()
