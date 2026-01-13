"""
Gerenciador de Sessões do SQLAlchemy
"""
import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models.orm import Base


class SessionManager:
    """Gerenciador singleton de sessões do SQLAlchemy"""

    _instance = None
    _engine = None
    _session_factory = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Inicializa o gerenciador (apenas uma vez)"""
        if self._engine is None:
            self._initialize()

    def _initialize(self):
        """Inicializa engine e session factory"""
        # Determinar caminho do banco
        db_path = os.getenv('DATABASE_PATH', 'database/sistema_questoes_v2.db')

        # Criar engine
        self._engine = create_engine(
            f'sqlite:///{db_path}',
            echo=False,  # Mudar para True para debug
            pool_pre_ping=True,
            connect_args={'check_same_thread': False}
        )

        # Criar session factory
        self._session_factory = sessionmaker(
            bind=self._engine,
            autocommit=False,
            autoflush=False
        )

    @property
    def engine(self):
        """Retorna a engine"""
        return self._engine

    def create_session(self) -> Session:
        """
        Cria uma nova sessão

        Returns:
            Session do SQLAlchemy
        """
        return self._session_factory()

    @contextmanager
    def session_scope(self):
        """
        Context manager para sessões com commit/rollback automático

        Usage:
            with session_manager.session_scope() as session:
                # usar session aqui
                pass
        """
        session = self.create_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def create_all_tables(self):
        """Cria todas as tabelas no banco"""
        Base.metadata.create_all(self._engine)

    def drop_all_tables(self):
        """Remove todas as tabelas do banco (CUIDADO!)"""
        Base.metadata.drop_all(self._engine)


# Instância global
session_manager = SessionManager()
