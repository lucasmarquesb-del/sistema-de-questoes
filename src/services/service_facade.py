"""
Service Facade - Ponto único de acesso aos services com gerenciamento de sessão
"""
from contextlib import contextmanager
from src.database import session_manager
from .questao_service import QuestaoService
from .lista_service import ListaService
from .tag_service import TagService
from .alternativa_service import AlternativaService


class ServiceFacade:
    """
    Facade que fornece acesso fácil aos services com gerenciamento de sessão

    Usage:
        # Opção 1: Context manager (recomendado)
        with services.transaction() as svc:
            questao = svc.questao.criar_questao(...)
            svc.lista.adicionar_questao(...)
            # Commit automático

        # Opção 2: Acesso direto (cuidado com commit manual)
        questao = services.questao.criar_questao(...)
        services.commit()
    """

    def __init__(self):
        """Inicializa facade"""
        self._session = None
        self._questao_service = None
        self._lista_service = None
        self._tag_service = None
        self._alternativa_service = None

    def _ensure_session(self):
        """Garante que há uma sessão ativa"""
        if self._session is None:
            self._session = session_manager.create_session()
            self._questao_service = QuestaoService(self._session)
            self._lista_service = ListaService(self._session)
            self._tag_service = TagService(self._session)
            self._alternativa_service = AlternativaService(self._session)

    @property
    def questao(self) -> QuestaoService:
        """Retorna QuestaoService"""
        self._ensure_session()
        return self._questao_service

    @property
    def lista(self) -> ListaService:
        """Retorna ListaService"""
        self._ensure_session()
        return self._lista_service

    @property
    def tag(self) -> TagService:
        """Retorna TagService"""
        self._ensure_session()
        return self._tag_service

    @property
    def alternativa(self) -> AlternativaService:
        """Retorna AlternativaService"""
        self._ensure_session()
        return self._alternativa_service

    @contextmanager
    def transaction(self):
        """
        Context manager para transações com commit/rollback automático

        Usage:
            with services.transaction() as svc:
                svc.questao.criar_questao(...)
                svc.lista.adicionar_questao(...)
                # Commit automático ao sair

        Yields:
            Self (ServiceFacade)
        """
        self._ensure_session()
        try:
            yield self
            self.commit()
        except Exception:
            self.rollback()
            raise
        finally:
            self.close()

    def commit(self):
        """Faz commit da sessão"""
        if self._session:
            self._session.commit()

    def rollback(self):
        """Faz rollback da sessão"""
        if self._session:
            self._session.rollback()

    def close(self):
        """Fecha a sessão"""
        if self._session:
            self._session.close()
            self._session = None
            self._questao_service = None
            self._lista_service = None
            self._tag_service = None
            self._alternativa_service = None


# Instância global
services = ServiceFacade()
